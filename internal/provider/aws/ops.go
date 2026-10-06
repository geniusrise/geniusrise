package aws

import (
	"context"
	"fmt"
	"sort"
	"strings"
	"time"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/service/ec2"
	ec2types "github.com/aws/aws-sdk-go-v2/service/ec2/types"
	"github.com/aws/aws-sdk-go-v2/service/iam"

	"github.com/geniusrise/geniusrise/internal/pricing"
	"github.com/geniusrise/geniusrise/internal/provider"
	"github.com/geniusrise/geniusrise/internal/spec"
)

const gatewayInstanceType = "t4g.micro"

func (p *Provider) Bootstrap(ctx context.Context, d *spec.Deployment, opts provider.BootstrapOpts) (*provider.GatewayInfo, error) {
	if opts.AdminToken == "" {
		return nil, fmt.Errorf("admin token required for bootstrap")
	}
	existing, err := p.findGateway(ctx, d.Name)
	if err == nil && existing != nil {
		ip := p.gatewayAddress(ctx, existing)
		if ip != "" {
			return &provider.GatewayInfo{
				URL:        "https://" + ip + ".sslip.io",
				AdminToken: opts.AdminToken,
			}, nil
		}
	}
	gwSG, nodeSG, err := p.ensureSecurityGroups(ctx, d)
	if err != nil {
		return nil, err
	}
	profileName, err := p.ensureGatewayRole(ctx, d)
	if err != nil {
		return nil, err
	}
	_, subnetID, err := p.defaultVPC(ctx)
	if err != nil {
		return nil, err
	}
	if d.Provider.Subnet != "" {
		subnetID = d.Provider.Subnet
	}
	ami, err := p.amiFor(ctx, "cpu")
	if err != nil {
		return nil, err
	}
	eip, err := p.allocateEIP(ctx, d.Name)
	if err != nil {
		return nil, err
	}
	run, err := p.ec2().RunInstances(ctx, &ec2.RunInstancesInput{
		ImageId:          aws.String(ami),
		InstanceType:     ec2types.InstanceType(gatewayInstanceType),
		MinCount:         aws.Int32(1),
		MaxCount:         aws.Int32(1),
		SubnetId:         aws.String(subnetID),
		SecurityGroupIds: []string{gwSG},
		IamInstanceProfile: &ec2types.IamInstanceProfileSpecification{
			Name: aws.String(profileName),
		},
		UserData:          aws.String(gatewayUserData(opts, opts.AdminToken, "")),
		TagSpecifications: tagSpecs(d.Name, "geniusrise:role", "gateway"),
		MetadataOptions: &ec2types.InstanceMetadataOptionsRequest{
			HttpTokens:   ec2types.HttpTokensStateRequired,
			HttpEndpoint: ec2types.InstanceMetadataEndpointStateEnabled,
		},
		BlockDeviceMappings: []ec2types.BlockDeviceMapping{{
			DeviceName: aws.String("/dev/sda1"),
			Ebs: &ec2types.EbsBlockDevice{
				VolumeSize:          aws.Int32(12),
				VolumeType:          ec2types.VolumeTypeGp3,
				DeleteOnTermination: aws.Bool(true),
			},
		}},
	})
	if err != nil {
		return nil, fmt.Errorf("run gateway instance: %w", err)
	}
	inst := run.Instances[0]
	instID := aws.ToString(inst.InstanceId)
	_, err = p.ec2().CreateTags(ctx, &ec2.CreateTagsInput{
		Resources: []string{instID, aws.ToString(eip.AllocationId)},
		Tags:      tagsFrom(tagSpecs(d.Name, "geniusrise:role", "gateway")),
	})
	if err != nil {
		return nil, err
	}
	if err := p.waitForRunning(ctx, instID); err != nil {
		return nil, err
	}
	_, err = p.ec2().AssociateAddress(ctx, &ec2.AssociateAddressInput{
		InstanceId:   aws.String(instID),
		AllocationId: eip.AllocationId,
	})
	if err != nil {
		return nil, fmt.Errorf("associate eip: %w", err)
	}
	ip := aws.ToString(eip.PublicIp)
	_ = nodeSG
	return &provider.GatewayInfo{
		URL:        "https://" + strings.ReplaceAll(ip, ".", "-") + ".sslip.io",
		AdminToken: opts.AdminToken,
		HostAddr:   ip + ":443",
	}, nil
}

func tagsFrom(specs []ec2types.TagSpecification) []ec2types.Tag {
	var out []ec2types.Tag
	for _, s := range specs {
		out = append(out, s.Tags...)
	}
	return out
}

func (p *Provider) allocateEIP(ctx context.Context, deployment string) (*ec2types.Address, error) {
	existing, err := p.ec2().DescribeAddresses(ctx, &ec2.DescribeAddressesInput{
		Filters: []ec2types.Filter{{Name: aws.String("tag:" + TagDeployment), Values: []string{deployment}}},
	})
	if err == nil && len(existing.Addresses) > 0 {
		return &existing.Addresses[0], nil
	}
	out, err := p.ec2().AllocateAddress(ctx, &ec2.AllocateAddressInput{
		Domain: ec2types.DomainTypeVpc,
		TagSpecifications: []ec2types.TagSpecification{{
			ResourceType: ec2types.ResourceTypeElasticIp,
			Tags:         []ec2types.Tag{{Key: aws.String(TagDeployment), Value: aws.String(deployment)}},
		}},
	})
	if err != nil {
		return nil, fmt.Errorf("allocate eip: %w", err)
	}
	return &ec2types.Address{
		AllocationId: out.AllocationId,
		PublicIp:     out.PublicIp,
	}, nil
}

func (p *Provider) findGateway(ctx context.Context, deployment string) (*ec2types.Instance, error) {
	out, err := p.ec2().DescribeInstances(ctx, &ec2.DescribeInstancesInput{
		Filters: []ec2types.Filter{
			{Name: aws.String("tag:" + TagDeployment), Values: []string{deployment}},
			{Name: aws.String("tag:geniusrise:role"), Values: []string{"gateway"}},
			{Name: aws.String("instance-state-name"), Values: []string{"pending", "running", "stopped", "stopping"}},
		},
	})
	if err != nil {
		return nil, err
	}
	for _, res := range out.Reservations {
		for _, inst := range res.Instances {
			return &inst, nil
		}
	}
	return nil, nil
}

func (p *Provider) gatewayAddress(ctx context.Context, inst *ec2types.Instance) string {
	alloc, err := p.ec2().DescribeAddresses(ctx, &ec2.DescribeAddressesInput{
		Filters: []ec2types.Filter{{Name: aws.String("instance-id"), Values: []string{aws.ToString(inst.InstanceId)}}},
	})
	if err == nil && len(alloc.Addresses) > 0 {
		return aws.ToString(alloc.Addresses[0].PublicIp)
	}
	return aws.ToString(inst.PublicIpAddress)
}

func (p *Provider) waitForRunning(ctx context.Context, instanceID string) error {
	deadline := time.Now().Add(3 * time.Minute)
	for time.Now().Before(deadline) {
		out, err := p.ec2().DescribeInstances(ctx, &ec2.DescribeInstancesInput{InstanceIds: []string{instanceID}})
		if err == nil && len(out.Reservations) > 0 && len(out.Reservations[0].Instances) > 0 {
			state := out.Reservations[0].Instances[0].State.Name
			if state == ec2types.InstanceStateNameRunning {
				return nil
			}
			if state == ec2types.InstanceStateNameTerminated {
				return fmt.Errorf("gateway instance terminated during bootstrap")
			}
		}
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-time.After(5 * time.Second):
		}
	}
	return fmt.Errorf("timeout waiting for %s to run", instanceID)
}

func (p *Provider) Offerings(ctx context.Context, region string) ([]pricing.Offering, error) {
	if p.snap == nil {
		return nil, fmt.Errorf("no price snapshot")
	}
	var out []pricing.Offering
	out = append(out, p.snap.Offerings(p.Name(), region)...)
	var spotTypes []string
	seen := map[string]bool{}
	for _, o := range out {
		if o.Capacity == pricing.CapacitySpot && !seen[o.InstanceType] {
			seen[o.InstanceType] = true
			spotTypes = append(spotTypes, o.InstanceType)
		}
	}
	if len(spotTypes) > 0 && region == p.region {
		hist, err := p.ec2().DescribeSpotPriceHistory(ctx, &ec2.DescribeSpotPriceHistoryInput{
			StartTime:           aws.Time(time.Now().Add(-3 * 24 * time.Hour)),
			ProductDescriptions: []string{"Linux/UNIX"},
			InstanceTypes:       toEc2Types(spotTypes),
		})
		if err == nil {
			lowest := map[string]float64{}
			for _, sp := range hist.SpotPriceHistory {
				var price float64
				fmt.Sscanf(aws.ToString(sp.SpotPrice), "%f", &price)
				it := string(sp.InstanceType)
				if v, ok := lowest[it]; !ok || price < v {
					lowest[it] = price
				}
			}
			for i := range out {
				if out[i].Capacity == pricing.CapacitySpot {
					if v, ok := lowest[out[i].InstanceType]; ok {
						out[i].USDPerHour = v
						out[i].Available = true
					}
				}
			}
		}
	}
	sort.SliceStable(out, func(i, j int) bool { return out[i].USDPerHour < out[j].USDPerHour })
	return out, nil
}

func toEc2Types(in []string) []ec2types.InstanceType {
	var out []ec2types.InstanceType
	for _, s := range in {
		out = append(out, ec2types.InstanceType(s))
	}
	return out
}

func (p *Provider) Launch(ctx context.Context, n provider.NodeSpec) (provider.Node, error) {
	mapping, ok := gpuClasses[n.GPUClass]
	if !ok {
		mapping = gpuClasses["cpu"]
	}
	ami, err := p.amiFor(ctx, n.GPUClass)
	if err != nil {
		return provider.Node{}, err
	}
	_, nodeSG, err := p.ensureSecurityGroups(ctx, &spec.Deployment{Name: n.Deployment})
	if err != nil {
		return provider.Node{}, err
	}
	_, subnetID, err := p.defaultVPC(ctx)
	if err != nil {
		return provider.Node{}, err
	}
	instanceType := mapping.InstanceTypes[0]
	if n.InstanceType != "" {
		instanceType = n.InstanceType
	}
	input := &ec2.RunInstancesInput{
		ImageId:          aws.String(ami),
		InstanceType:     ec2types.InstanceType(instanceType),
		MinCount:         aws.Int32(1),
		MaxCount:         aws.Int32(1),
		SubnetId:         aws.String(subnetID),
		SecurityGroupIds: []string{nodeSG},
		UserData:         aws.String(nodeUserData(n.Env)),
		TagSpecifications: tagSpecs(n.Deployment,
			"geniusrise:role", "node",
			"geniusrise:model", n.Model,
			"geniusrise:price_hr", fmt.Sprintf("%.4f", p.priceFor(n)),
		),
		MetadataOptions: &ec2types.InstanceMetadataOptionsRequest{
			HttpTokens:   ec2types.HttpTokensStateRequired,
			HttpEndpoint: ec2types.InstanceMetadataEndpointStateEnabled,
		},
	}
	if n.Capacity == spec.CapacitySpot || n.Capacity == spec.CapacitySpotFallback {
		input.InstanceMarketOptions = &ec2types.InstanceMarketOptionsRequest{
			MarketType: ec2types.MarketTypeSpot,
			SpotOptions: &ec2types.SpotMarketOptions{
				SpotInstanceType:             ec2types.SpotInstanceTypeOneTime,
				InstanceInterruptionBehavior: ec2types.InstanceInterruptionBehaviorTerminate,
			},
		}
	}
	run, err := p.ec2().RunInstances(ctx, input)
	if err != nil {
		return provider.Node{}, fmt.Errorf("run node instance: %w", err)
	}
	inst := run.Instances[0]
	return provider.Node{
		ID:           aws.ToString(inst.InstanceId),
		State:        provider.StateLaunching,
		GPUClass:     n.GPUClass,
		InstanceType: instanceType,
		Capacity:     n.Capacity,
		PricePerHour: p.priceFor(n),
		LaunchedAt:   time.Now().UTC(),
		Model:        n.Model,
		Tags:         n.Tags(),
	}, nil
}

func (p *Provider) priceFor(n provider.NodeSpec) float64 {
	if p.snap == nil {
		return 0
	}
	cap := pricing.CapacityOnDemand
	if n.Capacity == spec.CapacitySpot || n.Capacity == spec.CapacitySpotFallback {
		cap = pricing.CapacitySpot
	}
	if o, err := p.snap.Offering(p.Name(), p.region, n.GPUClass, cap); err == nil {
		return o.USDPerHour
	}
	return 0
}

func (p *Provider) List(ctx context.Context, deployment string) ([]provider.Node, error) {
	out, err := p.ec2().DescribeInstances(ctx, &ec2.DescribeInstancesInput{
		Filters: []ec2types.Filter{
			{Name: aws.String("tag:" + TagDeployment), Values: []string{deployment}},
			{Name: aws.String("tag:geniusrise:role"), Values: []string{"node"}},
			{Name: aws.String("instance-state-name"), Values: []string{"pending", "running", "stopping", "stopped"}},
		},
	})
	if err != nil {
		return nil, err
	}
	var nodes []provider.Node
	for _, res := range out.Reservations {
		for _, inst := range res.Instances {
			node := provider.Node{
				ID:           aws.ToString(inst.InstanceId),
				InstanceType: string(inst.InstanceType),
				LaunchedAt:   time.Now().UTC(),
			}
			node.State = stateFromEc2(inst.State.Name)
			for _, t := range inst.Tags {
				switch aws.ToString(t.Key) {
				case "geniusrise:model":
					node.Model = aws.ToString(t.Value)
				case "geniusrise:price_hr":
					fmt.Sscanf(aws.ToString(t.Value), "%f", &node.PricePerHour)
				}
			}
			if aws.ToString((*string)(&inst.InstanceLifecycle)) == "spot" {
				node.Capacity = spec.CapacitySpot
			} else {
				node.Capacity = spec.CapacityOnDemand
			}
			nodes = append(nodes, node)
		}
	}
	return nodes, nil
}

func stateFromEc2(s ec2types.InstanceStateName) string {
	switch s {
	case ec2types.InstanceStateNamePending:
		return provider.StateLaunching
	case ec2types.InstanceStateNameRunning:
		return provider.StateRunning
	case ec2types.InstanceStateNameStopping, ec2types.InstanceStateNameStopped:
		return provider.StateTerminating
	default:
		return provider.StateTerminated
	}
}

func (p *Provider) Terminate(ctx context.Context, id string) error {
	_, err := p.ec2().TerminateInstances(ctx, &ec2.TerminateInstancesInput{
		InstanceIds: []string{id},
	})
	return err
}

func (p *Provider) Destroy(ctx context.Context, d *spec.Deployment) error {
	nodes, err := p.List(ctx, d.Name)
	if err != nil {
		return err
	}
	for _, n := range nodes {
		if err := p.Terminate(ctx, n.ID); err != nil {
			return err
		}
	}
	if gw, err := p.findGateway(ctx, d.Name); err == nil && gw != nil {
		if err := p.Terminate(ctx, aws.ToString(gw.InstanceId)); err != nil {
			return err
		}
	}
	if err := p.releaseEIPs(ctx, d.Name); err != nil {
		return err
	}
	if err := p.deleteSecurityGroups(ctx, d); err != nil {
		return err
	}
	return p.deleteIAM(ctx, d)
}

func (p *Provider) releaseEIPs(ctx context.Context, deployment string) error {
	out, err := p.ec2().DescribeAddresses(ctx, &ec2.DescribeAddressesInput{
		Filters: []ec2types.Filter{{Name: aws.String("tag:" + TagDeployment), Values: []string{deployment}}},
	})
	if err != nil {
		return nil
	}
	for _, a := range out.Addresses {
		if a.AssociationId != nil {
			p.ec2().DisassociateAddress(ctx, &ec2.DisassociateAddressInput{AssociationId: a.AssociationId})
		}
		if _, err := p.ec2().ReleaseAddress(ctx, &ec2.ReleaseAddressInput{AllocationId: a.AllocationId}); err != nil {
			return err
		}
	}
	return nil
}

func (p *Provider) deleteSecurityGroups(ctx context.Context, d *spec.Deployment) error {
	for _, name := range []string{fmt.Sprintf("gr-%s-gw", d.Name), fmt.Sprintf("gr-%s-node", d.Name)} {
		sg, err := p.findSecurityGroup(ctx, name)
		if err != nil || sg == nil {
			continue
		}
		describe, err := p.ec2().DescribeSecurityGroups(ctx, &ec2.DescribeSecurityGroupsInput{GroupIds: []string{aws.ToString(sg.GroupId)}})
		if err == nil && len(describe.SecurityGroups) > 0 {
			for _, rule := range describe.SecurityGroups[0].IpPermissions {
				p.ec2().RevokeSecurityGroupIngress(ctx, &ec2.RevokeSecurityGroupIngressInput{GroupId: sg.GroupId, IpPermissions: []ec2types.IpPermission{rule}})
			}
		}
		if _, err := p.ec2().DeleteSecurityGroup(ctx, &ec2.DeleteSecurityGroupInput{GroupId: sg.GroupId}); err != nil {
			return err
		}
	}
	return nil
}

func (p *Provider) deleteIAM(ctx context.Context, d *spec.Deployment) error {
	c := p.iam()
	roleName := fmt.Sprintf("gr-%s-gw-role", d.Name)
	profileName := roleName + "-profile"
	policyName := fmt.Sprintf("gr-%s-gw-policy", d.Name)
	policyArn := policyARN(p.accountID, policyName)
	if _, err := c.RemoveRoleFromInstanceProfile(ctx, &iam.RemoveRoleFromInstanceProfileInput{
		InstanceProfileName: aws.String(profileName), RoleName: aws.String(roleName),
	}); err != nil {
	}
	if _, err := c.DeleteInstanceProfile(ctx, &iam.DeleteInstanceProfileInput{
		InstanceProfileName: aws.String(profileName),
	}); err != nil {
	}
	if _, err := c.DetachRolePolicy(ctx, &iam.DetachRolePolicyInput{
		RoleName: aws.String(roleName), PolicyArn: aws.String(policyArn),
	}); err != nil {
	}
	if _, err := c.DeletePolicy(ctx, &iam.DeletePolicyInput{PolicyArn: aws.String(policyArn)}); err != nil {
	}
	if _, err := c.DeleteRole(ctx, &iam.DeleteRoleInput{RoleName: aws.String(roleName)}); err != nil {
	}
	return nil
}
