package node

import (
	"bytes"
	"context"
	"crypto/tls"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"net/http"
	"os"
	"os/exec"
	"strings"
	"sync"
	"time"

	"github.com/geniusrise/geniusrise/internal/tunnel"
)

type Config struct {
	NodeID      string
	GatewayURL  string
	GatewayAddr string
	JoinToken   string
	CAFingerprint string
	AdminPort   int
	AdminToken  string
	HFToken     string

	EngineCmd    []string
	EngineEnv    map[string]string
	EnginePort   int
	EngineType   string
	ExternalURL  string
	ReadyTimeout time.Duration
}

const (
	heartbeatInterval = 5 * time.Second
	canaryInterval    = 60 * time.Second
	spotPollInterval  = 5 * time.Second
	maxRestartsWindow = 3
	restartWindow     = 10 * time.Minute
)

type Agent struct {
	cfg    Config
	mu     sync.Mutex
	cmd    *exec.Cmd
	logs   ringBuffer
	inflight int
	restarts []time.Time
	unhealthy bool
	engineReady bool
	spotNotice bool
	client *tunnel.Client
}

func New(cfg Config) *Agent {
	if cfg.ReadyTimeout == 0 {
		cfg.ReadyTimeout = 10 * time.Minute
	}
	if cfg.AdminPort == 0 {
		cfg.AdminPort = 9101
	}
	return &Agent{cfg: cfg}
}

func (a *Agent) Inflight() int {
	a.mu.Lock()
	defer a.mu.Unlock()
	return a.inflight
}

func (a *Agent) MarkUnhealthy() {
	a.mu.Lock()
	defer a.mu.Unlock()
	a.unhealthy = true
}

func (a *Agent) Run(ctx context.Context) error {
	if err := a.startEngine(ctx); err != nil {
		return fmt.Errorf("engine: %w", err)
	}
	adminLn, err := net.Listen("tcp", fmt.Sprintf("127.0.0.1:%d", a.cfg.AdminPort))
	if err != nil {
		return err
	}
	go a.serveAdmin(adminLn)

	jr, keyPEM, _, err := tunnel.Join(ctx, a.cfg.GatewayURL, a.cfg.JoinToken)
	if err != nil {
		return fmt.Errorf("join: %w", err)
	}
	tlsCfg, err := tunnel.ClientTLSConfig([]byte(jr.Cert), keyPEM, []byte(jr.CA), a.cfg.CAFingerprint)
	if err != nil {
		return err
	}
	dialAddr := a.cfg.GatewayAddr
	if dialAddr == "" {
		dialAddr = strings.TrimPrefix(strings.TrimPrefix(a.cfg.GatewayURL, "https://"), "http://")
	}
	conn, err := tunnel.DialTLS(ctx, dialAddr, tlsCfg)
	if err != nil {
		return fmt.Errorf("tunnel dial: %w", err)
	}
	tlsConn := conn.(*tls.Conn)
	client, err := tunnel.Connect(a.cfg.NodeID, dialAddr, tlsConn)
	if err != nil {
		return fmt.Errorf("tunnel connect: %w", err)
	}
	client.LocalDial = a.localDial
	a.mu.Lock()
	a.client = client
	a.mu.Unlock()
	defer client.Close()

	go a.watchControl(ctx, client)
	go a.heartbeats(ctx, client)
	go a.canaries(ctx, client)
	go a.watchSpot(ctx, client)

	<-ctx.Done()
	a.sendMsg(tunnel.Message{Type: tunnel.MsgDrain})
	a.stopEngine()
	return nil
}

func (a *Agent) localDial(port uint16) (net.Conn, error) {
	if port == uint16(a.cfg.AdminPort) {
		return net.DialTimeout("tcp", fmt.Sprintf("127.0.0.1:%d", a.cfg.AdminPort), 5*time.Second)
	}
	a.mu.Lock()
	a.inflight++
	a.mu.Unlock()
	conn, err := net.DialTimeout("tcp", fmt.Sprintf("127.0.0.1:%d", port), 5*time.Second)
	if err != nil {
		a.mu.Lock()
		a.inflight--
		a.mu.Unlock()
		return nil, err
	}
	go func() {
		buf := make([]byte, 1)
		for {
			if _, err := conn.Read(buf); err != nil {
				a.mu.Lock()
				a.inflight--
				a.mu.Unlock()
				return
			}
		}
	}()
	return conn, nil
}

func (a *Agent) startEngine(ctx context.Context) error {
	if a.cfg.ExternalURL != "" {
		if err := waitReady(ctx, a.cfg.ExternalURL+"/health", a.cfg.ReadyTimeout); err != nil {
			return err
		}
		a.mu.Lock()
		a.engineReady = true
		a.mu.Unlock()
		return nil
	}
	if len(a.cfg.EngineCmd) == 0 {
		return fmt.Errorf("no engine command")
	}
	cmd := exec.CommandContext(ctx, a.cfg.EngineCmd[0], a.cfg.EngineCmd[1:]...)
	cmd.Stdout = &a.logs
	cmd.Stderr = &a.logs
	cmd.Env = os.Environ()
	for k, v := range a.cfg.EngineEnv {
		cmd.Env = append(cmd.Env, k+"="+v)
	}
	if err := cmd.Start(); err != nil {
		return err
	}
	a.mu.Lock()
	a.cmd = cmd
	a.mu.Unlock()
	go func() {
		err := cmd.Wait()
		a.mu.Lock()
		a.engineReady = false
		a.mu.Unlock()
		if ctx.Err() != nil {
			return
		}
		a.logs.Write([]byte(fmt.Sprintf("[agent] engine exited: %v\n", err)))
		a.restartEngine(ctx)
	}()
	return waitReady(ctx, fmt.Sprintf("http://127.0.0.1:%d/health", a.cfg.EnginePort), a.cfg.ReadyTimeout)
}

func (a *Agent) restartEngine(ctx context.Context) {
	a.mu.Lock()
	now := time.Now()
	a.restarts = append(a.restarts, now)
	recent := 0
	for _, t := range a.restarts {
		if now.Sub(t) < restartWindow {
			recent++
		}
	}
	tooMany := recent > maxRestartsWindow
	a.mu.Unlock()
	if tooMany {
		a.MarkUnhealthy()
		return
	}
	backoff := time.Duration(recent) * 5 * time.Second
	select {
	case <-time.After(backoff):
	case <-ctx.Done():
		return
	}
	child, cancel := context.WithCancel(ctx)
	defer cancel()
	_ = a.startEngine(child)
}

func (a *Agent) stopEngine() {
	a.mu.Lock()
	cmd := a.cmd
	a.mu.Unlock()
	if cmd != nil && cmd.Process != nil {
		cmd.Process.Kill()
	}
}

func (a *Agent) EngineURL() string {
	if a.cfg.ExternalURL != "" {
		return strings.TrimSuffix(a.cfg.ExternalURL, "/")
	}
	return fmt.Sprintf("http://127.0.0.1:%d", a.cfg.EnginePort)
}

func waitReady(ctx context.Context, url string, timeout time.Duration) error {
	deadline := time.Now().Add(timeout)
	client := &http.Client{Timeout: 2 * time.Second}
	for time.Now().Before(deadline) {
		resp, err := client.Get(url)
		if err == nil {
			resp.Body.Close()
			if resp.StatusCode < 500 {
				return nil
			}
		}
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-time.After(2 * time.Second):
		}
	}
	return fmt.Errorf("engine not ready at %s after %s", url, timeout)
}

func (a *Agent) heartbeats(ctx context.Context, c *tunnel.Client) {
	t := time.NewTicker(heartbeatInterval)
	defer t.Stop()
	for {
		select {
		case <-ctx.Done():
			return
		case <-t.C:
			a.mu.Lock()
			unhealthy := a.unhealthy
			inflight := a.inflight
			a.mu.Unlock()
			msg := tunnel.Message{Type: tunnel.MsgHeartbeat, NodeID: a.cfg.NodeID, Inflight: inflight}
			if unhealthy {
				msg.Type = tunnel.MsgUnhealthy
			}
			a.sendMsg(msg)
		}
	}
}

func (a *Agent) sendMsg(msg tunnel.Message) {
	a.mu.Lock()
	c := a.client
	a.mu.Unlock()
	if c != nil {
		c.Send(msg)
	}
}

func (a *Agent) watchControl(ctx context.Context, c *tunnel.Client) {
	for ctx.Err() == nil {
		msg, err := c.ReadControl()
		if err != nil {
			return
		}
		switch msg.Type {
		case tunnel.MsgRestart:
			child, cancel := context.WithCancel(context.Background())
			a.stopEngine()
			_ = a.startEngine(child)
			cancel()
		case tunnel.MsgTerminate:
			a.logs.Write([]byte("[agent] terminate requested\n"))
			a.stopEngine()
			c.Close()
			os.Exit(0)
		}
	}
}

func (a *Agent) canaries(ctx context.Context, c *tunnel.Client) {
	t := time.NewTicker(canaryInterval)
	defer t.Stop()
	for {
		select {
		case <-ctx.Done():
			return
		case <-t.C:
			if err := a.canary(); err != nil {
				a.logs.Write([]byte(fmt.Sprintf("[agent] canary failed: %v\n", err)))
				child, cancel := context.WithCancel(ctx)
				a.stopEngine()
				a.restartEngine(child)
				cancel()
			}
		}
	}
}

func (a *Agent) canary() error {
	client := &http.Client{Timeout: 60 * time.Second}
	var body []byte
	switch a.cfg.EngineType {
	case "speaches":
		body, _ = json.Marshal(map[string]any{"model": "canary", "input": "hi"})
		return postJSON(client, a.EngineURL()+"/v1/audio/speech", body)
	default:
		body, _ = json.Marshal(map[string]any{
			"model": "canary", "max_tokens": 1,
			"messages": []map[string]string{{"role": "user", "content": "ping"}},
		})
		return postJSON(client, a.EngineURL()+"/v1/chat/completions", body)
	}
}

func postJSON(client *http.Client, url string, body []byte) error {
	resp, err := client.Post(url, "application/json", bytes.NewReader(body))
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	io.Copy(io.Discard, io.LimitReader(resp.Body, 4096))
	if resp.StatusCode >= 500 {
		return fmt.Errorf("canary status %d", resp.StatusCode)
	}
	return nil
}

func (a *Agent) watchSpot(ctx context.Context, c *tunnel.Client) {
	for {
		select {
		case <-ctx.Done():
			return
		case <-time.After(spotPollInterval):
			if a.spotNotice {
				continue
			}
			if provider, ok := spotInterrupted(); ok {
				a.mu.Lock()
				a.spotNotice = true
				a.mu.Unlock()
				a.logs.Write([]byte(fmt.Sprintf("[agent] spot interruption notice from %s\n", provider)))
				a.sendMsg(tunnel.Message{Type: tunnel.MsgSpotNotice, NodeID: a.cfg.NodeID})
				time.Sleep(90 * time.Second)
				a.stopEngine()
				os.Exit(0)
			}
		}
	}
}

var metadataClient = &http.Client{Timeout: 2 * time.Second}

func imdsToken() string {
	req, _ := http.NewRequest(http.MethodPut, "http://169.254.169.254/latest/api/token", nil)
	req.Header.Set("X-aws-ec2-metadata-token-ttl-seconds", "300")
	resp, err := metadataClient.Do(req)
	if err != nil {
		return ""
	}
	defer resp.Body.Close()
	b, _ := io.ReadAll(resp.Body)
	return string(b)
}

func spotInterrupted() (string, bool) {
	token := imdsToken()
	if token != "" {
		req, _ := http.NewRequest(http.MethodGet, "http://169.254.169.254/latest/meta-data/spot/instance-action", nil)
		req.Header.Set("X-aws-ec2-metadata-token", token)
		if resp, err := metadataClient.Do(req); err == nil {
			resp.Body.Close()
			if resp.StatusCode == http.StatusOK {
				return "aws", true
			}
		}
	}
	req, _ := http.NewRequest(http.MethodGet, "http://metadata.google.internal/computeMetadata/v1/instance/preempted", nil)
	req.Header.Set("Metadata-Flavor", "Google")
	if resp, err := metadataClient.Do(req); err == nil {
		defer resp.Body.Close()
		if resp.StatusCode == http.StatusOK {
			if b, _ := io.ReadAll(resp.Body); string(b) == "TRUE" {
				return "gcp", true
			}
		}
	}
	req2, _ := http.NewRequest(http.MethodPost, "http://169.254.169.254/metadata/scheduledevents?api-version=2019-08-01", nil)
	if resp, err := metadataClient.Do(req2); err == nil {
		defer resp.Body.Close()
		if resp.StatusCode == http.StatusOK {
			var ev struct {
				Events []struct {
					EventType string `json:"EventType"`
					Status    string `json:"Status"`
				} `json:"Events"`
			}
			if err := json.NewDecoder(resp.Body).Decode(&ev); err == nil {
				for _, e := range ev.Events {
					if e.Status == "Scheduled" && (e.EventType == "Preempt" || e.EventType == "Terminate") {
						return "azure", true
					}
				}
			}
		}
	}
	return "", false
}

type ringBuffer struct {
	mu  sync.Mutex
	buf []byte
	max int
}

func (r *ringBuffer) Write(p []byte) (int, error) {
	r.mu.Lock()
	defer r.mu.Unlock()
	if r.max == 0 {
		r.max = 128 * 1024
	}
	r.buf = append(r.buf, p...)
	if len(r.buf) > r.max {
		r.buf = r.buf[len(r.buf)-r.max:]
	}
	return len(p), nil
}

func (r *ringBuffer) Bytes() []byte {
	r.mu.Lock()
	defer r.mu.Unlock()
	out := make([]byte, len(r.buf))
	copy(out, r.buf)
	return out
}

func (a *Agent) serveAdmin(ln net.Listener) {
	mux := http.NewServeMux()
	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("ok"))
	})
	mux.HandleFunc("/logs", func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Query().Get("token") != a.cfg.AdminToken {
			http.Error(w, "forbidden", http.StatusForbidden)
			return
		}
		w.Header().Set("Content-Type", "text/plain")
		w.Write(a.logs.Bytes())
	})
	mux.HandleFunc("/metrics", func(w http.ResponseWriter, r *http.Request) {
		a.mu.Lock()
		inflight := a.inflight
		unhealthy := a.unhealthy
		restarts := len(a.restarts)
		a.mu.Unlock()
		fmt.Fprintf(w, "# TYPE geniusrise_node_inflight gauge\n")
		fmt.Fprintf(w, "geniusrise_node_inflight %d\n", inflight)
		fmt.Fprintf(w, "# TYPE geniusrise_node_unhealthy gauge\n")
		fmt.Fprintf(w, "geniusrise_node_unhealthy %d\n", boolToInt(unhealthy))
		fmt.Fprintf(w, "# TYPE geniusrise_node_restarts counter\n")
		fmt.Fprintf(w, "geniusrise_node_restarts %d\n", restarts)
	})
	srv := &http.Server{Handler: mux}
	srv.Serve(ln)
}

func boolToInt(b bool) int {
	if b {
		return 1
	}
	return 0
}
