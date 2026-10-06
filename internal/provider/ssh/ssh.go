package ssh

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"

	"golang.org/x/crypto/ssh"

	"github.com/geniusrise/geniusrise/internal/hostagent"
	"github.com/geniusrise/geniusrise/internal/pricing"
	"github.com/geniusrise/geniusrise/internal/provider"
	"github.com/geniusrise/geniusrise/internal/spec"
	"github.com/geniusrise/geniusrise/internal/tunnel"
)

type CallFunc func(nodeID string, msg tunnel.Message, timeout time.Duration) (*tunnel.Message, error)

type Provider struct {
	hosts []spec.SSHHost
	call  CallFunc
}

func New(d *spec.Deployment, call CallFunc) *Provider {
	return &Provider{hosts: d.Provider.Hosts, call: call}
}

func (p *Provider) Name() string { return spec.ProviderSSH }

func (p *Provider) SetCall(call CallFunc) { p.call = call }

func hostID(h spec.SSHHost) string {
	return strings.ReplaceAll(net.JoinHostPort(h.Addr, "22"), ":", "-")
}

func (p *Provider) hostByNode(nodeID string) spec.SSHHost {
	for _, h := range p.hosts {
		if strings.HasPrefix(nodeID, "gr-host-"+strings.ReplaceAll(hostID(h), ".", "-")) {
			return h
		}
	}
	if len(p.hosts) > 0 {
		return p.hosts[0]
	}
	return spec.SSHHost{}
}

func sshClient(h spec.SSHHost) (*ssh.Client, error) {
	keyPath := os.Getenv("GR_SSH_KEY")
	if keyPath == "" {
		if home, err := os.UserHomeDir(); err == nil {
			keyPath = filepath.Join(home, ".ssh", "id_ed25519")
			if _, err := os.Stat(keyPath); err != nil {
				keyPath = filepath.Join(home, ".ssh", "id_rsa")
			}
		}
	}
	var signer ssh.Signer
	if data, err := os.ReadFile(keyPath); err == nil {
		if s, err := ssh.ParsePrivateKey(data); err == nil {
			signer = s
		}
	}
	config := &ssh.ClientConfig{
		User:            h.User,
		HostKeyCallback: ssh.InsecureIgnoreHostKey(),
		Timeout:         15 * time.Second,
	}
	if signer != nil {
		config.Auth = []ssh.AuthMethod{ssh.PublicKeys(signer)}
	}
	return ssh.Dial("tcp", net.JoinHostPort(h.Addr, "22"), config)
}

func runSSH(client *ssh.Client, cmd string) (string, error) {
	sess, err := client.NewSession()
	if err != nil {
		return "", err
	}
	defer sess.Close()
	var out, errOut bytes.Buffer
	sess.Stdout = &out
	sess.Stderr = &errOut
	if err := sess.Run(cmd); err != nil {
		return out.String(), fmt.Errorf("%w: %s", err, strings.TrimSpace(errOut.String()))
	}
	return out.String(), nil
}

func (p *Provider) Bootstrap(ctx context.Context, d *spec.Deployment, opts provider.BootstrapOpts) (*provider.GatewayInfo, error) {
	if len(p.hosts) == 0 {
		return nil, fmt.Errorf("no ssh hosts configured")
	}
	host := p.hosts[0]
	client, err := sshClient(host)
	if err != nil {
		return nil, fmt.Errorf("ssh %s: %w (set GR_SSH_KEY if needed)", host.Addr, err)
	}
	defer client.Close()
	if _, err := runSSH(client, "command -v docker >/dev/null || { echo 'docker missing: install docker first' >&2; exit 1; }"); err != nil {
		return nil, err
	}
	if _, err := runSSH(client, "command -v nvidia-smi >/dev/null || echo 'warning: nvidia-smi not found (cpu-only host?)' >&2"); err != nil {
		return nil, err
	}
	image := opts.GatewayImage
	if image == "" {
		image = "ghcr.io/geniusrise/geniusrise:latest"
	}
	gwCmd := fmt.Sprintf(
		"docker run -d --name gr-%s-gateway --restart always -p 443:443 -v /var/lib/geniusrise:/data "+
			"-e GR_MODE=gateway -e GR_DATA_DIR=/data -e GR_ADMIN_TOKEN=%s -e GR_VERSION=%s %s",
		d.Name, opts.AdminToken, opts.Version, image)
	if out, err := runSSH(client, "docker inspect gr-"+d.Name+"-gateway >/dev/null 2>&1 || "+gwCmd); err != nil {
		return nil, fmt.Errorf("start gateway container: %w (%s)", err, out)
	}
	ip, err := runSSH(client, "hostname -I | awk '{print $1}'")
	if err != nil {
		ip = host.Addr
	}
	addr := strings.TrimSpace(ip)
	return &provider.GatewayInfo{
		URL:        "http://" + addr,
		AdminToken: opts.AdminToken,
		HostAddr:   addr + ":443",
	}, nil
}

func (p *Provider) Offerings(ctx context.Context, region string) ([]pricing.Offering, error) {
	var out []pricing.Offering
	for _, h := range p.hosts {
		out = append(out, pricing.Offering{
			GPUClass:     "cpu",
			InstanceType: "ssh:" + h.Addr,
			Capacity:     pricing.CapacityOnDemand,
			USDPerHour:   h.CostHr,
			Available:    true,
		})
	}
	return out, nil
}

func (p *Provider) Launch(ctx context.Context, n provider.NodeSpec) (provider.Node, error) {
	if p.call == nil {
		return provider.Node{}, fmt.Errorf("ssh provider requires the gateway call bus")
	}
	used, err := p.usedGPUs()
	if err != nil {
		return provider.Node{}, err
	}
	chosen := spec.SSHHost{}
	chosenGPU := -1
	for _, h := range p.hosts {
		for i := 0; i < h.GPUs; i++ {
			key := h.Addr + "#" + fmt.Sprint(i)
			if !used[key] {
				chosen, chosenGPU, used[key] = h, i, true
				break
			}
		}
		if chosenGPU >= 0 {
			break
		}
	}
	if chosenGPU < 0 {
		return provider.Node{}, fmt.Errorf("no free gpu slots in the ssh pool")
	}
	name := fmt.Sprintf("gr-node-%s-%d", strings.ReplaceAll(n.Model, ".", "-"), time.Now().UnixNano()%1e6)
	env := map[string]string{}
	for k, v := range n.Env {
		env[k] = v
	}
	env["GR_IMAGE"] = n.Image
	env["GR_MODEL"] = n.Model
	data, _ := json.Marshal(hostagent.ContainerSpec{
		GPUIndex: chosenGPU, Name: name, Image: imageFor(env), Env: env,
	})
	reply, err := p.call(hostNodeID(chosen), tunnel.Message{Type: tunnel.MsgHostRun, Data: data}, 60*time.Second)
	if err != nil {
		return provider.Node{}, err
	}
	_ = reply
	cost := 0.0
	for _, h := range p.hosts {
		cost += h.CostHr
	}
	return provider.Node{
		ID: name, State: provider.StateLaunching, GPUClass: "cpu",
		InstanceType: "ssh:" + chosen.Addr, Capacity: spec.CapacityOnDemand,
		PricePerHour: cost / float64(totalGPUs(p.hosts)), LaunchedAt: time.Now().UTC(),
		Model: n.Model, Tags: n.Tags(),
	}, nil
}

func imageFor(env map[string]string) string {
	if v := env["GR_IMAGE"]; v != "" {
		return v
	}
	return "ghcr.io/geniusrise/geniusrise:latest"
}

func totalGPUs(hosts []spec.SSHHost) int {
	t := 0
	for _, h := range hosts {
		t += h.GPUs
	}
	return t
}

func hostNodeID(h spec.SSHHost) string {
	return "host-" + strings.ReplaceAll(strings.ReplaceAll(h.Addr, ".", "-"), ":", "-")
}

func (p *Provider) usedGPUs() (map[string]bool, error) {
	used := map[string]bool{}
	if p.call == nil {
		return used, nil
	}
	for _, h := range p.hosts {
		reply, err := p.call(hostNodeID(h), tunnel.Message{Type: tunnel.MsgHostList}, 15*time.Second)
		if err != nil {
			continue
		}
		var list []hostagent.ContainerInfo
		if err := json.Unmarshal(reply.Data, &list); err != nil {
			continue
		}
		for _, c := range list {
			if strings.Contains(c.State, "Up") || strings.Contains(c.State, "Created") || strings.Contains(c.State, "Restarting") {
				used[h.Addr+"#"+fmt.Sprint(c.GPU)] = true
			}
		}
	}
	return used, nil
}

func (p *Provider) List(ctx context.Context, deployment string) ([]provider.Node, error) {
	var out []provider.Node
	if p.call == nil {
		return out, nil
	}
	for _, h := range p.hosts {
		reply, err := p.call(hostNodeID(h), tunnel.Message{Type: tunnel.MsgHostList}, 15*time.Second)
		if err != nil {
			continue
		}
		var list []hostagent.ContainerInfo
		if err := json.Unmarshal(reply.Data, &list); err != nil {
			continue
		}
		for _, c := range list {
			if !strings.HasPrefix(c.Name, "gr-node-") {
				continue
			}
			state := provider.StateRunning
			if !strings.Contains(c.State, "Up") {
				state = provider.StateTerminated
			}
			out = append(out, provider.Node{
				ID: c.Name, State: state, GPUClass: "cpu",
				InstanceType: "ssh:" + h.Addr, Capacity: spec.CapacityOnDemand,
				Model: c.Model, LaunchedAt: time.Now().UTC(),
			})
		}
	}
	sort.Slice(out, func(i, j int) bool { return out[i].ID < out[j].ID })
	return out, nil
}

func (p *Provider) Terminate(ctx context.Context, id string) error {
	if p.call == nil {
		return fmt.Errorf("gateway call bus unavailable")
	}
	data, _ := json.Marshal(map[string]string{"name": id})
	for _, h := range p.hosts {
		if _, err := p.call(hostNodeID(h), tunnel.Message{Type: tunnel.MsgHostStop, Data: data}, 30*time.Second); err == nil {
			return nil
		}
	}
	return fmt.Errorf("no host could stop %s", id)
}

func (p *Provider) Destroy(ctx context.Context, d *spec.Deployment) error {
	nodes, err := p.List(ctx, d.Name)
	if err != nil {
		return err
	}
	for _, n := range nodes {
		if err := p.Terminate(ctx, n.ID); err != nil {
			return err
		}
	}
	if len(p.hosts) > 0 {
		client, err := sshClient(p.hosts[0])
		if err != nil {
			return nil
		}
		defer client.Close()
		runSSH(client, "docker rm -f gr-"+d.Name+"-gateway >/dev/null 2>&1 || true")
	}
	return nil
}
