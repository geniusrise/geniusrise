package spec

import (
	"fmt"
	"os"
	"regexp"
	"strings"
	"time"

	"gopkg.in/yaml.v3"
)

const (
	Version = 1

	ProviderAWS        = "aws"
	ProviderGCP        = "gcp"
	ProviderAzure      = "azure"
	ProviderRunPod     = "runpod"
	ProviderLambda     = "lambda"
	ProviderHyperbolic = "hyperbolic"
	ProviderSSH        = "ssh"
	ProviderFake       = "fake"

	CapacitySpot         = "spot"
	CapacityOnDemand     = "on-demand"
	CapacitySpotFallback = "spot-fallback"
	CapacityServerless   = "serverless"
)

var Providers = []string{ProviderAWS, ProviderGCP, ProviderAzure, ProviderRunPod, ProviderLambda, ProviderHyperbolic, ProviderSSH, ProviderFake}
var Capacities = []string{CapacitySpot, CapacityOnDemand, CapacitySpotFallback, CapacityServerless}

var nameRe = regexp.MustCompile(`^[a-z0-9][a-z0-9-]{2,31}$`)

type Provider struct {
	Type        string    `yaml:"type"`
	Region      string    `yaml:"region"`
	Capacity    string    `yaml:"capacity"`
	Subnet      string    `yaml:"subnet"`
	Credentials string    `yaml:"credentials"`
	Hosts       []SSHHost `yaml:"hosts"`
}

type SSHHost struct {
	Addr   string  `yaml:"addr"`
	User   string  `yaml:"user"`
	GPUs   int     `yaml:"gpus"`
	CostHr float64 `yaml:"cost_hr"`
}

type Budget struct {
	MonthlyUSD *float64 `yaml:"monthly_usd"`
}

type Alerts struct {
	Webhook string `yaml:"webhook"`
}

type Gateway struct {
	Domain     string `yaml:"domain"`
	Host       string `yaml:"host"`
	URL        string `yaml:"url"`
	AdminToken string `yaml:"admin_token"`
}

type Replicas struct {
	Min int `yaml:"min"`
	Max int `yaml:"max"`
}

type Model struct {
	ID          string   `yaml:"id"`
	Variant     string   `yaml:"variant"`
	Replicas    Replicas `yaml:"replicas"`
	IdleTimeout string   `yaml:"idle_timeout"`
}

type Limits struct {
	RPM            int64 `yaml:"rpm"`
	TokensPerDay   int64 `yaml:"tokens_per_day"`
	STTMBPerDay    int64 `yaml:"stt_mb_per_day"`
	TTSCharsPerDay int64 `yaml:"tts_chars_per_day"`
}

type Key struct {
	Name   string   `yaml:"name"`
	Key    string   `yaml:"key"`
	Models []string `yaml:"models"`
	Limits Limits   `yaml:"limits"`
}

type Deployment struct {
	Version  int               `yaml:"version"`
	Name     string            `yaml:"name"`
	Provider Provider          `yaml:"provider"`
	Budget   *Budget           `yaml:"budget"`
	Alerts   *Alerts           `yaml:"alerts"`
	Gateway  Gateway           `yaml:"gateway"`
	Models   []Model           `yaml:"models"`
	Keys     []Key             `yaml:"keys"`
	Secrets  map[string]string `yaml:"secrets"`
}

func (m Model) IdleDuration() (time.Duration, error) {
	if m.IdleTimeout == "" {
		return 15 * time.Minute, nil
	}
	return time.ParseDuration(m.IdleTimeout)
}

func Parse(data []byte) (*Deployment, error) {
	var d Deployment
	dec := yaml.NewDecoder(strings.NewReader(string(data)))
	dec.KnownFields(true)
	if err := dec.Decode(&d); err != nil {
		return nil, fmt.Errorf("parse deploy.yaml: %w", err)
	}
	if err := d.Validate(); err != nil {
		return nil, err
	}
	return &d, nil
}

var ErrNotImplemented = fmt.Errorf("provider is not implemented yet")

func ResolveEnvFile(path string) ([]byte, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	return ResolveEnv(data)
}

func Load(path string) (*Deployment, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	return Parse(data)
}

func contains(list []string, s string) bool {
	for _, v := range list {
		if v == s {
			return true
		}
	}
	return false
}

func (d *Deployment) Validate() error {
	if d.Version != Version {
		return fmt.Errorf("version must be %d", Version)
	}
	if !nameRe.MatchString(d.Name) {
		return fmt.Errorf("name %q must match %s", d.Name, nameRe.String())
	}
	if !contains(Providers, d.Provider.Type) {
		return fmt.Errorf("provider.type %q must be one of %s", d.Provider.Type, strings.Join(Providers, ", "))
	}
	if d.Provider.Type == ProviderSSH {
		if len(d.Provider.Hosts) == 0 {
			return fmt.Errorf("provider.hosts is required for ssh")
		}
		for i, h := range d.Provider.Hosts {
			if h.Addr == "" {
				return fmt.Errorf("provider.hosts[%d].addr is required", i)
			}
			if h.User == "" {
				return fmt.Errorf("provider.hosts[%d].user is required", i)
			}
			if h.GPUs < 1 {
				return fmt.Errorf("provider.hosts[%d].gpus must be >= 1", i)
			}
		}
	} else if d.Provider.Region == "" {
		return fmt.Errorf("provider.region is required for %s", d.Provider.Type)
	}
	if d.Provider.Capacity == "" {
		d.Provider.Capacity = CapacityOnDemand
	}
	if !contains(Capacities, d.Provider.Capacity) {
		return fmt.Errorf("provider.capacity %q must be one of %s", d.Provider.Capacity, strings.Join(Capacities, ", "))
	}
	if d.Provider.Capacity == CapacityServerless && d.Provider.Type != ProviderRunPod {
		return fmt.Errorf("provider.capacity serverless is only supported for runpod")
	}
	if (d.Provider.Type == ProviderLambda || d.Provider.Type == ProviderHyperbolic) && d.Gateway.Host == "" {
		return fmt.Errorf("gateway.host is required for %s (no CPU instances available)", d.Provider.Type)
	}
	if len(d.Models) == 0 {
		return fmt.Errorf("at least one model is required")
	}
	seenModels := map[string]bool{}
	for i, m := range d.Models {
		if m.ID == "" {
			return fmt.Errorf("models[%d].id is required", i)
		}
		if seenModels[m.ID] {
			return fmt.Errorf("models[%d].id %q is duplicated", i, m.ID)
		}
		seenModels[m.ID] = true
		if m.Replicas.Min < 0 {
			return fmt.Errorf("models[%d].replicas.min must be >= 0", i)
		}
		if m.Replicas.Max < 1 {
			d.Models[i].Replicas.Max = 1
		}
		if m.Replicas.Max < m.Replicas.Min {
			return fmt.Errorf("models[%d].replicas.max (%d) must be >= min (%d)", i, m.Replicas.Max, m.Replicas.Min)
		}
		if _, err := m.IdleDuration(); err != nil {
			return fmt.Errorf("models[%d].idle_timeout: %w", i, err)
		}
	}
	seenKeys := map[string]bool{}
	for i, k := range d.Keys {
		if k.Name == "" {
			return fmt.Errorf("keys[%d].name is required", i)
		}
		if seenKeys[k.Name] {
			return fmt.Errorf("keys[%d].name %q is duplicated", i, k.Name)
		}
		seenKeys[k.Name] = true
		if k.Key == "" {
			return fmt.Errorf("keys[%d].key is required", i)
		}
		if len(k.Models) == 0 {
			d.Keys[i].Models = []string{"*"}
		}
	}
	if d.Budget != nil && d.Budget.MonthlyUSD != nil && *d.Budget.MonthlyUSD <= 0 {
		return fmt.Errorf("budget.monthly_usd must be > 0")
	}
	return nil
}

var envRe = regexp.MustCompile(`\$\{([A-Za-z_][A-Za-z0-9_]*)(:-([^}]*))?\}`)

func ResolveString(s string, lookup func(string) (string, bool)) (string, error) {
	if lookup == nil {
		lookup = func(string) (string, bool) { return "", false }
	}
	var err error
	out := envRe.ReplaceAllStringFunc(s, func(m string) string {
		sub := envRe.FindStringSubmatch(m)
		name, def := sub[1], sub[3]
		if v, ok := lookup(name); ok && v != "" {
			return v
		}
		if sub[2] != "" {
			return def
		}
		if err == nil {
			err = fmt.Errorf("environment variable %s is not set", name)
		}
		return m
	})
	return out, err
}

func resolveNode(n *yaml.Node, lookup func(string) (string, bool)) error {
	switch n.Kind {
	case yaml.DocumentNode:
		return resolveNode(n.Content[0], lookup)
	case yaml.MappingNode:
		for _, c := range n.Content {
			if err := resolveNode(c, lookup); err != nil {
				return err
			}
		}
	case yaml.SequenceNode:
		for _, c := range n.Content {
			if err := resolveNode(c, lookup); err != nil {
				return err
			}
		}
	case yaml.ScalarNode:
		if n.Tag == "!!str" {
			v, err := ResolveString(n.Value, lookup)
			if err != nil {
				line := n.Line
				return fmt.Errorf("line %d: %w", line, err)
			}
			n.Value = v
		}
	}
	return nil
}

func ResolveEnv(data []byte) ([]byte, error) {
	var root yaml.Node
	if err := yaml.Unmarshal(data, &root); err != nil {
		return nil, err
	}
	if err := resolveNode(&root, func(name string) (string, bool) {
		v, ok := os.LookupEnv(name)
		return v, ok
	}); err != nil {
		return nil, err
	}
	var out strings.Builder
	enc := yaml.NewEncoder(&out)
	enc.SetIndent(2)
	if err := enc.Encode(&root); err != nil {
		return nil, err
	}
	enc.Close()
	return []byte(out.String()), nil
}

func LoadResolved(path string) (*Deployment, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	data, err = ResolveEnv(data)
	if err != nil {
		return nil, err
	}
	return Parse(data)
}

func Marshal(d *Deployment) ([]byte, error) {
	var b strings.Builder
	enc := yaml.NewEncoder(&b)
	enc.SetIndent(2)
	if err := enc.Encode(d); err != nil {
		return nil, err
	}
	enc.Close()
	return []byte(b.String()), nil
}

func WriteBack(path string, mutate func(*Deployment)) error {
	data, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	var root yaml.Node
	if err := yaml.Unmarshal(data, &root); err != nil {
		return err
	}
	doc := root.Content[0]
	var d Deployment
	if err := doc.Decode(&d); err != nil {
		return err
	}
	mutate(&d)
	if err := setMappingValue(doc, "gateway", func(gw *yaml.Node) {
		setField(gw, "url", d.Gateway.URL)
		setField(gw, "admin_token", d.Gateway.AdminToken)
	}); err != nil {
		return err
	}
	var out strings.Builder
	enc := yaml.NewEncoder(&out)
	enc.SetIndent(2)
	if err := enc.Encode(&root); err != nil {
		return err
	}
	enc.Close()
	tmp := path + ".tmp"
	if err := os.WriteFile(tmp, []byte(out.String()), 0o600); err != nil {
		return err
	}
	return os.Rename(tmp, path)
}

func setMappingValue(doc *yaml.Node, key string, mutate func(*yaml.Node)) error {
	for i := 0; i+1 < len(doc.Content); i += 2 {
		if doc.Content[i].Value == key {
			mutate(doc.Content[i+1])
			return nil
		}
	}
	k := &yaml.Node{Kind: yaml.ScalarNode, Tag: "!!str", Value: key}
	v := &yaml.Node{Kind: yaml.MappingNode, Tag: "!!map"}
	doc.Content = append(doc.Content, k, v)
	mutate(v)
	return nil
}

func setField(m *yaml.Node, key, value string) {
	for i := 0; i+1 < len(m.Content); i += 2 {
		if m.Content[i].Value == key {
			m.Content[i+1].Value = value
			m.Content[i+1].Tag = "!!str"
			return
		}
	}
	m.Content = append(m.Content,
		&yaml.Node{Kind: yaml.ScalarNode, Tag: "!!str", Value: key},
		&yaml.Node{Kind: yaml.ScalarNode, Tag: "!!str", Value: value},
	)
}
