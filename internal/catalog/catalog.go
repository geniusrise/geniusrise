package catalog

import (
	"embed"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"

	"gopkg.in/yaml.v3"
)

//go:embed all:files
var embedded embed.FS

const (
	TypeLLM = "llm"
	TypeSTT = "stt"
	TypeTTS = "tts"

	EngineVLLM     = "vllm"
	EngineLlamaCPP = "llamacpp"
	EngineSpeaches = "speaches"
)

var Types = []string{TypeLLM, TypeSTT, TypeTTS}
var Engines = []string{EngineVLLM, EngineLlamaCPP, EngineSpeaches}

var GPUS = []string{"cpu", "T4", "L4", "A10G", "L40S", "A100-40", "A100-80", "H100", "H200"}

type Tested struct {
	Date          string `yaml:"date"`
	Provider      string `yaml:"provider"`
	GPU           string `yaml:"gpu"`
	EngineVersion string `yaml:"engine_version"`
}

type VariantCapacity struct {
	Concurrency int `yaml:"concurrency"`
}

type Variant struct {
	Name     string          `yaml:"name"`
	Engine   string          `yaml:"engine"`
	HFRepo   string          `yaml:"hf_repo"`
	File     string          `yaml:"file"`
	GPUs     []string        `yaml:"gpus"`
	Args     []string        `yaml:"args"`
	Capacity VariantCapacity `yaml:"capacity"`
	Tested   *Tested         `yaml:"tested"`
}

type Recipe struct {
	ID             string    `yaml:"id"`
	Type           string    `yaml:"type"`
	License        string    `yaml:"license"`
	Gated          bool      `yaml:"gated"`
	DefaultVariant string    `yaml:"default_variant"`
	Variants       []Variant `yaml:"variants"`
}

func (r *Recipe) Variant(name string) (*Variant, error) {
	if name == "" {
		name = r.DefaultVariant
	}
	for i := range r.Variants {
		if r.Variants[i].Name == name {
			return &r.Variants[i], nil
		}
	}
	return nil, fmt.Errorf("catalog %q has no variant %q", r.ID, name)
}

type Catalog struct {
	Recipes map[string]*Recipe
	Source  string
}

func parseOne(data []byte) (*Recipe, error) {
	var r Recipe
	dec := yaml.NewDecoder(strings.NewReader(string(data)))
	dec.KnownFields(true)
	if err := dec.Decode(&r); err != nil {
		return nil, err
	}
	return &r, nil
}

func validate(r *Recipe) error {
	if r.ID == "" {
		return fmt.Errorf("recipe id is required")
	}
	if !contains(Types, r.Type) {
		return fmt.Errorf("%s: type %q must be one of %s", r.ID, r.Type, strings.Join(Types, ", "))
	}
	if len(r.Variants) == 0 {
		return fmt.Errorf("%s: at least one variant is required", r.ID)
	}
	if r.DefaultVariant == "" {
		r.DefaultVariant = r.Variants[0].Name
	}
	seen := map[string]bool{}
	for i := range r.Variants {
		v := &r.Variants[i]
		if v.Name == "" {
			return fmt.Errorf("%s: variants[%d].name is required", r.ID, i)
		}
		if seen[v.Name] {
			return fmt.Errorf("%s: variant %q is duplicated", r.ID, v.Name)
		}
		seen[v.Name] = true
		if !contains(Engines, v.Engine) {
			return fmt.Errorf("%s/%s: engine %q must be one of %s", r.ID, v.Name, v.Engine, strings.Join(Engines, ", "))
		}
		if v.HFRepo == "" {
			return fmt.Errorf("%s/%s: hf_repo is required", r.ID, v.Name)
		}
		if v.Engine == EngineLlamaCPP && v.File == "" {
			return fmt.Errorf("%s/%s: file is required for llamacpp", r.ID, v.Name)
		}
		if len(v.GPUs) == 0 {
			return fmt.Errorf("%s/%s: at least one gpu class is required", r.ID, v.Name)
		}
		for _, g := range v.GPUs {
			if !contains(GPUS, g) {
				return fmt.Errorf("%s/%s: gpu class %q must be one of %s", r.ID, v.Name, g, strings.Join(GPUS, ", "))
			}
		}
		if (r.Type == TypeSTT || r.Type == TypeTTS) && v.Engine != EngineSpeaches {
			return fmt.Errorf("%s/%s: %s models must use the speaches engine", r.ID, v.Name, r.Type)
		}
		if r.Type == TypeLLM && v.Engine == EngineSpeaches {
			return fmt.Errorf("%s/%s: llm models cannot use the speaches engine", r.ID, v.Name)
		}
		if v.Capacity.Concurrency < 1 {
			v.Capacity.Concurrency = 1
		}
		if v.Tested == nil {
			return fmt.Errorf("%s/%s: tested block is required", r.ID, v.Name)
		}
		if _, err := time.Parse("2006-01-02", v.Tested.Date); err != nil {
			return fmt.Errorf("%s/%s: tested.date must be YYYY-MM-DD", r.ID, v.Name)
		}
	}
	if _, err := r.Variant(r.DefaultVariant); err != nil {
		return err
	}
	return nil
}

func contains(list []string, s string) bool {
	for _, v := range list {
		if v == s {
			return true
		}
	}
	return false
}

func LoadDir(fs readDirFS, dir string) (*Catalog, error) {
	entries, err := fs.ReadDir(dir)
	if err != nil {
		return nil, err
	}
	c := &Catalog{Recipes: map[string]*Recipe{}, Source: dir}
	for _, e := range entries {
		if e.IsDir() || (!strings.HasSuffix(e.Name(), ".yaml") && !strings.HasSuffix(e.Name(), ".yml")) {
			continue
		}
		data, err := fs.ReadFile(filepath.Join(dir, e.Name()))
		if err != nil {
			return nil, err
		}
		r, err := parseOne(data)
		if err != nil {
			return nil, fmt.Errorf("%s: %w", e.Name(), err)
		}
		if err := validate(r); err != nil {
			return nil, err
		}
		if _, dup := c.Recipes[r.ID]; dup {
			return nil, fmt.Errorf("duplicate catalog id %q", r.ID)
		}
		c.Recipes[r.ID] = r
	}
	return c, nil
}

type readDirFS interface {
	ReadDir(name string) ([]os.DirEntry, error)
	ReadFile(name string) ([]byte, error)
}

func Embedded() (*Catalog, error) {
	return LoadDir(embedded, "files")
}

func Load(source string) (*Catalog, error) {
	if source == "" {
		return Embedded()
	}
	var data []byte
	var err error
	if strings.HasPrefix(source, "http://") || strings.HasPrefix(source, "https://") {
		resp, herr := http.Get(source)
		if herr != nil {
			return nil, herr
		}
		defer resp.Body.Close()
		if resp.StatusCode != http.StatusOK {
			return nil, fmt.Errorf("catalog %s: status %d", source, resp.StatusCode)
		}
		data, err = io.ReadAll(resp.Body)
	} else if st, serr := os.Stat(source); serr == nil && st.IsDir() {
		return LoadDir(os.DirFS(source).(readDirFS), ".")
	} else {
		data, err = os.ReadFile(source)
	}
	if err != nil {
		return nil, err
	}
	var list []*Recipe
	if err := yaml.Unmarshal(data, &list); err != nil {
		return loadDirSource(source)
	}
	c := &Catalog{Recipes: map[string]*Recipe{}, Source: source}
	for _, r := range list {
		if err := validate(r); err != nil {
			return nil, err
		}
		if _, dup := c.Recipes[r.ID]; dup {
			return nil, fmt.Errorf("duplicate catalog id %q", r.ID)
		}
		c.Recipes[r.ID] = r
	}
	return c, nil
}

func loadDirSource(dir string) (*Catalog, error) {
	return LoadDir(os.DirFS(dir).(readDirFS), ".")
}

func (c *Catalog) Get(id string) (*Recipe, error) {
	r, ok := c.Recipes[id]
	if !ok {
		return nil, fmt.Errorf("model %q is not in the catalog", id)
	}
	return r, nil
}

func (c *Catalog) List() []*Recipe {
	out := make([]*Recipe, 0, len(c.Recipes))
	for _, r := range c.Recipes {
		out = append(out, r)
	}
	return out
}
