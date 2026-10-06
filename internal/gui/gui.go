package gui

import (
	"embed"
	"encoding/json"
	"fmt"
	"html/template"
	"io"
	"net"
	"net/http"
	"os"
	"strings"

	"github.com/geniusrise/geniusrise/internal/catalog"
	"github.com/geniusrise/geniusrise/internal/planner"
	"github.com/geniusrise/geniusrise/internal/pricing"
	"github.com/geniusrise/geniusrise/internal/spec"
)

//go:embed all:templates static
var files embed.FS

type Server struct {
	File        string
	CatalogFlag string
	session     string
	ln          net.Listener
	srv         *http.Server
}

func New(file, catalogFlag string) (*Server, error) {
	return &Server{File: file, CatalogFlag: catalogFlag}, nil
}

func (s *Server) Start() (string, error) {
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		return "", err
	}
	s.ln = ln
	s.session = fmt.Sprintf("grs_%x", randomBytes(16))
	mux := http.NewServeMux()
	_ = mux
	mux.HandleFunc("/", s.guard(s.page("index.html")))
	mux.HandleFunc("/models", s.guard(s.page("models.html")))
	mux.HandleFunc("/provider", s.guard(s.page("provider.html")))
	mux.HandleFunc("/keys", s.guard(s.page("keys.html")))
	mux.HandleFunc("/plan", s.guard(s.page("plan.html")))
	mux.HandleFunc("/status", s.guard(s.statusPage))
	mux.HandleFunc("/yaml", s.guard(s.yamlPage))
	mux.HandleFunc("/api/spec", s.guard(s.apiSpec))
	mux.HandleFunc("/api/catalog", s.guard(s.apiCatalog))
	mux.HandleFunc("/api/plan", s.guard(s.apiPlan))
	mux.HandleFunc("/api/compare", s.guard(s.apiCompare))
	mux.HandleFunc("/api/status", s.guard(s.apiStatus))
	mux.HandleFunc("/api/apply", s.guard(s.apiApply))
	mux.HandleFunc("/api/yaml", s.guard(s.apiYAML))
	mux.HandleFunc("/static/", func(w http.ResponseWriter, r *http.Request) {
		if strings.Contains(r.URL.Path, "..") {
			http.NotFound(w, r)
			return
		}
		http.FileServer(http.FS(files)).ServeHTTP(w, r)
	})
	s.srv = &http.Server{Handler: s.outer(mux)}
	go s.srv.Serve(ln)
	return fmt.Sprintf("http://127.0.0.1:%d/%s/", ln.Addr().(*net.TCPAddr).Port, s.session), nil
}

func (s *Server) outer(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Host != s.ln.Addr().String() && !strings.HasPrefix(r.Host, "127.0.0.1") && !strings.HasPrefix(r.Host, "localhost") {
			http.Error(w, "bad host", http.StatusForbidden)
			return
		}
		w.Header().Set("X-Frame-Options", "DENY")
		w.Header().Set("X-Content-Type-Options", "nosniff")
		w.Header().Set("Referrer-Policy", "no-referrer")
		if strings.Contains(r.URL.Path, s.session) {
			r.URL.Path = strings.Replace(r.URL.Path, "/"+s.session, "", 1)
			if r.URL.Path == "" {
				r.URL.Path = "/"
			}
			http.SetCookie(w, &http.Cookie{Name: "gr_session", Value: s.session, HttpOnly: true, SameSite: http.SameSiteStrictMode, Path: "/"})
			next.ServeHTTP(w, r)
			return
		}
		if strings.HasPrefix(r.URL.Path, "/static/") || checkSession(s.session, r) {
			next.ServeHTTP(w, r)
			return
		}
		http.Error(w, "session invalid", http.StatusForbidden)
	})
}

func (s *Server) Stop() {
	if s.srv != nil {
		s.srv.Close()
	}
}

func randomBytes(n int) []byte {
	b := make([]byte, n)
	for i := range b {
		b[i] = byte(i*31 + 7)
	}
	f, err := os.Open("/dev/urandom")
	if err == nil {
		defer f.Close()
		f.Read(b)
	}
	return b
}

func (s *Server) guard(next http.HandlerFunc) http.HandlerFunc {
	return next
}

func checkSession(session string, r *http.Request) bool {
	c, err := r.Cookie("gr_session")
	return err == nil && c.Value == session
}

func (s *Server) page(name string) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		tmpl, err := template.ParseFS(files, "templates/layout.html", "templates/"+name)
		if err != nil {
			http.Error(w, err.Error(), 500)
			return
		}
		d, err := spec.Load(s.File)
		dErr := ""
		if err != nil {
			dErr = err.Error()
			d = &spec.Deployment{}
		}
		http.SetCookie(w, &http.Cookie{Name: "gr_session", Value: s.session, HttpOnly: true, SameSite: http.SameSiteStrictMode, Path: "/"})
		tmpl.Execute(w, map[string]any{"D": d, "Error": dErr})
	}
}

func (s *Server) statusPage(w http.ResponseWriter, r *http.Request) {
	s.page("status.html")(w, r)
}

func (s *Server) yamlPage(w http.ResponseWriter, r *http.Request) {
	s.page("yaml.html")(w, r)
}

func (s *Server) loadSpec() (*spec.Deployment, error) {
	return spec.Load(s.File)
}

func (s *Server) apiSpec(w http.ResponseWriter, r *http.Request) {
	d, err := s.loadSpec()
	if err != nil {
		writeErr(w, err)
		return
	}
	writeJSON(w, d)
}

func (s *Server) apiCatalog(w http.ResponseWriter, r *http.Request) {
	cat, err := catalog.Load(s.CatalogFlag)
	if err != nil {
		writeErr(w, err)
		return
	}
	writeJSON(w, cat.List())
}

func (s *Server) apiPlan(w http.ResponseWriter, r *http.Request) {
	d, cat, snap, err := s.planInputs()
	if err != nil {
		writeErr(w, err)
		return
	}
	p, err := planner.Plan(d, cat, snap)
	if err != nil {
		writeErr(w, err)
		return
	}
	writeJSON(w, p)
}

func (s *Server) apiCompare(w http.ResponseWriter, r *http.Request) {
	d, cat, snap, err := s.planInputs()
	if err != nil {
		writeErr(w, err)
		return
	}
	plans, err := planner.Compare(d, cat, snap)
	if err != nil {
		writeErr(w, err)
		return
	}
	writeJSON(w, plans)
}

func (s *Server) planInputs() (*spec.Deployment, *catalog.Catalog, *pricing.Snapshot, error) {
	d, err := s.loadSpec()
	if err != nil {
		return nil, nil, nil, err
	}
	data, err := spec.ResolveEnvFile(s.File)
	if err != nil {
		return nil, nil, nil, err
	}
	d, err = spec.Parse(data)
	if err != nil {
		return nil, nil, nil, err
	}
	cat, err := catalog.Load(s.CatalogFlag)
	if err != nil {
		return nil, nil, nil, err
	}
	snap, err := pricing.Load("")
	if err != nil {
		return nil, nil, nil, err
	}
	return d, cat, snap, nil
}

func (s *Server) apiStatus(w http.ResponseWriter, r *http.Request) {
	d, err := s.loadSpec()
	if err != nil {
		writeErr(w, err)
		return
	}
	if d.Gateway.URL == "" {
		writeJSON(w, map[string]any{"error": "not bootstrapped"})
		return
	}
	c := newClient(d.Gateway.URL, d.Gateway.AdminToken)
	st, err := c.status()
	if err != nil {
		writeJSON(w, map[string]any{"error": err.Error()})
		return
	}
	writeJSON(w, st)
}

func (s *Server) apiApply(w http.ResponseWriter, r *http.Request) {
	flusher, _ := w.(http.Flusher)
	progress := func(format string, args ...any) {
		fmt.Fprintf(w, format+"\n", args...)
		if flusher != nil {
			flusher.Flush()
		}
	}
	if err := s.runApply(r.Context(), progress); err != nil {
		progress("ERROR: %v", err)
		return
	}
}

func (s *Server) apiYAML(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		data, err := os.ReadFile(s.File)
		if err != nil {
			writeErr(w, err)
			return
		}
		w.Header().Set("Content-Type", "text/yaml")
		w.Write(data)
		return
	}
	body, err := io.ReadAll(io.LimitReader(r.Body, 1<<20))
	if err != nil {
		writeErr(w, err)
		return
	}
	if _, err := spec.Parse(body); err != nil {
		writeErr(w, err)
		return
	}
	tmp := s.File + ".tmp"
	if err := os.WriteFile(tmp, body, 0o600); err != nil {
		writeErr(w, err)
		return
	}
	if err := os.Rename(tmp, s.File); err != nil {
		writeErr(w, err)
		return
	}
	writeJSON(w, map[string]string{"status": "saved"})
}

func writeErr(w http.ResponseWriter, err error) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusBadRequest)
	fmt.Fprintf(w, `{"error":%q}`, err.Error())
}

func writeJSON(w io.Writer, v any) {
	_ = json.NewEncoder(w).Encode(v)
}
