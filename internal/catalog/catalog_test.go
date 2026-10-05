package catalog

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestEmbeddedLoads(t *testing.T) {
	c, err := Embedded()
	if err != nil {
		t.Fatal(err)
	}
	want := []string{"llama-3.1-8b-instruct", "llama-3.2-3b-instruct", "qwen2.5-7b-instruct", "whisper-large-v3-turbo", "whisper-small", "kokoro-82m", "piper"}
	for _, id := range want {
		if _, err := c.Get(id); err != nil {
			t.Fatal(err)
		}
	}
	if len(c.Recipes) != len(want) {
		t.Fatalf("want %d recipes, got %d", len(want), len(c.Recipes))
	}
}

func TestVariantLookup(t *testing.T) {
	c, _ := Embedded()
	r, _ := c.Get("llama-3.1-8b-instruct")
	v, err := r.Variant("")
	if err != nil || v.Name != "awq" {
		t.Fatalf("default variant: %v %+v", err, v)
	}
	if _, err := r.Variant("nope"); err == nil {
		t.Fatal("expected error for unknown variant")
	}
}

func TestEngineCommands(t *testing.T) {
	c, _ := Embedded()
	r, _ := c.Get("llama-3.1-8b-instruct")
	awq, _ := r.Variant("awq")
	cmd, err := awq.EngineCommand("")
	if err != nil {
		t.Fatal(err)
	}
	if cmd[0] != "vllm" || cmd[2] != awq.HFRepo {
		t.Fatalf("bad vllm cmd: %v", cmd)
	}
	cpu, _ := r.Variant("q4-cpu")
	cmd, err = cpu.EngineCommand("/models")
	if err != nil {
		t.Fatal(err)
	}
	joined := strings.Join(cmd, " ")
	if !strings.Contains(joined, "/models/"+cpu.HFRepo+"/"+cpu.File) {
		t.Fatalf("bad llamacpp cmd: %v", cmd)
	}
	stt, _ := c.Get("whisper-large-v3-turbo")
	cpuSTT, _ := stt.Variant("cpu")
	if _, err := cpuSTT.EngineCommand(""); err != nil {
		t.Fatal(err)
	}
}

func TestLoadFromDir(t *testing.T) {
	dir := t.TempDir()
	src := `id: test-model
type: llm
license: mit
variants:
  - name: fp16
    engine: vllm
    hf_repo: org/model
    gpus: [T4]
    capacity: {concurrency: 8}
    tested: {date: "2026-10-01", provider: aws, gpu: T4, engine_version: "0.11.0"}
`
	if err := os.WriteFile(filepath.Join(dir, "test-model.yaml"), []byte(src), 0o600); err != nil {
		t.Fatal(err)
	}
	c, err := Load(dir)
	if err != nil {
		t.Fatal(err)
	}
	if _, err := c.Get("test-model"); err != nil {
		t.Fatal(err)
	}
}

func TestValidationErrors(t *testing.T) {
	dir := t.TempDir()
	cases := []struct {
		name, yaml, wantErr string
	}{
		{"missing tested", `id: m
type: llm
license: mit
variants:
  - name: fp16
    engine: vllm
    hf_repo: org/model
    gpus: [T4]
`, "tested"},
		{"bad engine", `id: m
type: llm
license: mit
variants:
  - name: fp16
    engine: custom
    hf_repo: org/model
    gpus: [T4]
    tested: {date: "2026-10-01", provider: aws, gpu: T4, engine_version: "1"}
`, "engine"},
		{"stt on vllm", `id: m
type: stt
license: mit
variants:
  - name: fp16
    engine: vllm
    hf_repo: org/model
    gpus: [T4]
    tested: {date: "2026-10-01", provider: aws, gpu: T4, engine_version: "1"}
`, "speaches"},
		{"bad gpu", `id: m
type: llm
license: mit
variants:
  - name: fp16
    engine: vllm
    hf_repo: org/model
    gpus: [MRR]
    tested: {date: "2026-10-01", provider: aws, gpu: MRR, engine_version: "1"}
`, "gpu class"},
		{"llamacpp needs file", `id: m
type: llm
license: mit
variants:
  - name: q4
    engine: llamacpp
    hf_repo: org/model
    gpus: [cpu]
    tested: {date: "2026-10-01", provider: ssh, gpu: cpu, engine_version: "1"}
`, "file"},
		{"unknown field", `id: m
typee: llm
`, ""},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			if err := os.WriteFile(filepath.Join(dir, "m.yaml"), []byte(c.yaml), 0o600); err != nil {
				t.Fatal(err)
			}
			_, err := LoadDir(os.DirFS(dir).(interface {
				ReadDir(string) ([]os.DirEntry, error)
				ReadFile(string) ([]byte, error)
			}), ".")
			if c.wantErr == "" {
				if err == nil {
					t.Fatal("expected error")
				}
				return
			}
			if err == nil || !strings.Contains(err.Error(), c.wantErr) {
				t.Fatalf("want %q, got %v", c.wantErr, err)
			}
		})
	}
}
