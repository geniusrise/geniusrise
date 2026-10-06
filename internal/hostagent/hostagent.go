package hostagent

import (
	"context"
	"encoding/json"
	"fmt"
	"log/slog"
	"net"
	"os"
	"os/exec"
	"strings"
	"time"

	"github.com/geniusrise/geniusrise/internal/tunnel"
)

type Config struct {
	NodeID      string
	GatewayURL  string
	GatewayAddr string
	JoinToken   string
	HostID      string
	DockerBin   string
	PlainDial   bool
	Logger      *slog.Logger
}

type Agent struct {
	cfg    Config
	logger *slog.Logger
}

type ContainerSpec struct {
	GPUIndex int               `json:"gpu_index"`
	Name     string            `json:"name"`
	Image    string            `json:"image"`
	Env      map[string]string `json:"env"`
}

type ContainerInfo struct {
	Name  string `json:"name"`
	State string `json:"state"`
	GPU   int    `json:"gpu"`
	Model string `json:"model"`
}

func New(cfg Config) *Agent {
	if cfg.Logger == nil {
		cfg.Logger = slog.New(slog.NewTextHandler(os.Stderr, nil))
	}
	if cfg.DockerBin == "" {
		cfg.DockerBin = "docker"
	}
	return &Agent{cfg: cfg, logger: cfg.Logger}
}

func (a *Agent) HostNodeID() string {
	if a.cfg.HostID != "" {
		return "host-" + a.cfg.HostID
	}
	return "host-" + a.cfg.NodeID
}

func (a *Agent) Run(ctx context.Context) error {
	jr, keyPEM, _, jerr := tunnel.Join(ctx, a.cfg.GatewayURL, a.cfg.JoinToken)
	if jerr != nil {
		return fmt.Errorf("join: %w", jerr)
	}
	dialAddr := a.cfg.GatewayAddr
	if dialAddr == "" {
		dialAddr = strings.TrimPrefix(strings.TrimPrefix(a.cfg.GatewayURL, "https://"), "http://")
	}
	var rawConn net.Conn
	var err error
	if a.cfg.PlainDial {
		d := &net.Dialer{Timeout: 30 * time.Second}
		rawConn, err = d.DialContext(ctx, "tcp", dialAddr)
		if err == nil {
			if perr := tunnel.WritePlainPrefix(rawConn, a.HostNodeID()); perr != nil {
				rawConn.Close()
				return perr
			}
		}
	} else {
		tlsCfg, cerr := tunnel.ClientTLSConfig([]byte(jr.Cert), keyPEM, []byte(jr.CA), "")
		if cerr != nil {
			return cerr
		}
		rawConn, err = tunnel.DialTLS(ctx, dialAddr, tlsCfg)
	}
	if err != nil {
		return err
	}
	client, err := tunnel.Connect(a.HostNodeID(), dialAddr, rawConn)
	if err != nil {
		return fmt.Errorf("connect: %w", err)
	}
	defer client.Close()
	a.logger.Info("host agent connected", "host", a.HostNodeID())
	for ctx.Err() == nil {
		msg, err := client.ReadControl()
		if err != nil {
			return err
		}
		if msg.ReqID == "" {
			continue
		}
		reply := tunnel.Message{ReqID: msg.ReqID, Type: tunnel.MsgReply}
		switch msg.Type {
		case tunnel.MsgHostRun:
			var spec ContainerSpec
			if err := json.Unmarshal(msg.Data, &spec); err != nil {
				reply.Error = err.Error()
			} else if err := a.runContainer(ctx, spec); err != nil {
				reply.Error = err.Error()
			} else {
				reply.NodeID = spec.Name
			}
		case tunnel.MsgHostStop:
			var payload struct {
				Name string `json:"name"`
			}
			json.Unmarshal(msg.Data, &payload)
			if err := a.stopContainer(payload.Name); err != nil {
				reply.Error = err.Error()
			}
		case tunnel.MsgHostList:
			list, err := a.listContainers()
			if err != nil {
				reply.Error = err.Error()
			} else {
				data, _ := json.Marshal(list)
				reply.Data = data
			}
		default:
			continue
		}
		client.Send(reply)
	}
	return nil
}

func (a *Agent) runContainer(ctx context.Context, spec ContainerSpec) error {
	args := []string{"run", "-d", "--name", spec.Name, "--restart", "always",
		"--read-only", "--tmpfs", "/tmp"}
	if spec.GPUIndex >= 0 {
		args = append(args, "--gpus", fmt.Sprintf("device=%d", spec.GPUIndex))
	}
	args = append(args,
		"--label", "geniusrise.managed=1",
		"--label", fmt.Sprintf("geniusrise.gpu=%d", spec.GPUIndex),
		"--label", "geniusrise.model="+spec.Env["GR_MODEL"],
	)
	for k, v := range spec.Env {
		args = append(args, "-e", k+"="+v)
	}
	args = append(args, spec.Image)
	cmd := exec.CommandContext(ctx, a.cfg.DockerBin, args...)
	out, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("docker run %s: %s", spec.Name, strings.TrimSpace(string(out)))
	}
	a.logger.Info("started container", "name", spec.Name, "gpu", spec.GPUIndex)
	return nil
}

func (a *Agent) stopContainer(name string) error {
	cmd := exec.Command(a.cfg.DockerBin, "rm", "-f", name)
	out, err := cmd.CombinedOutput()
	if err != nil && !strings.Contains(string(out), "No such object") {
		return fmt.Errorf("docker rm %s: %s", name, strings.TrimSpace(string(out)))
	}
	return nil
}

func (a *Agent) listContainers() ([]ContainerInfo, error) {
	cmd := exec.Command(a.cfg.DockerBin, "ps", "-a",
		"--filter", "name=gr-",
		"--format", "{{.Names}}\t{{.Status}}\t{{.Label \"geniusrise.model\"}}\t{{.Label \"geniusrise.gpu\"}}")
	out, err := cmd.Output()
	if err != nil {
		return nil, err
	}
	var list []ContainerInfo
	for _, line := range strings.Split(strings.TrimSpace(string(out)), "\n") {
		if line == "" {
			continue
		}
		parts := strings.Split(line, "\t")
		info := ContainerInfo{Name: parts[0], State: "unknown"}
		if len(parts) > 1 {
			info.State = parts[1]
		}
		if len(parts) > 2 {
			info.Model = parts[2]
		}
		if len(parts) > 3 {
			fmt.Sscanf(parts[3], "%d", &info.GPU)
		}
		list = append(list, info)
	}
	return list, nil
}
