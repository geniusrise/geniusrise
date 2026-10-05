package planner

import (
	"strings"
	"testing"

	"github.com/geniusrise/geniusrise/internal/catalog"
	"github.com/geniusrise/geniusrise/internal/pricing"
	"github.com/geniusrise/geniusrise/internal/spec"
)

func load(t *testing.T) (*catalog.Catalog, *pricing.Snapshot) {
	t.Helper()
	cat, err := catalog.Embedded()
	if err != nil {
		t.Fatal(err)
	}
	snap, err := pricing.Embedded()
	if err != nil {
		t.Fatal(err)
	}
	return cat, snap
}

const base = `version: 1
name: acme-ai
provider:
  type: aws
  region: us-east-1
  capacity: spot-fallback
budget:
  monthly_usd: 500
models:
  - id: llama-3.1-8b-instruct
    variant: awq
    replicas: {min: 0, max: 2}
secrets:
  hf_token: hf_x
`

func TestPlanBasic(t *testing.T) {
	cat, snap := load(t)
	d, err := spec.Parse([]byte(base))
	if err != nil {
		t.Fatal(err)
	}
	p, err := Plan(d, cat, snap)
	if err != nil {
		t.Fatal(err)
	}
	if p.Provider != "aws" || len(p.Models) != 1 {
		t.Fatalf("bad plan: %+v", p)
	}
	m := p.Models[0]
	if m.Ranked[0].Capacity != pricing.CapacitySpot {
		t.Fatalf("spot-fallback should prefer spot: %+v", m.Ranked[0])
	}
	if m.MonthlyMaxUSD <= 0 || p.GatewayMonthlyUSD != 11.0 {
		t.Fatalf("bad costs: %+v", m)
	}
	if len(p.Warnings) != 0 {
		t.Fatalf("unexpected warnings: %v", p.Warnings)
	}
}

func TestPlanGatedModelWithoutToken(t *testing.T) {
	cat, snap := load(t)
	src := strings.Replace(base, "  hf_token: hf_x\n", "", 1)
	d, err := spec.Parse([]byte(src))
	if err != nil {
		t.Fatal(err)
	}
	if _, err := Plan(d, cat, snap); err == nil || !strings.Contains(err.Error(), "gated") {
		t.Fatalf("want gated error, got %v", err)
	}
}

func TestPlanUnknownModel(t *testing.T) {
	cat, snap := load(t)
	src := strings.Replace(base, "id: llama-3.1-8b-instruct", "id: gpt-99", 1)
	d, _ := spec.Parse([]byte(src))
	if _, err := Plan(d, cat, snap); err == nil || !strings.Contains(err.Error(), "catalog") {
		t.Fatalf("want catalog error, got %v", err)
	}
}

func TestPlanBudgetErrors(t *testing.T) {
	cat, snap := load(t)
	tight := strings.Replace(base, "monthly_usd: 500", "monthly_usd: 1", 1)
	d, _ := spec.Parse([]byte(tight))
	_, err := Plan(d, cat, snap)
	if err == nil || !strings.Contains(err.Error(), "exceeds budget") {
		t.Fatalf("want min-budget error, got %v", err)
	}
	lowMax := strings.Replace(base, "monthly_usd: 500", "monthly_usd: 20", 1)
	d2, _ := spec.Parse([]byte(lowMax))
	p2, err := Plan(d2, cat, snap)
	if err != nil {
		t.Fatal(err)
	}
	found := false
	for _, w := range p2.Warnings {
		if strings.Contains(w, "cap will bind") {
			found = true
		}
	}
	if !found {
		t.Fatalf("want binding warning, got %v", p2.Warnings)
	}
}

const sshSrc = `version: 1
name: homelab
provider:
  type: ssh
  hosts:
    - {addr: 10.0.0.5, user: ubuntu, gpus: 2, cost_hr: 0.2}
models:
  - id: llama-3.2-3b-instruct
    variant: q4-cpu
    replicas: {min: 1, max: 3}
secrets:
  hf_token: hf_x
`

func TestPlanSSH(t *testing.T) {
	cat, snap := load(t)
	src := sshSrc
	d, err := spec.Parse([]byte(src))
	if err != nil {
		t.Fatal(err)
	}
	p, err := Plan(d, cat, snap)
	if err != nil {
		t.Fatal(err)
	}
	m := p.Models[0]
	if m.MonthlyMaxUSD < m.MonthlyMinUSD || p.GatewayMonthlyUSD != 0 {
		t.Fatalf("bad ssh plan: %+v", m)
	}
	gpuSrc := strings.Replace(src, "variant: q4-cpu", "variant: fp16", 1)
	d2, _ := spec.Parse([]byte(gpuSrc))
	if _, err := Plan(d2, cat, snap); err == nil || !strings.Contains(err.Error(), "cpu variant") {
		t.Fatalf("want cpu-variant error, got %v", err)
	}
	over := strings.Replace(src, "{min: 1, max: 3}", "{min: 3, max: 3}", 1)
	over = strings.Replace(over, "replicas: {min: 3, max: 3}", "replicas: {min: 5, max: 5}", 1)
	d3, _ := spec.Parse([]byte(over))
	if _, err := Plan(d3, cat, snap); err == nil || !strings.Contains(err.Error(), "pool") {
		t.Fatalf("want pool error, got %v", err)
	}
}

func TestPlanFake(t *testing.T) {
	cat, snap := load(t)
	src := `version: 1
name: test-deploy
provider:
  type: fake
  region: fake
models:
  - id: qwen2.5-7b-instruct
    replicas: {min: 0, max: 1}
`
	d, _ := spec.Parse([]byte(src))
	p, err := Plan(d, cat, snap)
	if err != nil {
		t.Fatal(err)
	}
	if len(p.Models[0].Ranked) == 0 {
		t.Fatal("fake provider should synthesize offerings")
	}
}

func TestCompare(t *testing.T) {
	cat, snap := load(t)
	d, _ := spec.Parse([]byte(base))
	plans, err := Compare(d, cat, snap)
	if err != nil {
		t.Fatal(err)
	}
	if _, ok := plans["aws"]; !ok {
		t.Fatal("aws missing from comparison")
	}
	if _, ok := plans["ssh"]; !ok {
		t.Fatal("ssh missing from comparison")
	}
}

func TestDescribe(t *testing.T) {
	cat, snap := load(t)
	d, _ := spec.Parse([]byte(base))
	p, _ := Plan(d, cat, snap)
	s := p.Describe()
	if !strings.Contains(s, "llama-3.1-8b-instruct") || !strings.Contains(s, "total") {
		t.Fatalf("bad describe:\n%s", s)
	}
}
