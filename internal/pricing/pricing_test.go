package pricing

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
	"time"
)

func TestEmbeddedParses(t *testing.T) {
	s, err := Embedded()
	if err != nil {
		t.Fatal(err)
	}
	o, err := s.Offering("aws", "us-east-1", "L4", CapacitySpot)
	if err != nil {
		t.Fatal(err)
	}
	if o.InstanceType != "g6.xlarge" || o.USDPerHour <= 0 {
		t.Fatalf("bad offering: %+v", o)
	}
	if s.GatewayMonthly("aws") != 11.0 {
		t.Fatalf("bad gateway cost: %v", s.GatewayMonthly("aws"))
	}
	if _, err := s.Offering("aws", "us-east-1", "H200", CapacityOnDemand); err == nil {
		t.Fatal("expected missing offering error")
	}
}

func TestCacheRoundTrip(t *testing.T) {
	dir, err := os.MkdirTemp("", "grprices")
	if err != nil {
		t.Fatal(err)
	}
	t.Setenv("XDG_CACHE_HOME", dir)
	s := &Snapshot{GeneratedAt: time.Now().UTC()}
	data, _ := json.Marshal(s)
	if err := SaveCache(data); err != nil {
		t.Fatal(err)
	}
	got, err := LoadCached()
	if err != nil {
		t.Fatal(err)
	}
	if got.GeneratedAt.IsZero() {
		t.Fatal("cache round trip failed")
	}
	if _, err := LoadCached(); err != nil {
		t.Fatal(err)
	}
	_ = filepath.Join(dir)
}

func TestStaleCache(t *testing.T) {
	dir, err := os.MkdirTemp("", "grprices2")
	if err != nil {
		t.Fatal(err)
	}
	t.Setenv("XDG_CACHE_HOME", dir)
	s := &Snapshot{GeneratedAt: time.Now().UTC().Add(-48 * time.Hour)}
	data, _ := json.Marshal(s)
	if err := SaveCache(data); err != nil {
		t.Fatal(err)
	}
	if _, err := LoadCached(); err == nil {
		t.Fatal("expected stale error")
	}
}

func TestLoadFallsBackToEmbedded(t *testing.T) {
	dir, err := os.MkdirTemp("", "grprices3")
	if err != nil {
		t.Fatal(err)
	}
	t.Setenv("XDG_CACHE_HOME", dir)
	s, err := Load("http://127.0.0.1:0/none.json")
	if err != nil {
		t.Fatal(err)
	}
	if _, err := s.Offering("runpod", "global", "H100", CapacityOnDemand); err != nil {
		t.Fatal(err)
	}
}

func TestRenderTable(t *testing.T) {
	s, _ := Embedded()
	out := s.RenderTable()
	if len(out) == 0 {
		t.Fatal("empty table")
	}
}
