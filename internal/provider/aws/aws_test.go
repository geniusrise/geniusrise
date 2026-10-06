package aws

import (
	"encoding/base64"
	"strings"
	"testing"

	"github.com/geniusrise/geniusrise/internal/provider"
	"github.com/geniusrise/geniusrise/internal/spec"
)

func decodeUD(t *testing.T, b64 string) string {
	t.Helper()
	raw, err := base64.StdEncoding.DecodeString(b64)
	if err != nil {
		t.Fatal(err)
	}
	return string(raw)
}

func TestGatewayUserData(t *testing.T) {
	ud := decodeUD(t, gatewayUserData(provider.BootstrapOpts{Version: "1.2.3"}, "tok123", ""))
	if !strings.Contains(ud, "docker.io") || !strings.Contains(ud, "GR_ADMIN_TOKEN=tok123") {
		t.Fatalf("bad gateway user data:\n%s", ud)
	}
	if !strings.Contains(ud, "GR_VERSION=1.2.3") {
		t.Fatalf("version missing:\n%s", ud)
	}
	if !strings.Contains(ud, "-p 443:443") {
		t.Fatalf("port missing:\n%s", ud)
	}
}

func TestNodeUserData(t *testing.T) {
	ud := decodeUD(t, nodeUserData(map[string]string{
		"GR_IMAGE": "ghcr.io/geniusrise/vllm:test", "GR_JOIN_TOKEN": "a.b",
		"HF_TOKEN": "hf_x", "GR_GPU_INDEX": "1",
	}))
	if !strings.Contains(ud, "--gpus device=1") {
		t.Fatalf("gpu index missing:\n%s", ud)
	}
	if !strings.Contains(ud, "-e HF_TOKEN=hf_x") {
		t.Fatalf("env missing:\n%s", ud)
	}
	if !strings.Contains(ud, "-e GR_JOIN_TOKEN=a.b") {
		t.Fatalf("join token missing:\n%s", ud)
	}
	if strings.Contains(ud, "-e GR_IMAGE") {
		t.Fatalf("image leaked into env flags:\n%s", ud)
	}
	ud2 := decodeUD(t, nodeUserData(map[string]string{"GR_IMAGE": "img"}))
	if !strings.Contains(ud2, "--gpus all") {
		t.Fatalf("default gpus missing:\n%s", ud2)
	}
}

func TestTags(t *testing.T) {
	ts := tags("acme", "geniusrise:role", "gateway")
	if len(ts) != 2 || ts[0].Key == nil || *ts[0].Value != "acme" {
		t.Fatalf("bad tags: %+v", ts)
	}
	found := false
	for _, tag := range ts {
		if *tag.Key == "geniusrise:role" && *tag.Value == "gateway" {
			found = true
		}
	}
	if !found {
		t.Fatal("role tag missing")
	}
}

func TestGPUClassMapping(t *testing.T) {
	for class, m := range gpuClasses {
		if m.GPUClass != class || len(m.InstanceTypes) == 0 {
			t.Fatalf("bad mapping for %s", class)
		}
	}
	if gpuClasses["T4"].InstanceTypes[0] != "g4dn.xlarge" {
		t.Fatal("T4 should map to g4dn")
	}
	if gpuClasses["A10G"].InstanceTypes[0] != "g5.xlarge" {
		t.Fatal("A10G should map to g5")
	}
}

func TestPolicyARN(t *testing.T) {
	if policyARN("123", "gr-x-gw-policy") != "arn:aws:iam::123:policy/gr-x-gw-policy" {
		t.Fatal("bad arn")
	}
}

var _ = spec.ProviderAWS
