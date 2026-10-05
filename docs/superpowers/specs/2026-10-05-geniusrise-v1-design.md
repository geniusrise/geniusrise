# Geniusrise v1 — Design Spec

Date: 2026-10-05 Status: Draft, pending user review

## 1. Purpose

Geniusrise v1 is an open source, turnkey system that lets an individual, a
community, a local ISP or a company run open LLM, speech-to-text (STT) and
text-to-speech (TTS) models on their own infrastructure. One person, typically a
standard IT generalist, does the whole job:

1. Write or click together one `deploy.yaml`: provider, region, budget, models
   and API keys.
2. Run `geniusrise apply`.
3. Get one OpenAI-compatible HTTPS endpoint that autoscales within the budget.

After that, maintenance means editing the list of models, keys and limits, then
applying again.

### Goals

- Support **LLM, STT and TTS only**.
- Pick the most efficient tested runtime for each model automatically.
- Keep the infrastructure footprint minimal: no Kubernetes, no new VPCs, no NAT
  gateways, no load balancers.
- Keep **zero customer data on any geniusrise-operated service.** There is no
  hosted backend.
- Ship one Go binary that acts as CLI, local GUI, gateway daemon and node agent.
- Keep maintenance low enough for a very small team.

### Non-goals (v1)

- Vision, image generation, embeddings, fine-tuning, training, batch jobs.
- Deployments that span more than one provider. Each deployment uses exactly one
  provider.
- Gateway high availability. The gateway is a single instance in v1.
- OIDC/SSO and a built-in end-user chat UI. Users bring their own
  OpenAI-compatible clients.
- Arbitrary Hugging Face models. Only models in the curated catalog can be
  deployed. A community can point the binary at its own catalog.
- Packing several models onto one GPU. One replica runs on one node.
- Weight caching or disk snapshots for faster cold starts (deferred to v2).
- Verifying image signatures on nodes (deferred to v2).

## 2. Repositories

| Repo                        | Role                                                                                                                            |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `geniusrise/geniusrise`     | The product: Go source for all modes, the embedded GUI, the catalog, engine image Dockerfiles, `install.sh`, CI, and this spec. |
| `geniusrise/geniusrise.com` | Landing page: static HTML and CSS on GitHub Pages, with no build step.                                                          |
| `geniusrise/docs`           | User and developer docs at `docs.geniusrise.com` (mkdocs-material on GitHub Pages).                                             |
| `geniusrise/.github`        | Org profile.                                                                                                                    |

All other org repos get archived (see §12).

## 3. Architecture

```
 laptop / admin box                     customer's cloud (one provider)
┌──────────────────────┐   HTTPS +    ┌──────────────────────────────────┐
│ geniusrise CLI / gui │──admin token─▶│ geniusrise gateway (tiny CPU VM) │
│  reads deploy.yaml   │              │  OpenAI API · keys · autoscaler  │
│  uses local creds    │              │  budget · reconciler · adapter   │
└──────────────────────┘              └────────┬─────────────────────────┘
        ▲                                      ▲ reverse tunnel (node dials out,
 end users (API keys) ─── HTTPS ───────────────┤  mTLS + yamux on :443)
                                     ┌─────────┴─────────┐ ┌───────────────┐
                                     │ GPU/CPU node      │ │ node ...      │
                                     │ geniusrise node   │ │               │
                                     │  └ vllm/llamacpp/ │ │               │
                                     │    speaches       │ │               │
                                     └───────────────────┘ └───────────────┘
```

### 3.1 Binary modes

| Mode                   | Runs on                                                       | Responsibility                                                                                                                       |
| ---------------------- | ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| `geniusrise <cmd>`     | admin machine                                                 | Plan, bootstrap, push config, status, destroy. Uses local cloud credentials (`~/.aws`, gcloud ADC, `az login`, env vars, SSH agent). |
| `geniusrise gui`       | admin machine                                                 | Local web UI on `127.0.0.1`. A thin layer over the same functions as the CLI. Reads and writes the YAML file on disk.                |
| `geniusrise gateway`   | small CPU VM in the customer's cloud, or a user-supplied host | Public OpenAI-compatible API, API key auth and limits, routing, autoscaling, budget enforcement, reconcile loop, provider calls.     |
| `geniusrise node`      | each replica (entrypoint of the engine image)                 | Supervises the engine, joins the gateway's tunnel, runs health and canary checks, reports metrics, watches for spot interruptions.   |
| `geniusrise host join` | each SSH/bare-metal host (systemd)                            | Host agent. Starts and stops engine containers on local GPUs when the gateway asks.                                                  |

### 3.2 Control flow

1. **First `apply`:** the CLI resolves the spec and plans it. It then calls
   `Provider.Bootstrap` with local credentials, which creates the gateway, its
   scoped role, firewall rules and IP. It pushes the resolved config to
   `PUT /admin/config` and writes `gateway.url` and `gateway.admin_token` back
   into `deploy.yaml`.
2. **Later `apply`:** the CLI pushes the config. The gateway diffs it against
   what's running and converges.
3. **The gateway reconcile loop**, every 15s:
   - compute the desired replicas for each model (autoscaler plus budget)
   - launch or terminate nodes through the provider adapter
   - terminate tagged orphans

## 4. `deploy.yaml` specification

- The file holds desired state plus the fields that `apply` writes back.
- Any string value may be plain text or `${ENV_VAR}`. The CLI resolves env vars
  locally before pushing.
- Unknown fields are a hard error. Secrets may be stored in plain text; the file
  belongs to the user.

```yaml
version: 1
name: acme-ai # deployment id; [a-z0-9-]{3,32}; used in names/tags

provider:
  type: aws # aws | gcp | azure | runpod | lambda | hyperbolic | ssh
  region: us-east-1 # not used for ssh
  capacity: spot-fallback # spot | on-demand | spot-fallback | serverless (runpod only)
  subnet: null # optional (aws/gcp/azure): use instead of default network
  credentials: null # optional; default = local SDK credential chain
  hosts: # ssh only
    - { addr: 10.0.0.5, user: ubuntu, gpus: 2, cost_hr: 0.30 }
    - { addr: 10.0.0.6, user: ubuntu, gpus: 1 }

budget:
  monthly_usd: 500 # hard cap; null = unlimited; ssh default null

alerts:
  webhook: https://ntfy.sh/acme-ai # optional; generic JSON POST

gateway:
  domain: ai.acme.com # optional; default <ip-dashed>.sslip.io
  host: null # optional ssh://user@host; required for lambda, hyperbolic
  url: https://ai.acme.com # written by apply
  admin_token: gr_admin_… # written by apply if absent (>=32 random bytes)

models:
  - id: llama-3.1-8b-instruct # must exist in catalog
    variant: awq # optional; must be a catalog variant
    replicas: { min: 0, max: 4 } # defaults: min 0, max 1
    idle_timeout: 15m # default 15m
  - id: whisper-large-v3-turbo
    replicas: { min: 1, max: 2 }
  - id: kokoro-82m

keys:
  - name: alice
    key: ${ALICE_KEY}
    models: ['*'] # default ["*"]
    limits: # all optional
      rpm: 60
      tokens_per_day: 200000
      stt_mb_per_day: 200
      tts_chars_per_day: 100000

secrets:
  hf_token: ${HF_TOKEN}
  # runpod_api_key, lambda_api_key, hyperbolic_api_key
```

Semantics:

- **Capacity modes:**
  - `on-demand` is what users call "dedicated". Reserved instances and dedicated
    hosts are not modelled.
  - `spot-fallback` tries spot first and falls back to on-demand.
- **Where the gateway is placed by default:**

  | Provider           | Gateway placement                                               |
  | ------------------ | --------------------------------------------------------------- |
  | aws, gcp, azure    | small VM in the same region                                     |
  | runpod             | CPU pod                                                         |
  | ssh                | first host                                                      |
  | lambda, hyperbolic | `gateway.host` is required (these clouds have no CPU instances) |

- **SSH pools are fixed.** `max` is bounded by the GPUs that physically exist.
  Spend is `cost_hr` × uptime (default 0).
- **API model names** are the catalog `id`.
- **Validation** runs in the CLI before any push, and again in the gateway when
  it receives a config.

## 5. Catalog

- `catalog/*.yaml` in the repo, one file per model, embedded at build time.
- `--catalog <path|url>` (a CLI flag, also stored in the gateway config)
  replaces the embedded catalog with a third-party one that uses the same schema
  and is validated the same way.

```yaml
id: llama-3.1-8b-instruct
type: llm # llm | stt | tts
license: llama3.1
gated: true # requires secrets.hf_token
default_variant: awq
variants:
  - name: awq
    engine: vllm # vllm | llamacpp | speaches
    hf_repo: hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4
    file: null # llamacpp: GGUF filename
    gpus: [L4, A10G, L40S] # tested classes, preference order
    args: [--max-model-len, '16384', --gpu-memory-utilization, '0.92']
    capacity: { concurrency: 32 } # autoscaler target per replica
    tested: { date: 2026-10-01, provider: aws, gpu: L4, engine_version: '0.x' }
```

- **GPU classes:** `cpu, T4, L4, A10G, L40S, A100-40, A100-80, H100, H200`.
- **Engines (v1):**

  | Engine     | Use                                                      | API                                            |
  | ---------- | -------------------------------------------------------- | ---------------------------------------------- |
  | `vllm`     | LLMs on GPU                                              | OpenAI chat/completions                        |
  | `llamacpp` | LLMs on CPU or small GPU                                 | OpenAI chat/completions                        |
  | `speaches` | STT (faster-whisper) and TTS (Kokoro, Piper); CPU or GPU | `/v1/audio/transcriptions`, `/v1/audio/speech` |

- **Images:**
  - Named `ghcr.io/geniusrise/<engine>:<upstream-ver>-gr<agent-ver>`.
  - Each one is the upstream image plus the `geniusrise` binary, with
    `geniusrise node` as the entrypoint.
  - Each release pins images by digest.
  - A weekly CI job rebuilds them on upstream releases. CI signs them with
    cosign.
- **Recipe PRs** must include `tested:`. CI validates the schema; GPU smoke
  tests are manual.

## 6. Pricing and planner

### 6.1 Price snapshot (no customer credentials)

- A daily GitHub Actions job (`tools/pricegen`) publishes `prices.json` as a
  release asset.
- It covers every provider × region × GPU class × capacity mode, giving
  `{instance_type, usd_hr, available}`.

| Provider           | Source                                                                     | Auth (CI secret) |
| ------------------ | -------------------------------------------------------------------------- | ---------------- |
| AWS on-demand      | Pricing API `GetProducts`                                                  | read-only IAM    |
| AWS spot           | `DescribeSpotPriceHistory`, min and median per region                      | read-only IAM    |
| GCP                | Cloud Billing Catalog. Machine shape price = GPU SKU + vCPU SKU + RAM SKU. | API key          |
| Azure              | Retail Prices API (includes spot)                                          | none             |
| RunPod             | GraphQL `gpuTypes` (secure, community, spot, stock)                        | API key          |
| Lambda, Hyperbolic | instance-types endpoints                                                   | API key          |
| SSH                | `hosts[].cost_hr`                                                          | —                |

- The binary embeds the snapshot from build time as a fallback.
- The CLI, GUI and gateway fetch the latest snapshot and cache it for 24h.

### 6.2 Live refinement (gateway)

At launch time the gateway:

- queries the live spot price in the target AZ, or RunPod stock
- picks the cheapest available offering from the planner's ranked list
- tags the instance with `geniusrise:price_hr`

### 6.3 Planner

The planner is a pure function: `Plan(spec, catalog, prices) → Plan`.

1. For each model:

   - pick the variant
   - list its tested GPU classes
   - drop classes the provider doesn't offer in the region
   - rank by price for the capacity mode

   For `spot-fallback`, spot offerings come first, then on-demand.

2. One replica = one node. For SSH, models are assigned to `(host, gpu_index)`.
   If they don't fit, that's an error.
3. Output, per model:
   - the ranked offerings
   - $/hr
   - $/month at min and at max replicas
   - the deployment total, which includes the gateway VM, disk and IP
4. If the cost at **min** replicas exceeds the budget, planning fails with an
   error. If the cost at **max** exceeds it, planning succeeds with a warning
   that the cap will bind.
5. `geniusrise plan --compare` runs the planner for every provider and prints a
   table. This works without any cloud account.

## 7. Gateway

### 7.1 Endpoints

| Path                                                | Auth                  | Purpose                                                     |
| --------------------------------------------------- | --------------------- | ----------------------------------------------------------- |
| `POST /v1/chat/completions`, `POST /v1/completions` | API key               | LLM, streaming SSE supported                                |
| `POST /v1/audio/transcriptions`                     | API key               | STT                                                         |
| `POST /v1/audio/speech`                             | API key               | TTS                                                         |
| `GET /v1/models`                                    | API key               | the models this key may use                                 |
| `GET/PUT /admin/config`                             | admin token           | last-applied YAML (secrets resolved)                        |
| `GET /admin/status`                                 | admin token           | pools, nodes, spend, alerts (JSON; SSE variant for the GUI) |
| `GET /admin/usage`                                  | admin token           | per-key usage for the current day and month                 |
| `GET /admin/logs?node=`                             | admin token           | last 1000 engine log lines                                  |
| `POST /admin/nodes/{id}/restart`                    | admin token           | restart a node's engine                                     |
| `GET /metrics`                                      | admin token           | Prometheus                                                  |
| `/node/join`, `/node/connect`                       | join token, then mTLS | node registration and reverse tunnel                        |

- **TLS:** handled by `certmagic` using TLS-ALPN-01 on port 443 only. The
  hostname is `gateway.domain` or `<ip-dashed>.sslip.io`. On RunPod, the RunPod
  proxy terminates TLS.

### 7.2 Auth, limits and privacy

- **API keys:**
  - Held in memory as SHA-256 hashes.
  - Compared in constant time.
  - Failed auth is rate-limited per source IP.
- **Limits:**
  - `rpm` is a token bucket.
  - `tokens_per_day` counts from the engine's `usage` field. For streaming, the
    gateway injects `stream_options.include_usage=true` and reads the final
    chunk.
  - `stt_mb_per_day` is measured from the request body size.
  - `tts_chars_per_day` is the length of the `input` field.
  - Days are UTC.
- **Privacy:** prompts, completions and audio are never logged or stored. The
  request log is a metadata-only ring buffer: time, key name, model, tokens,
  bytes, latency and status.
- **Request size limits:** 25 MB for audio and 2 MB for JSON.
- **Timeouts:** 10 minutes per request, 60s idle for streaming. These are fixed
  in v1, with no YAML field.

### 7.3 Routing

- Requests go to the ready node with the fewest outstanding requests in the
  model's pool.
- **When there are no ready nodes:**
  1. Trigger a scale-up.
  2. Hold the request up to `cold_wait` (fixed at 20s in v1).
  3. If still none, return `503` with `Retry-After` set to the estimated time
     until a replica is ready.
- **Retries:** if a node fails before sending any response bytes, the request is
  retried once on another node.

### 7.4 Autoscaler (per model, every 15s)

```
desired = clamp(ceil(avg_inflight_1m / (concurrency * 0.7)), min, max)
```

- Nodes that are launching count toward capacity.
- Scale-up happens immediately. Scale-down happens after 5 minutes below target.
- Scale to zero happens after `idle_timeout` with no requests.
- The budget state (§7.5) can override `desired` downward.

### 7.5 Budget (calendar month, UTC)

- `spend` = Σ over nodes (uptime × `price_hr` tag) + gateway VM + disks + IPs.
- It's an estimate. Egress and minor charges are excluded, and the docs say so.

| Spend / budget | Action                                                                                            |
| -------------- | ------------------------------------------------------------------------------------------------- |
| ≥ 80%          | alert (webhook)                                                                                   |
| ≥ 90%          | **freeze**: no scale-ups; scale-down continues                                                    |
| ≥ 95%          | **cap**: every model's desired = 0; alert; lasts until the month rolls over or `budget` is raised |

The gateway VM stays up when the cap trips.

### 7.6 Spot interruptions

- The node agent watches the provider's interruption signal:
  - AWS: the 2-minute instance-action notice
  - GCP: preemption metadata
  - Azure: Scheduled Events
- **On a notice:**
  - The node stops taking new requests and lets in-flight requests finish.
  - The gateway launches a replacement, using the next offering in the ranked
    list. With `spot-fallback` that can be on-demand.

### 7.7 Self-healing

| Layer                         | Detects                                                                                                                  | Action                                                                                                            |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------- |
| node agent → engine           | process exit; `/health` failing; canary inference (1 token, or 1s of audio/text) failing or exceeding timeout, every 60s | restart the engine with exponential backoff; after 3 failures in 10 minutes, report `unhealthy`                   |
| gateway → node                | 3 missed heartbeats (5s interval); `unhealthy` reported; >50% 5xx over 1 minute                                          | stop routing, terminate, launch a replacement                                                                     |
| gateway reconciler → provider | instances tagged with the deployment but not in the registry                                                             | terminate                                                                                                         |
| systemd / provider → gateway  | gateway process crash; VM failure                                                                                        | `Restart=always`; provider auto-recovery enabled                                                                  |
| CLI → gateway                 | gateway unreachable                                                                                                      | `geniusrise status` reports it; `apply --recreate-gateway` rebuilds it from YAML + tags + the persisted data disk |

### 7.8 Persistence

- The gateway data directory sits on a small persistent disk:
  - `config.yaml`, the last-applied config
  - `state.json`, written atomically every 30s with the spend ledger, usage
    counters and node registry
  - `ca/`, the per-deployment CA used for node mTLS
- No database.

## 8. Node agent and images

### 8.1 Lifecycle

1. **Boot.**
   - The node receives `GR_GATEWAY`, `GR_JOIN_TOKEN`, `GR_CA_FINGERPRINT`,
     `GR_MODEL`, `GR_VARIANT` and `HF_TOKEN`, through cloud-init, container env
     vars or the host agent.
   - The join token is single-use and valid for 30 minutes.
2. **Join.**
   - The agent pins the gateway certificate by fingerprint and sends a CSR plus
     the join token to `/node/join`.
   - It receives a client certificate signed by the deployment CA.
3. **Tunnel.**
   - The agent dials `/node/connect` with mTLS and runs yamux.
   - The gateway opens streams to the node over this session. Nodes listen on no
     ports.
4. **Engine.**
   - The agent starts the engine as a child process bound to `127.0.0.1`. The
     engine downloads weights from Hugging Face itself.
   - The node registers `ready` once the engine's `/health` passes and a canary
     succeeds.
5. **Run.**
   - The agent proxies streams and reports in-flight requests and queue depth
     (from vLLM `/metrics`, or counted by the agent for the other engines).
   - It also runs the canary and the spot watcher, and keeps a ring buffer of
     logs.

### 8.2 How each provider boots a node

- **VM providers:**

  - Use a stock GPU base image that ships the NVIDIA driver, Docker and
    nvidia-container-toolkit:

    | Provider | Base image                                |
    | -------- | ----------------------------------------- |
    | AWS      | DLAMI Base (ID from public SSM parameter) |
    | GCP      | Deep Learning VM                          |
    | Azure    | Ubuntu HPC/DSVM                           |
    | Lambda   | Lambda Stack                              |

  - cloud-init runs
    `docker run --gpus all --restart=always --read-only --tmpfs … -e … <image>@<digest>`.
  - CPU variants use plain Ubuntu, and cloud-init installs Docker.

- **RunPod pods:** the image runs directly with env vars.
- **RunPod serverless:** the image runs as a load-balancing endpoint worker in
  "direct" mode. The agent serves HTTP with a shared secret instead of using the
  tunnel. RunPod does the scaling. The gateway sets workers min/max and sets
  max=0 when the cap trips. This is the only exception to the tunnel model.
- **SSH hosts:**
  - `geniusrise host join <gateway> <token>` installs a systemd host agent.
    `apply` runs this over SSH, or the user runs it by hand.
  - The host agent dials the gateway and runs one engine container per GPU
    (`--gpus device=N`).
  - After join, the gateway needs no SSH access.
  - `geniusrise doctor ssh://host` checks the driver, Docker and toolkit.

### 8.3 Security baseline

- **GPU nodes:**
  - no inbound firewall rules
  - no SSH keypair (where the provider allows it)
  - no cloud IAM role
  - IMDSv2 required on AWS
  - unprivileged containers with a read-only root filesystem except the cache
    directory
  - outbound access only
- **Gateway VM:**
  - inbound 443 only, with no SSH
  - a cloud role scoped by deployment tag or name prefix to launch, terminate
    and describe instances, plus read access to pricing
- **Images:** pinned by digest and signed in CI.

## 9. Provider adapters

```go
type Provider interface {
    Bootstrap(ctx context.Context, d DeploymentSpec) (Gateway, error)
    Offerings(ctx context.Context, region string) ([]Offering, error)
    Launch(ctx context.Context, n NodeSpec) (NodeID, error)
    List(ctx context.Context, deployment string) ([]Node, error)
    Terminate(ctx context.Context, id NodeID) error
    Destroy(ctx context.Context, deployment string) error
}
```

- **Callers:** the CLI calls `Bootstrap` and `Destroy` with local credentials.
  The gateway calls the rest with its instance role or stored API key.
- **Idempotency:** every create is get-or-create by name `gr-<deployment>-*` or
  by tag `geniusrise:deployment`.
- **Ownership:** `Destroy` and orphan cleanup only touch resources carrying our
  tag or name prefix.

| Provider           | Phase         | Resources created                                                                                                                                                                                                                                                                                                                                                |
| ------------------ | ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| fake               | P1            | in-memory (tests)                                                                                                                                                                                                                                                                                                                                                |
| ssh                | P1            | none (host agents only)                                                                                                                                                                                                                                                                                                                                          |
| aws                | P1            | in the default VPC (or `subnet`), no NAT:<br>• 2 SGs (gateway: 443 in; nodes: none)<br>• IAM role + instance profile (gateway only)<br>• Elastic IP<br>• `t4g.micro` gateway + 1 GB gp3 data volume<br>About $11/month floor.                                                                                                                                    |
| gcp                | P2            | • firewall rule allowing 443 to tag `gr-gw`<br>• **deny-all inbound** rule to `gr-node` at priority 100 (overrides the default network's SSH/RDP rules)<br>• gateway service account with IAM conditions on the name prefix<br>• static IP<br>• `e2-micro` gateway<br>Spot via `provisioningModel: SPOT`.                                                        |
| azure              | P2            | resource group `gr-<name>` containing:<br>• vnet, 2 NSGs<br>• gateway public IP<br>• `B1s` gateway with a managed identity that is Contributor on that resource group only<br>Each node gets a public IP with a deny-all-inbound NSG, because Azure is retiring default outbound access. Spot priority with eviction=Delete. Destroy deletes the resource group. |
| runpod             | P3            | gateway CPU pod; GPU pods (secure cloud by default; community cloud opt-in with a warning); serverless load-balancing endpoints                                                                                                                                                                                                                                  |
| lambda, hyperbolic | P3            | GPU instances only. **Risk:** account-wide firewall rules and required SSH keys limit how far nodes can be locked down. Verify the API in P3 and document the residual exposure.                                                                                                                                                                                 |
| modal              | P4 or dropped | Needs the `modal` CLI (Python) because Modal has no public REST deploy API. Re-check this before P4.                                                                                                                                                                                                                                                             |

## 10. CLI and GUI

### 10.1 CLI

```
geniusrise init                      # wizard → deploy.yaml
geniusrise catalog [query]
geniusrise plan [-f file] [--compare]
geniusrise apply [-f file] [--recreate-gateway]
geniusrise status [-f file]
geniusrise logs <model|node> [-f file]
geniusrise destroy [-f file]
geniusrise key new
geniusrise doctor [-f file | ssh://host]
geniusrise gui [-f file]
geniusrise upgrade
geniusrise gateway | node | host join   # daemon modes
```

- **`-f` default:** `./deploy.yaml`.
- **`doctor` checks:**
  - credentials
  - GPU quotas, including what to file for an increase (AWS Service Quotas G/VT
    on-demand and spot vCPUs, GCP regional GPU quota, Azure family vCPU quota)
  - default network present
  - SSH host readiness
- **Upgrades:**
  - `apply` notices when the gateway's version doesn't match the CLI's. The
    gateway then downloads the matching release binary, checks its checksum and
    restarts.
  - When an image digest changes, nodes are replaced one at a time (start new,
    drain old).

### 10.2 GUI

- **Tech:** Go `html/template` + htmx + Pico.css, vendored and embedded with
  `go:embed`. No npm or build step. Live status uses SSE.
- **Security:**
  - binds to `127.0.0.1` on a random free port
  - the URL carries a random session token
  - a Host header check blocks DNS rebinding
- **Screens:**

  1. **Deployment:** open or create a file.
  2. **Models:** catalog browser; add a model; set min/max/idle.
  3. **Provider & budget:** provider, region, capacity, budget, alerts; cost
     comparison table across providers.
  4. **Keys:** add, generate and remove keys; set limits.
  5. **Plan & apply:** diff, monthly cost range, Apply with streamed progress.
  6. **Status:** pools, nodes, spend vs budget, alerts, logs.

  Every screen has a YAML tab that edits in both directions. The file on disk is
  always the source of truth.

## 11. Code layout, error handling, testing

### 11.1 Layout

```
cmd/geniusrise/          entrypoint, mode dispatch
internal/spec            types, strict parse, env resolution, validation
internal/catalog         recipe types, embedded loader
internal/pricing         snapshot types, fetch + cache
internal/planner         pure planning
internal/gateway         api, auth, limits, router, autoscaler, budget, reconciler, state
internal/tunnel          join/CSR, mTLS, yamux
internal/node            engine supervisor, canary, metrics, spot watcher
internal/hostagent       ssh host mode
internal/provider        interface; fake, ssh, aws, gcp, azure, runpod, lambda, hyperbolic
internal/gui             handlers, templates, static
internal/cli             commands
catalog/                 *.yaml
images/<engine>/         Dockerfile
tools/pricegen/          price snapshot generator
install.sh
.github/workflows/       ci, release (goreleaser), images (weekly), prices (daily)
```

Dependencies:

- aws-sdk-go-v2, GCP compute client, Azure arm\* SDKs
- yaml.v3, certmagic, hashicorp/yamux, cobra
- RunPod, Lambda and Hyperbolic through `net/http`

### 11.2 Error handling

- **`apply` is idempotent.** After a partial failure, run it again.
- **Quota or permission errors** are detected before any resources are created
  (in `doctor` and in the pre-flight step of `apply`). They're reported with
  remediation steps.
- **Capacity errors:** move to the next ranked offering with exponential
  backoff, and alert after 3 consecutive failures for a model.
- **Invalid config pushed to the gateway:** rejected with field-level errors.
  The gateway keeps the previous config.
- **Bootstrap failure:** the error names the resources created so far. Running
  `apply` again resumes; `destroy` removes them.

### 11.3 Testing

- **Unit tests:**
  - spec validation with golden files
  - planner table tests against a fixed `prices.json`
  - autoscaler and budget on a simulated clock, including month rollover
  - limits and usage accounting
- **In-process integration tests**, run on every PR: the gateway with the fake
  provider and a fake engine (OpenAI chat with streaming, plus audio).
  Scenarios:
  - scale up from zero, then stream
  - canary-detected hang leads to replacement
  - spot interruption with fallback to on-demand
  - orphan cleanup
  - budget at 80/90/95%
  - invalid config rejected
  - key limits enforced
  - gateway restart restores `state.json`
- **Provider contract suite:** a single shared suite.
  - In CI it runs against the fake provider.
  - Against real clouds it runs through `make e2e PROVIDER=<p>`: opt-in or
    nightly, in a budget-capped test account, using `cpu` variants (a tiny GGUF
    model on llama.cpp).
- **Catalog:** CI validates the schema; the `tested:` block is required.

## 12. Migration and cleanup

0. **The owner rotates the leaked credentials (blocking).**
   - The public `geniusrise.com` repo tracks a `.env` file containing AWS keys.
   - The public `docs` repo has AWS keys in its history.
   - Local `deploy.md` and `genius.yml` contain AWS keys, an HF token and an
     Azure Postgres password.
1. **`geniusrise`:**
   - Push the local uncommitted plugin-split refactor to branch
     `archive/plugin-split-2025`.
   - Reset local master to `origin/master`.
   - Tag `v0.2.0-python-final`.
   - Replace the Python code with the Go layout above on master.
2. **`geniusrise.com`:**
   - Fast-forward to origin and tag `v1-cra-final`.
   - Replace with a static landing page on GitHub Pages and remove `.env`.
3. **`docs`:**
   - Tag `v1-final`.
   - Rewrite the content (user guide, provider guides, catalog contribution,
     architecture) and serve it at `docs.geniusrise.com`.
4. **Archive on GitHub:**
   `healthcare, torch-ocaml, esp32, biology, helm-charts, examples, databases, listeners, geniusrise-util, geniusrise-cloud, kubernetes, pytorch-llm-algebra, Diffusion-Pullback, geniusrise-ocr, geniusrise-prompt-actions, transformers-memory, geniusrise.ai, geniusrise-openai, geniusrise-indexing, geniusrise-exit-proxy`.
   - Already archived: `vision, text, audio, geniusrise-huggingface`.
   - Not touched: `geniusrise.health`, `awesome-healthcare-datasets`.
5. **Local folder:** move everything except `geniusrise/`, `geniusrise.com/` and
   `geniusrise-docs/` into `_archive/`. Nothing is deleted.

## 13. Phasing

| Phase | Scope                                                                                                                                                                                         | Done when                                                                                                                                     |
| ----- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| P0    | Cleanup (§12)                                                                                                                                                                                 | archive done, repos tagged, credentials rotated                                                                                               |
| P1    | spec, catalog (5–8 recipes: 2–3 LLMs, whisper, kokoro, piper), pricing, planner, gateway, tunnel, node agent, 3 engine images, CLI, GUI, providers `fake` + `ssh` + `aws`, landing page, docs | an IT generalist goes from a blank AWS account to a working OpenAI endpoint with LLM + STT + TTS in under 30 minutes, following only the docs |
| P2    | `gcp`, `azure`                                                                                                                                                                                | contract suite passes on both                                                                                                                 |
| P3    | `runpod` (pods + serverless), `lambda`, `hyperbolic`                                                                                                                                          | contract suite passes; residual security risks documented                                                                                     |
| P4    | `modal` or drop                                                                                                                                                                               | decision recorded                                                                                                                             |

## 14. Risks

- **GPU quota friction** on new hyperscaler accounts. Mitigated by `doctor` and
  clear docs, but it can't be removed.
- **Spend is estimated**, so real invoices will differ somewhat. Enforcing at
  95% and documenting this is the mitigation.
- **sslip.io + Let's Encrypt** depends on a third-party DNS service. A real
  domain is recommended for production.
- **Upstream engine churn** (vLLM, speaches flags). Mitigated by pinned digests,
  the `tested:` block in recipes and weekly rebuilds.
- **A single gateway** is a single point of failure. Recovery takes about a
  minute through systemd and provider auto-recovery, and `--recreate-gateway`
  covers the rest.
- **Lambda/Hyperbolic network controls** may be weaker than the baseline (§9).
