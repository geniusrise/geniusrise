package hostagent

import (
	"context"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/geniusrise/geniusrise/internal/tunnel"
)

func fakeDocker(t *testing.T, stateDir string) string {
	t.Helper()
	dir := t.TempDir()
	script := filepath.Join(dir, "docker")
	os.WriteFile(script, []byte(`#!/bin/sh
set -e
mkdir -p `+stateDir+`
case "$1" in
  run)
    echo "container started" >> `+stateDir+`/log
    name=""
    gpu=""
    prev=""
    for a in "$@"; do
      if [ "$prev" = "--name" ]; then name="$a"; fi
      if [ "$prev" = "--gpus" ]; then gpu="$a"; fi
      prev="$a"
    done
    echo "$name $gpu" >> `+stateDir+`/runs
    echo "fakeid123"
    ;;
  rm)
    for a in "$@"; do echo "stopped:$a" >> `+stateDir+`/log; done
    ;;
  ps)
    echo -e "gr-node-m1-1\tUp 2 minutes\tllama\t0"
    echo -e "gr-node-m1-2\tExited (0)\twhisper\t1"
    ;;
esac
`), 0o755)
	return script
}

func TestHostAgentControl(t *testing.T) {
	stateDir := t.TempDir()
	docker := fakeDocker(t, stateDir)
	agent := New(Config{NodeID: "h1", HostID: "myhost", DockerBin: docker})

	if agent.HostNodeID() != "host-myhost" {
		t.Fatalf("bad host id: %s", agent.HostNodeID())
	}

	spec := ContainerSpec{GPUIndex: 1, Name: "gr-node-test-1", Image: "img:test",
		Env: map[string]string{"GR_JOIN_TOKEN": "x"}}
	if err := agent.runContainer(context.Background(), spec); err != nil {
		t.Fatal(err)
	}
	data, _ := os.ReadFile(filepath.Join(stateDir, "runs"))
	if !strings.Contains(string(data), "gr-node-test-1 device=1") {
		t.Fatalf("run not recorded: %s", data)
	}

	if err := agent.stopContainer("gr-node-test-1"); err != nil {
		t.Fatal(err)
	}

	list, err := agent.listContainers()
	if err != nil {
		t.Fatal(err)
	}
	if len(list) != 2 || list[0].Name != "gr-node-m1-1" || list[0].GPU != 0 || list[0].Model != "llama" {
		t.Fatalf("bad list: %+v", list)
	}
	if list[1].GPU != 1 {
		t.Fatalf("bad gpu parse: %+v", list[1])
	}
}

var _ = tunnel.MsgHostRun
var _ = time.Second
