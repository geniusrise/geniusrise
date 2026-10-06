# geniusrise

**Run open LLM, STT and TTS models on your own infrastructure, in the simplest way possible.**

One binary. One yaml file. One OpenAI-compatible endpoint that autoscales inside your budget.

```bash
curl -fsSL https://geniusrise.com/install.sh | sh
geniusrise init
geniusrise plan
geniusrise apply
```

That gives you:

- an HTTPS endpoint that speaks the OpenAI API (`/v1/chat/completions`, `/v1/audio/transcriptions`, `/v1/audio/speech`)
- tested, optimized runtimes per model (vLLM, llama.cpp, speaches)
- autoscaling with scale-to-zero and a hard monthly budget cap
- API keys with per-key rate and usage limits
- nodes with **zero inbound ports** — they dial the gateway over mTLS, so it works behind NAT and firewalls too

## What it looks like

```yaml
version: 1
name: acme-ai
provider:
  type: aws            # aws | gcp | azure | runpod | lambda | hyperbolic | ssh
  region: us-east-1
  capacity: spot-fallback
budget:
  monthly_usd: 500     # hard cap: alert at 80%, freeze at 90%, scale to zero at 95%
models:
  - id: llama-3.1-8b-instruct
    variant: awq
    replicas: {min: 0, max: 4}
  - id: whisper-large-v3-turbo
  - id: kokoro-82m
keys:
  - name: alice
    key: ${ALICE_KEY}
    limits: {rpm: 60, tokens_per_day: 200000}
```

`deploy.yaml` is the only state you own. Maintenance = edit the model list and limits, then `geniusrise apply` again.

## Architecture

```
 you                        your cloud
┌────────────────┐          ┌──────────────────────────────┐
│ geniusrise cli │─admin───▶│ geniusrise gateway (tiny vm) │◀── users (api keys)
│ geniusrise gui │          │  keys · autoscaler · budget  │
└────────────────┘          └──────────────▲───────────────┘
                                           │ reverse tunnel (mTLS, nodes dial out)
                              ┌────────────┴────────────┐
                              │ gpu nodes: vllm /       │
                              │ llama.cpp / speaches    │
                              └─────────────────────────┘
```

- **No kubernetes, no vpcs, no nat gateways, no load balancers.** AWS footprint: 2 security groups, 1 scoped IAM role, 1 elastic IP, 1 `t4g.micro` gateway. About $11/month floor.
- **No hosted backend.** Your cloud credentials never leave your machine (bootstrap) and your own cloud (operation). Nothing about you is stored by geniusrise.
- **Curated catalog.** Only tested model recipes ship by default; communities can point `--catalog` at their own.

## Commands

```
geniusrise init        create deploy.yaml
geniusrise catalog     list curated models
geniusrise plan        placement + $/month (--compare across providers)
geniusrise apply       bootstrap gateway + push config
geniusrise status      pools, nodes, spend vs budget
geniusrise destroy     remove everything we created
geniusrise doctor      credentials, quotas, ssh host readiness
geniusrise gui         local web ui on 127.0.0.1
geniusrise gateway     daemon mode (in your cloud)
geniusrise node        daemon mode (engine image entrypoint)
geniusrise host join   daemon mode (ssh/bare-metal host)
```

## Providers

| phase | provider | notes |
|---|---|---|
| P1 | aws, ssh (bare metal / homelab / isp), fake (tests) | default vpc only; ssh pools run docker per gpu |
| P2 | gcp, azure | same minimal pattern |
| P3 | runpod (pods + serverless), lambda, hyperbolic | gpu-only clouds need `gateway.host` |
| P4 | modal | pending a REST deploy API |

Prices come from a [daily published snapshot](https://github.com/geniusrise/geniusrise/releases/tag/prices), refined live at launch time, so `plan --compare` works before you have a cloud account.

## Development

```
make test    # unit + in-process integration (gateway + fake provider + fake engine)
make vet
make e2e PROVIDER=aws    # opt-in real-cloud contract tests
```

Docs: [docs.geniusrise.com](https://docs.geniusrise.com) · Design spec: `docs/superpowers/specs/`.

License: Apache-2.0
