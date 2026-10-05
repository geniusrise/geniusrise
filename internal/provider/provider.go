package provider

import (
	"context"
	"fmt"
	"sort"
	"sync"
	"time"

	"github.com/geniusrise/geniusrise/internal/pricing"
	"github.com/geniusrise/geniusrise/internal/spec"
)

type NodeSpec struct {
	Deployment    string
	Model         string
	Variant       string
	Engine        string
	HFRepo        string
	File          string
	Image         string
	GPUClass      string
	InstanceType  string
	Capacity      string
	Region        string
	Concurrency   int
	Env           map[string]string
	JoinToken     string
	GatewayAddr   string
	CAFingerprint string
}

func (n NodeSpec) Tags() map[string]string {
	return map[string]string{
		"geniusrise:deployment": n.Deployment,
		"geniusrise:model":      n.Model,
		"geniusrise:variant":    n.Variant,
	}
}

type Node struct {
	ID           string
	State        string
	GPUClass     string
	InstanceType string
	Capacity     string
	PricePerHour float64
	LaunchedAt   time.Time
	Model        string
	Tags         map[string]string
}

const (
	StateLaunching   = "launching"
	StateRunning     = "running"
	StateTerminating = "terminating"
	StateTerminated  = "terminated"
)

type GatewayInfo struct {
	URL        string
	AdminToken string
	HostAddr   string
}

type BootstrapOpts struct {
	GatewayImage      string
	Version           string
	ExternalGatewayURL string
	AdminToken        string
}

type Provider interface {
	Name() string
	Bootstrap(ctx context.Context, d *spec.Deployment, opts BootstrapOpts) (*GatewayInfo, error)
	Offerings(ctx context.Context, region string) ([]pricing.Offering, error)
	Launch(ctx context.Context, n NodeSpec) (Node, error)
	List(ctx context.Context, deployment string) ([]Node, error)
	Terminate(ctx context.Context, id string) error
	Destroy(ctx context.Context, d *spec.Deployment) error
}

type Fake struct {
	mu           sync.Mutex
	nextID       int
	Nodes        map[string]*Node
	LaunchDelay  time.Duration
	LaunchFail   int
	launchCount  int
	Calls        []string
	offerings    []pricing.Offering
	BootstrapFn  func(d *spec.Deployment, opts BootstrapOpts) (*GatewayInfo, error)
	Gateway      *GatewayInfo
}

func NewFake() *Fake {
	return &Fake{Nodes: map[string]*Node{}}
}

func (f *Fake) Name() string { return spec.ProviderFake }

func (f *Fake) SetOfferings(o []pricing.Offering) {
	f.mu.Lock()
	defer f.mu.Unlock()
	f.offerings = o
}

func (f *Fake) record(call string) {
	f.mu.Lock()
	defer f.mu.Unlock()
	f.Calls = append(f.Calls, call)
}

func (f *Fake) Bootstrap(ctx context.Context, d *spec.Deployment, opts BootstrapOpts) (*GatewayInfo, error) {
	f.record("bootstrap")
	if f.BootstrapFn != nil {
		return f.BootstrapFn(d, opts)
	}
	if f.Gateway != nil {
		return f.Gateway, nil
	}
	return &GatewayInfo{URL: opts.ExternalGatewayURL, AdminToken: opts.AdminToken}, nil
}

func (f *Fake) Offerings(ctx context.Context, region string) ([]pricing.Offering, error) {
	f.record("offerings")
	f.mu.Lock()
	defer f.mu.Unlock()
	if f.offerings != nil {
		return f.offerings, nil
	}
	classes := []string{"cpu", "T4", "L4", "A10G", "L40S", "A100-40", "A100-80", "H100"}
	out := make([]pricing.Offering, 0, len(classes))
	for i, c := range classes {
		out = append(out, pricing.Offering{
			GPUClass: c, InstanceType: "fake-" + c, Capacity: pricing.CapacityOnDemand,
			USDPerHour: float64(i) * 0.1, Available: true,
		})
		out = append(out, pricing.Offering{
			GPUClass: c, InstanceType: "fake-" + c, Capacity: pricing.CapacitySpot,
			USDPerHour: float64(i) * 0.05, Available: true,
		})
	}
	return out, nil
}

func (f *Fake) Launch(ctx context.Context, n NodeSpec) (Node, error) {
	f.record("launch:" + n.Model)
	f.mu.Lock()
	f.launchCount++
	count := f.launchCount
	fail := f.LaunchFail
	delay := f.LaunchDelay
	f.mu.Unlock()
	if fail > 0 && count <= fail {
		return Node{}, fmt.Errorf("fake: simulated launch failure %d", count)
	}
	if delay > 0 {
		select {
		case <-time.After(delay):
		case <-ctx.Done():
			return Node{}, ctx.Err()
		}
	}
	f.mu.Lock()
	defer f.mu.Unlock()
	f.nextID++
	id := fmt.Sprintf("fake-node-%d", f.nextID)
	node := Node{
		ID: id, State: StateRunning, GPUClass: n.GPUClass, InstanceType: n.InstanceType,
		Capacity: n.Capacity, PricePerHour: 0.10, LaunchedAt: time.Now().UTC(),
		Model: n.Model, Tags: n.Tags(),
	}
	f.Nodes[id] = &node
	return node, nil
}

func (f *Fake) List(ctx context.Context, deployment string) ([]Node, error) {
	f.record("list")
	f.mu.Lock()
	defer f.mu.Unlock()
	var out []Node
	for _, n := range f.Nodes {
		if n.Tags["geniusrise:deployment"] == deployment && n.State != StateTerminated {
			out = append(out, *n)
		}
	}
	sort.Slice(out, func(i, j int) bool { return out[i].ID < out[j].ID })
	return out, nil
}

func (f *Fake) Terminate(ctx context.Context, id string) error {
	f.record("terminate:" + id)
	f.mu.Lock()
	defer f.mu.Unlock()
	if n, ok := f.Nodes[id]; ok {
		n.State = StateTerminated
	}
	return nil
}

func (f *Fake) Destroy(ctx context.Context, d *spec.Deployment) error {
	f.record("destroy")
	f.mu.Lock()
	defer f.mu.Unlock()
	for _, n := range f.Nodes {
		n.State = StateTerminated
	}
	return nil
}

func (f *Fake) SimulateInterruption(id string) {
	f.mu.Lock()
	defer f.mu.Unlock()
	if n, ok := f.Nodes[id]; ok {
		n.State = StateTerminated
	}
}

func (f *Fake) CallCount(prefix string) int {
	f.mu.Lock()
	defer f.mu.Unlock()
	c := 0
	for _, call := range f.Calls {
		if len(call) >= len(prefix) && call[:len(prefix)] == prefix {
			c++
		}
	}
	return c
}
