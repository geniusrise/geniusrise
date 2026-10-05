package planner

import (
	"fmt"
	"sort"
	"strings"

	"github.com/geniusrise/geniusrise/internal/catalog"
	"github.com/geniusrise/geniusrise/internal/pricing"
	"github.com/geniusrise/geniusrise/internal/spec"
)

const HoursPerMonth = 730

type Slot struct {
	Host    string
	GPUIndex int
}

type ModelPlan struct {
	ID             string
	Type           string
	Variant        string
	Engine         string
	HFRepo         string
	Concurrency    int
	Min, Max       int
	Ranked         []pricing.Offering
	MonthlyMinUSD  float64
	MonthlyMaxUSD  float64
	Slots          []Slot
}

type Result struct {
	Provider        string
	Region          string
	GatewayMonthlyUSD float64
	Models          []ModelPlan
	TotalMinUSD     float64
	TotalMaxUSD     float64
	Warnings        []string
}

func (p *Result) Describe() string {
	var b strings.Builder
	fmt.Fprintf(&b, "provider %s (%s), gateway floor $%.2f/month\n", p.Provider, p.Region, p.GatewayMonthlyUSD)
	for _, m := range p.Models {
		if len(m.Ranked) > 0 {
			top := m.Ranked[0]
			fmt.Fprintf(&b, "  %s [%s/%s]: %s %s $%.4f/hr → $%.2f–%.2f/month (%d–%d replicas)\n",
				m.ID, m.Variant, m.Engine, top.GPUClass, top.InstanceType, top.USDPerHour, m.MonthlyMinUSD, m.MonthlyMaxUSD, m.Min, m.Max)
		} else if len(m.Slots) > 0 {
			fmt.Fprintf(&b, "  %s [%s/%s]: ssh slots %s → $%.2f–%.2f/month (%d–%d replicas)\n",
				m.ID, m.Variant, m.Engine, slotsString(m.Slots), m.MonthlyMinUSD, m.MonthlyMaxUSD, m.Min, m.Max)
		}
	}
	fmt.Fprintf(&b, "total: $%.2f–%.2f/month\n", p.TotalMinUSD, p.TotalMaxUSD)
	for _, w := range p.Warnings {
		fmt.Fprintf(&b, "warning: %s\n", w)
	}
	return b.String()
}

func slotsString(slots []Slot) string {
	parts := make([]string, len(slots))
	for i, s := range slots {
		parts[i] = fmt.Sprintf("%s#%d", s.Host, s.GPUIndex)
	}
	return strings.Join(parts, ",")
}

func fakeOfferings(classes []string) []pricing.Offering {
	var out []pricing.Offering
	for _, c := range classes {
		out = append(out, pricing.Offering{GPUClass: c, InstanceType: "fake-" + c, Capacity: pricing.CapacityOnDemand, USDPerHour: 0, Available: true})
	}
	return out
}

func offeringsFor(snap *pricing.Snapshot, provider, region string, classes []string, capacity string) []pricing.Offering {
	if provider == spec.ProviderFake {
		return fakeOfferings(classes)
	}
	var out []pricing.Offering
	wantSpot := capacity == spec.CapacitySpot || capacity == spec.CapacitySpotFallback
	wantOD := capacity == spec.CapacityOnDemand || capacity == spec.CapacitySpotFallback || capacity == spec.CapacityServerless
	for _, class := range classes {
		for _, o := range snap.Offerings(provider, region) {
			if o.GPUClass != class || !o.Available {
				continue
			}
			if o.Capacity == pricing.CapacitySpot && wantSpot {
				out = append(out, o)
			}
			if o.Capacity == pricing.CapacityOnDemand && wantOD {
				out = append(out, o)
			}
		}
	}
	sort.SliceStable(out, func(i, j int) bool {
		if (out[i].Capacity == pricing.CapacitySpot) != (out[j].Capacity == pricing.CapacitySpot) {
			return out[i].Capacity == pricing.CapacitySpot
		}
		return out[i].USDPerHour < out[j].USDPerHour
	})
	return out
}

func Plan(d *spec.Deployment, cat *catalog.Catalog, snap *pricing.Snapshot) (*Result, error) {
	p := &Result{Provider: d.Provider.Type, Region: d.Provider.Region}
	if d.Provider.Type == spec.ProviderFake && p.Region == "" {
		p.Region = "fake"
	}
	if d.Provider.Type == spec.ProviderSSH {
		p.Region = "ssh"
	}
	p.GatewayMonthlyUSD = snap.GatewayMonthly(d.Provider.Type)

	var totalSlots []Slot
	if d.Provider.Type == spec.ProviderSSH {
		for _, h := range d.Provider.Hosts {
			for i := 0; i < h.GPUs; i++ {
				totalSlots = append(totalSlots, Slot{Host: h.Addr, GPUIndex: i})
			}
		}
	}

	minSum := 0
	for _, m := range d.Models {
		recipe, err := cat.Get(m.ID)
		if err != nil {
			return nil, err
		}
		variant, err := recipe.Variant(m.Variant)
		if err != nil {
			return nil, err
		}
		if recipe.Gated {
			if d.Secrets["hf_token"] == "" {
				return nil, fmt.Errorf("%s is gated: set secrets.hf_token", m.ID)
			}
		}
		mp := ModelPlan{
			ID: m.ID, Type: recipe.Type, Variant: variant.Name, Engine: variant.Engine,
			HFRepo: variant.HFRepo, Concurrency: variant.Capacity.Concurrency,
			Min: m.Replicas.Min, Max: m.Replicas.Max,
		}
		if d.Provider.Type == spec.ProviderSSH {
			if variant.UsesGPU() {
				for _, g := range variant.GPUs {
					if g != "cpu" {
						return nil, fmt.Errorf("%s/%s needs a cpu variant for ssh pools (gpu %s not supported on ssh hosts)", m.ID, variant.Name, g)
					}
				}
			}
			if mp.Max > len(totalSlots) {
				mp.Max = len(totalSlots)
				p.Warnings = append(p.Warnings, fmt.Sprintf("%s: max clamped to %d (pool size)", m.ID, mp.Max))
			}
			if mp.Max < mp.Min {
				return nil, fmt.Errorf("%s: min %d exceeds pool of %d gpus", m.ID, mp.Min, len(totalSlots))
			}
			cost := 0.0
			for _, h := range d.Provider.Hosts {
				cost += h.CostHr
			}
			mp.MonthlyMinUSD = cost * float64(mp.Min) * HoursPerMonth
			mp.MonthlyMaxUSD = cost * float64(mp.Max) * HoursPerMonth
			for i := 0; i < mp.Max; i++ {
				mp.Slots = append(mp.Slots, Slot{})
			}
			minSum += mp.Min
		} else {
			mp.Ranked = offeringsFor(snap, d.Provider.Type, p.Region, variant.GPUs, d.Provider.Capacity)
			if len(mp.Ranked) == 0 {
				return nil, fmt.Errorf("%s/%s: no %s offerings for %s in %s (gpus: %s)",
					m.ID, variant.Name, d.Provider.Capacity, d.Provider.Type, p.Region, strings.Join(variant.GPUs, ","))
			}
			mp.MonthlyMinUSD = mp.Ranked[0].USDPerHour * float64(mp.Min) * HoursPerMonth
			mp.MonthlyMaxUSD = mp.Ranked[0].USDPerHour * float64(mp.Max) * HoursPerMonth
		}
		p.Models = append(p.Models, mp)
		p.TotalMinUSD += mp.MonthlyMinUSD
		p.TotalMaxUSD += mp.MonthlyMaxUSD
	}
	if d.Provider.Type == spec.ProviderSSH && minSum > len(totalSlots) {
		return nil, fmt.Errorf("sum of min replicas (%d) exceeds pool of %d gpus", minSum, len(totalSlots))
	}
	p.TotalMinUSD += p.GatewayMonthlyUSD
	p.TotalMaxUSD += p.GatewayMonthlyUSD
	if d.Budget != nil && d.Budget.MonthlyUSD != nil {
		budget := *d.Budget.MonthlyUSD
		if p.TotalMinUSD > budget {
			return nil, fmt.Errorf("cost at min replicas ($%.2f/month) exceeds budget $%.2f: lower min replicas, pick cheaper variants or raise the budget", p.TotalMinUSD, budget)
		}
		if p.TotalMaxUSD > budget {
			p.Warnings = append(p.Warnings, fmt.Sprintf("cost at max replicas ($%.2f/month) exceeds budget $%.2f: the cap will bind and scale-ups will freeze", p.TotalMaxUSD, budget))
		}
	}
	return p, nil
}

func switchToCPUVariants(d *spec.Deployment, cat *catalog.Catalog) (bool, error) {
	for i := range d.Models {
		recipe, err := cat.Get(d.Models[i].ID)
		if err != nil {
			return false, err
		}
		v, err := recipe.Variant(d.Models[i].Variant)
		if err != nil {
			return false, err
		}
		if !v.UsesGPU() {
			continue
		}
		for _, cand := range recipe.Variants {
			if !cand.UsesGPU() {
				d.Models[i].Variant = cand.Name
				break
			}
		}
		nv, _ := recipe.Variant(d.Models[i].Variant)
		if nv.UsesGPU() {
			return false, fmt.Errorf("%s has no cpu variant", d.Models[i].ID)
		}
	}
	return true, nil
}

func Compare(d *spec.Deployment, cat *catalog.Catalog, snap *pricing.Snapshot) (map[string]*Result, error) {
	out := map[string]*Result{}
	providers := []string{spec.ProviderAWS, spec.ProviderGCP, spec.ProviderAzure, spec.ProviderRunPod, spec.ProviderLambda, spec.ProviderHyperbolic, spec.ProviderSSH}
	for _, prov := range providers {
		cp := *d
		cp.Provider.Type = prov
		cp.Provider.Capacity = d.Provider.Capacity
		if prov == spec.ProviderSSH {
			cp.Provider.Region = ""
			if len(cp.Provider.Hosts) == 0 {
				cp.Provider.Hosts = []spec.SSHHost{{Addr: "host1", User: "u", GPUs: 4}}
			}
			cp.Budget = nil
			ok, err := switchToCPUVariants(&cp, cat)
			if err != nil || !ok {
				continue
			}
		} else {
			cp.Provider.Hosts = nil
			cp.Gateway.Host = ""
			if prov == spec.ProviderLambda || prov == spec.ProviderHyperbolic {
				continue
			}
			if prov == spec.ProviderRunPod {
				cp.Provider.Region = "global"
			} else if cp.Provider.Region == "" || cp.Provider.Region == "global" {
				cp.Provider.Region = "us-east-1"
			}
			if snap.Offerings(prov, cp.Provider.Region) == nil {
				continue
			}
			if cp.Provider.Capacity == spec.CapacityServerless && prov != spec.ProviderRunPod {
				cp.Provider.Capacity = spec.CapacityOnDemand
			}
		}
		if err := cp.Validate(); err != nil {
			continue
		}
		if plan, err := Plan(&cp, cat, snap); err == nil {
			out[prov] = plan
		}
	}
	if len(out) == 0 {
		return nil, fmt.Errorf("no provider can run this deployment")
	}
	return out, nil
}
