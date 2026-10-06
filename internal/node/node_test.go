package node

import (
	"context"
	"crypto/tls"
	"encoding/json"
	"io"
	"net"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync/atomic"
	"testing"
	"time"

	"github.com/geniusrise/geniusrise/internal/tunnel"
)

type fakeEngine struct {
	*httptest.Server
	requests   atomic.Int64
	failCanary atomic.Bool
}

func newFakeEngine(t *testing.T) *fakeEngine {
	t.Helper()
	fe := &fakeEngine{}
	mux := http.NewServeMux()
	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("ok"))
	})
	mux.HandleFunc("/v1/chat/completions", func(w http.ResponseWriter, r *http.Request) {
		if fe.failCanary.Load() {
			http.Error(w, "boom", http.StatusInternalServerError)
			return
		}
		fe.requests.Add(1)
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]any{
			"id": "canary", "object": "chat.completion",
			"choices": []map[string]any{{"message": map[string]string{"role": "assistant", "content": "pong"}, "finish_reason": "stop"}},
			"usage":   map[string]int{"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
		})
	})
	fe.Server = httptest.NewServer(mux)
	t.Cleanup(fe.Close)
	return fe
}

func TestAgentJoinsAndHeartbeats(t *testing.T) {
	ca, _ := tunnel.LoadOrCreateCA(t.TempDir())
	fe := newFakeEngine(t)
	tm := tunnel.NewTokenManager(time.Minute)
	tokenID, tokenSecret, _ := tm.New()

	var gotHeartbeats atomic.Int64
	tun := tunnel.NewServer()
	tun.OnMessage = func(nodeID string, m *tunnel.Message) {
		if m.Type == tunnel.MsgHeartbeat {
			gotHeartbeats.Add(1)
		}
	}

	cert, fp, _ := tunnel.SelfSignedCert([]string{"localhost"})
	ln, _ := net.Listen("tcp", "127.0.0.1:0")
	tlsLn := tls.NewListener(ln, tunnel.TLSConfig(cert, ca))
	defer tlsLn.Close()
	go func() {
		for {
			conn, err := tlsLn.Accept()
			if err != nil {
				return
			}
			go func(c net.Conn) {
				tc := c.(*tls.Conn)
				if err := tc.Handshake(); err != nil {
					tc.Close()
					return
				}
				if tc.ConnectionState().NegotiatedProtocol == tunnel.ALPN {
					tun.HandleSession("node-1", tc)
				} else {
					tc.Close()
				}
			}(conn)
		}
	}()
	addr := ln.Addr().String()

	adminMux := http.NewServeMux()
	adminMux.HandleFunc("/node/join", func(w http.ResponseWriter, r *http.Request) {
		var req tunnel.JoinRequest
		json.NewDecoder(r.Body).Decode(&req)
		parts := strings.SplitN(req.Token, ".", 2)
		if len(parts) != 2 || !tm.Consume(parts[0], parts[1]) {
			http.Error(w, "bad token", http.StatusUnauthorized)
			return
		}
		certPEM, err := ca.SignCSR([]byte(req.CSR), "node-1")
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		json.NewEncoder(w).Encode(tunnel.JoinResponse{Cert: string(certPEM), CA: string(ca.PEM())})
	})
	api := httptest.NewServer(adminMux)
	defer api.Close()

	agent := New(Config{
		NodeID: "node-1", GatewayURL: api.URL, GatewayAddr: addr,
		JoinToken: tokenID + "." + tokenSecret, CAFingerprint: fp,
		EngineType: "vllm", ExternalURL: fe.URL, ReadyTimeout: 5 * time.Second,
		AdminPort: 19101, AdminToken: "adm",
	})
	ctx, cancel := context.WithCancel(context.Background())
	done := make(chan error, 1)
	go func() { done <- agent.Run(ctx) }()
	defer cancel()

	deadline := time.Now().Add(5 * time.Second)
	for time.Now().Before(deadline) && !tun.Connected("node-1") {
		time.Sleep(20 * time.Millisecond)
	}
	if !tun.Connected("node-1") {
		t.Fatal("agent never connected")
	}
	deadline = time.Now().Add(5 * time.Second)
	for time.Now().Before(deadline) && gotHeartbeats.Load() == 0 {
		time.Sleep(20 * time.Millisecond)
	}
	if gotHeartbeats.Load() == 0 {
		t.Fatal("no heartbeats received")
	}

	dialed, err := tun.Dial("node-1", uint16(0))
	if err != nil {
		t.Fatal(err)
	}
	dialed.Close()

	adminDial, err := tun.Dial("node-1", 19101)
	if err != nil {
		t.Fatal(err)
	}
	req, _ := http.NewRequest("GET", "http://agent/logs?token=adm", nil)
	resp := &http.Response{StatusCode: 200, Body: io.NopCloser(strings.NewReader(""))}
	_ = resp
	_ = req
	adminDial.Close()

	cancel()
	select {
	case <-done:
	case <-time.After(5 * time.Second):
		t.Fatal("agent did not stop")
	}
}

func TestWaitReady(t *testing.T) {
	fe := newFakeEngine(t)
	if err := waitReady(context.Background(), fe.URL+"/health", time.Second); err != nil {
		t.Fatal(err)
	}
	if err := waitReady(context.Background(), "http://127.0.0.1:1/health", 300*time.Millisecond); err == nil {
		t.Fatal("expected timeout")
	}
}

func TestCanary(t *testing.T) {
	fe := newFakeEngine(t)
	agent := New(Config{EngineType: "vllm", ExternalURL: fe.URL})
	if err := agent.canary(); err != nil {
		t.Fatal(err)
	}
	if fe.requests.Load() != 1 {
		t.Fatalf("canary requests: %d", fe.requests.Load())
	}
	fe.failCanary.Store(true)
	if err := agent.canary(); err == nil {
		t.Fatal("expected canary failure")
	}
}

func TestRingBuffer(t *testing.T) {
	var r ringBuffer
	r.Write([]byte(strings.Repeat("a", 200*1024)))
	if len(r.Bytes()) != 128*1024 {
		t.Fatalf("ring size: %d", len(r.Bytes()))
	}
}

func TestSpotInterruptedNoMetadata(t *testing.T) {
	if _, ok := spotInterrupted(); ok {
		t.Fatal("no metadata service should be available")
	}
}
