# geniusrise-state-redis Package

## Directory Structure

```
geniusrise-state-redis/
  geniusrise_state_redis/
    __init__.py
    redis_state.py
  setup.py
  README.md
  requirements.txt
```

## Implementation

### setup.py

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
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/geniusrise/geniusrise-state-redis",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
)
```

### requirements.txt

```
geniusrise>=0.2.0
redis>=5.0.0
jsonpickle>=3.0.0
```

### README.md

````markdown
# Geniusrise Redis State Backend

This package provides Redis state backend for the Geniusrise framework.

## Installation

```bash
pip install geniusrise-state-redis
```
````

## Usage

Once installed, the Redis state backend will be automatically available in your
Geniusrise application:

```python
from geniusrise import Task
from geniusrise.core.state import STATE_BACKENDS

# Check if Redis backend is available
if "redis" in STATE_BACKENDS:
    # Create a task with Redis state
    task = Task.create(
        some_task_class,
        state_type="redis",
        redis_host="localhost",
        redis_port=6379,
        redis_db=0
    )
```

Or in YAML configuration:

```yaml
version: '1'

tasks:
  my_task:
    name: SomeTask
    state:
      type: redis
      args:
        redis_host: localhost
        redis_port: 6379
        redis_db: 0
    # ... other configuration
```

## Configuration

The Redis state backend supports the following configuration options:

- `redis_host`: Redis server hostname (default: "localhost")
- `redis_port`: Redis server port (default: 6379)
- `redis_db`: Redis database number (default: 0)

````

### geniusrise_state_redis/__init__.py

```python
# 🧠 Geniusrise
# Copyright (C) 2023-2025  geniusrise.ai
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from geniusrise_state_redis.redis_state import RedisState

__version__ = "0.1.0"
__all__ = ["RedisState", "register_plugin"]

def register_plugin():
    """
    Register this plugin with the Geniusrise framework.
    This function is called by the plugin discovery system.
    """
    try:
        from geniusrise.core.state import register_state_backend
        register_state_backend("redis", RedisState)
        return {"redis": RedisState}
    except ImportError:
        # This might happen during setup or if geniusrise is not installed
        return {}
````

### geniusrise_state_redis/redis_state.py

```python
# 🧠 Geniusrise
# Copyright (C) 2023-2025  geniusrise.ai
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import jsonpickle
import redis
from typing import Dict, Optional, Any

from geniusrise.core.state import State


class RedisState(State):
    """
    RedisState: A state manager that stores state in Redis.

    This manager provides a fast, in-memory storage solution using Redis.

    Attributes:
        redis (redis.Redis): The Redis connection.
    """

    def __init__(self, task_id: str, host: str, port: int, db: int) -> None:
        """
        Initialize a new Redis state manager.

        Args:
            task_id (str): The task identifier.
            host (str): The host of the Redis server.
            port (int): The port of the Redis server.
            db (int): The database number to connect to.
        """
        super().__init__(task_id=task_id)
        self.redis = redis.Redis(host=host, port=port, db=db)
        self.log.info(f"Connected to Redis at {host}:{port}, DB: {db}")

    def get(self, task_id: str, key: str) -> Optional[Dict[str, Any]]:
        """
        Get the state associated with a task and key.

        Args:
            task_id (str): The task identifier.
            key (str): The key to get the state for.

        Returns:
            Optional[Dict[str, Any]]: The state associated with the task and key, if it exists.
        """
        redis_key = f"{task_id}:{key}"
        value = self.redis.get(redis_key)
        if not value:
            self.log.warning(f"Key '{redis_key}' not found in Redis.")
            return None
        else:
            return jsonpickle.decode(value.decode("utf-8"))

    def set(self, task_id: str, key: str, value: Dict[str, Any]) -> None:
        """
        Set the state associated with a task and key.

        Args:
            task_id (str): The task identifier.
            key (str): The key to set the state for.
            value (Dict[str, Any]): The state to set.
        """
        redis_key = f"{task_id}:{key}"
        try:
            self.redis.set(redis_key, jsonpickle.encode(value))
            self.log.info(f"State for key '{redis_key}' set in Redis.")
        except Exception as e:
            self.log.exception(f"Failed to set state in Redis: {e}")
            raise
```
