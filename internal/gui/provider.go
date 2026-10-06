package gui

import (
	"context"

	"github.com/geniusrise/geniusrise/internal/pricing"
	"github.com/geniusrise/geniusrise/internal/provider"
	"github.com/geniusrise/geniusrise/internal/provider/aws"
	sshprov "github.com/geniusrise/geniusrise/internal/provider/ssh"
	"github.com/geniusrise/geniusrise/internal/spec"
)

func providerForCLI(ctx context.Context, d *spec.Deployment, snap *pricing.Snapshot) (provider.Provider, error) {
	switch d.Provider.Type {
	case spec.ProviderFake:
		return provider.NewFake(), nil
	case spec.ProviderSSH:
		return sshprov.New(d, nil), nil
	case spec.ProviderAWS:
		return aws.New(ctx, d.Provider.Region, snap, "gui")
	}
	return nil, spec.ErrNotImplemented
}
