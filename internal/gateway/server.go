package gateway

import (
	"context"
	"crypto/tls"
	"encoding/binary"
	"io"
	"log/slog"
	"net"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"

	"github.com/geniusrise/geniusrise/internal/catalog"
	"github.com/geniusrise/geniusrise/internal/pricing"
	"github.com/geniusrise/geniusrise/internal/provider"
	"github.com/geniusrise/geniusrise/internal/spec"
	"github.com/geniusrise/geniusrise/internal/tunnel"
)

type Options struct {
	DataDir    string
	Addr       string
	Provider   provider.Provider
	Catalog    *catalog.Catalog
	Prices     *pricing.Snapshot
	Version    string
	Logger     *slog.Logger
	AdminToken string
	PlainHTTP  bool
}

type nodeEntry struct {
	ID           string
	Model        string
	State        string
	JoinToken    string
	LaunchedAt   time.Time
	LastBeat     time.Time
	Inflight     int
	Unhealthy    bool
	PricePerHour float64
}

type pool struct {
	mu        sync.Mutex
	model     spec.Model
	recipe    *catalog.Recipe
	variant   *catalog.Variant
	nodes     map[string]*nodeEntry
	history   []float64
	lowSince  time.Time
	idleSince time.Time
	tunnels   *tunnel.Server
}

func (p *pool) readyNodes() []*nodeEntry {
	p.mu.Lock()
	defer p.mu.Unlock()
	var out []*nodeEntry
	for _, n := range p.nodes {
		if n.State == provider.StateRunning && !n.Unhealthy && p.tunnels.Connected(n.ID) {
			out = append(out, n)
		}
	}
	return out
}

func (p *pool) countByState() (launching, running int) {
	p.mu.Lock()
	defer p.mu.Unlock()
	for _, n := range p.nodes {
		if n.State == provider.StateLaunching {
			launching++
		}
		if n.State == provider.StateRunning {
			running++
		}
	}
	return
}

func (p *pool) recordInflight(v int) {
	p.mu.Lock()
	defer p.mu.Unlock()
	p.history = append(p.history, float64(v))
	if len(p.history) > 12 {
		p.history = p.history[len(p.history)-12:]
	}
}

func (p *pool) avgInflight1m() float64 {
	p.mu.Lock()
	defer p.mu.Unlock()
	if len(p.history) == 0 {
		return 0
	}
	sum := 0.0
	for _, v := range p.history {
		sum += v
	}
	return sum / float64(len(p.history))
}

type Server struct {
	opts   Options
	logger *slog.Logger

	cfgMu sync.RWMutex
	cfg   *spec.Deployment

	state   *State
	tunnels *tunnel.Server
	ca      *tunnel.CA
	tm      *tunnel.TokenManager

	poolsMu sync.Mutex
	pools   map[string]*pool

	joinTokensMu sync.Mutex
	joinTokens   map[string]string

	metricsMu sync.Mutex
	metrics   map[string]float64

	auth        *authStore
	publicBase  string
	fingerprint string
	httpSrv     *http.Server
	ln          net.Listener
	stopCh      chan struct{}
	stopOnce    sync.Once
}

func New(opts Options) (*Server, error) {
	if opts.Logger == nil {
		opts.Logger = slog.New(slog.NewTextHandler(os.Stderr, nil))
	}
	if err := os.MkdirAll(opts.DataDir, 0o700); err != nil {
		return nil, err
	}
	ca, err := tunnel.LoadOrCreateCA(filepath.Join(opts.DataDir, "ca"))
	if err != nil {
		return nil, err
	}
	state, err := LoadState(filepath.Join(opts.DataDir, "state.json"))
	if err != nil {
		return nil, err
	}
	s := &Server{
		opts:       opts,
		auth:       newAuthStore(),
		logger:     opts.Logger,
		state:      state,
		ca:         ca,
		tm:         tunnel.NewTokenManager(30 * time.Minute),
		tunnels:    tunnel.NewServer(),
		pools:      map[string]*pool{},
		joinTokens: map[string]string{},
		metrics:    map[string]float64{},
		stopCh:     make(chan struct{}),
	}
	cfgPath := filepath.Join(opts.DataDir, "config.yaml")
	if data, err := os.ReadFile(cfgPath); err == nil {
		if cfg, err := spec.Parse(data); err == nil {
			s.cfg = cfg
		} else {
			s.logger.Error("saved config invalid", "err", err)
		}
	}
	s.tunnels.OnMessage = s.onNodeMessage
	if cb, ok := opts.Provider.(interface {
		SetCall(func(nodeID string, msg tunnel.Message, timeout time.Duration) (*tunnel.Message, error))
	}); ok {
		cb.SetCall(s.tunnels.Call)
	}
	return s, nil
}

func (s *Server) Addr() string {
	if s.ln == nil {
		return ""
	}
	return s.ln.Addr().String()
}

func (s *Server) Config() *spec.Deployment {
	s.cfgMu.RLock()
	defer s.cfgMu.RUnlock()
	return s.cfg
}

func (s *Server) setConfig(cfg *spec.Deployment) {
	s.cfgMu.Lock()
	s.cfg = cfg
	s.cfgMu.Unlock()
}

func (s *Server) Start(ctx context.Context) error {
	mux := http.NewServeMux()
	mux.HandleFunc("/node/join", s.handleJoin)
	mux.HandleFunc("/v1/models", s.authPublic(s.handleModels))
	mux.HandleFunc("/v1/chat/completions", s.authPublic(s.handleChat))
	mux.HandleFunc("/v1/completions", s.authPublic(s.handleChat))
	mux.HandleFunc("/v1/audio/transcriptions", s.authPublic(s.handleAudioSTT))
	mux.HandleFunc("/v1/audio/speech", s.authPublic(s.handleAudioTTS))
	mux.HandleFunc("/admin/config", s.authAdmin(s.handleAdminConfig))
	mux.HandleFunc("/admin/status", s.authAdmin(s.handleAdminStatus))
	mux.HandleFunc("/admin/usage", s.authAdmin(s.handleAdminUsage))
	mux.HandleFunc("/admin/logs", s.authAdmin(s.handleAdminLogs))
	mux.HandleFunc("/admin/nodes/", s.authAdmin(s.handleAdminNodeAction))
	mux.HandleFunc("/admin/version", s.authAdmin(s.handleAdminVersion))
	mux.HandleFunc("/metrics", s.authAdmin(s.handleMetrics))
	mux.HandleFunc("/healthz", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("ok"))
	})

	ln, err := net.Listen("tcp", s.opts.Addr)
	if err != nil {
		return err
	}
	s.ln = ln
	s.httpSrv = &http.Server{
		Handler:           mux,
		ReadHeaderTimeout: 10 * time.Second,
	}

	cert, fingerprint, err := tunnel.SelfSignedCert([]string{"localhost", strings.ReplaceAll(ln.Addr().String(), ":", "-")})
	if err != nil {
		return err
	}
	s.fingerprint = fingerprint
	apiTLS := tunnel.TLSConfig(cert, s.ca)

	demux := newDemuxListener(ln.Addr())
	go s.httpSrv.Serve(demux)
	go func() {
		for {
			conn, err := ln.Accept()
			if err != nil {
				return
			}
			go s.routeConn(conn, demux, apiTLS)
		}
	}()

	s.rebuildPools()
	go s.loop(ctx, 15*time.Second, s.reconcile)
	go s.loop(ctx, 15*time.Second, s.enforceBudget)
	go s.loop(ctx, 30*time.Second, func(ctx context.Context) {
		if err := s.state.Save(filepath.Join(s.opts.DataDir, "state.json")); err != nil {
			s.logger.Error("state save failed", "err", err)
		}
	})
	s.logger.Info("gateway listening", "addr", ln.Addr().String())
	<-s.stopCh
	return nil
}

func (s *Server) routeConn(conn net.Conn, demux *demuxListener, cfg *tls.Config) {
	if s.opts.PlainHTTP {
		first := make([]byte, 1)
		conn.SetReadDeadline(time.Now().Add(30 * time.Second))
		if _, err := io.ReadFull(conn, first); err != nil {
			conn.Close()
			return
		}
		conn.SetReadDeadline(time.Time{})
		if first[0] == tunnel.PlainPrefixByte {
			var lenBuf [2]byte
			if _, err := io.ReadFull(conn, lenBuf[:]); err != nil {
				conn.Close()
				return
			}
			id := make([]byte, binary.BigEndian.Uint16(lenBuf[:]))
			if _, err := io.ReadFull(conn, id); err != nil {
				conn.Close()
				return
			}
			if err := s.tunnels.HandleSession(string(id), conn); err != nil {
				conn.Close()
			}
			return
		}
		select {
		case demux.conns <- &prefixConn{Conn: conn, prefix: first}:
		case <-demux.done:
			conn.Close()
		}
		return
	}
	tc := tls.Server(conn, cfg)
	if err := tc.Handshake(); err != nil {
		tc.Close()
		return
	}
	if tc.ConnectionState().NegotiatedProtocol == tunnel.ALPN {
		nodeID := "unknown"
		if len(tc.ConnectionState().PeerCertificates) > 0 {
			nodeID = tc.ConnectionState().PeerCertificates[0].Subject.CommonName
		}
		if err := s.tunnels.HandleSession(nodeID, tc); err != nil {
			tc.Close()
		}
		return
	}
	select {
	case demux.conns <- tc:
	case <-demux.done:
		tc.Close()
	}
}

func (s *Server) Stop() {
	s.stopOnce.Do(func() {
		close(s.stopCh)
		if s.httpSrv != nil {
			s.httpSrv.Close()
		}
		if s.ln != nil {
			s.ln.Close()
		}
	})
}

func (s *Server) loop(ctx context.Context, every time.Duration, fn func(context.Context)) {
	t := time.NewTicker(every)
	defer t.Stop()
	for {
		select {
		case <-ctx.Done():
			return
		case <-s.stopCh:
			return
		case <-t.C:
			fn(ctx)
		}
	}
}

type prefixConn struct {
	net.Conn
	prefix []byte
}

func (c *prefixConn) Read(p []byte) (int, error) {
	if len(c.prefix) > 0 {
		n := copy(p, c.prefix)
		c.prefix = c.prefix[n:]
		return n, nil
	}
	return c.Conn.Read(p)
}

type demuxListener struct {
	conns chan net.Conn
	done  chan struct{}
	addr  net.Addr
}

func newDemuxListener(addr net.Addr) *demuxListener {
	return &demuxListener{conns: make(chan net.Conn), done: make(chan struct{}), addr: addr}
}

func (d *demuxListener) Accept() (net.Conn, error) {
	select {
	case c := <-d.conns:
		return c, nil
	case <-d.done:
		return nil, net.ErrClosed
	}
}

func (d *demuxListener) Close() error {
	select {
	case <-d.done:
	default:
		close(d.done)
	}
	return nil
}

func (d *demuxListener) Addr() net.Addr { return d.addr }
