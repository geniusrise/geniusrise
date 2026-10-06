package cli

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/geniusrise/geniusrise/internal/catalog"
	"github.com/geniusrise/geniusrise/internal/planner"
	"github.com/geniusrise/geniusrise/internal/pricing"
	"github.com/geniusrise/geniusrise/internal/provider"
	"github.com/geniusrise/geniusrise/internal/spec"
)

func generateToken(prefix string) string {
	b := make([]byte, 24)
	rand.Read(b)
	return prefix + hex.EncodeToString(b)
}

func newProvider(ctx context.Context, d *spec.Deployment, snap *pricing.Snapshot, version string) (provider.Provider, error) {
	switch d.Provider.Type {
	case spec.ProviderFake:
		return provider.NewFake(), nil
	case spec.ProviderSSH:
		return newSshProvider(d), nil
	case spec.ProviderAWS:
		return newAwsProvider(ctx, d.Provider.Region, snap, version)
	}
	return nil, fmt.Errorf("provider %s is not implemented yet (planned for a later phase)", d.Provider.Type)
}

func loadCatalog(flag string) (*catalog.Catalog, error) {
	return catalog.Load(flag)
}

func loadPrices(url string) (*pricing.Snapshot, error) {
	return pricing.Load(url)
}

func loadForPlan(path, catalogFlag string) (*spec.Deployment, *catalog.Catalog, *pricing.Snapshot, error) {
	d, err := spec.LoadResolved(path)
	if err != nil {
		return nil, nil, nil, err
	}
	cat, err := loadCatalog(catalogFlag)
	if err != nil {
		return nil, nil, nil, err
	}
	snap, err := loadPrices("")
	if err != nil {
		return nil, nil, nil, err
	}
	return d, cat, snap, nil
}

type gwClient struct {
	base  string
	token string
	http  *http.Client
}

func newGWClient(url, token string) *gwClient {
	return &gwClient{base: strings.TrimSuffix(url, "/"), token: token, http: &http.Client{Timeout: 60 * time.Second}}
}

func (c *gwClient) do(method, path string, body []byte, contentType string) (int, []byte, error) {
	var rdr io.Reader
	if body != nil {
		rdr = strings.NewReader(string(body))
	}
	req, err := http.NewRequest(method, c.base+path, rdr)
	if err != nil {
		return 0, nil, err
	}
	req.Header.Set("Authorization", "Bearer "+c.token)
	if contentType != "" {
		req.Header.Set("Content-Type", contentType)
	}
	resp, err := c.http.Do(req)
	if err != nil {
		return 0, nil, err
	}
	defer resp.Body.Close()
	data, err := io.ReadAll(resp.Body)
	return resp.StatusCode, data, err
}

func (c *gwClient) pushConfig(d *spec.Deployment) error {
	yamlData, err := spec.Marshal(d)
	if err != nil {
		return err
	}
	status, body, err := c.do(http.MethodPut, "/admin/config", yamlData, "application/yaml")
	if err != nil {
		return err
	}
	if status != http.StatusOK {
		return fmt.Errorf("gateway rejected config (%d): %s", status, body)
	}
	return nil
}

func (c *gwClient) status() (map[string]any, error) {
	status, body, err := c.do(http.MethodGet, "/admin/status", nil, "")
	if err != nil {
		return nil, err
	}
	if status != http.StatusOK {
		return nil, fmt.Errorf("status %d: %s", status, body)
	}
	var out map[string]any
	if err := json.Unmarshal(body, &out); err != nil {
		return nil, err
	}
	return out, nil
}

func (c *gwClient) version() (string, error) {
	status, body, err := c.do(http.MethodGet, "/admin/version", nil, "")
	if err != nil {
		return "", err
	}
	if status != http.StatusOK {
		return "", fmt.Errorf("status %d", status)
	}
	var v struct {
		Version string `json:"version"`
	}
	if err := json.Unmarshal(body, &v); err != nil {
		return "", err
	}
	return v.Version, nil
}

func renderStatus(st map[string]any) string {
	var b strings.Builder
	fmt.Fprintf(&b, "deployment: %v\n", st["deployment"])
	fmt.Fprintf(&b, "provider:   %v\n", st["provider"])
	fmt.Fprintf(&b, "version:    %v\n", st["version"])
	if budget, ok := st["budget_usd"]; ok {
		fmt.Fprintf(&b, "budget:     $%v/month\n", budget)
	}
	fmt.Fprintf(&b, "spend:      $%.2f this month\n", st["spend_usd"])
	if models, ok := st["models"].([]any); ok {
		for _, m := range models {
			mm := m.(map[string]any)
			fmt.Fprintf(&b, "\nmodel %v (min=%v max=%v)\n", mm["id"], mm["min"], mm["max"])
			if nodes, ok := mm["nodes"].([]any); ok {
				for _, n := range nodes {
					nn := n.(map[string]any)
					fmt.Fprintf(&b, "  node %-40s state=%-10s inflight=%v unhealthy=%v $%.4f/hr\n",
						nn["id"], nn["state"], nn["inflight"], nn["unhealthy"], nn["price_hr"])
				}
			} else {
				fmt.Fprintf(&b, "  no nodes\n")
			}
		}
	}
	if alerts, ok := st["alerts"].([]any); ok && len(alerts) > 0 {
		fmt.Fprintf(&b, "\nrecent alerts:\n")
		for _, a := range alerts {
			aa := a.(map[string]any)
			fmt.Fprintf(&b, "  [%v] %v: %v\n", aa["level"], aa["at"], aa["message"])
		}
	}
	return b.String()
}

func gwURLFromSpec(d *spec.Deployment) (string, string, error) {
	if d.Gateway.URL == "" {
		return "", "", fmt.Errorf("gateway.url is empty: run `geniusrise apply` first")
	}
	if d.Gateway.AdminToken == "" {
		return "", "", fmt.Errorf("gateway.admin_token is empty: run `geniusrise apply` first")
	}
	return d.Gateway.URL, d.Gateway.AdminToken, nil
}

func planOrDie(path, catalogFlag string, compare bool) {
	d, cat, snap, err := loadForPlan(path, catalogFlag)
	if err != nil {
		fatalf("%v", err)
	}
	if compare {
		plans, err := planner.Compare(d, cat, snap)
		if err != nil {
			fatalf("%v", err)
		}
		for _, prov := range []string{spec.ProviderSSH, spec.ProviderAWS, spec.ProviderGCP, spec.ProviderAzure, spec.ProviderRunPod} {
			if p, ok := plans[prov]; ok {
				fmt.Printf("=== %s\n%s\n", prov, p.Describe())
			}
		}
		return
	}
	p, err := planner.Plan(d, cat, snap)
	if err != nil {
		fatalf("%v", err)
	}
	fmt.Print(p.Describe())
}

var _ = os.Stdout
