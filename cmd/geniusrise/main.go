package main

import (
	"os"

	"github.com/geniusrise/geniusrise/internal/cli"
)

func main() {
	if err := cli.Execute(); err != nil {
		os.Exit(1)
	}
}
