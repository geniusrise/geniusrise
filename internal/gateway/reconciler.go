package gateway

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"math"
	"net/http"
	"os"
	"sort"
	"strings"
	"time"

	"github.com/geniusrise/geniusrise/internal/catalog"
	"github.com/geniusrise/geniusrise/internal/planner"
	"github.com/geniusrise/geniusrise/internal/pricing"
	"github.com/geniusrise/geniusrise/internal/provider"
	"github.com/geniusrise/geniusrise/internal/spec"
	"github.com/geniusrise/geniusrise/internal/tunnel"
)

const (
	scaleDownDelay    = 5 * time.Minute
	heartbeatGrace    = 15 * time.Second
	coldWait          = 20 * time.Second
	targetUtilization = 0.7
)

func (s *Server) rebuildPools() {
	cfg := s.Config()
	if cfg == nil {
		return
	}
	s.poolsMu.Lock()
	defer s.poolsMu.Unlock()
	for _, m := range cfg.Models {
		if _, ok := s.pools[m.ID]; ok {
			p := s.pools[m.ID]
			p.mu.Lock()
			p.model = m
			p.mu.Unlock()
			continue
		}
		recipe, err := s.opts.Catalog.Get(m.ID)
		if err != nil {
			s.logger.Error("unknown model in config", "model", m.ID, "err", err)
			continue
		}
		variant, err := recipe.Variant(m.Variant)
		if err != nil {
			s.logger.Error("unknown variant", "model", m.ID, "err", err)
			continue
		}
		s.pools[m.ID] = &pool{
			model:     m,
			recipe:    recipe,
			variant:   variant,
			nodes:     map[string]*nodeEntry{},
			tunnels:   s.tunnels,
			idleSince: time.Now(),
		}
	}
	for id := range s.pools {
		known := false
		for _, m := range cfg.Models {
			if m.ID == id {
				known = true
				break
			}
		}
		if !known {
			p := s.pools[id]
			p.mu.Lock()
			nodes := make([]*nodeEntry, 0, len(p.nodes))
			for _, n := range p.nodes {
				nodes = append(nodes, n)
			}
			p.mu.Unlock()
			for _, n := range nodes {
				go s.terminateNode(context.Background(), id, n.ID)
			}
			delete(s.pools, id)
		}
	}
	s.auth.reload(cfg.Keys)
}

func (s *Server) poolFor(model string) *pool {
	s.poolsMu.Lock()
	defer s.poolsMu.Unlock()
	return s.pools[model]
}

func (s *Server) allPools() map[string]*pool {
	s.poolsMu.Lock()
	defer s.poolsMu.Unlock()
	out := map[string]*pool{}
	for k, v := range s.pools {
		out[k] = v
	}
	return out
}

func (s *Server) reconcile(ctx context.Context) {
	cfg := s.Config()
	if cfg == nil {
		return
	}
	s.rebuildPools()
	for _, p := range s.allPools() {
		ready := p.readyNodes()
		totalInflight := 0
		for _, n := range ready {
			totalInflight += n.Inflight
		}
		p.recordInflight(totalInflight)
		desired := s.desiredReplicas(p)
		s.scalePool(ctx, p, desired)
	}
	s.cleanupOrphans(ctx)
}

func (s *Server) desiredReplicas(p *pool) int {
	p.mu.Lock()
	conc := p.variant.Capacity.Concurrency
	minR := p.model.Replicas.Min
	maxR := p.model.Replicas.Max
	idle := p.idleSince
	low := p.lowSince
	avg := 0.0
	if len(p.history) > 0 {
		for _, v := range p.history {
			avg += v
		}
		avg /= float64(len(p.history))
	}
	launching, running := 0, 0
	for _, n := range p.nodes {
		if n.State == provider.StateLaunching {
			launching++
		}
		if n.State == provider.StateRunning {
			running++
		}
	}
	nodeCount := len(p.nodes)
	if avg > 0 || idle.IsZero() {
		p.idleSince = time.Now()
	}
	p.mu.Unlock()
	if maxR < minR {
		maxR = minR
	}
	if _, frozen, capped := s.state.BudgetState(); frozen || capped {
		return minR
	}
	desired := int(math.Ceil(avg / float64(conc) * (1 / targetUtilization)))
	if desired < minR {
		desired = minR
	}
	if desired > maxR {
		desired = maxR
	}
	current := launching + running
	if desired < current && running+launching > minR {
		if low.IsZero() {
			p.mu.Lock()
			p.lowSince = time.Now()
			p.mu.Unlock()
			desired = current
		} else if time.Since(low) >= scaleDownDelay {
			p.mu.Lock()
			p.lowSince = time.Now()
			p.mu.Unlock()
		} else {
			desired = current
		}
	} else {
		p.mu.Lock()
		p.lowSince = time.Time{}
		p.mu.Unlock()
	}
	idleDur, _ := p.model.IdleDuration()
	if minR == 0 && avg == 0 && !idle.IsZero() && time.Since(idle) > idleDur && nodeCount > 0 {
		return 0
	}
	return desired
}

func (s *Server) scalePool(ctx context.Context, p *pool, desired int) {
	p.mu.Lock()
	nodes := make([]*nodeEntry, 0, len(p.nodes))
	for _, n := range p.nodes {
		nodes = append(nodes, n)
	}
	p.mu.Unlock()
	sort.Slice(nodes, func(i, j int) bool { return nodes[i].LaunchedAt.Before(nodes[j].LaunchedAt) })
	current := len(nodes)
	if current < desired {
		for i := current; i < desired; i++ {
			go s.launchNode(ctx, p)
		}
		return
	}
	if current > desired {
		excess := current - desired
		for i := 0; i < excess; i++ {
			n := nodes[len(nodes)-1-i]
			go s.terminateNode(ctx, p.model.ID, n.ID)
		}
	}
}

func (s *Server) offeringsFor(p *pool) ([]pricing.Offering, error) {
	cfg := s.Config()
	if cfg == nil {
		return nil, fmt.Errorf("no config")
	}
	if cfg.Provider.Type == spec.ProviderSSH {
		return []pricing.Offering{{GPUClass: "cpu", InstanceType: "ssh-host", Capacity: pricing.CapacityOnDemand, USDPerHour: sshHostCost(cfg)}}, nil
	}
	ranked := planner.Ranked(s.opts.Prices, cfg.Provider.Type, regionFor(cfg), p.variant.GPUs, cfg.Provider.Capacity)
	if len(ranked) == 0 {
		return nil, fmt.Errorf("no offerings for %s", p.model.ID)
	}
	return ranked, nil
}

func sshHostCost(cfg *spec.Deployment) float64 {
	total := 0.0
	for _, h := range cfg.Provider.Hosts {
		total += h.CostHr
	}
	return total
}

func regionFor(cfg *spec.Deployment) string {
	if cfg.Provider.Type == spec.ProviderFake {
		return "fake"
	}
	if cfg.Provider.Type == spec.ProviderSSH {
		return "ssh"
	}
	return cfg.Provider.Region
}

func (s *Server) launchNode(ctx context.Context, p *pool) {
	cfg := s.Config()
	if cfg == nil || p == nil {
		return
	}
	nodeID := fmt.Sprintf("gr-%s-%s-%d", cfg.Name, p.model.ID, time.Now().UnixNano()%1e6)
	tokenID, tokenSecret, err := s.tm.New()
	if err != nil {
		s.logger.Error("join token", "err", err)
		return
	}
	s.joinTokensMu.Lock()
	s.joinTokens[nodeID] = tokenID + "." + tokenSecret
	s.joinTokensMu.Unlock()

	entry := &nodeEntry{ID: nodeID, Model: p.model.ID, State: provider.StateLaunching, LaunchedAt: time.Now().UTC(), JoinToken: tokenID + "." + tokenSecret}
	p.mu.Lock()
	p.nodes[nodeID] = entry
	p.mu.Unlock()

	ranked, err := s.offeringsFor(p)
	if err != nil {
		s.logger.Error("offerings", "err", err)
		return
	}
	chosen := ranked[0]
	image := engineImage(p.variant.Engine)
	ns := provider.NodeSpec{
		Image:      image,
		Deployment: cfg.Name, Model: p.model.ID, Variant: p.variant.Name,
		Engine: p.variant.Engine, HFRepo: p.variant.HFRepo, File: p.variant.File,
		GPUClass: chosen.GPUClass, InstanceType: chosen.InstanceType,
		Capacity: string(chosen.Capacity),
		Region:   regionFor(cfg), Concurrency: p.variant.Capacity.Concurrency,
		Env: map[string]string{}, JoinToken: tokenID + "." + tokenSecret,
		GatewayAddr: s.publicAddr(), CAFingerprint: s.fingerprint,
	}
	engineEnv := map[string]string{
		"GR_NODE_ID":        nodeID,
		"GR_GATEWAY_URL":    s.publicURL(),
		"GR_GATEWAY_ADDR":   s.publicAddr(),
		"GR_JOIN_TOKEN":     tokenID + "." + tokenSecret,
		"GR_CA_FINGERPRINT": s.fingerprint,
	}
	if cfg.Secrets["hf_token"] != "" {
		engineEnv["HF_TOKEN"] = cfg.Secrets["hf_token"]
	}
	specJSON, _ := json.Marshal(map[string]any{
		"cmd":            engineCommandFor(p.variant),
		"port":           p.variant.EnginePort(),
		"type":           engineTypeFor(p.variant),
		"gateway_url":    s.publicURL(),
		"gateway_addr":   s.publicAddr(),
		"join_token":     tokenID + "." + tokenSecret,
		"ca_fingerprint": s.fingerprint,
		"node_id":        nodeID,
	})
	engineEnv["GR_ENGINE_SPEC"] = string(specJSON)
	ns.Env = engineEnv

	node, err := s.opts.Provider.Launch(ctx, ns)
	if err != nil {
		s.logger.Error("launch failed", "model", p.model.ID, "err", err)
		p.mu.Lock()
		delete(p.nodes, nodeID)
		p.mu.Unlock()
		s.joinTokensMu.Lock()
		delete(s.joinTokens, nodeID)
		s.joinTokensMu.Unlock()
		s.alertOnLaunchFailures(p)
		return
	}
	p.mu.Lock()
	if e, ok := p.nodes[nodeID]; ok {
		e.ID = node.ID
		e.PricePerHour = node.PricePerHour
	}
	if node.ID != nodeID {
		p.nodes[node.ID] = p.nodes[nodeID]
		delete(p.nodes, nodeID)
	}
	p.mu.Unlock()
	s.state.StartNode(node.ID, p.model.ID, node.PricePerHour)
}

func (s *Server) alertOnLaunchFailures(p *pool) {
	s.metricAdd("launch_failures_total", 1)
}

func (s *Server) terminateNode(ctx context.Context, model, nodeID string) {
	p := s.poolFor(model)
	if p != nil {
		p.mu.Lock()
		if _, ok := p.nodes[nodeID]; !ok {
			p.mu.Unlock()
			return
		}
		delete(p.nodes, nodeID)
		p.mu.Unlock()
	}
	if err := s.opts.Provider.Terminate(ctx, nodeID); err != nil {
		s.logger.Error("terminate failed", "node", nodeID, "err", err)
	}
	s.state.EndNode(nodeID)
	s.tunnels.RemoveSession(nodeID)
}

func (s *Server) cleanupOrphans(ctx context.Context) {
	cfg := s.Config()
	if cfg == nil {
		return
	}
	nodes, err := s.opts.Provider.List(ctx, cfg.Name)
	if err != nil {
		return
	}
	known := map[string]bool{}
	for _, p := range s.allPools() {
		p.mu.Lock()
		for id := range p.nodes {
			known[id] = true
		}
		p.mu.Unlock()
	}
	for _, n := range nodes {
		if !known[n.ID] {
			s.logger.Warn("terminating orphan node", "node", n.ID, "model", n.Model)
			if err := s.opts.Provider.Terminate(ctx, n.ID); err == nil {
				s.state.EndNode(n.ID)
			}
		}
	}
	s.state.PruneNodes(known)
}

func (s *Server) enforceBudget(ctx context.Context) {
	cfg := s.Config()
	if cfg == nil || cfg.Budget == nil || cfg.Budget.MonthlyUSD == nil {
		return
	}
	budget := *cfg.Budget.MonthlyUSD
	now := time.Now().UTC()
	spend := spendWithGateway(s.state.MonthSpend(now), s.gatewayMonthly(), now)
	ratio := spend / budget
	level, _, _ := s.state.BudgetState()
	switch {
	case ratio >= 0.95:
		if level < 3 {
			s.state.AddAlert("critical", fmt.Sprintf("budget cap reached: $%s of $%s — scaling to zero until the month resets or the budget is raised", fmtUSD(spend), fmtUSD(budget)))
			s.state.SetBudget(3, true, true)
			s.sendAlert(cfg, "critical", spend, budget)
			for _, p := range s.allPools() {
				s.scalePool(ctx, p, 0)
			}
		}
	case ratio >= 0.90:
		if level < 2 {
			s.state.AddAlert("warning", fmt.Sprintf("budget 90%% reached ($%s of $%s): scale-ups frozen", fmtUSD(spend), fmtUSD(budget)))
			s.state.SetBudget(2, true, false)
			s.sendAlert(cfg, "warning", spend, budget)
		}
	case ratio >= 0.80:
		if level < 1 {
			s.state.AddAlert("info", fmt.Sprintf("budget 80%% reached ($%s of $%s)", fmtUSD(spend), fmtUSD(budget)))
			s.state.SetBudget(1, false, false)
			s.sendAlert(cfg, "info", spend, budget)
		}
	default:
		if level > 0 && ratio < 0.80 {
			s.state.SetBudget(0, false, false)
		}
	}
	s.recordMetrics("gateway_spend_usd", spend)
	s.recordMetrics("gateway_budget_usd", budget)
}

func (s *Server) gatewayMonthly() float64 {
	cfg := s.Config()
	if cfg == nil || s.opts.Prices == nil {
		return 0
	}
	return s.opts.Prices.GatewayMonthly(cfg.Provider.Type)
}

func (s *Server) sendAlert(cfg *spec.Deployment, level string, spend, budget float64) {
	if cfg.Alerts == nil || cfg.Alerts.Webhook == "" {
		return
	}
	payload, _ := json.Marshal(alertPayload{
		Deployment: cfg.Name, Level: level,
		Message: level + " budget threshold", SpendUSD: spend, BudgetUSD: budget,
		At: time.Now().UTC().Format(time.RFC3339),
	})
	go func() {
		client := &http.Client{Timeout: 10 * time.Second}
		resp, err := client.Post(cfg.Alerts.Webhook, "application/json", strings.NewReader(string(payload)))
		if err != nil {
			s.logger.Error("alert webhook", "err", err)
			return
		}
		io.Copy(io.Discard, resp.Body)
		resp.Body.Close()
	}()
}

func (s *Server) publicAddr() string {
	if s.opts.Addr != "" && s.opts.Addr != ":0" {
		if s.ln != nil {
			return s.ln.Addr().String()
		}
	}
	return "127.0.0.1:0"
}

func (s *Server) publicURL() string {
	if s.publicBase != "" {
		return s.publicBase
	}
	return "http://" + s.publicAddr()
}

func engineImage(engine string) string {
	tag := os.Getenv("GR_IMAGE_TAG")
	if tag == "" {
		tag = "latest"
	}
	return fmt.Sprintf("ghcr.io/geniusrise/%s:%s", engine, tag)
}

func gpuClassFor(v *catalog.Variant) string {
	for _, g := range v.GPUs {
		if g != "cpu" {
			return g
		}
	}
	return "cpu"
}

func capacityFor(cfg *spec.Deployment) string {
	return cfg.Provider.Capacity
}

func engineTypeFor(v *catalog.Variant) string { return v.Engine }

func engineCommandFor(v *catalog.Variant) []string {
	cmd, err := v.EngineCommand("")
	if err != nil {
		return nil
	}
	return cmd
}

func (s *Server) onNodeMessage(nodeID string, msg *tunnel.Message) {
	switch msg.Type {
	case tunnel.MsgRegister, tunnel.MsgHeartbeat:
		s.markNode(nodeID, func(n *nodeEntry) {
			n.LastBeat = time.Now()
			n.Inflight = msg.Inflight
			n.State = provider.StateRunning
		})
	case tunnel.MsgUnhealthy:
		s.markNode(nodeID, func(n *nodeEntry) { n.Unhealthy = true })
		s.logger.Warn("node reported unhealthy", "node", nodeID)
	case tunnel.MsgSpotNotice:
		s.logger.Warn("node spot interruption", "node", nodeID)
		s.markNode(nodeID, func(n *nodeEntry) { n.State = provider.StateTerminating })
		cfg := s.Config()
		if cfg != nil {
			go s.launchNode(context.Background(), s.poolFor(modelForNode(s, nodeID)))
		}
	}
}

func modelForNode(s *Server, nodeID string) string {
	for _, p := range s.allPools() {
		p.mu.Lock()
		_, ok := p.nodes[nodeID]
		p.mu.Unlock()
		if ok {
			return p.model.ID
		}
	}
	return ""
}

func (s *Server) markNode(nodeID string, fn func(*nodeEntry)) {
	for _, p := range s.allPools() {
		p.mu.Lock()
		n, ok := p.nodes[nodeID]
		if ok {
			fn(n)
		}
		p.mu.Unlock()
		if ok {
			return
		}
	}
}
