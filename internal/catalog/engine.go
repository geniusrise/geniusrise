package catalog

import (
	"fmt"
	"strings"
)

type EngineSpec struct {
	Port int
	Path string
}

var EngineSpecs = map[string]EngineSpec{
	EngineVLLM:     {Port: 8000, Path: "/v1"},
	EngineLlamaCPP: {Port: 8080, Path: "/v1"},
	EngineSpeaches: {Port: 8000, Path: "/v1"},
}

func (v *Variant) EnginePort() int { return EngineSpecs[v.Engine].Port }

func (v *Variant) EngineCommand(modelDir string) ([]string, error) {
	switch v.Engine {
	case EngineVLLM:
		args := []string{"vllm", "serve", v.HFRepo,
			"--port", fmt.Sprint(v.EnginePort()),
			"--host", "127.0.0.1"}
		args = append(args, v.Args...)
		return args, nil
	case EngineLlamaCPP:
		if v.File == "" {
			return nil, fmt.Errorf("variant %s: gguf file is required", v.Name)
		}
		gguf := v.HFRepo + "/" + v.File
		if modelDir != "" {
			gguf = modelDir + "/" + v.HFRepo + "/" + v.File
		}
		args := []string{"llama-server",
			"--model", gguf,
			"--alias", gguf,
			"--host", "127.0.0.1",
			"--port", fmt.Sprint(v.EnginePort()),
			"--ctx-size", "8192"}
		args = append(args, v.Args...)
		return args, nil
	case EngineSpeaches:
		args := []string{"speaches",
			"--host", "127.0.0.1",
			"--port", fmt.Sprint(v.EnginePort())}
		args = append(args, v.Args...)
		return args, nil
	}
	return nil, fmt.Errorf("unknown engine %q", v.Engine)
}

func (v *Variant) HFDownload() []string {
	if v.Engine == EngineLlamaCPP && v.File != "" {
		return []string{v.HFRepo + "/" + v.File}
	}
	return []string{v.HFRepo}
}

func (v *Variant) UsesGPU() bool {
	for _, g := range v.GPUs {
		if g != "cpu" {
			return true
		}
	}
	return false
}

func (r *Recipe) Summary() string {
	variants := make([]string, len(r.Variants))
	for i, v := range r.Variants {
		variants[i] = v.Name
	}
	return fmt.Sprintf("%s (%s): variants [%s], license %s", r.ID, r.Type, strings.Join(variants, ", "), r.License)
}
