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
