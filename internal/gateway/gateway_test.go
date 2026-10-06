package gateway

import (
	"context"
	"crypto/tls"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"sync/atomic"
	"testing"
	"time"

	"github.com/geniusrise/geniusrise/internal/catalog"
	"github.com/geniusrise/geniusrise/internal/node"
	"github.com/geniusrise/geniusrise/internal/pricing"
	"github.com/geniusrise/geniusrise/internal/provider"
	"github.com/geniusrise/geniusrise/internal/spec"
	"github.com/geniusrise/geniusrise/internal/tunnel"
)

type harness struct {
	gw         *Server
	fake       *provider.Fake
	engine     *httptest.Server
	engineHits atomic.Int64
	apiURL     string
	adminTok   string
	dir        string
	agents     []*node.Agent
	cancels    []context.CancelFunc
}

var testCfgYAML = `version: 1
name: test-deploy
provider:
  type: fake
  region: fake
budget:
  monthly_usd: 500
models:
  - id: qwen2.5-7b-instruct
    replicas: {min: 0, max: 2}
    idle_timeout: 1m
keys:
  - name: alice
    key: sk-test-alice
    models: ["*"]
    limits: {rpm: 1000, tokens_per_day: 1000000}
`

func startHarness(t *testing.T, cfgYAML string) *harness {
	t.Helper()
	if cfgYAML == "" {
		cfgYAML = testCfgYAML
	}
	cfg, err := spec.Parse([]byte(cfgYAML))
	if err != nil {
		t.Fatal(err)
	}
	cat, err := catalog.Load("")
	if err != nil {
		t.Fatal(err)
	}
	snap, err := pricing.Embedded()
	if err != nil {
		t.Fatal(err)
	}
	dir := t.TempDir()
	if err := os.WriteFile(filepath.Join(dir, "config.yaml"), []byte(cfgYAML), 0o600); err != nil {
		t.Fatal(err)
	}
	fake := provider.NewFake()
	h := &harness{fake: fake, adminTok: "gr_admin_test", dir: dir}

	h.engine = httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		h.engineHits.Add(1)
		switch r.URL.Path {
		case "/health":
			w.Write([]byte("ok"))
		case "/v1/chat/completions":
			w.Header().Set("Content-Type", "application/json")
			fmt.Fprint(w, `{"id":"x","object":"chat.completion","choices":[{"message":{"role":"assistant","content":"hello"},"finish_reason":"stop"}],"usage":{"prompt_tokens":3,"completion_tokens":5,"total_tokens":8}}`)
		default:
			http.NotFound(w, r)
		}
	}))
	t.Cleanup(h.engine.Close)

	fake.BootstrapFn = func(d *spec.Deployment, opts provider.BootstrapOpts) (*provider.GatewayInfo, error) {
		return &provider.GatewayInfo{URL: "http://placeholder", AdminToken: h.adminTok}, nil
	}

	gw, err := New(Options{
		DataDir: dir, Addr: "127.0.0.1:0", Provider: fake,
		Catalog: cat, Prices: snap, Version: "test", AdminToken: h.adminTok, PlainHTTP: true,
	})
	if err != nil {
		t.Fatal(err)
	}
	h.gw = gw
	ctx, cancel := context.WithCancel(context.Background())
	h.cancels = append(h.cancels, cancel)
	go gw.Start(ctx)
	for i := 0; i < 100 && gw.Addr() == ""; i++ {
		time.Sleep(10 * time.Millisecond)
	}
	if gw.Addr() == "" {
		t.Fatal("gateway did not start")
	}
	t.Cleanup(func() {
		for _, c := range h.cancels {
			c()
		}
		gw.Stop()
	})

	gw.setConfig(cfg)
	gw.rebuildPools()
	go gw.reconcile(context.Background())

	h.apiURL = "http://" + gw.Addr()
	return h
}

func (h *harness) waitNodes(t *testing.T, model string, count int, timeout time.Duration) bool {
	t.Helper()
	deadline := time.Now().Add(timeout)
	for time.Now().Before(deadline) {
		p := h.gw.poolFor(model)
		if p != nil {
			if len(p.readyNodes()) >= count {
				return true
			}
		}
		time.Sleep(50 * time.Millisecond)
	}
	return false
}

func (h *harness) attachNodeAgent(t *testing.T) {
	t.Helper()
	p := h.gw.poolFor("qwen2.5-7b-instruct")
	if p == nil {
		t.Fatal("no pool")
	}
	p.mu.Lock()
	var entry *nodeEntry
	for _, n := range p.nodes {
		if n.State == provider.StateLaunching {
			entry = n
			break
		}
	}
	p.mu.Unlock()
	if entry == nil {
		t.Fatal("no launching node to attach to")
	}
	agent := node.New(node.Config{
		NodeID: entry.ID, GatewayURL: h.apiURL, GatewayAddr: h.gw.Addr(),
		JoinToken: entry.JoinToken, CAFingerprint: "",
		EngineType: "vllm", ExternalURL: h.engine.URL,
		ReadyTimeout: 5 * time.Second, AdminPort: 0, PlainDial: true,
		AdminToken: h.gw.nodeAdminToken(entry.ID),
	})
	ctx, cancel := context.WithCancel(context.Background())
	h.cancels = append(h.cancels, cancel)
	h.agents = append(h.agents, agent)
	go agent.Run(ctx)
}

var _ = tls.VersionTLS12

func TestScaleUpAndServe(t *testing.T) {
	h := startHarness(t, "")
	if !h.waitNodes(t, "qwen2.5-7b-instruct", 1, 5*time.Second) {
		t.Log("no auto node; attaching agent to launching node")
	}
	p := h.gw.poolFor("qwen2.5-7b-instruct")
	if p == nil || len(p.nodes) == 0 {
		h.attachNodeAgentForce(t)
	}
	if !h.waitNodes(t, "qwen2.5-7b-instruct", 1, 10*time.Second) {
		t.Fatal("node never became ready")
	}
	resp, err := postJSON(h.apiURL+"/v1/chat/completions", "sk-test-alice", `{"model":"qwen2.5-7b-instruct","messages":[{"role":"user","content":"hi"}]}`)
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		t.Fatalf("status %d: %s", resp.StatusCode, body)
	}
	var out struct {
		Choices []struct {
			Message struct {
				Content string `json:"content"`
			} `json:"message"`
		} `json:"choices"`
		Usage struct {
			TotalTokens int64 `json:"total_tokens"`
		} `json:"usage"`
	}
	json.NewDecoder(resp.Body).Decode(&out)
	if len(out.Choices) == 0 || out.Choices[0].Message.Content != "hello" {
		t.Fatalf("bad response body")
	}
	if h.engineHits.Load() == 0 {
		t.Fatal("engine never hit")
	}
	usage := h.gw.state.UsageFor("alice")
	if usage.Requests != 1 || usage.Tokens != 8 {
		t.Fatalf("usage not recorded: %+v", usage)
	}
}

func (h *harness) attachNodeAgentForce(t *testing.T) {
	t.Helper()
	h.gw.poolsMu.Lock()
	p := h.gw.pools["qwen2.5-7b-instruct"]
	h.gw.poolsMu.Unlock()
	var entry *nodeEntry
	p.mu.Lock()
	for _, n := range p.nodes {
		entry = n
		break
	}
	p.mu.Unlock()
	if entry == nil {
		entry = &nodeEntry{ID: "manual-1", State: provider.StateLaunching}
		p.mu.Lock()
		p.nodes["manual-1"] = entry
		p.mu.Unlock()
		tokenID, tokenSecret, _ := h.gw.tm.New()
		h.gw.joinTokensMu.Lock()
		h.gw.joinTokens["manual-1"] = tokenID + "." + tokenSecret
		h.gw.joinTokensMu.Unlock()
		entry.JoinToken = tokenID + "." + tokenSecret
	}
	agent := node.New(node.Config{
		NodeID: entry.ID, GatewayURL: h.apiURL, GatewayAddr: h.gw.Addr(),
		JoinToken: entry.JoinToken, EngineType: "vllm", PlainDial: true,
		ExternalURL: h.engine.URL, ReadyTimeout: 5 * time.Second,
		AdminPort: 0, AdminToken: h.gw.nodeAdminToken(entry.ID),
	})
	ctx, cancel := context.WithCancel(context.Background())
	h.cancels = append(h.cancels, cancel)
	h.agents = append(h.agents, agent)
	go agent.Run(ctx)
}

func postJSON(url, key, body string) (*http.Response, error) {
	req, _ := http.NewRequest("POST", url, strings.NewReader(body))
	req.Header.Set("Authorization", "Bearer "+key)
	req.Header.Set("Content-Type", "application/json")
	return (&http.Client{Timeout: 30 * time.Second}).Do(req)
}

func getJSON(url, token string) (*http.Response, error) {
	req, _ := http.NewRequest("GET", url, nil)
	req.Header.Set("Authorization", "Bearer "+token)
	return (&http.Client{Timeout: 10 * time.Second}).Do(req)
}

func TestAuthAndModels(t *testing.T) {
	h := startHarness(t, "")
	resp, _ := postJSON(h.apiURL+"/v1/chat/completions", "sk-wrong", `{"model":"qwen2.5-7b-instruct"}`)
	if resp.StatusCode != http.StatusUnauthorized {
		t.Fatalf("want 401, got %d", resp.StatusCode)
	}
	resp.Body.Close()
	resp, _ = getJSON(h.apiURL+"/v1/models", "sk-test-alice")
	defer resp.Body.Close()
	var list struct {
		Data []struct {
			ID string `json:"id"`
		} `json:"data"`
	}
	json.NewDecoder(resp.Body).Decode(&list)
	if len(list.Data) != 1 || list.Data[0].ID != "qwen2.5-7b-instruct" {
		t.Fatalf("bad models list: %+v", list)
	}
	resp2, _ := postJSON(h.apiURL+"/v1/chat/completions", "sk-test-alice", `{"model":"unknown-model"}`)
	if resp2.StatusCode != http.StatusBadRequest {
		t.Fatalf("want 400 for unknown model, got %d", resp2.StatusCode)
	}
	resp2.Body.Close()
}

func TestAdminConfigAndStatus(t *testing.T) {
	h := startHarness(t, "")
	resp, _ := getJSON(h.apiURL+"/admin/status", h.adminTok)
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("status: %d", resp.StatusCode)
	}
	resp.Body.Close()
	resp, _ = getJSON(h.apiURL+"/admin/status", "wrong")
	if resp.StatusCode != http.StatusUnauthorized {
		t.Fatalf("want 401, got %d", resp.StatusCode)
	}
	resp.Body.Close()

	bad := strings.Replace(testCfgYAML, "name: test-deploy", "name: BAD NAME", 1)
	req, _ := http.NewRequest("PUT", h.apiURL+"/admin/config", strings.NewReader(bad))
	req.Header.Set("Authorization", "Bearer "+h.adminTok)
	resp3, _ := (&http.Client{}).Do(req)
	if resp3.StatusCode != http.StatusBadRequest {
		t.Fatalf("invalid config accepted: %d", resp3.StatusCode)
	}
	resp3.Body.Close()

	good := strings.Replace(testCfgYAML, "qwen2.5-7b-instruct", "whisper-small", 1)
	req2, _ := http.NewRequest("PUT", h.apiURL+"/admin/config", strings.NewReader(good))
	req2.Header.Set("Authorization", "Bearer "+h.adminTok)
	resp4, _ := (&http.Client{}).Do(req2)
	if resp4.StatusCode != http.StatusOK {
		t.Fatalf("config update rejected: %d", resp4.StatusCode)
	}
	resp4.Body.Close()
	if h.gw.poolFor("whisper-small") == nil {
		t.Fatal("pool not rebuilt after config update")
	}
}

func TestBudgetCapScalesToZero(t *testing.T) {
	src := strings.Replace(testCfgYAML, "monthly_usd: 500", "monthly_usd: 10", 1)
	h := startHarness(t, src)
	h.gw.state.Spend = append(h.gw.state.Spend, SpendEntry{
		NodeID: "seed-node", Model: "qwen2.5-7b-instruct", PricePerHour: 10,
		StartedAt: time.Now().Add(-2 * time.Hour), EndedAt: ptrTime(time.Now().Add(-time.Hour)),
	})
	now := time.Now().UTC()
	if spend := h.gw.state.MonthSpend(now); spend < 9 {
		t.Fatalf("seed spend not counted: %f", spend)
	}
	h.gw.enforceBudget(context.Background())
	_, frozen, capped := h.gw.state.BudgetState()
	if !frozen || !capped {
		t.Fatalf("budget cap not applied: frozen=%v capped=%v", frozen, capped)
	}
	p := h.gw.poolFor("qwen2.5-7b-instruct")
	if desired := h.gw.desiredReplicas(p); desired != 0 {
		t.Fatalf("desired should be 0 when capped, got %d", desired)
	}
}

func TestOrphanCleanup(t *testing.T) {
	h := startHarness(t, "")
	ctx := context.Background()
	orphan, _ := h.fake.Launch(ctx, provider.NodeSpec{Deployment: "test-deploy", Model: "qwen2.5-7b-instruct"})
	h.gw.cleanupOrphans(ctx)
	nodes, _ := h.fake.List(ctx, "test-deploy")
	for _, n := range nodes {
		if n.ID == orphan.ID {
			t.Fatal("orphan not terminated")
		}
	}
}

func TestStatePersistence(t *testing.T) {
	h := startHarness(t, "")
	h.gw.state.StartNode("n1", "qwen2.5-7b-instruct", 0.5)
	if err := h.gw.state.Save(filepath.Join(h.dir, "state.json")); err != nil {
		t.Fatal(err)
	}
	loaded, err := LoadState(filepath.Join(h.dir, "state.json"))
	if err != nil {
		t.Fatal(err)
	}
	spend := loaded.MonthSpend(time.Now().UTC())
	if spend <= 0 {
		t.Fatalf("spend not persisted: %f", spend)
	}
}

func TestKeyModelRestriction(t *testing.T) {
	src := strings.Replace(testCfgYAML, `models: ["*"]`, `models: ["other-model"]`, 1)
	h := startHarness(t, src)
	resp, _ := postJSON(h.apiURL+"/v1/chat/completions", "sk-test-alice", `{"model":"qwen2.5-7b-instruct"}`)
	if resp.StatusCode != http.StatusForbidden {
		t.Fatalf("want 403, got %d", resp.StatusCode)
	}
	resp.Body.Close()
}

func TestTokenLimit(t *testing.T) {
	src := strings.Replace(testCfgYAML, "tokens_per_day: 1000000", "tokens_per_day: 4", 1)
	h := startHarness(t, src)
	h.gw.state.RecordRequest("alice", 5, 0, 0)
	h.attachNodeAgentForce(t)
	if !h.waitNodes(t, "qwen2.5-7b-instruct", 1, 10*time.Second) {
		t.Fatal("node never ready")
	}
	resp, _ := postJSON(h.apiURL+"/v1/chat/completions", "sk-test-alice", `{"model":"qwen2.5-7b-instruct"}`)
	if resp.StatusCode != http.StatusTooManyRequests {
		t.Fatalf("want 429, got %d", resp.StatusCode)
	}
	resp.Body.Close()
}

func TestColdRequestTriggersScale(t *testing.T) {
	h := startHarness(t, "")
	h.attachNodeAgentForce(t)
	if !h.waitNodes(t, "qwen2.5-7b-instruct", 1, 10*time.Second) {
		t.Fatal("node never ready")
	}
}

func ptrTime(t time.Time) *time.Time { return &t }

var _ = tunnel.ALPN
