package cli

import (
	"context"
	"fmt"
	"os"
	"os/exec"
	"strings"

	"github.com/spf13/cobra"

	"github.com/geniusrise/geniusrise/internal/gui"
	"github.com/geniusrise/geniusrise/internal/planner"
	"github.com/geniusrise/geniusrise/internal/spec"
)

var (
	fileFlag     string
	catalogFlag  string
	compareFlag  bool
	yesFlag      bool
	recreateFlag bool
	priceURLFlag string
)

func init() {
	rootCmd.AddCommand(initCmd, catalogCmd, planCmd, applyCmd, statusCmd, logsCmd, destroyCmd, keyCmd, doctorCmd, guiCmd, upgradeCmd, gatewayCmd, nodeCmd, hostJoinCmd)
	for _, c := range []*cobra.Command{planCmd, applyCmd, statusCmd, logsCmd, destroyCmd, doctorCmd, guiCmd} {
		c.Flags().StringVarP(&fileFlag, "file", "f", "deploy.yaml", "deployment file")
	}
	for _, c := range []*cobra.Command{planCmd, applyCmd, statusCmd, catalogCmd, guiCmd} {
		c.Flags().StringVar(&catalogFlag, "catalog", "", "catalog source: path or URL (default: embedded)")
	}
	planCmd.Flags().BoolVar(&compareFlag, "compare", false, "compare across all providers")
	planCmd.Flags().StringVar(&priceURLFlag, "prices", "", "price snapshot URL")
	applyCmd.Flags().BoolVar(&recreateFlag, "recreate-gateway", false, "bootstrap the gateway even if one exists")
	destroyCmd.Flags().BoolVarP(&yesFlag, "yes", "y", false, "do not ask for confirmation")
}

var initCmd = &cobra.Command{
	Use:   "init",
	Short: "Create a starter deploy.yaml interactively",
	Run: func(cmd *cobra.Command, args []string) {
		if _, err := os.Stat(fileFlag); err == nil {
			fatalf("%s already exists", fileFlag)
		}
		fmt.Print("deployment name (e.g. acme-ai): ")
		name := readLine()
		fmt.Print("provider [aws/gcp/azure/runpod/lambda/hyperbolic/ssh]: ")
		prov := readLine()
		fmt.Print("region (us-east-1, empty for ssh): ")
		region := readLine()
		fmt.Print("monthly budget in USD (empty = unlimited): ")
		budget := readLine()
		fmt.Print("first model id (e.g. llama-3.2-3b-instruct): ")
		model := readLine()
		tpl := strings.ReplaceAll(initTemplate, "__NAME__", orDefault(name, "my-ai"))
		tpl = strings.ReplaceAll(tpl, "__PROVIDER__", orDefault(prov, "aws"))
		tpl = strings.ReplaceAll(tpl, "__REGION__", region)
		tpl = strings.ReplaceAll(tpl, "__BUDGET__", budget)
		tpl = strings.ReplaceAll(tpl, "__MODEL__", orDefault(model, "llama-3.2-3b-instruct"))
		if prov == "ssh" {
			tpl = strings.ReplaceAll(tpl, "  region: \n", "  hosts:\n    - {addr: 10.0.0.5, user: ubuntu, gpus: 1}\n")
		}
		if budget == "" {
			tpl = strings.ReplaceAll(tpl, "budget:\n  monthly_usd: \n", "")
		}
		if err := os.WriteFile(fileFlag, []byte(tpl), 0o600); err != nil {
			fatalf("%v", err)
		}
		fmt.Printf("wrote %s\nnext: geniusrise plan -f %s, then geniusrise apply -f %s\n", fileFlag, fileFlag, fileFlag)
	},
}

const initTemplate = `version: 1
name: __NAME__
provider:
  type: __PROVIDER__
  region: __REGION__
  capacity: spot-fallback
budget:
  monthly_usd: __BUDGET__
models:
  - id: __MODEL__
    replicas: {min: 0, max: 1}
    idle_timeout: 15m
keys:
  - name: main
    key: ${GENIUSRISE_KEY}
secrets:
  hf_token: ${HF_TOKEN}
`

func orDefault(v, def string) string {
	if strings.TrimSpace(v) == "" {
		return def
	}
	return strings.TrimSpace(v)
}

func readLine() string {
	var line string
	fmt.Scanln(&line)
	return strings.TrimSpace(line)
}

var planCmd = &cobra.Command{
	Use:   "plan",
	Short: "Show placement and monthly cost without deploying",
	Run: func(cmd *cobra.Command, args []string) {
		planOrDie(fileFlag, catalogFlag, compareFlag)
	},
}

var applyCmd = &cobra.Command{
	Use:   "apply",
	Short: "Bootstrap the gateway if needed and push the config",
	Run:   runApply,
}

func runApply(cmd *cobra.Command, args []string) {
	ctx := context.Background()
	d, cat, snap, err := loadForPlan(fileFlag, catalogFlag)
	if err != nil {
		fatalf("%v", err)
	}
	if _, err := planner.Plan(d, cat, snap); err != nil {
		fatalf("plan: %v", err)
	}
	if d.Gateway.AdminToken == "" {
		d.Gateway.AdminToken = generateToken("gr_admin_")
	}
	if d.Gateway.URL == "" || recreateFlag {
		prov, err := newProvider(ctx, d, snap, rootCmd.Version)
		if err != nil {
			fatalf("%v", err)
		}
		opts := providerOpts(d)
		fmt.Printf("bootstrapping gateway on %s...\n", d.Provider.Type)
		info, err := prov.Bootstrap(ctx, d, opts)
		if err != nil {
			fatalf("bootstrap: %v\nresources created so far are tagged %q: rerun apply to retry, or `geniusrise destroy` to clean up", err, "geniusrise:deployment="+d.Name)
		}
		d.Gateway.URL = info.URL
		fmt.Printf("gateway: %s\n", info.URL)
	}
	if err := spec.WriteBack(fileFlag, func(dd *spec.Deployment) {
		dd.Gateway.URL = d.Gateway.URL
		dd.Gateway.AdminToken = d.Gateway.AdminToken
	}); err != nil {
		fatalf("write back: %v", err)
	}
	client := newGWClient(d.Gateway.URL, d.Gateway.AdminToken)
	if err := client.pushConfig(d); err != nil {
		fatalf("push config: %v", err)
	}
	fmt.Println("config applied. the gateway is converging.")
	st, err := client.status()
	if err == nil {
		fmt.Print(renderStatus(st))
	}
}

var statusCmd = &cobra.Command{
	Use:   "status",
	Short: "Show pools, nodes and spend from the gateway",
	Run: func(cmd *cobra.Command, args []string) {
		d, err := spec.LoadResolved(fileFlag)
		if err != nil {
			fatalf("%v", err)
		}
		url, token, err := gwURLFromSpec(d)
		if err != nil {
			fatalf("%v", err)
		}
		st, err := newGWClient(url, token).status()
		if err != nil {
			fatalf("gateway unreachable (%v)\nrun `geniusrise apply --recreate-gateway` to rebuild it", err)
		}
		fmt.Print(renderStatus(st))
	},
}

var logsCmd = &cobra.Command{
	Use:   "logs <node>",
	Short: "Fetch engine logs for a node",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		d, err := spec.LoadResolved(fileFlag)
		if err != nil {
			fatalf("%v", err)
		}
		url, token, err := gwURLFromSpec(d)
		if err != nil {
			fatalf("%v", err)
		}
		c := newGWClient(url, token)
		status, body, err := c.do("GET", "/admin/logs?node="+args[0], nil, "")
		if err != nil {
			fatalf("%v", err)
		}
		if status != 200 {
			fatalf("logs: %s", body)
		}
		os.Stdout.Write(body)
	},
}

var destroyCmd = &cobra.Command{
	Use:   "destroy",
	Short: "Terminate all nodes, the gateway and every resource we own",
	Run: func(cmd *cobra.Command, args []string) {
		ctx := context.Background()
		d, _, snap, err := loadForPlan(fileFlag, catalogFlag)
		if err != nil {
			fatalf("%v", err)
		}
		if !yesFlag {
			fmt.Printf("this terminates every resource tagged geniusrise:deployment=%s in %s. type the deployment name to confirm: ", d.Name, d.Provider.Type)
			if readLine() != d.Name {
				fatalf("aborted")
			}
		}
		prov, err := newProvider(ctx, d, snap, rootCmd.Version)
		if err != nil {
			fatalf("%v", err)
		}
		if err := prov.Destroy(ctx, d); err != nil {
			fatalf("destroy: %v", err)
		}
		fmt.Println("destroyed. clearing gateway.url from deploy.yaml")
		_ = spec.WriteBack(fileFlag, func(dd *spec.Deployment) {
			dd.Gateway.URL = ""
		})
	},
}

var keyCmd = &cobra.Command{
	Use:   "key new",
	Short: "Generate an API key to paste into keys:",
	Run: func(cmd *cobra.Command, args []string) {
		fmt.Println(generateToken("sk-gr-"))
	},
}

var catalogCmd = &cobra.Command{
	Use:   "catalog [query]",
	Short: "List curated models",
	Run: func(cmd *cobra.Command, args []string) {
		cat, err := loadCatalog(catalogFlag)
		if err != nil {
			fatalf("%v", err)
		}
		q := ""
		if len(args) > 0 {
			q = strings.ToLower(args[0])
		}
		for _, r := range cat.List() {
			if q != "" && !strings.Contains(strings.ToLower(r.ID+" "+r.Type), q) {
				continue
			}
			fmt.Println(r.Summary())
		}
	},
}

var doctorCmd = &cobra.Command{
	Use:   "doctor",
	Short: "Check credentials, quotas and host readiness before apply",
	Run: func(cmd *cobra.Command, args []string) {
		ctx := context.Background()
		if len(args) > 0 && strings.HasPrefix(args[0], "ssh://") {
			doctorSSH(args[0])
			return
		}
		d, _, snap, err := loadForPlan(fileFlag, catalogFlag)
		if err != nil {
			fatalf("%v", err)
		}
		prov, err := newProvider(ctx, d, snap, rootCmd.Version)
		if err != nil {
			fatalf("%v", err)
		}
		if offs, err := prov.Offerings(ctx, d.Provider.Region); err != nil {
			fmt.Printf("offerings: ERROR %v\n", err)
		} else {
			fmt.Printf("offerings: %d available in %s\n", len(offs), d.Provider.Region)
		}
		if err := doctorProvider(ctx, prov, d); err != nil {
			fmt.Printf("provider check: %v\n", err)
		}
	},
}

func doctorSSH(target string) {
	c := strings.TrimPrefix(target, "ssh://")
	fmt.Printf("checking %s\n", c)
	for _, probe := range []struct {
		name, cmd string
	}{
		{"ssh reachable", "true"},
		{"docker", "command -v docker"},
		{"nvidia driver", "command -v nvidia-smi"},
		{"gpu count", "nvidia-smi --list-gpus | wc -l"},
		{"nvidia container toolkit", "docker info | grep -i nvidia || ls /etc/docker/daemon.json"},
	} {
		_ = exec.Command("ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5", c, probe.cmd).Run()
		fmt.Printf("  %-26s (verify manually: ssh %s %s)\n", probe.name, c, probe.cmd)
	}
}

var upgradeCmd = &cobra.Command{
	Use:   "upgrade",
	Short: "Download the latest release binary",
	Run: func(cmd *cobra.Command, args []string) {
		fatalf("upgrades arrive with the first tagged release; for now reinstall via install.sh")
	},
}

var guiCmd = &cobra.Command{
	Use:   "gui",
	Short: "Open the local web UI (binds to 127.0.0.1)",
	Run: func(cmd *cobra.Command, args []string) {
		s, err := gui.New(fileFlag, catalogFlag)
		if err != nil {
			fatalf("%v", err)
		}
		url, err := s.Start()
		if err != nil {
			fatalf("%v", err)
		}
		fmt.Printf("gui running at %s\n", url)
		if err := openBrowser(url); err != nil {
			fmt.Println("open the url above in your browser")
		}
		select {}
	},
}

func openBrowser(url string) error {
	runners := []string{"xdg-open", "open"}
	for _, r := range runners {
		if _, err := exec.LookPath(r); err == nil {
			return exec.Command(r, url).Start()
		}
	}
	return fmt.Errorf("no browser runner")
}
