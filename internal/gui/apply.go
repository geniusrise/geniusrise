package gui

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
	"time"

	"github.com/geniusrise/geniusrise/internal/catalog"
	"github.com/geniusrise/geniusrise/internal/planner"
	"github.com/geniusrise/geniusrise/internal/pricing"
	"github.com/geniusrise/geniusrise/internal/provider"
	"github.com/geniusrise/geniusrise/internal/spec"
)

type gwHTTP struct {
	base  string
	token string
	hc    *http.Client
}

func newClient(url, token string) *gwHTTP {
	return &gwHTTP{base: strings.TrimSuffix(url, "/"), token: token, hc: &http.Client{Timeout: 30 * time.Second}}
}

func (c *gwHTTP) status() (map[string]any, error) {
	req, _ := http.NewRequest("GET", c.base+"/admin/status", nil)
	req.Header.Set("Authorization", "Bearer "+c.token)
	resp, err := c.hc.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	var out map[string]any
	if err := json.NewDecoder(resp.Body).Decode(&out); err != nil {
		return nil, err
	}
	return out, nil
}

func (c *gwHTTP) push(cfg *spec.Deployment) error {
	data, err := spec.Marshal(cfg)
	if err != nil {
		return err
	}
	req, _ := http.NewRequest("PUT", c.base+"/admin/config", strings.NewReader(string(data)))
	req.Header.Set("Authorization", "Bearer "+c.token)
	req.Header.Set("Content-Type", "application/yaml")
	resp, err := c.hc.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		body := make([]byte, 512)
		n, _ := resp.Body.Read(body)
		return fmt.Errorf("gateway rejected config (%d): %s", resp.StatusCode, body[:n])
	}
	return nil
}

func (s *Server) runApply(ctx context.Context, progress func(string, ...any)) error {
	data, err := spec.ResolveEnvFile(s.File)
	if err != nil {
		return err
	}
	d, err := spec.Parse(data)
	if err != nil {
		return err
	}
	cat, err := catalog.Load(s.CatalogFlag)
	if err != nil {
		return err
	}
	snap, err := pricing.Load("")
	if err != nil {
		return err
	}
	p, err := planner.Plan(d, cat, snap)
	if err != nil {
		return fmt.Errorf("plan: %w", err)
	}
	progress("plan ok: $%.2f–%.2f/month", p.TotalMinUSD, p.TotalMaxUSD)
	if d.Gateway.AdminToken == "" {
		d.Gateway.AdminToken = newAdminToken()
	}
	if d.Gateway.URL == "" {
		prov, err := newCLIProvider(ctx, d, snap)
		if err != nil {
			return err
		}
		progress("bootstrapping gateway on %s...", d.Provider.Type)
		info, err := prov.Bootstrap(ctx, d, provider.BootstrapOpts{AdminToken: d.Gateway.AdminToken, Version: "gui"})
		if err != nil {
			return fmt.Errorf("bootstrap: %w", err)
		}
		d.Gateway.URL = info.URL
		progress("gateway: %s", info.URL)
	}
	if err := spec.WriteBack(s.File, func(dd *spec.Deployment) {
		dd.Gateway.URL = d.Gateway.URL
		dd.Gateway.AdminToken = d.Gateway.AdminToken
	}); err != nil {
		return fmt.Errorf("write back: %w", err)
	}
	progress("pushing config...")
	if err := newClient(d.Gateway.URL, d.Gateway.AdminToken).push(d); err != nil {
		return err
	}
	progress("applied. the gateway is converging.")
	return nil
}

func newAdminToken() string {
	b := make([]byte, 24)
	rand.Read(b)
	return "gr_admin_" + hex.EncodeToString(b)
}

func newCLIProvider(ctx context.Context, d *spec.Deployment, snap *pricing.Snapshot) (provider.Provider, error) {
	return providerForCLI(ctx, d, snap)
}
