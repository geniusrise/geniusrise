package cli

import (
	"context"
	"encoding/json"
	"fmt"
	"log/slog"
	"os"
	"os/signal"
	"syscall"

	"github.com/spf13/cobra"

	"github.com/geniusrise/geniusrise/internal/catalog"
	"github.com/geniusrise/geniusrise/internal/gateway"
	"github.com/geniusrise/geniusrise/internal/hostagent"
	"github.com/geniusrise/geniusrise/internal/node"
	"github.com/geniusrise/geniusrise/internal/pricing"
	"github.com/geniusrise/geniusrise/internal/provider"
	"github.com/geniusrise/geniusrise/internal/spec"
)

func newSshProvider(d *spec.Deployment) provider.Provider {
	p := newSsh(d)
	return p
}

var gatewayCmd = &cobra.Command{
	Use:   "gateway",
	Short: "Run the gateway daemon (inside the customer's cloud)",
	Run: func(cmd *cobra.Command, args []string) {
		dataDir := envOr("GR_DATA_DIR", "/var/lib/geniusrise")
		adminToken := os.Getenv("GR_ADMIN_TOKEN")
		version := envOr("GR_VERSION", rootCmd.Version)
		addr := envOr("GR_ADDR", ":443")
		logger := slog.New(slog.NewTextHandler(os.Stdout, nil))
		ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
		defer stop()

		cfgData, err := os.ReadFile(dataDir + "/config.yaml")
		if err != nil {
			logger.Error("no config yet: the CLI pushes it after bootstrap", "err", err)
		}
		var d *spec.Deployment
		if err == nil {
			d, err = spec.Parse(cfgData)
			if err != nil {
				logger.Error("config invalid", "err", err)
			}
		}
		snap, err := pricing.Load("")
		if err != nil {
			logger.Error("prices", "err", err)
			fatalf("%v", err)
		}
		cat, err := catalog.Load(os.Getenv("GR_CATALOG"))
		if err != nil {
			fatalf("%v", err)
		}
		var prov provider.Provider
		if d != nil {
			prov, err = newProviderForGateway(ctx, d, snap, version)
			if err != nil {
				logger.Error("provider init; will retry on config push", "err", err)
			}
		}
		if prov == nil {
			prov = provider.NewFake()
		}
		gw, err := gateway.New(gateway.Options{
			DataDir: dataDir, Addr: addr, Provider: prov, Catalog: cat, Prices: snap,
			Version: version, Logger: logger, AdminToken: adminToken,
			PlainHTTP: os.Getenv("GR_PLAIN") == "1",
		})
		if err != nil {
			fatalf("%v", err)
		}
		if err := gw.Start(ctx); err != nil {
			fatalf("%v", err)
		}
	},
}

var nodeCmd = &cobra.Command{
	Use:   "node",
	Short: "Run the node agent (entrypoint of engine images)",
	Run: func(cmd *cobra.Command, args []string) {
		var es struct {
			Cmd           []string          `json:"cmd"`
			Port          int               `json:"port"`
			Type          string            `json:"type"`
			GatewayURL    string            `json:"gateway_url"`
			GatewayAddr   string            `json:"gateway_addr"`
			JoinToken     string            `json:"join_token"`
			CAFingerprint string            `json:"ca_fingerprint"`
			NodeID        string            `json:"node_id"`
			ExternalURL   string            `json:"external_url"`
			Env           map[string]string `json:"env"`
		}
		raw := os.Getenv("GR_ENGINE_SPEC")
		if raw == "" {
			fatalf("GR_ENGINE_SPEC is empty: the gateway sets it when launching a node")
		}
		if err := json.Unmarshal([]byte(raw), &es); err != nil {
			fatalf("engine spec: %v", err)
		}
		env := map[string]string{}
		for _, kv := range os.Environ() {
			for k := range es.Env {
				if len(kv) > len(k)+1 && kv[:len(k)+1] == k+"=" {
					env[k] = kv[len(k)+1:]
				}
			}
		}
		agent := node.New(node.Config{
			NodeID: es.NodeID, GatewayURL: es.GatewayURL, GatewayAddr: es.GatewayAddr,
			JoinToken: es.JoinToken, CAFingerprint: es.CAFingerprint,
			EngineCmd: es.Cmd, EnginePort: es.Port, EngineType: es.Type,
			HFToken: os.Getenv("HF_TOKEN"), PlainDial: os.Getenv("GR_PLAIN") == "1",
		})
		ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
		defer stop()
		if err := agent.Run(ctx); err != nil {
			fatalf("%v", err)
		}
	},
}

var hostJoinCmd = &cobra.Command{
	Use:   "host join <gateway> <token>",
	Short: "Attach this machine's GPUs to a deployment (run as root)",
	Args:  cobra.ExactArgs(2),
	Run: func(cmd *cobra.Command, args []string) {
		hostID := envOr("GR_HOST_ID", hostname())
		agent := hostagent.New(hostagent.Config{
			NodeID: hostID, HostID: hostID,
			GatewayURL: args[0], JoinToken: args[1],
			PlainDial: os.Getenv("GR_PLAIN") == "1",
		})
		ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
		defer stop()
		if err := agent.Run(ctx); err != nil {
			fatalf("%v", err)
		}
	},
}

func envOr(k, def string) string {
	if v := os.Getenv(k); v != "" {
		return v
	}
	return def
}

func hostname() string {
	h, err := os.Hostname()
	if err != nil {
		return "unknown"
	}
	return h
}

var _ = fmt.Sprintf
