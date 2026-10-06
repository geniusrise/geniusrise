package cli

import (
	"context"
	"fmt"

	"github.com/geniusrise/geniusrise/internal/pricing"
	"github.com/geniusrise/geniusrise/internal/provider"
	"github.com/geniusrise/geniusrise/internal/provider/aws"
	sshprov "github.com/geniusrise/geniusrise/internal/provider/ssh"
	"github.com/geniusrise/geniusrise/internal/spec"
)

func newSsh(d *spec.Deployment) provider.Provider {
	return sshprov.New(d, nil)
}

func newAwsProvider(ctx context.Context, region string, snap *pricing.Snapshot, version string) (provider.Provider, error) {
	return aws.New(ctx, region, snap, version)
}

func newProviderForGateway(ctx context.Context, d *spec.Deployment, snap *pricing.Snapshot, version string) (provider.Provider, error) {
	switch d.Provider.Type {
	case spec.ProviderSSH:
		p := sshprov.New(d, nil)
		return p, nil
	case spec.ProviderAWS, spec.ProviderFake:
		return aws.New(ctx, d.Provider.Region, snap, version)
	}
	return nil, fmt.Errorf("provider %s is not implemented yet", d.Provider.Type)
}

func providerOpts(d *spec.Deployment) provider.BootstrapOpts {
	return provider.BootstrapOpts{
		Version:    rootCmd.Version,
		AdminToken: d.Gateway.AdminToken,
	}
}

func doctorProvider(ctx context.Context, p provider.Provider, d *spec.Deployment) error {
	if a, ok := p.(*aws.Provider); ok {
		return a.Doctor(ctx, d)
	}
	return nil
}
