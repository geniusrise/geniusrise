package ssh

import (
	"context"
	"encoding/json"
	"testing"
	"time"

	"github.com/geniusrise/geniusrise/internal/hostagent"
	"github.com/geniusrise/geniusrise/internal/provider"
	"github.com/geniusrise/geniusrise/internal/spec"
	"github.com/geniusrise/geniusrise/internal/tunnel"
)

func testSpec() *spec.Deployment {
	return &spec.Deployment{
		Name: "homelab",
		Provider: spec.Provider{Type: spec.ProviderSSH, Hosts: []spec.SSHHost{
			{Addr: "10.0.0.5", User: "u", GPUs: 2, CostHr: 0.2},
			{Addr: "10.0.0.6", User: "u", GPUs: 1, CostHr: 0.1},
		}},
	}
}

func fakeCall(containers map[string][]hostagent.ContainerInfo) CallFunc {
	return func(nodeID string, msg tunnel.Message, timeout time.Duration) (*tunnel.Message, error) {
		reply := &tunnel.Message{ReqID: msg.ReqID, Type: tunnel.MsgReply}
		switch msg.Type {
		case tunnel.MsgHostRun:
			var cs hostagent.ContainerSpec
			json.Unmarshal(msg.Data, &cs)
			reply.NodeID = cs.Name
		case tunnel.MsgHostList:
			data, _ := json.Marshal(containers[nodeID])
			reply.Data = data
		case tunnel.MsgHostStop:
			var payload struct{ Name string }
			json.Unmarshal(msg.Data, &payload)
			delete(containers, payload.Name)
		}
		return reply, nil
	}
}

func TestLaunchPicksFreeGPU(t *testing.T) {
	containers := map[string][]hostagent.ContainerInfo{
		"host-10-0-0-5": {{Name: "gr-node-x", State: "Up 5 minutes", GPU: 0, Model: "m"}},
	}
	p := New(testSpec(), fakeCall(containers))
	node, err := p.Launch(context.Background(), provider.NodeSpec{Deployment: "homelab", Model: "llama", Env: map[string]string{}})
	if err != nil {
		t.Fatal(err)
	}
	if node.ID == "" || node.PricePerHour <= 0 {
		t.Fatalf("bad node: %+v", node)
	}
}

func TestOfferings(t *testing.T) {
	p := New(testSpec(), fakeCall(map[string][]hostagent.ContainerInfo{}))
	offs, err := p.Offerings(context.Background(), "ssh")
	if err != nil || len(offs) != 2 {
		t.Fatalf("offerings: %v %v", offs, err)
	}
	if offs[0].USDPerHour != 0.2 {
		t.Fatalf("bad cost: %+v", offs[0])
	}
}

func TestListAggregatesHosts(t *testing.T) {
	containers := map[string][]hostagent.ContainerInfo{
		"host-10-0-0-5": {
			{Name: "gr-node-a", State: "Up", GPU: 0, Model: "llama"},
			{Name: "unrelated", State: "Up", GPU: 1},
		},
		"host-10-0-0-6": {
			{Name: "gr-node-b", State: "Exited (0)", GPU: 0, Model: "whisper"},
		},
	}
	p := New(testSpec(), fakeCall(containers))
	nodes, err := p.List(context.Background(), "homelab")
	if err != nil {
		t.Fatal(err)
	}
	if len(nodes) != 2 {
		t.Fatalf("want 2 managed nodes, got %+v", nodes)
	}
	states := map[string]string{}
	for _, n := range nodes {
		states[n.ID] = n.State
	}
	if states["gr-node-b"] != provider.StateTerminated {
		t.Fatalf("exited container should be terminated: %+v", states)
	}
}
