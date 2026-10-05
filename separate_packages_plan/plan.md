# Plan for Completely Separating Optional Packages

## Overview

We will completely split optional components into their own packages:

1. Core Package (geniusrise)

   - Task
   - Base State class and InMemoryState
   - Base Input/Output classes
   - Basic utilities

2. State Backend Packages:

   - geniusrise-state-redis
   - geniusrise-state-postgres
   - geniusrise-state-dynamo

3. Data Backend Packages:

   - geniusrise-data-s3 (for batch)
   - geniusrise-data-kafka (for streaming)

4. Runner Packages (already planned):
   - geniusrise-runner-k8s
   - geniusrise-runner-docker
   - geniusrise-runner-openstack

## Implementation Steps

### 1. Core Package Cleanup

- Remove all optional backend implementations from core
- Keep only base classes and InMemoryState
- Update imports and core functionality to rely only on interfaces
- Create plugin system for registering backends

### 2. Create State Backend Packages

For each state backend (redis, postgres, dynamo):

- Create package structure with setup.py
- Move implementation files
- Ensure dependencies are correctly specified
- Implement auto-registration with core

### 3. Create Data Backend Packages

For data backends (s3, kafka):

- Create package structure with setup.py
- Move implementation files
- Ensure dependencies are correctly specified
- Implement auto-registration with core

### 4. Update Core to Handle Plugins

- Create plugin discovery mechanism
- Add backend registration interface
- Update documentation for plugin installation

## Directory Structure

```
geniusrise/
  geniusrise/
    core/
      state/
        __init__.py
        base.py
        memory.py  # InMemoryState stays in core
      data/
        __init__.py
        input.py
        output.py

geniusrise-state-redis/
  geniusrise_state_redis/
    __init__.py
    redis_state.py

geniusrise-state-postgres/
  geniusrise_state_postgres/
    __init__.py
    postgres_state.py

geniusrise-state-dynamo/
  geniusrise_state_dynamo/
    __init__.py
    dynamo_state.py

geniusrise-data-s3/
  geniusrise_data_s3/
    __init__.py
    batch_input.py
    batch_output.py

geniusrise-data-kafka/
  geniusrise_data_kafka/
    __init__.py
    streaming_input.py
    streaming_output.py
```

## Package Setup

### Example setup.py for Redis State

```python
from setuptools import setup, find_packages

setup(
    name="geniusrise-state-redis",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "geniusrise>=0.2.0",
        "redis>=5.0.0",
        "jsonpickle>=3.0.0",
    ],
    entry_points={
        "geniusrise.plugins.state": [
            "redis=geniusrise_state_redis:register_plugin",
        ],
    },
    author="Geniusrise",
    author_email="ixaxaar@geniusrise.ai",
    description="Redis state backend for Geniusrise",
)
```

## Plugin Registration

Each package's `__init__.py` should include a `register_plugin` function:

```python
def register_plugin():
    from geniusrise.core.state import register_state_backend
    from geniusrise_state_redis.redis_state import RedisState

    register_state_backend("redis", RedisState)
    return {"redis": RedisState}
```

## Timeline

1. Core cleanup - 1 day
2. State backend packages - 2 days
3. Data backend packages - 2 days
4. Plugin system implementation - 1 day
5. Documentation and testing - 2 days

Total: Approximately 8 days of work
