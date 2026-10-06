package gui

import (
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

const testYAML = `version: 1
name: gui-test
provider:
  type: fake
  region: fake
models:
  - id: qwen2.5-7b-instruct
    replicas: {min: 0, max: 1}
keys:
  - name: main
    key: sk-gui-test
`

func startGUI(t *testing.T) (string, *Server) {
	t.Helper()
	dir := t.TempDir()
	file := filepath.Join(dir, "deploy.yaml")
	if err := os.WriteFile(file, []byte(testYAML), 0o600); err != nil {
		t.Fatal(err)
	}
	s, err := New(file, "")
	if err != nil {
		t.Fatal(err)
	}
	url, err := s.Start()
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(s.Stop)
	return url, s
}

func TestSessionGuard(t *testing.T) {
	url, s := startGUI(t)
	resp, err := http.Get(url)
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("session url rejected: %d", resp.StatusCode)
	}
	cookie := resp.Cookies()
	if len(cookie) == 0 {
		t.Fatal("no session cookie set")
	}
	req, _ := http.NewRequest("GET", strings.Replace(url, "/"+s.session+"/", "/api/spec", 1), nil)
	for _, c := range cookie {
		req.AddCookie(c)
	}
	resp2, err := http.DefaultClient.Do(req)
	if err != nil {
		t.Fatal(err)
	}
	defer resp2.Body.Close()
	if resp2.StatusCode != http.StatusOK {
		t.Fatalf("api with cookie rejected: %d", resp2.StatusCode)
	}
	req3, _ := http.NewRequest("GET", strings.Replace(url, "/"+s.session+"/", "/api/spec", 1), nil)
	resp3, err := http.DefaultClient.Do(req3)
	if err != nil {
		t.Fatal(err)
	}
	resp3.Body.Close()
	if resp3.StatusCode != http.StatusForbidden {
		t.Fatalf("api without cookie should be 403, got %d", resp3.StatusCode)
	}
}

func TestPlanEndpoint(t *testing.T) {
	url, _ := startGUI(t)
	resp, err := http.Get(url + "api/plan")
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		body := make([]byte, 256)
		n, _ := resp.Body.Read(body)
		t.Fatalf("plan: %d %s", resp.StatusCode, body[:n])
	}
	var p struct {
		Models []struct {
			ID string `json:"ID"`
		} `json:"Models"`
	}
	json.NewDecoder(resp.Body).Decode(&p)
	if len(p.Models) != 1 || p.Models[0].ID != "qwen2.5-7b-instruct" {
		t.Fatalf("bad plan: %+v", p)
	}
}

func TestYAMLEndpointRejectsInvalid(t *testing.T) {
	url, _ := startGUI(t)
	resp, err := http.Post(url+"api/yaml", "text/yaml", strings.NewReader("version: 1\nname: BAD\n"))
	if err != nil {
		t.Fatal(err)
	}
	resp.Body.Close()
	if resp.StatusCode != http.StatusBadRequest {
		t.Fatalf("invalid yaml accepted: %d", resp.StatusCode)
	}
	resp2, err := http.Post(url+"api/yaml", "text/yaml", strings.NewReader(testYAML))
	if err != nil {
		t.Fatal(err)
	}
	resp2.Body.Close()
	if resp2.StatusCode != http.StatusOK {
		t.Fatalf("valid yaml rejected: %d", resp2.StatusCode)
	}
}

func TestStaticServed(t *testing.T) {
	url, _ := startGUI(t)
	resp, err := http.Get(url + "../static/static/style.css")
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("css: %d", resp.StatusCode)
	}
}

var _ = fmt.Sprintf
