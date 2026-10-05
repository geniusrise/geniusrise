package provider

import (
	"context"
	"testing"
	"time"

	"github.com/geniusrise/geniusrise/internal/spec"
)

func TestFakeLifecycle(t *testing.T) {
	f := NewFake()
	ctx := context.Background()
	d := &spec.Deployment{Name: "t"}
	gw, err := f.Bootstrap(ctx, d, BootstrapOpts{ExternalGatewayURL: "http://127.0.0.1:1", AdminToken: "tok"})
	if err != nil {
		t.Fatal(err)
	}
	if gw.AdminToken != "tok" {
		t.Fatalf("bad gateway info: %+v", gw)
	}
	offs, err := f.Offerings(ctx, "any")
	if err != nil || len(offs) == 0 {
		t.Fatalf("offerings: %v %v", offs, err)
	}
	n, err := f.Launch(ctx, NodeSpec{Deployment: "t", Model: "m1", GPUClass: "L4", InstanceType: "fake-L4", Capacity: "spot"})
	if err != nil {
		t.Fatal(err)
	}
	if n.State != StateRunning || n.PricePerHour <= 0 {
		t.Fatalf("bad node: %+v", n)
	}
	list, err := f.List(ctx, "t")
	if err != nil || len(list) != 1 {
		t.Fatalf("list: %v %v", list, err)
	}
	if list[0].Tags["geniusrise:deployment"] != "t" {
		t.Fatalf("tags: %v", list[0].Tags)
	}
	if err := f.Terminate(ctx, n.ID); err != nil {
		t.Fatal(err)
	}
	list, _ = f.List(ctx, "t")
	if len(list) != 0 {
		t.Fatalf("terminated node still listed: %v", list)
	}
}

func TestFakeLaunchFailure(t *testing.T) {
	f := NewFake()
	f.LaunchFail = 1
	if _, err := f.Launch(context.Background(), NodeSpec{Model: "m"}); err == nil {
		t.Fatal("expected failure")
	}
	if _, err := f.Launch(context.Background(), NodeSpec{Model: "m"}); err != nil {
		t.Fatal(err)
	}
}

func TestFakeLaunchDelay(t *testing.T) {
	f := NewFake()
	f.LaunchDelay = 50 * time.Millisecond
	start := time.Now()
	if _, err := f.Launch(context.Background(), NodeSpec{Model: "m"}); err != nil {
		t.Fatal(err)
	}
	if time.Since(start) < 40*time.Millisecond {
		t.Fatal("delay not applied")
	}
}
