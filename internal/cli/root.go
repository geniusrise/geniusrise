package cli

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"
)

var rootCmd = &cobra.Command{
	Use:     "geniusrise",
	Short:   "Run open LLM, STT and TTS models on your own infrastructure",
	Version: "0.1.0-dev",
}

func Execute() error {
	rootCmd.SetOut(os.Stdout)
	return rootCmd.Execute()
}

func init() {
	rootCmd.SetErrPrefix("error:")
	rootCmd.CompletionOptions.DisableDefaultCmd = true
}

func fatalf(format string, args ...any) {
	fmt.Fprintf(os.Stderr, "error: "+format+"\n", args...)
	os.Exit(1)
}
