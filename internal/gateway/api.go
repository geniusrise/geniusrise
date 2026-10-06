package gateway

import (
	"bytes"
	"context"
	"crypto/subtle"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"net/http"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"sync/atomic"
	"time"

	"github.com/geniusrise/geniusrise/internal/spec"
	"github.com/geniusrise/geniusrise/internal/tunnel"
)

func (s *Server) handleJoin(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method", http.StatusMethodNotAllowed)
		return
	}
	var req tunnel.JoinRequest
	if err := json.NewDecoder(io.LimitReader(r.Body, 1<<20)).Decode(&req); err != nil {
		http.Error(w, "bad request", http.StatusBadRequest)
		return
	}
	s.joinTokensMu.Lock()
	valid := false
	for id, tok := range s.joinTokens {
		if subtle.ConstantTimeCompare([]byte(req.Token), []byte(tok)) == 1 {
			valid = s.tm.Consume(strings.SplitN(tok, ".", 2)[0], strings.SplitN(tok, ".", 2)[1])
			if valid {
				delete(s.joinTokens, id)
			}
			break
		}
	}
	s.joinTokensMu.Unlock()
	if !valid {
		http.Error(w, `{"error":"invalid join token"}`, http.StatusUnauthorized)
		return
	}
	certPEM, err := s.ca.SignCSR([]byte(req.CSR), nodeIDOf(s, req.Token))
	if err != nil {
		http.Error(w, "csr", http.StatusBadRequest)
		return
	}
	resp := tunnel.JoinResponse{Cert: string(certPEM), CA: string(s.ca.PEM()), GatewayAddr: s.publicAddr()}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func (s *Server) joinTokensMapCopy() map[string]string {
	s.joinTokensMu.Lock()
	defer s.joinTokensMu.Unlock()
	out := map[string]string{}
	for k, v := range s.joinTokens {
		out[k] = v
	}
	return out
}

func nodeIDOf(s *Server, token string) string {
	s.joinTokensMu.Lock()
	defer s.joinTokensMu.Unlock()
	for id, tok := range s.joinTokens {
		if tok == token {
			return id
		}
	}
	return "unknown-node"
}

func (s *Server) handleModels(w http.ResponseWriter, r *http.Request) {
	kc, _ := keyFrom(r.Context())
	cfg := s.Config()
	type modelObj struct {
		ID      string `json:"id"`
		Object  string `json:"object"`
		OwnedBy string `json:"owned_by"`
	}
	data := []modelObj{}
	for _, m := range cfg.Models {
		if kc.allowsModel(m.ID) {
			data = append(data, modelObj{ID: m.ID, Object: "model", OwnedBy: "geniusrise"})
		}
	}
	sort.Slice(data, func(i, j int) bool { return data[i].ID < data[j].ID })
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]any{"object": "list", "data": data})
}

type chatRequest struct {
	Model  string `json:"model"`
	Stream bool   `json:"stream"`
	Input  string `json:"input"`
}

func (s *Server) modelFromRequest(r *http.Request, body []byte) (string, error) {
	var cr chatRequest
	if err := json.Unmarshal(body, &cr); err != nil {
		return "", fmt.Errorf("invalid json body")
	}
	if cr.Model == "" {
		return "", fmt.Errorf("model is required")
	}
	cfg := s.Config()
	for _, m := range cfg.Models {
		if m.ID == cr.Model {
			return cr.Model, nil
		}
	}
	return "", fmt.Errorf("model %q not found", cr.Model)
}

func (s *Server) handleChat(w http.ResponseWriter, r *http.Request) {
	kc, _ := keyFrom(r.Context())
	body, err := io.ReadAll(io.LimitReader(r.Body, maxJSONBody))
	if err != nil {
		http.Error(w, "read", http.StatusBadRequest)
		return
	}
	model, err := s.modelFromRequest(r, body)
	if err != nil {
		writeOpenAIError(w, http.StatusBadRequest, err.Error(), "invalid_request_error")
		return
	}
	if !kc.allowsModel(model) {
		writeOpenAIError(w, http.StatusForbidden, "key cannot use model "+model, "auth")
		return
	}
	var cr chatRequest
	json.Unmarshal(body, &cr)
	if cr.Stream {
		injectStreamUsage(&body)
	}
	usage := s.proxyToModel(w, r, kc, model, body, "tokens")
	s.state.RecordRequest(kc.name, usage, 0, 0)
	s.metricAdd("requests_total", 1)
}

func (s *Server) handleAudioSTT(w http.ResponseWriter, r *http.Request) {
	kc, _ := keyFrom(r.Context())
	r.Body = http.MaxBytesReader(w, r.Body, maxAudioBody)
	body, err := io.ReadAll(r.Body)
	if err != nil {
		writeOpenAIError(w, http.StatusRequestEntityTooLarge, "audio body too large (max 25MB)", "invalid_request_error")
		return
	}
	model, err := modelFromRequestMultipart(body)
	if err != nil {
		writeOpenAIError(w, http.StatusBadRequest, err.Error(), "invalid_request_error")
		return
	}
	if !kc.allowsModel(model) {
		writeOpenAIError(w, http.StatusForbidden, "key cannot use model "+model, "auth")
		return
	}
	s.state.RecordRequest(kc.name, 0, int64(len(body)), 0)
	s.proxyToModel(w, r, kc, model, body, "")
	s.metricAdd("requests_total", 1)
}

func (s *Server) handleAudioTTS(w http.ResponseWriter, r *http.Request) {
	kc, _ := keyFrom(r.Context())
	body, err := io.ReadAll(io.LimitReader(r.Body, maxJSONBody))
	if err != nil {
		http.Error(w, "read", http.StatusBadRequest)
		return
	}
	var tr struct {
		Model string `json:"model"`
		Input string `json:"input"`
	}
	if err := json.Unmarshal(body, &tr); err != nil || tr.Model == "" {
		writeOpenAIError(w, http.StatusBadRequest, "model and input are required", "invalid_request_error")
		return
	}
	cfg := s.Config()
	found := false
	for _, m := range cfg.Models {
		if m.ID == tr.Model {
			found = true
			break
		}
	}
	if !found {
		writeOpenAIError(w, http.StatusBadRequest, "model "+tr.Model+" not found", "invalid_request_error")
		return
	}
	if !kc.allowsModel(tr.Model) {
		writeOpenAIError(w, http.StatusForbidden, "key cannot use model "+tr.Model, "auth")
		return
	}
	s.state.RecordRequest(kc.name, 0, 0, int64(len(tr.Input)))
	s.proxyToModel(w, r, kc, tr.Model, body, "")
	s.metricAdd("requests_total", 1)
}

func modelFromRequestMultipart(body []byte) (string, error) {
	for _, line := range strings.Split(string(body[:min(len(body), 8192)]), "\n") {
		if strings.Contains(line, `name="model"`) {
			parts := strings.Split(line, `name="model"`)
			if len(parts) == 2 {
				rest := strings.TrimSpace(parts[1])
				rest = strings.Trim(rest, "\r-")
				return strings.TrimSpace(rest), nil
			}
		}
	}
	return "", fmt.Errorf("model is required")
}

func injectStreamUsage(body *[]byte) {
	var m map[string]any
	if err := json.Unmarshal(*body, &m); err != nil {
		return
	}
	if stream, ok := m["stream"].(bool); ok && stream {
		opts, ok := m["stream_options"].(map[string]any)
		if !ok {
			opts = map[string]any{}
		}
		opts["include_usage"] = true
		m["stream_options"] = opts
		if nb, err := json.Marshal(m); err == nil {
			*body = nb
		}
	}
}

func writeOpenAIError(w http.ResponseWriter, status int, message, typ string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(map[string]any{
		"error": map[string]string{"message": message, "type": typ},
	})
}

const nodeAdminPort = 9101

var totalTokensRe = regexp.MustCompile(`"total_tokens":\s*(\d+)`)

type countingReader struct {
	r      io.Reader
	tokens *int64
}

func (c *countingReader) Read(p []byte) (int, error) {
	n, err := c.r.Read(p)
	if n > 0 {
		if ms := totalTokensRe.FindAllSubmatch(p[:n], -1); len(ms) > 0 {
			if v, perr := strconv.ParseInt(string(ms[len(ms)-1][1]), 10, 64); perr == nil {
				atomic.StoreInt64(c.tokens, v)
			}
		}
	}
	return n, err
}

func (s *Server) proxyToModel(w http.ResponseWriter, r *http.Request, kc keyCtx, model string, body []byte, _ string) int64 {
	p := s.poolFor(model)
	if p == nil {
		writeOpenAIError(w, http.StatusNotFound, "model not deployed", "invalid_request_error")
		return 0
	}
	usage := s.checkLimits(kc)
	if usage != nil {
		writeOpenAIError(w, http.StatusTooManyRequests, *usage, "rate_limit")
		return 0
	}
	node, ok := s.pickNode(p)
	if !ok {
		s.triggerScale(model)
		if node, ok = s.waitForNode(r.Context(), p); !ok {
			w.Header().Set("Retry-After", "120")
			writeOpenAIError(w, http.StatusServiceUnavailable, "model is cold, retry after scale-up", "server_error")
			return 0
		}
	}
	var tokens int64
	s.forwardToNode(w, r, node, model, body, &tokens)
	return tokens
}

func (s *Server) checkLimits(kc keyCtx) *string {
	u := s.state.UsageFor(kc.name)
	if kc.limits.TokensPerDay > 0 && u.Tokens >= kc.limits.TokensPerDay {
		msg := "daily token limit exceeded"
		return &msg
	}
	if kc.limits.STTMBPerDay > 0 && u.STTBytes >= kc.limits.STTMBPerDay<<20 {
		msg := "daily transcription limit exceeded"
		return &msg
	}
	if kc.limits.TTSCharsPerDay > 0 && u.TTSChars >= kc.limits.TTSCharsPerDay {
		msg := "daily synthesis limit exceeded"
		return &msg
	}
	return nil
}

func (s *Server) pickNode(p *pool) (*nodeEntry, bool) {
	ready := p.readyNodes()
	if len(ready) == 0 {
		return nil, false
	}
	sort.Slice(ready, func(i, j int) bool { return ready[i].Inflight < ready[j].Inflight })
	return ready[0], true
}

func (s *Server) triggerScale(model string) {
	p := s.poolFor(model)
	if p == nil {
		return
	}
	go s.reconcile(context.Background())
}

func (s *Server) waitForNode(ctx context.Context, p *pool) (*nodeEntry, bool) {
	deadline := time.Now().Add(coldWait)
	for time.Now().Before(deadline) {
		select {
		case <-ctx.Done():
			return nil, false
		case <-time.After(500 * time.Millisecond):
		}
		if n, ok := s.pickNode(p); ok {
			return n, true
		}
	}
	return nil, false
}

func (s *Server) forwardToNode(w http.ResponseWriter, r *http.Request, node *nodeEntry, model string, body []byte, tokens *int64) {
	enginePort := s.enginePortFor(model)
	conn, err := s.tunnels.Dial(node.ID, uint16(enginePort))
	if err != nil {
		writeOpenAIError(w, http.StatusBadGateway, "node unreachable", "server_error")
		return
	}
	defer conn.Close()
	proxyReq, err := http.NewRequestWithContext(r.Context(), r.Method, "http://node"+r.URL.Path, bytes.NewReader(body))
	if err != nil {
		writeOpenAIError(w, http.StatusInternalServerError, "proxy", "server_error")
		return
	}
	proxyReq.Header = r.Header.Clone()
	proxyReq.Header.Del("Authorization")
	proxyReq.ContentLength = int64(len(body))
	resp, err := (&http.Client{
		Transport: &http.Transport{
			DialContext: func(ctx context.Context, _, _ string) (net.Conn, error) {
				return conn, nil
			},
			DisableCompression: true,
		},
	}).Do(proxyReq)
	if err != nil {
		s.logger.Error("proxy", "node", node.ID, "err", err)
		s.markNode(node.ID, func(n *nodeEntry) { n.Unhealthy = true })
		writeOpenAIError(w, http.StatusBadGateway, "engine error", "server_error")
		return
	}
	defer resp.Body.Close()
	for k, vv := range resp.Header {
		for _, v := range vv {
			w.Header().Add(k, v)
		}
	}
	w.WriteHeader(resp.StatusCode)
	var reader io.Reader = resp.Body
	if tokens != nil {
		reader = &countingReader{r: resp.Body, tokens: tokens}
	}
	flusher, _ := w.(http.Flusher)
	buf := make([]byte, 32*1024)
	for {
		n, err := reader.Read(buf)
		if n > 0 {
			if _, werr := w.Write(buf[:n]); werr != nil {
				return
			}
			if flusher != nil {
				flusher.Flush()
			}
		}
		if err != nil {
			return
		}
	}
}

func (s *Server) enginePortFor(model string) int {
	p := s.poolFor(model)
	if p == nil {
		return 8000
	}
	return p.variant.EnginePort()
}

func (s *Server) handleAdminConfig(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		cfg := s.Config()
		if cfg == nil {
			http.Error(w, `{"error":"not configured"}`, http.StatusNotFound)
			return
		}
		w.Header().Set("Content-Type", "application/yaml")
		if yamlData, err := spec.Marshal(cfg); err == nil {
			w.Write(yamlData)
		}
	case http.MethodPut:
		data, err := io.ReadAll(io.LimitReader(r.Body, 1<<20))
		if err != nil {
			http.Error(w, "read", http.StatusBadRequest)
			return
		}
		cfg, err := spec.Parse(data)
		if err != nil {
			http.Error(w, fmt.Sprintf(`{"error":%q}`, err.Error()), http.StatusBadRequest)
			return
		}
		if err := os.WriteFile(filepath.Join(s.opts.DataDir, "config.yaml"), data, 0o600); err != nil {
			http.Error(w, "persist", http.StatusInternalServerError)
			return
		}
		s.setConfig(cfg)
		s.rebuildPools()
		go s.reconcile(context.Background())
		w.Write([]byte(`{"status":"applied"}`))
	default:
		http.Error(w, "method", http.StatusMethodNotAllowed)
	}
}

func (s *Server) handleAdminStatus(w http.ResponseWriter, r *http.Request) {
	cfg := s.Config()
	if cfg == nil {
		http.Error(w, `{"error":"not configured"}`, http.StatusNotFound)
		return
	}
	type nodeStatus struct {
		ID        string    `json:"id"`
		State     string    `json:"state"`
		Inflight  int       `json:"inflight"`
		Unhealthy bool      `json:"unhealthy"`
		PriceHr   float64   `json:"price_hr"`
		Launched  time.Time `json:"launched_at"`
	}
	type modelStatus struct {
		ID    string       `json:"id"`
		Min   int          `json:"min"`
		Max   int          `json:"max"`
		Nodes []nodeStatus `json:"nodes"`
	}
	now := time.Now().UTC()
	spend := spendWithGateway(s.state.MonthSpend(now), s.gatewayMonthly(), now)
	resp := map[string]any{
		"deployment": cfg.Name,
		"provider":   cfg.Provider.Type,
		"version":    s.opts.Version,
		"spend_usd":  spend,
		"alerts":     s.state.Alerts,
		"models":     []modelStatus{},
	}
	if cfg.Budget != nil && cfg.Budget.MonthlyUSD != nil {
		resp["budget_usd"] = *cfg.Budget.MonthlyUSD
	}
	var models []modelStatus
	for _, m := range cfg.Models {
		ms := modelStatus{ID: m.ID, Min: m.Replicas.Min, Max: m.Replicas.Max, Nodes: []nodeStatus{}}
		if p := s.poolFor(m.ID); p != nil {
			p.mu.Lock()
			for _, n := range p.nodes {
				ms.Nodes = append(ms.Nodes, nodeStatus{ID: n.ID, State: n.State, Inflight: n.Inflight, Unhealthy: n.Unhealthy, PriceHr: n.PricePerHour, Launched: n.LaunchedAt})
			}
			p.mu.Unlock()
		}
		models = append(models, ms)
	}
	resp["models"] = models
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func (s *Server) handleAdminUsage(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(s.state.AllUsage())
}

func (s *Server) handleAdminLogs(w http.ResponseWriter, r *http.Request) {
	nodeID := r.URL.Query().Get("node")
	if nodeID == "" {
		http.Error(w, `{"error":"node param required"}`, http.StatusBadRequest)
		return
	}
	conn, err := s.tunnels.Dial(nodeID, nodeAdminPort)
	if err != nil {
		http.Error(w, `{"error":"node unreachable"}`, http.StatusBadGateway)
		return
	}
	defer conn.Close()
	token := s.nodeAdminToken(nodeID)
	req, _ := http.NewRequest("GET", "http://node/logs?token="+token, nil)
	resp, err := (&http.Client{
		Transport: &http.Transport{DialContext: func(ctx context.Context, _, _ string) (net.Conn, error) { return conn, nil }},
	}).Do(req)
	if err != nil {
		http.Error(w, `{"error":"logs fetch failed"}`, http.StatusBadGateway)
		return
	}
	defer resp.Body.Close()
	w.Header().Set("Content-Type", "text/plain")
	io.Copy(w, resp.Body)
}

func (s *Server) nodeAdminToken(nodeID string) string {
	cfg := s.Config()
	if cfg == nil {
		return ""
	}
	return "gr-node-" + hashKey(cfg.Name + nodeID)[:16]
}

func (s *Server) handleAdminNodeAction(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method", http.StatusMethodNotAllowed)
		return
	}
	parts := strings.Split(strings.Trim(r.URL.Path, "/"), "/")
	if len(parts) != 4 {
		http.Error(w, `{"error":"bad path"}`, http.StatusBadRequest)
		return
	}
	nodeID, action := parts[2], parts[3]
	switch action {
	case "restart":
		if err := s.tunnels.SendControl(nodeID, tunnel.Message{Type: tunnel.MsgRestart}); err != nil {
			http.Error(w, `{"error":"node unreachable"}`, http.StatusBadGateway)
			return
		}
		w.Write([]byte(`{"status":"restarting"}`))
	case "terminate":
		s.terminateNode(r.Context(), modelForNode(s, nodeID), nodeID)
		w.Write([]byte(`{"status":"terminating"}`))
	default:
		http.Error(w, `{"error":"unknown action"}`, http.StatusBadRequest)
	}
}

func (s *Server) handleAdminVersion(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"version": s.opts.Version})
}

func (s *Server) handleMetrics(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "text/plain")
	s.metricsMu.Lock()
	m := map[string]float64{}
	for k, v := range s.metrics {
		m[k] = v
	}
	s.metricsMu.Unlock()
	now := time.Now().UTC()
	spend := spendWithGateway(s.state.MonthSpend(now), s.gatewayMonthly(), now)
	fmt.Fprintf(w, "# TYPE geniusrise_spend_usd gauge\ngeniusrise_spend_usd %.4f\n", spend)
	for k, v := range m {
		fmt.Fprintf(w, "%s %.4f\n", k, v)
	}
	for _, id := range s.tunnels.Nodes() {
		fmt.Fprintf(w, "geniusrise_node_connected{node=%q} 1\n", id)
	}
}
