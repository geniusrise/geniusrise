package tunnel

import (
	"context"
	"crypto/tls"
	"encoding/json"
	"io"
	"net"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync"
	"testing"
	"time"
)

type recordingTLSServer struct {
	srv *http.Server
	ln  net.Listener
}

type demuxListener struct {
	c    chan net.Conn
	done chan struct{}
}

func newDemux() *demuxListener {
	return &demuxListener{c: make(chan net.Conn), done: make(chan struct{})}
}

func (d *demuxListener) Accept() (net.Conn, error) {
	select {
	case c := <-d.c:
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

func (d *demuxListener) Addr() net.Addr { return dummyAddr{} }

type dummyAddr struct{}

func (dummyAddr) Network() string { return "tcp" }
func (dummyAddr) String() string  { return "demux" }

func startGateway(t *testing.T, ca *CA) (string, *Server, string) {
	t.Helper()
	cert, fp, err := SelfSignedCert([]string{"localhost"})
	if err != nil {
		t.Fatal(err)
	}
	srv := NewServer()
	mux := http.NewServeMux()
	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("ok"))
	})
	ts := &http.Server{Handler: mux}
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	tlsLn := tls.NewListener(ln, TLSConfig(cert, ca))
	demux := newDemux()
	go ts.Serve(demux)
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
				if tc.ConnectionState().NegotiatedProtocol == ALPN {
					srv.HandleSession("test-node", tc)
				} else {
					select {
					case demux.c <- tc:
					case <-demux.done:
						tc.Close()
					}
				}
			}(conn)
		}
	}()
	t.Cleanup(func() { ts.Close(); tlsLn.Close(); demux.Close() })
	return ln.Addr().String(), srv, fp
}

func TestCAAndCSR(t *testing.T) {
	ca, err := LoadOrCreateCA(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	if ca.Fingerprint() == "" {
		t.Fatal("empty fingerprint")
	}
	_, csr, err := GenerateKeyPair()
	if err != nil {
		t.Fatal(err)
	}
	certPEM, err := ca.SignCSR(csr, "node-1")
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(string(certPEM), "CERTIFICATE") {
		t.Fatal("bad cert pem")
	}
}

func TestTokenManager(t *testing.T) {
	tm := NewTokenManager(time.Minute)
	id, secret, err := tm.New()
	if err != nil {
		t.Fatal(err)
	}
	if !tm.Consume(id, secret) {
		t.Fatal("valid token rejected")
	}
	if tm.Consume(id, secret) {
		t.Fatal("token reusable")
	}
	if tm.Consume(id, "wrong") {
		t.Fatal("wrong secret accepted")
	}
	id2, _, _ := tm.New()
	time.Sleep(10 * time.Millisecond)
	tm2 := NewTokenManager(time.Nanosecond)
	id3, secret3, _ := tm2.New()
	time.Sleep(2 * time.Millisecond)
	if tm2.Consume(id3, secret3) {
		t.Fatal("expired token accepted")
	}
	_ = id2
}

func TestTunnelRoundTrip(t *testing.T) {
	ca, _ := LoadOrCreateCA(t.TempDir())
	engine, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	defer engine.Close()
	go func() {
		for {
			c, err := engine.Accept()
			if err != nil {
				return
			}
			go func(c net.Conn) {
				io.Copy(c, c)
				c.Close()
			}(c)
		}
	}()
	enginePort := uint16(engine.Addr().(*net.TCPAddr).Port)

	addr, srv, fp := startGateway(t, ca)

	keyPEM, csr, _ := GenerateKeyPair()
	certPEM, err := ca.SignCSR(csr, "test-node")
	if err != nil {
		t.Fatal(err)
	}
	tlsCfg, err := ClientTLSConfig(certPEM, keyPEM, ca.PEM(), fp)
	if err != nil {
		t.Fatal(err)
	}
	conn, err := DialTLS(context.Background(), addr, tlsCfg)
	if err != nil {
		t.Fatal(err)
	}
	client, err := Connect("test-node", addr, conn)
	if err != nil {
		t.Fatal(err)
	}
	defer client.Close()

	deadline := time.Now().Add(2 * time.Second)
	for time.Now().Before(deadline) && !srv.Connected("test-node") {
		time.Sleep(10 * time.Millisecond)
	}
	if !srv.Connected("test-node") {
		t.Fatal("node not connected")
	}

	dialed, err := srv.Dial("test-node", enginePort)
	if err != nil {
		t.Fatal(err)
	}
	msg := "hello-through-tunnel"
	var wg sync.WaitGroup
	wg.Add(1)
	go func() {
		defer wg.Done()
		dialed.Write([]byte(msg))
	}()
	buf := make([]byte, len(msg))
	done := make(chan struct{})
	go func() {
		io.ReadFull(dialed, buf)
		close(done)
	}()
	select {
	case <-done:
	case <-time.After(2 * time.Second):
		t.Fatal("tunnel round trip timed out")
	}
	wg.Wait()
	if string(buf) != msg {
		t.Fatalf("got %q", buf)
	}

	if err := client.Send(Message{Type: MsgHeartbeat, NodeID: "test-node", Inflight: 3}); err != nil {
		t.Fatal(err)
	}
	if err := srv.SendControl("test-node", Message{Type: MsgDrain}); err != nil {
		t.Fatal(err)
	}
}

func jsonDecode(r *http.Request, out any) error {
	return json.NewDecoder(r.Body).Decode(out)
}

func jsonEncode(w http.ResponseWriter, v any) {
	json.NewEncoder(w).Encode(v)
}

func TestJoinHTTPEndpoint(t *testing.T) {
	ca, _ := LoadOrCreateCA(t.TempDir())
	tm := NewTokenManager(time.Minute)
	id, secret, _ := tm.New()
	called := false
	ts := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/node/join" {
			http.NotFound(w, r)
			return
		}
		var req JoinRequest
		if err := jsonDecode(r, &req); err != nil {
			http.Error(w, err.Error(), 400)
			return
		}
		if !tm.Consume(strings.SplitN(req.Token, ".", 2)[0], strings.SplitN(req.Token, ".", 2)[1]) {
			http.Error(w, "bad token", 401)
			return
		}
		certPEM, err := ca.SignCSR([]byte(req.CSR), "node-9")
		if err != nil {
			http.Error(w, err.Error(), 500)
			return
		}
		called = true
		jsonEncode(w, JoinResponse{Cert: string(certPEM), CA: string(ca.PEM())})
	}))
	defer ts.Close()
	resp, keyPEM, _, err := Join(context.Background(), ts.URL, id+"."+secret)
	if err != nil {
		t.Fatal(err)
	}
	if resp.Cert == "" || keyPEM == nil || !called {
		t.Fatalf("join failed: %+v", resp)
	}
	_, _, _, err = Join(context.Background(), ts.URL, id+"."+secret)
	if err == nil {
		t.Fatal("token reuse allowed")
	}
}
