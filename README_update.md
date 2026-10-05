# Geniusrise - Plugin-based Architecture

Geniusrise has been updated to use a fully modular, plugin-based architecture.
This means that:

1. The core package is now lightweight, containing only essential components
2. Optional features are available as separate installable packages
3. Plugins are automatically discovered and registered when installed

## Core Package

The core package includes:

- Task class (unified from previous Bolt/Spout concepts)
- Base Input/Output interfaces
- Base State interface and InMemoryState implementation
- Plugin discovery and registration system

## Optional Plugins

### State Backends

```bash
# Redis state backend
pip install geniusrise-state-redis

# PostgreSQL state backend
pip install geniusrise-state-postgres

# DynamoDB state backend
pip install geniusrise-state-dynamo
```

### Data Backends

```bash
# S3/File batch data handling
pip install geniusrise-data-s3

# Kafka streaming data handling
pip install geniusrise-data-kafka
```

### Infrastructure Runners

```bash
# Kubernetes runner
pip install geniusrise-runner-k8s

# Docker runner
pip install geniusrise-runner-docker

# OpenStack runner
pip install geniusrise-runner-openstack
```

## Convenience Installation

For convenience, you can still use the extras_require mechanism to install
plugins:

```bash
# Install with Redis and S3 support
pip install "geniusrise[redis,s3]"

# Install everything
pip install "geniusrise[full]"
```

## Checking Available Components

You can check which components are available in your current installation:

```python
from geniusrise import show_available_components

# Show all available components
components = show_available_components()
print(components)
```

This will output something like:

```python
{
    "state_backends": ["memory", "redis"],
    "input_backends": ["batch"],
    "output_backends": ["batch"],
    "runners": ["k8s"]
}
```

## Using with YAML Configuration

Your existing YAML configuration files will continue to work as before. When a
component is referenced in the YAML file but not installed, you'll get a helpful
error message directing you to install the required plugin.

```yaml
version: '1'

tasks:
  my_task:
    name: SomeTaskClass
    state:
      type: redis # Requires geniusrise-state-redis
      args:
        redis_host: localhost
        redis_port: 6379
        redis_db: 0
    input:
      type: batch # Requires geniusrise-data-s3
      args:
        input_folder: ./input
        input_s3_bucket: my-bucket
        input_s3_folder: input-data
    output:
      type: batch # Requires geniusrise-data-s3
      args:
        output_folder: ./output
        output_s3_bucket: my-bucket
        output_s3_folder: output-data
    method: process
    args:
      param1: value1
      param2: value2
```

## Creating Your Own Plugins

You can create your own plugins for Geniusrise by following the plugin
development guide. See `docs/PLUGIN_DEVELOPMENT.md` for details.
