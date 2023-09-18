#!/usr/bin/env bash

# Create an EKS cluster with 2 node groups - one with GPU and one without

eksctl create cluster \
    --name=geniusrise-dev \
    --region=us-east-1 \
    --version=auto \
    --vpc-private-subnets=subnet-0434a4633a9a47a37,subnet-0c9fd7d91018e2fa7,subnet-048aa1bc149e9335f \
    --vpc-public-subnets=subnet-0cc02560abd69ce96,subnet-021a12dcae39e5264,subnet-0666dce19a2c9e5a9 \
    --tags="Project=GeniusRise,Environment=Dev" \
    --managed \
    --asg-access \
    --full-ecr-access \
    --ssh-access \
    --install-nvidia-plugin \
    --install-neuron-plugin \
    --auto-kubeconfig

eksctl create nodegroup \
    --cluster=geniusrise-dev \
    --name=non-gpu \
    --node-type=t3a.medium \
    --nodes=0 \
    --nodes-min=0 \
    --nodes-max=3 \
    --region=us-east-1 \
    --full-ecr-access \
    --asg-access \
    --ssh-access \
    --managed

eksctl create nodegroup \
    --cluster=geniusrise-dev \
    --name=gpu \
    --node-type=p3.2xlarge \
    --nodes=0 \
    --nodes-min=0 \
    --nodes-max=3 \
    --region=us-east-1 \
    --full-ecr-access \
    --asg-access \
    --ssh-access \
    --managed \
    --install-nvidia-plugin

eksctl create iamidentitymapping \
    --cluster geniusrise-dev \
    --region us-east-1 \
    --arn arn:aws:iam::1:user/god \
    --group system:masters \
    --username god \
    --no-duplicate-arns

eksctl create iamserviceaccount \
    --name ebs-csi-controller-sa \
    --namespace kube-system \
    --cluster geniusrise-dev \
    --role-name AmazonEKS_EBS_CSI_DriverRole \
    --role-only \
    --attach-policy-arn arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy \
    --approve

oidc_id=$(aws eks describe-cluster --name geniusrise-dev --query "cluster.identity.oidc.issuer" --output text | cut -d '/' -f 5)
aws iam list-open-id-connect-providers | grep "$oidc_id" | cut -d "/" -f4\n

eksctl utils associate-iam-oidc-provider --cluster geniusrise-dev --approve

ksctl create addon \
    --name aws-ebs-csi-driver \
    --cluster geniusrise-dev \
    --service-account-role-arn arn:aws:iam::1:role/AmazonEKS_EBS_CSI_DriverRole \
    --force
