package pricing

import (
	_ "embed"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"
)

//go:embed files/prices.json
var embedded string

const DefaultSnapshotURL = "https://github.com/geniusrise/geniusrise/releases/latest/download/prices.json"

type Capacity string

const (
	CapacityOnDemand Capacity = "on-demand"
	CapacitySpot     Capacity = "spot"
)

type Offering struct {
	GPUClass     string   `json:"gpu_class"`
	InstanceType string   `json:"instance_type"`
	Capacity     Capacity `json:"capacity"`
	USDPerHour   float64  `json:"usd_hr"`
	Available    bool     `json:"available"`
}

type Snapshot struct {
	GeneratedAt time.Time                           `json:"generated_at"`
	GatewayMonthlyUSD map[string]float64            `json:"gateway_monthly_usd"`
	Providers   map[string]map[string][]Offering    `json:"providers"`
}

func (s *Snapshot) Offerings(provider, region string) []Offering {
	if s.Providers == nil {
		return nil
	}
	return s.Providers[provider][region]
}

func (s *Snapshot) Offering(provider, region, gpuClass string, capacity Capacity) (*Offering, error) {
	for _, o := range s.Offerings(provider, region) {
		if o.GPUClass == gpuClass && o.Capacity == capacity {
			return &o, nil
		}
	}
	return nil, fmt.Errorf("no %s offering for %s/%s/%s", capacity, provider, region, gpuClass)
}

func Parse(data []byte) (*Snapshot, error) {
	var s Snapshot
	if err := json.Unmarshal(data, &s); err != nil {
		return nil, err
	}
	if s.Providers == nil {
		s.Providers = map[string]map[string][]Offering{}
	}
	if s.GatewayMonthlyUSD == nil {
		s.GatewayMonthlyUSD = map[string]float64{}
	}
	return &s, nil
}

func Embedded() (*Snapshot, error) {
	return Parse([]byte(embedded))
}

func cachePath() string {
	if dir, err := os.UserCacheDir(); err == nil {
		return filepath.Join(dir, "geniusrise", "prices.json")
	}
	return filepath.Join(os.TempDir(), "geniusrise-prices.json")
}

func LoadCached() (*Snapshot, error) {
	p := cachePath()
	data, err := os.ReadFile(p)
	if err != nil {
		return nil, err
	}
	s, err := Parse(data)
	if err != nil {
		return nil, err
	}
	if time.Since(s.GeneratedAt) > 24*time.Hour {
		return nil, fmt.Errorf("price snapshot is stale")
	}
	return s, nil
}

func SaveCache(data []byte) error {
	p := cachePath()
	if err := os.MkdirAll(filepath.Dir(p), 0o755); err != nil {
		return err
	}
	return os.WriteFile(p, data, 0o644)
}

func Fetch(url string) ([]byte, error) {
	if url == "" {
		url = DefaultSnapshotURL
	}
	resp, err := http.Get(url)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode == http.StatusOK {
		return io.ReadAll(resp.Body)
	}
	return nil, fmt.Errorf("price snapshot %s: status %d", url, resp.StatusCode)
}

func Load(url string) (*Snapshot, error) {
	if s, err := LoadCached(); err == nil {
		return s, nil
	}
	if data, err := Fetch(url); err == nil {
		if s, err := Parse(data); err == nil {
			_ = SaveCache(data)
			return s, nil
		}
	}
	return Embedded()
}

func (s *Snapshot) Regions(provider string) []string {
	seen := map[string]bool{}
	var out []string
	for r := range s.Providers[provider] {
		if !seen[r] {
			seen[r] = true
			out = append(out, r)
		}
	}
	return out
}

func (s *Snapshot) GatewayMonthly(provider string) float64 {
	if v, ok := s.GatewayMonthlyUSD[provider]; ok {
		return v
	}
	return 10.0
}

func (s *Snapshot) RenderTable() string {
	var b strings.Builder
	fmt.Fprintf(&b, "%-10s %-16s %-6s %-18s %-10s %s\n", "provider", "region", "gpu", "instance", "$/hr", "capacity")
	for p, regions := range s.Providers {
		names := make([]string, 0, len(regions))
		for r := range regions {
			names = append(names, r)
		}
		sortStrings(names)
		for _, r := range names {
			off := regions[r]
			sorted := append([]Offering(nil), off...)
			sortOfferings(&sorted)
			for _, o := range sorted {
				fmt.Fprintf(&b, "%-10s %-16s %-6s %-18s %-10.4f %s\n", p, r, o.GPUClass, o.InstanceType, o.USDPerHour, o.Capacity)
			}
		}
	}
	return b.String()
}

func sortStrings(s []string) {
	for i := 1; i < len(s); i++ {
		for j := i; j > 0 && s[j] < s[j-1]; j-- {
			s[j], s[j-1] = s[j-1], s[j]
		}
	}
}

func sortOfferings(o *[]Offering) {
	a := *o
	for i := 1; i < len(a); i++ {
		for j := i; j > 0 && a[j].GPUClass+a[j].InstanceType < a[j-1].GPUClass+a[j-1].InstanceType; j-- {
			a[j], a[j-1] = a[j-1], a[j]
		}
	}
}
