package tunnel

import (
	"bufio"
	"encoding/binary"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"sync"
	"time"

	"github.com/hashicorp/yamux"
)

const ALPN = "gr-tunnel"

const ControlPort = uint16(0)

type Message struct {
	Type    string `json:"type"`
	NodeID  string `json:"node_id,omitempty"`
	Inflight int   `json:"inflight,omitempty"`
	Queue   int   `json:"queue,omitempty"`
	Error   string `json:"error,omitempty"`
}

const (
	MsgRegister   = "register"
	MsgHeartbeat  = "heartbeat"
	MsgUnhealthy  = "unhealthy"
	MsgDrain      = "drain"
	MsgRestart    = "restart"
	MsgTerminate  = "terminate"
	MsgSpotNotice = "spot_notice"
)

type Server struct {
	mu       sync.Mutex
	sessions map[string]*yamux.Session
	OnRegister func(nodeID string, control io.ReadWriteCloser)
}

func NewServer() *Server {
	return &Server{sessions: map[string]*yamux.Session{}}
}

func (s *Server) HandleSession(nodeID string, conn net.Conn) error {
	cfg := yamux.DefaultConfig()
	cfg.KeepAliveInterval = 10 * time.Second
	sess, err := yamux.Server(conn, cfg)
	if err != nil {
		return err
	}
	s.mu.Lock()
	if old, ok := s.sessions[nodeID]; ok {
		old.GoAway()
	}
	s.sessions[nodeID] = sess
	s.mu.Unlock()
	go func() {
		for {
			stream, err := sess.Accept()
			if err != nil {
				return
			}
			go s.handleStream(nodeID, stream.(net.Conn))
		}
	}()
	return nil
}

func (s *Server) handleStream(nodeID string, stream net.Conn) {
	var portBuf [2]byte
	if _, err := io.ReadFull(stream, portBuf[:]); err != nil {
		stream.Close()
		return
	}
	port := binary.BigEndian.Uint16(portBuf[:])
	if port == ControlPort {
		if s.OnRegister != nil {
			s.OnRegister(nodeID, stream)
		}
		return
	}
	engine := net.TCPAddr{IP: net.IPv4(127, 0, 0, 1), Port: int(port)}
	target, err := net.DialTimeout("tcp", engine.String(), 5*time.Second)
	if err != nil {
		stream.Close()
		return
	}
	go pipe(stream, target)
}

func pipe(a, b net.Conn) {
	defer a.Close()
	defer b.Close()
	done := make(chan struct{}, 2)
	go func() { io.Copy(a, b); done <- struct{}{} }()
	go func() { io.Copy(b, a); done <- struct{}{} }()
	<-done
}

func (s *Server) Dial(nodeID string, port uint16) (net.Conn, error) {
	s.mu.Lock()
	sess := s.sessions[nodeID]
	s.mu.Unlock()
	if sess == nil {
		return nil, fmt.Errorf("node %s is not connected", nodeID)
	}
	stream, err := sess.Open()
	if err != nil {
		return nil, err
	}
	var portBuf [2]byte
	binary.BigEndian.PutUint16(portBuf[:], port)
	if _, err := stream.Write(portBuf[:]); err != nil {
		stream.Close()
		return nil, err
	}
	return stream, nil
}

func (s *Server) SendControl(nodeID string, msg Message) error {
	conn, err := s.Dial(nodeID, ControlPort)
	if err != nil {
		return err
	}
	defer conn.Close()
	data, _ := json.Marshal(msg)
	_, err = conn.Write(append(data, '\n'))
	return err
}

func (s *Server) Connected(nodeID string) bool {
	s.mu.Lock()
	defer s.mu.Unlock()
	sess := s.sessions[nodeID]
	return sess != nil && !sess.IsClosed()
}

func (s *Server) RemoveSession(nodeID string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	delete(s.sessions, nodeID)
}

func (s *Server) Nodes() []string {
	s.mu.Lock()
	defer s.mu.Unlock()
	var out []string
	for id, sess := range s.sessions {
		if !sess.IsClosed() {
			out = append(out, id)
		}
	}
	return out
}

type Client struct {
	NodeID      string
	GatewayAddr string
	session     *yamux.Session
	Control     io.ReadWriteCloser
	ctrlReader  *bufio.Reader
}

func Connect(nodeID, gatewayAddr string, conn net.Conn) (*Client, error) {
	cfg := yamux.DefaultConfig()
	cfg.KeepAliveInterval = 10 * time.Second
	sess, err := yamux.Client(conn, cfg)
	if err != nil {
		return nil, err
	}
	c := &Client{NodeID: nodeID, GatewayAddr: gatewayAddr, session: sess}
	ctrl, err := c.openStream(ControlPort)
	if err != nil {
		sess.Close()
		return nil, err
	}
	c.Control = ctrl
	c.ctrlReader = bufio.NewReader(ctrl)
	reg, _ := json.Marshal(Message{Type: MsgRegister, NodeID: nodeID})
	if _, err := ctrl.Write(append(reg, '\n')); err != nil {
		sess.Close()
		return nil, err
	}
	go func() {
		for {
			stream, err := sess.Accept()
			if err != nil {
				return
			}
			go c.handleStream(stream)
		}
	}()
	return c, nil
}

func (c *Client) handleStream(stream net.Conn) {
	var portBuf [2]byte
	if _, err := io.ReadFull(stream, portBuf[:]); err != nil {
		stream.Close()
		return
	}
	port := binary.BigEndian.Uint16(portBuf[:])
	if port == ControlPort {
		return
	}
	target, err := net.DialTimeout("tcp", fmt.Sprintf("127.0.0.1:%d", port), 5*time.Second)
	if err != nil {
		stream.Close()
		return
	}
	pipe(stream, target)
}

func (c *Client) openStream(port uint16) (net.Conn, error) {
	stream, err := c.session.Open()
	if err != nil {
		return nil, err
	}
	var portBuf [2]byte
	binary.BigEndian.PutUint16(portBuf[:], port)
	if _, err := stream.Write(portBuf[:]); err != nil {
		stream.Close()
		return nil, err
	}
	return stream, nil
}

func (c *Client) Send(msg Message) error {
	data, _ := json.Marshal(msg)
	_, err := c.Control.Write(append(data, '\n'))
	return err
}

func (c *Client) ReadControl() (*Message, error) {
	var m Message
	if err := json.NewDecoder(c.ctrlReader).Decode(&m); err != nil {
		return nil, err
	}
	return &m, nil
}

func (c *Client) Close() error { return c.session.Close() }
