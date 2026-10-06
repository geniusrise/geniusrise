package gateway

import (
	"context"
	"crypto/rand"
	"crypto/sha256"
	"crypto/subtle"
	"encoding/hex"
	"fmt"
	"net"
	"net/http"
	"sync"
	"time"

	"github.com/geniusrise/geniusrise/internal/spec"
)

const (
	maxJSONBody   = 2 << 20
	maxAudioBody  = 25 << 20
	maxConnsPerIP = 100
)

type keyCtx struct {
	name   string
	limits spec.Limits
	models []string
}

type rateBucket struct {
	tokens float64
	last   time.Time
}

type authStore struct {
	mu      sync.Mutex
	hashes  map[string]keyCtx
	buckets map[string]*rateBucket
}

func newAuthStore() *authStore {
	return &authStore{hashes: map[string]keyCtx{}, buckets: map[string]*rateBucket{}}
}

func hashKey(k string) string {
	sum := sha256.Sum256([]byte(k))
	return hex.EncodeToString(sum[:])
}

func (a *authStore) reload(keys []spec.Key) {
	a.mu.Lock()
	defer a.mu.Unlock()
	a.hashes = map[string]keyCtx{}
	for _, k := range keys {
		a.hashes[hashKey(k.Key)] = keyCtx{name: k.Name, limits: k.Limits, models: k.Models}
	}
}

func (a *authStore) lookup(presented string) (keyCtx, bool) {
	h := hashKey(presented)
	a.mu.Lock()
	defer a.mu.Unlock()
	kc, ok := a.hashes[h]
	if !ok {
		return keyCtx{}, false
	}
	if kc.limits.RPM > 0 {
		b, ok := a.buckets[kc.name]
		if !ok {
			b = &rateBucket{tokens: float64(kc.limits.RPM), last: time.Now()}
			a.buckets[kc.name] = b
		}
		now := time.Now()
		b.tokens += now.Sub(b.last).Seconds() * float64(kc.limits.RPM) / 60.0
		if b.tokens > float64(kc.limits.RPM) {
			b.tokens = float64(kc.limits.RPM)
		}
		b.last = now
		if b.tokens < 1 {
			return kc, false
		}
		b.tokens--
	}
	return kc, true
}

func (kc keyCtx) allowsModel(m string) bool {
	for _, allowed := range kc.models {
		if allowed == "*" || allowed == m {
			return true
		}
	}
	return false
}

type ipLimiter struct {
	mu    sync.Mutex
	count map[string]int
}

func newIPLimiter() *ipLimiter { return &ipLimiter{count: map[string]int{}} }

func (l *ipLimiter) acquire(ip string) bool {
	l.mu.Lock()
	defer l.mu.Unlock()
	if l.count[ip] >= maxConnsPerIP {
		return false
	}
	l.count[ip]++
	return true
}

func (l *ipLimiter) release(ip string) {
	l.mu.Lock()
	defer l.mu.Unlock()
	if l.count[ip] > 0 {
		l.count[ip]--
	}
}

var badAuthIPs = newIPLimiter()

func (s *Server) adminToken() string {
	if s.opts.AdminToken != "" {
		return s.opts.AdminToken
	}
	cfg := s.Config()
	if cfg != nil {
		return cfg.Gateway.AdminToken
	}
	return ""
}

func (s *Server) authPublic(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		cfg := s.Config()
		if cfg == nil {
			http.Error(w, `{"error":{"message":"deployment not configured","type":"server_error"}}`, http.StatusServiceUnavailable)
			return
		}
		ip, _, _ := net.SplitHostPort(r.RemoteAddr)
		if !badAuthIPs.acquire(ip) {
			http.Error(w, `{"error":{"message":"too many connections","type":"rate_limit"}}`, http.StatusTooManyRequests)
			return
		}
		defer badAuthIPs.release(ip)
		token := bearer(r)
		if token == "" {
			w.Header().Set("WWW-Authenticate", `Bearer realm="geniusrise"`)
			http.Error(w, `{"error":{"message":"missing api key","type":"auth"}}`, http.StatusUnauthorized)
			return
		}
		kc, ok := s.auth.lookup(token)
		if !ok {
			time.Sleep(200 * time.Millisecond)
			http.Error(w, `{"error":{"message":"invalid api key","type":"auth"}}`, http.StatusUnauthorized)
			return
		}
		next(w, r.WithContext(withKey(r.Context(), kc)))
	}
}

func (s *Server) authAdmin(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		token := bearer(r)
		want := s.adminToken()
		if want == "" || subtle.ConstantTimeCompare([]byte(token), []byte(want)) != 1 {
			http.Error(w, `{"error":{"message":"unauthorized","type":"auth"}}`, http.StatusUnauthorized)
			return
		}
		next(w, r)
	}
}

func bearer(r *http.Request) string {
	h := r.Header.Get("Authorization")
	if len(h) > 7 && (h[:7] == "Bearer " || h[:7] == "bearer ") {
		return h[7:]
	}
	return ""
}

type ctxKey int

const keyCtxID ctxKey = 1

func withKey(ctx context.Context, kc keyCtx) context.Context {
	return context.WithValue(ctx, keyCtxID, kc)
}

func keyFrom(ctx context.Context) (keyCtx, bool) {
	kc, ok := ctx.Value(keyCtxID).(keyCtx)
	return kc, ok
}

func GenerateAPIKey() string {
	b := make([]byte, 24)
	rand.Read(b)
	return "sk-gr-" + hex.EncodeToString(b)
}

func (s *Server) recordMetrics(name string, v float64) {
	s.metricsMu.Lock()
	defer s.metricsMu.Unlock()
	s.metrics[name] = v
}

func (s *Server) metricAdd(name string, v float64) {
	s.metricsMu.Lock()
	defer s.metricsMu.Unlock()
	s.metrics[name] += v
}

func fmtUSD(v float64) string { return fmt.Sprintf("%.2f", v) }
