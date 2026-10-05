package tunnel

import (
	"bytes"
	"context"
	"crypto/ed25519"
	"crypto/rand"
	"crypto/sha256"
	"crypto/tls"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"math/big"
	"net"
	"net/http"
	"time"
)

func bytesReader(b []byte) *bytes.Reader { return bytes.NewReader(b) }

func SelfSignedCert(names []string) (tls.Certificate, string, error) {
	pub, priv, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		return tls.Certificate{}, "", err
	}
	tmpl := &x509.Certificate{
		SerialNumber: big.NewInt(1),
		Subject:      pkix.Name{CommonName: names[0]},
		DNSNames:     names,
		IPAddresses:  []net.IP{net.ParseIP("127.0.0.1"), net.ParseIP("::1")},
		NotBefore:    time.Now().Add(-time.Hour),
		NotAfter:     time.Now().AddDate(1, 0, 0),
		KeyUsage:     x509.KeyUsageDigitalSignature | x509.KeyUsageKeyEncipherment,
		ExtKeyUsage:  []x509.ExtKeyUsage{x509.ExtKeyUsageServerAuth},
	}
	der, err := x509.CreateCertificate(rand.Reader, tmpl, tmpl, pub, priv)
	if err != nil {
		return tls.Certificate{}, "", err
	}
	cert := tls.Certificate{Certificate: [][]byte{der}, PrivateKey: priv}
	sum := sha256.Sum256(der)
	return cert, hex.EncodeToString(sum[:]), nil
}

func TLSConfig(apiCert tls.Certificate, ca *CA) *tls.Config {
	base := &tls.Config{
		Certificates: []tls.Certificate{apiCert},
		NextProtos:   []string{"h2", "http/1.1", ALPN},
		MinVersion:   tls.VersionTLS12,
	}
	return &tls.Config{
		MinVersion: tls.VersionTLS12,
		NextProtos: []string{"h2", "http/1.1", ALPN},
		GetCertificate: func(*tls.ClientHelloInfo) (*tls.Certificate, error) {
			return &apiCert, nil
		},
		GetConfigForClient: func(hello *tls.ClientHelloInfo) (*tls.Config, error) {
			for _, p := range hello.SupportedProtos {
				if p == ALPN {
					tunnelCfg := base.Clone()
					tunnelCfg.ClientCAs = x509.NewCertPool()
					tunnelCfg.ClientCAs.AddCert(ca.Cert)
					tunnelCfg.ClientAuth = tls.RequireAndVerifyClientCert
					return tunnelCfg, nil
				}
			}
			return base.Clone(), nil
		},
	}
}

func ClientTLSConfig(certPEM, keyPEM, caPEM []byte, fingerprint string) (*tls.Config, error) {
	cert, err := tls.X509KeyPair(certPEM, keyPEM)
	if err != nil {
		return nil, err
	}
	roots := x509.NewCertPool()
	if !roots.AppendCertsFromPEM(caPEM) {
		return nil, errors.New("bad gateway ca pem")
	}
	cfg := &tls.Config{
		Certificates: []tls.Certificate{cert},
		RootCAs:      roots,
		NextProtos:   []string{ALPN},
		MinVersion:   tls.VersionTLS12,
	}
	if fingerprint != "" {
		cfg.InsecureSkipVerify = true
		cfg.VerifyPeerCertificate = func(rawCerts [][]byte, _ [][]*x509.Certificate) error {
			for _, raw := range rawCerts {
				sum := sha256.Sum256(raw)
				if hex.EncodeToString(sum[:]) == fingerprint {
					return nil
				}
			}
			return errors.New("gateway certificate fingerprint mismatch")
		}
	}
	return cfg, nil
}

func DialTLS(ctx context.Context, addr string, cfg *tls.Config) (net.Conn, error) {
	d := &net.Dialer{Timeout: 30 * time.Second}
	return tls.DialWithDialer(d, "tcp", addr, cfg)
}

type JoinRequest struct {
	Token string `json:"token"`
	CSR   string `json:"csr"`
}

type JoinResponse struct {
	Cert         string `json:"cert"`
	CA           string `json:"ca"`
	GatewayAddr  string `json:"gateway_addr"`
	EngineSpec   json.RawMessage `json:"engine_spec,omitempty"`
}

func Join(ctx context.Context, gatewayURL, token string) (*JoinResponse, []byte, string, error) {
	keyPEM, csrPEM, err := GenerateKeyPair()
	if err != nil {
		return nil, nil, "", err
	}
	body, _ := json.Marshal(JoinRequest{Token: token, CSR: string(csrPEM)})
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, gatewayURL+"/node/join", bytesReader(body))
	if err != nil {
		return nil, nil, "", err
	}
	req.Header.Set("Content-Type", "application/json")
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return nil, nil, "", err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, nil, "", fmt.Errorf("join: status %d", resp.StatusCode)
	}
	var jr JoinResponse
	if err := json.NewDecoder(resp.Body).Decode(&jr); err != nil {
		return nil, nil, "", err
	}
	if jr.Cert == "" {
		return nil, nil, "", errors.New("join: empty certificate")
	}
	return &jr, keyPEM, string(csrPEM), nil
}
