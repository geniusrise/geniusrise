package aws

import (
	"context"
	"encoding/base64"
	"fmt"
	"sort"
	"strings"

	"github.com/aws/aws-sdk-go-v2/aws"
	awsconfig "github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/ec2"
	ec2types "github.com/aws/aws-sdk-go-v2/service/ec2/types"
	"github.com/aws/aws-sdk-go-v2/service/iam"
	iamtypes "github.com/aws/aws-sdk-go-v2/service/iam/types"
	"github.com/aws/aws-sdk-go-v2/service/servicequotas"
	"github.com/aws/aws-sdk-go-v2/service/ssm"
	"github.com/aws/aws-sdk-go-v2/service/sts"

	"github.com/geniusrise/geniusrise/internal/pricing"
	"github.com/geniusrise/geniusrise/internal/provider"
	"github.com/geniusrise/geniusrise/internal/spec"
)

const (
	TagDeployment     = "geniusrise:deployment"
	gatewayImage      = "ghcr.io/geniusrise/geniusrise:latest"
	gatewayRoleSuffix = "-gw-role"
)

type GPUClassMapping struct {
	GPUClass      string
	InstanceTypes []string
	AMIFilter     string
}

var gpuClasses = map[string]GPUClassMapping{
	"cpu":     {GPUClass: "cpu", InstanceTypes: []string{"c7i.xlarge"}},
	"T4":      {GPUClass: "T4", InstanceTypes: []string{"g4dn.xlarge"}},
	"A10G":    {GPUClass: "A10G", InstanceTypes: []string{"g5.xlarge"}},
	"L4":      {GPUClass: "L4", InstanceTypes: []string{"g6.xlarge"}},
	"L40S":    {GPUClass: "L40S", InstanceTypes: []string{"g6e.xlarge"}},
	"A100-40": {GPUClass: "A100-40", InstanceTypes: []string{"p4d.24xlarge"}},
	"A100-80": {GPUClass: "A100-80", InstanceTypes: []string{"p4de.24xlarge"}},
	"H100":    {GPUClass: "H100", InstanceTypes: []string{"p5.48xlarge"}},
}

var dlamiSSMParams = map[string]string{
	"us-east-1":    "/aws/service/deeplearning/ami/x86_64-base-oss-nvidia-driver-gpu-cuda12.2.2-sagemaker-distribution-1.6.0/ubuntu-20.04/latest/ami-id",
	"us-west-2":    "/aws/service/deeplearning/ami/x86_64-base-oss-nvidia-driver-gpu-cuda12.2.2-sagemaker-distribution-1.6.0/ubuntu-20.04/latest/ami-id",
	"eu-central-1": "/aws/service/deeplearning/ami/x86_64-base-oss-nvidia-driver-gpu-cuda12.2.2-sagemaker-distribution-1.6.0/ubuntu-20.04/latest/ami-id",
	"ap-south-1":   "/aws/service/deeplearning/ami/x86_64-base-oss-nvidia-driver-gpu-cuda12.2.2-sagemaker-distribution-1.6.0/ubuntu-20.04/latest/ami-id",
}

var ubuntuSSMParam = "/aws/service/canonical/ubuntu/server/24.04/stable/current/amd64/hvm/ebs-gp2/ami-id"

type Provider struct {
	cfg       aws.Config
	region    string
	accountID string
	snap      *pricing.Snapshot
	version   string
}

func New(ctx context.Context, region string, snap *pricing.Snapshot, version string) (*Provider, error) {
	if region == "" {
		region = "us-east-1"
	}
	cfg, err := awsconfig.LoadDefaultConfig(ctx, awsconfig.WithRegion(region))
	if err != nil {
		return nil, fmt.Errorf("aws credentials: %w", err)
	}
	accountID := ""
	if out, err := sts.NewFromConfig(cfg).GetCallerIdentity(ctx, &sts.GetCallerIdentityInput{}); err == nil {
		accountID = aws.ToString(out.Account)
	}
	return &Provider{cfg: cfg, region: region, accountID: accountID, snap: snap, version: version}, nil
}

func (p *Provider) Name() string { return spec.ProviderAWS }

func (p *Provider) ec2() *ec2.Client { return ec2.NewFromConfig(p.cfg) }
func (p *Provider) iam() *iam.Client { return iam.NewFromConfig(p.cfg) }
func (p *Provider) ssm() *ssm.Client { return ssm.NewFromConfig(p.cfg) }

func tags(d string, extra ...string) []ec2types.Tag {
	tags := []ec2types.Tag{{Key: aws.String(TagDeployment), Value: aws.String(d)}}
	for i := 0; i+1 < len(extra); i += 2 {
		tags = append(tags, ec2types.Tag{Key: aws.String(extra[i]), Value: aws.String(extra[i+1])})
	}
	return tags
}

func tagSpecs(d string, extra ...string) []ec2types.TagSpecification {
	return []ec2types.TagSpecification{{ResourceType: ec2types.ResourceTypeInstance, Tags: tags(d, extra...)}}
}

func (p *Provider) defaultVPC(ctx context.Context) (vpcID string, subnetID string, err error) {
	out, err := p.ec2().DescribeVpcs(ctx, &ec2.DescribeVpcsInput{
		Filters: []ec2types.Filter{{Name: aws.String("is-default"), Values: []string{"true"}}},
	})
	if err != nil {
		return "", "", fmt.Errorf("describe vpcs: %w", err)
	}
	if len(out.Vpcs) == 0 {
		return "", "", fmt.Errorf("no default VPC found: create one, or set provider.subnet in deploy.yaml")
	}
	vpcID = aws.ToString(out.Vpcs[0].VpcId)
	subnets, err := p.ec2().DescribeSubnets(ctx, &ec2.DescribeSubnetsInput{
		Filters: []ec2types.Filter{
			{Name: aws.String("vpc-id"), Values: []string{vpcID}},
			{Name: aws.String("default-for-az"), Values: []string{"true"}},
		},
	})
	if err != nil || len(subnets.Subnets) == 0 {
		return "", "", fmt.Errorf("no subnets in default vpc: %w", err)
	}
	return vpcID, aws.ToString(subnets.Subnets[0].SubnetId), nil
}

func (p *Provider) findSecurityGroup(ctx context.Context, name string) (*ec2types.SecurityGroup, error) {
	out, err := p.ec2().DescribeSecurityGroups(ctx, &ec2.DescribeSecurityGroupsInput{
		GroupNames: []string{name},
	})
	if err != nil {
		if strings.Contains(err.Error(), "does not exist") || strings.Contains(err.Error(), "InvalidGroup.NotFound") {
			return nil, nil
		}
		return nil, err
	}
	if len(out.SecurityGroups) == 0 {
		return nil, nil
	}
	return &out.SecurityGroups[0], nil
}

func (p *Provider) ensureSecurityGroups(ctx context.Context, d *spec.Deployment) (gwSG, nodeSG string, err error) {
	gwName := fmt.Sprintf("gr-%s-gw", d.Name)
	nodeName := fmt.Sprintf("gr-%s-node", d.Name)
	vpcID, _, err := p.defaultVPC(ctx)
	if err != nil {
		return "", "", err
	}
	if d.Provider.Subnet != "" {
		sub, err := p.ec2().DescribeSubnets(ctx, &ec2.DescribeSubnetsInput{SubnetIds: []string{d.Provider.Subnet}})
		if err == nil && len(sub.Subnets) > 0 {
			vpcID = aws.ToString(sub.Subnets[0].VpcId)
		}
	}
	gw, err := p.findSecurityGroup(ctx, gwName)
	if err != nil {
		return "", "", err
	}
	if gw == nil {
		out, err := p.ec2().CreateSecurityGroup(ctx, &ec2.CreateSecurityGroupInput{
			GroupName:   aws.String(gwName),
			Description: aws.String("geniusrise gateway: 443 in"),
			VpcId:       aws.String(vpcID),
			TagSpecifications: []ec2types.TagSpecification{{
				ResourceType: ec2types.ResourceTypeSecurityGroup,
				Tags:         tags(d.Name),
			}},
		})
		if err != nil {
			return "", "", fmt.Errorf("create gateway sg: %w", err)
		}
		gwID := aws.ToString(out.GroupId)
		_, err = p.ec2().AuthorizeSecurityGroupIngress(ctx, &ec2.AuthorizeSecurityGroupIngressInput{
			GroupId: aws.String(gwID),
			IpPermissions: []ec2types.IpPermission{{
				IpProtocol: aws.String("tcp"),
				FromPort:   aws.Int32(443),
				ToPort:     aws.Int32(443),
				IpRanges:   []ec2types.IpRange{{CidrIp: aws.String("0.0.0.0/0")}},
			}},
		})
		if err != nil && !strings.Contains(err.Error(), "already exists") {
			return "", "", fmt.Errorf("authorize gw sg: %w", err)
		}
		gw = &ec2types.SecurityGroup{GroupId: aws.String(gwID)}
	}
	node, err := p.findSecurityGroup(ctx, nodeName)
	if err != nil {
		return "", "", err
	}
	if node == nil {
		out, err := p.ec2().CreateSecurityGroup(ctx, &ec2.CreateSecurityGroupInput{
			GroupName:   aws.String(nodeName),
			Description: aws.String("geniusrise node: no inbound"),
			VpcId:       aws.String(vpcID),
			TagSpecifications: []ec2types.TagSpecification{{
				ResourceType: ec2types.ResourceTypeSecurityGroup,
				Tags:         tags(d.Name),
			}},
		})
		if err != nil {
			return "", "", fmt.Errorf("create node sg: %w", err)
		}
		node = &ec2types.SecurityGroup{GroupId: out.GroupId}
	}
	return aws.ToString(gw.GroupId), aws.ToString(node.GroupId), nil
}

var gwAssumeRole = `{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"ec2.amazonaws.com"},"Action":"sts:AssumeRole"}]}`

var gwPolicy = `{
  "Version": "2012-10-17",
  "Statement": [
    {"Effect": "Allow","Action": ["ec2:RunInstances","ec2:TerminateInstances","ec2:StopInstances","ec2:StartInstances","ec2:Describe*"],"Resource": "*"},
    {"Effect": "Allow","Action": ["iam:PassRole"],"Resource": "*"},
    {"Effect": "Allow","Action": ["pricing:GetProducts"],"Resource": "*"}
  ]
}`

func (p *Provider) ensureGatewayRole(ctx context.Context, d *spec.Deployment) (profile string, err error) {
	c := p.iam()
	roleName := fmt.Sprintf("gr-%s-gw-role", d.Name)
	profileName := roleName + "-profile"
	_, err = c.GetRole(ctx, &iam.GetRoleInput{RoleName: aws.String(roleName)})
	if err != nil {
		_, err = c.CreateRole(ctx, &iam.CreateRoleInput{
			RoleName:                 aws.String(roleName),
			AssumeRolePolicyDocument: aws.String(gwAssumeRole),
			Tags:                     []iamtypes.Tag{{Key: aws.String(TagDeployment), Value: aws.String(d.Name)}},
		})
		if err != nil {
			return "", fmt.Errorf("create role: %w", err)
		}
	}
	policyName := fmt.Sprintf("gr-%s-gw-policy", d.Name)
	_, err = c.GetPolicy(ctx, &iam.GetPolicyInput{PolicyArn: aws.String(policyARN(p.accountID, policyName))})
	if err != nil {
		_, err = c.CreatePolicy(ctx, &iam.CreatePolicyInput{
			PolicyName:     aws.String(policyName),
			PolicyDocument: aws.String(gwPolicy),
		})
		if err != nil && !strings.Contains(err.Error(), "EntityAlreadyExists") {
			return "", fmt.Errorf("create policy: %w", err)
		}
	}
	_, err = c.AttachRolePolicy(ctx, &iam.AttachRolePolicyInput{
		RoleName:  aws.String(roleName),
		PolicyArn: aws.String(policyARN(p.accountID, policyName)),
	})
	if err != nil && !strings.Contains(err.Error(), "EntityAlreadyExists") {
		return "", fmt.Errorf("attach policy: %w", err)
	}
	_, err = c.GetInstanceProfile(ctx, &iam.GetInstanceProfileInput{InstanceProfileName: aws.String(profileName)})
	if err != nil {
		_, err = c.CreateInstanceProfile(ctx, &iam.CreateInstanceProfileInput{
			InstanceProfileName: aws.String(profileName),
			Tags:                []iamtypes.Tag{{Key: aws.String(TagDeployment), Value: aws.String(d.Name)}},
		})
		if err != nil {
			return "", fmt.Errorf("create profile: %w", err)
		}
		_, err = c.AddRoleToInstanceProfile(ctx, &iam.AddRoleToInstanceProfileInput{
			InstanceProfileName: aws.String(profileName),
			RoleName:            aws.String(roleName),
		})
		if err != nil && !strings.Contains(err.Error(), "EntityAlreadyExists") {
			return "", fmt.Errorf("add role to profile: %w", err)
		}
	}
	return profileName, nil
}

func policyARN(account, name string) string {
	return fmt.Sprintf("arn:aws:iam::%s:policy/%s", account, name)
}

func gatewayUserData(opts provider.BootstrapOpts, adminToken string, eipHint string) string {
	image := opts.GatewayImage
	if image == "" {
		image = gatewayImage
	}
	version := opts.Version
	if version == "" {
		version = "latest"
	}
	script := fmt.Sprintf(`#!/bin/bash
set -euo pipefail
apt-get update -y
apt-get install -y docker.io
systemctl enable --now docker
mkdir -p /var/lib/geniusrise
docker run -d --name geniusrise-gateway \
  --restart always \
  -p 443:443 \
  -v /var/lib/geniusrise:/data \
  -e GR_MODE=gateway \
  -e GR_DATA_DIR=/data \
  -e GR_ADMIN_TOKEN=%s \
  -e GR_VERSION=%s \
  %s
`, adminToken, version, image)
	return base64.StdEncoding.EncodeToString([]byte(script))
}

func (p *Provider) amiFor(ctx context.Context, gpuClass string) (string, error) {
	param := ubuntuSSMParam
	if gpuClass != "cpu" {
		if _, ok := dlamiSSMParams[p.region]; !ok {
			return "", fmt.Errorf("region %s has no known DLAMI parameter; set provider.region to a supported one", p.region)
		}
		param = dlamiSSMParams[p.region]
	}
	out, err := p.ssm().GetParameter(ctx, &ssm.GetParameterInput{Name: aws.String(param)})
	if err != nil {
		return "", fmt.Errorf("ssm %s: %w", param, err)
	}
	return aws.ToString(out.Parameter.Value), nil
}

func nodeUserData(env map[string]string) string {
	env = cloneMap(env)
	image := env["GR_IMAGE"]
	gpuIndex := env["GR_GPU_INDEX"]
	delete(env, "GR_IMAGE")
	delete(env, "GR_GPU_INDEX")
	delete(env, "GR_HAS_DOCKER")
	var b strings.Builder
	b.WriteString("#!/bin/bash\nset -euo pipefail\n")
	if env["GR_HAS_DOCKER"] != "1" {
		b.WriteString("apt-get update -y && apt-get install -y docker.io || true\nsystemctl enable --now docker || true\n")
	}
	var flags []string
	for k, v := range env {
		flags = append(flags, fmt.Sprintf("-e %s=%s", k, v))
	}
	sort.Strings(flags)
	gpus := "--gpus all"
	if gpuIndex != "" {
		gpus = fmt.Sprintf("--gpus device=%s", gpuIndex)
	}
	b.WriteString(fmt.Sprintf("docker run -d --name geniusrise-node --restart always --read-only --tmpfs /tmp %s %s %s\n", gpus, strings.Join(flags, " "), image))
	return base64.StdEncoding.EncodeToString([]byte(b.String()))
}

func cloneMap(m map[string]string) map[string]string {
	out := map[string]string{}
	for k, v := range m {
		out[k] = v
	}
	return out
}

func (p *Provider) Doctor(ctx context.Context, d *spec.Deployment) error {
	c := sts.NewFromConfig(p.cfg)
	out, err := c.GetCallerIdentity(ctx, &sts.GetCallerIdentityInput{})
	if err != nil {
		return fmt.Errorf("credentials: %w (run `aws configure` or set AWS_* env vars)", err)
	}
	fmt.Printf("aws identity: %s (account %s)\n", aws.ToString(out.Arn), aws.ToString(out.Account))
	if _, _, err := p.defaultVPC(ctx); err != nil {
		return fmt.Errorf("default vpc: %w", err)
	}
	fmt.Println("default vpc: ok")
	sq := servicequotas.NewFromConfig(p.cfg, func(o *servicequotas.Options) { o.Region = p.region })
	for _, q := range []struct {
		code, name string
	}{
		{"L-417A185B", "Running On-Demand G and VT instances"},
		{"L-3819A6DF", "G and VT Spot instances"},
	} {
		quota, err := sq.GetServiceQuota(ctx, &servicequotas.GetServiceQuotaInput{
			ServiceCode: aws.String("ec2"), QuotaCode: aws.String(q.code),
		})
		if err != nil {
			fmt.Printf("quota %s: unable to check (%v)\n", q.name, err)
			continue
		}
		v := quota.Quota.Value
		if v == nil || *v < 4 {
			fmt.Printf("quota %s: %.0f vCPUs — REQUEST AN INCREASE: https://console.aws.amazon.com/servicequotas/home/services/ec2/quotas/%s\n", q.name, deref(v), q.code)
		} else {
			fmt.Printf("quota %s: %.0f vCPUs — ok\n", q.name, deref(v))
		}
	}
	return nil
}

func deref(v *float64) float64 {
	if v == nil {
		return 0
	}
	return *v
}
