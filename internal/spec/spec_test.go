package spec

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

const minimal = `version: 1
name: acme-ai
provider:
  type: aws
  region: us-east-1
  capacity: spot-fallback
budget:
  monthly_usd: 500
models:
  - id: llama-3.1-8b-instruct
    variant: awq
    replicas: {min: 0, max: 4}
    idle_timeout: 15m
  - id: whisper-large-v3-turbo
    replicas: {min: 1, max: 2}
keys:
  - name: alice
    key: ${ALICE_KEY}
    models: ["*"]
    limits: {rpm: 60, tokens_per_day: 200000, stt_mb_per_day: 200, tts_chars_per_day: 100000}
secrets:
  hf_token: ${HF_TOKEN}
`

func TestParseMinimal(t *testing.T) {
	d, err := Parse([]byte(minimal))
	if err != nil {
		t.Fatal(err)
	}
	if d.Name != "acme-ai" || d.Provider.Type != ProviderAWS || d.Provider.Capacity != CapacitySpotFallback {
		t.Fatalf("bad parse: %+v", d)
	}
	if len(d.Models) != 2 || d.Models[0].Replicas.Max != 4 {
		t.Fatalf("bad models: %+v", d.Models)
	}
	dur, _ := d.Models[1].IdleDuration()
	if dur.Minutes() != 15 {
		t.Fatalf("default idle timeout not applied: %v", dur)
	}
	if d.Models[1].Replicas.Max != 2 {
		t.Fatalf("default max not applied")
	}
}

func TestStrictRejectsUnknownField(t *testing.T) {
	bad := strings.Replace(minimal, "name: acme-ai", "name: acme-ai\nnmae: typo", 1)
	if _, err := Parse([]byte(bad)); err == nil {
		t.Fatal("expected unknown field error")
	}
}

func TestValidateErrors(t *testing.T) {
	cases := []struct {
		name, src, wantErr string
	}{
		{"bad name", strings.Replace(minimal, "name: acme-ai", "name: ACME", 1), "name"},
		{"bad provider", strings.Replace(minimal, "type: aws", "type: dreamhost", 1), "provider.type"},
		{"region missing", strings.Replace(minimal, "  region: us-east-1\n", "", 1), "region"},
		{"serverless non-runpod", strings.Replace(minimal, "capacity: spot-fallback", "capacity: serverless", 1), "serverless"},
		{"lambda needs gateway host", strings.Replace(minimal, "type: aws", "type: lambda", 1), "gateway.host"},
		{"duplicate model", strings.Replace(minimal, "  - id: whisper-large-v3-turbo", "  - id: llama-3.1-8b-instruct", 1), "duplicated"},
		{"duplicate key", strings.Replace(minimal, "secrets:", "  - name: alice\n    key: sk-x\nsecrets:", 1), "duplicated"},
		{"no models", strings.Replace(minimal, "models:\n  - id: llama-3.1-8b-instruct\n    variant: awq\n    replicas: {min: 0, max: 4}\n    idle_timeout: 15m\n  - id: whisper-large-v3-turbo\n    replicas: {min: 1, max: 2}\n", "models: []\n", 1), "model"},
		{"bad budget", strings.Replace(minimal, "monthly_usd: 500", "monthly_usd: -1", 1), "budget"},
		{"bad idle timeout", strings.Replace(minimal, "idle_timeout: 15m", "idle_timeout: 15x", 1), "idle_timeout"},
		{"replicas max < min", strings.Replace(minimal, "{min: 0, max: 4}", "{min: 3, max: 2}", 1), "replicas.max"},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			_, err := Parse([]byte(c.src))
			if err == nil || !strings.Contains(err.Error(), c.wantErr) {
				t.Fatalf("want error containing %q, got %v", c.wantErr, err)
			}
		})
	}
}

func TestValidateSSH(t *testing.T) {
	src := `version: 1
name: home-lab
provider:
  type: ssh
  hosts:
    - {addr: 10.0.0.5, user: ubuntu, gpus: 2}
models:
  - id: llama-3.1-8b-instruct
keys:
  - name: bob
    key: sk-bob
`
	if _, err := Parse([]byte(src)); err != nil {
		t.Fatal(err)
	}
	d, _ := Parse([]byte(src))
	if d.Models[0].Replicas.Max != 1 || d.Models[0].Replicas.Min != 0 {
		t.Fatalf("default replicas not applied: %+v", d.Models[0].Replicas)
	}
	if len(d.Keys[0].Models) != 1 || d.Keys[0].Models[0] != "*" {
		t.Fatal("default key models not applied")
	}
	noHosts := strings.Replace(src, "    - {addr: 10.0.0.5, user: ubuntu, gpus: 2}\n", "", 1)
	if _, err := Parse([]byte(noHosts)); err == nil || !strings.Contains(err.Error(), "hosts") {
		t.Fatalf("want hosts error, got %v", err)
	}
}

func TestResolveEnv(t *testing.T) {
	t.Setenv("ALICE_KEY", "sk-alice")
	t.Setenv("HF_TOKEN", "hf_tok")
	out, err := ResolveEnv([]byte(minimal))
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(string(out), "sk-alice") || !strings.Contains(string(out), "hf_tok") {
		t.Fatalf("env not resolved:\n%s", out)
	}
	if _, err := Parse(out); err != nil {
		t.Fatalf("resolved yaml invalid: %v", err)
	}
}

func TestResolveEnvMissing(t *testing.T) {
	os.Unsetenv("ALICE_KEY")
	os.Unsetenv("HF_TOKEN")
	_, err := ResolveEnv([]byte(minimal))
	if err == nil || !strings.Contains(err.Error(), "ALICE_KEY") {
		t.Fatalf("want missing env error, got %v", err)
	}
}

func TestResolveEnvDefault(t *testing.T) {
	os.Unsetenv("MISSING_VAR")
	out, err := ResolveString("prefix-${MISSING_VAR:-abc}-suffix", nil)
	if err != nil || out != "prefix-abc-suffix" {
		t.Fatalf("got %q err %v", out, err)
	}
}

func TestWriteBackPreservesComments(t *testing.T) {
	src := `version: 1
name: acme-ai
provider:
  type: aws
  region: us-east-1
models:
  - id: llama-3.1-8b-instruct
gateway:
  # written by apply
  url: ""
`
	dir := t.TempDir()
	p := filepath.Join(dir, "deploy.yaml")
	if err := os.WriteFile(p, []byte(src), 0o600); err != nil {
		t.Fatal(err)
	}
	err := WriteBack(p, func(d *Deployment) {
		d.Gateway.URL = "https://1-2-3-4.sslip.io"
		d.Gateway.AdminToken = "gr_admin_test"
	})
	if err != nil {
		t.Fatal(err)
	}
	data, _ := os.ReadFile(p)
	s := string(data)
	if !strings.Contains(s, "# written by apply") {
		t.Fatalf("comment lost:\n%s", s)
	}
	d, err := Load(p)
	if err != nil {
		t.Fatal(err)
	}
	if d.Gateway.URL != "https://1-2-3-4.sslip.io" || d.Gateway.AdminToken != "gr_admin_test" {
		t.Fatalf("writeback failed: %+v", d.Gateway)
	}
}
