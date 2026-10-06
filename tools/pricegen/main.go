package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"os"
	"sort"
	"time"

	"github.com/geniusrise/geniusrise/internal/pricing"
)

func main() {
	out := flag.String("out", "prices.json", "output file")
	flag.Parse()

	s := &pricing.Snapshot{
		GeneratedAt:       time.Now().UTC(),
		GatewayMonthlyUSD: map[string]float64{"aws": 11, "gcp": 7, "azure": 9, "runpod": 8, "lambda": 0, "hyperbolic": 0, "ssh": 0},
		Providers:         map[string]map[string][]pricing.Offering{},
	}
	var warnings []string
	add := func(p string, fn func() (map[string][]pricing.Offering, error)) {
		offs, err := fn()
		if err != nil {
			warnings = append(warnings, fmt.Sprintf("%s: %v", p, err))
			return
		}
		s.Providers[p] = offs
	}
	add("azure", fetchAzure)
	add("gcp", fetchGCP)
	add("runpod", fetchRunPod)
	add("lambda", fetchLambda)
	add("hyperbolic", fetchHyperbolic)
	add("aws", fetchAWS)

	if len(s.Providers) == 0 {
		log.Fatal("no providers fetched")
	}
	data, err := json.MarshalIndent(s, "", "  ")
	if err != nil {
		log.Fatal(err)
	}
	if err := os.WriteFile(*out, data, 0o644); err != nil {
		log.Fatal(err)
	}
	for _, w := range warnings {
		fmt.Fprintln(os.Stderr, "warning:", w)
	}
	fmt.Printf("wrote %s with %d providers\n", *out, len(s.Providers))
}

func merge(dest map[string][]pricing.Offering, src map[string][]pricing.Offering) {
	for r, offs := range src {
		dest[r] = append(dest[r], offs...)
	}
}

func sortedRegions(m map[string][]pricing.Offering) []string {
	var out []string
	for r := range m {
		out = append(out, r)
	}
	sort.Strings(out)
	return out
}
