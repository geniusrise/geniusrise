#!/usr/bin/env bash

NAME="autoscale-mum"
CLOUD="ace"
SUBNET_CIDR="10.0.0.0/24"
START_IP="10.0.0.10"
END_IP="10.0.0.200"
DNS_SERVER_IP="1.1.1.1"
GATEWAY_IP="10.0.0.1"
EXTERNAL_NETWORK="External_Net_MUM"

# Create the network
openstack --os-cloud "$CLOUD" network create --enable "$NAME"

# Create the subnet
openstack --os-cloud "$CLOUD" subnet create \
  --network "$NAME" \
  --subnet-range "$SUBNET_CIDR" \
  --allocation-pool start="$START_IP",end="$END_IP" \
  --dns-nameserver "$DNS_SERVER_IP" \
  --gateway "$GATEWAY_IP" \
  "$NAME"

# Create the router
openstack --os-cloud "$CLOUD" router create "$NAME-router"

# Attach the subnet to the router
openstack --os-cloud "$CLOUD" router add subnet "$NAME-router" "$NAME"

# Set the router as the gateway for the subnet
openstack --os-cloud "$CLOUD" router set --external-gateway "$EXTERNAL_NETWORK" "$NAME-router"
