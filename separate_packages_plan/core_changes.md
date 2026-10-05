# Core Package Changes

## Files to Remove

### State Backends

- `geniusrise/core/state/redis.py`
- `geniusrise/core/state/postgres.py`
- `geniusrise/core/state/dynamo.py`

### Data Backends

- `geniusrise/core/data/batch_input.py`
- `geniusrise/core/data/batch_output.py`
- `geniusrise/core/data/streaming_input.py`
- `geniusrise/core/data/streaming_output.py`

## New Plugin System

### State Backend Registration

Create a new file: `geniusrise/core/state/registry.py`

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

import logging
import importlib.metadata
from typing import Dict, Type, Any, Callable

from geniusrise.core.state.base import State

logger = logging.getLogger(__name__)

# Registry of available state backends
STATE_BACKENDS: Dict[str, Type[State]] = {}

def register_state_backend(name: str, backend_class: Type[State]) -> None:
    """
    Register a state backend with the Geniusrise framework.

    Args:
        name: The name to register the backend under
        backend_class: The state backend class
    """
    if name in STATE_BACKENDS:
        logger.warning(f"State backend '{name}' is already registered. Overwriting.")

    STATE_BACKENDS[name] = backend_class
    logger.info(f"Registered state backend: {name}")

def discover_state_backends() -> None:
    """
    Discover and load state backends using entry_points.
    """
    try:
        entry_points = importlib.metadata.entry_points(group="geniusrise.plugins.state")

        for entry_point in entry_points:
            try:
                register_func = entry_point.load()
                register_func()
                logger.info(f"Loaded state backend plugin: {entry_point.name}")
            except Exception as e:
                logger.error(f"Failed to load state backend plugin {entry_point.name}: {e}")
    except Exception as e:
        logger.debug(f"Error discovering state backends: {e}")

# Register built-in state backends
from geniusrise.core.state.memory import InMemoryState
register_state_backend("memory", InMemoryState)

# Discover plugins on import
discover_state_backends()
```

### Data Backend Registration

Create new files:

- `geniusrise/core/data/input_registry.py`
- `geniusrise/core/data/output_registry.py`

Example for input_registry.py:

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

import logging
import importlib.metadata
from typing import Dict, Type, Any, Callable

from geniusrise.core.data.input import Input

logger = logging.getLogger(__name__)

# Registry of available input backends
INPUT_BACKENDS: Dict[str, Type[Input]] = {}

def register_input_backend(name: str, backend_class: Type[Input]) -> None:
    """
    Register an input backend with the Geniusrise framework.

    Args:
        name: The name to register the backend under
        backend_class: The input backend class
    """
    if name in INPUT_BACKENDS:
        logger.warning(f"Input backend '{name}' is already registered. Overwriting.")

    INPUT_BACKENDS[name] = backend_class
    logger.info(f"Registered input backend: {name}")

def discover_input_backends() -> None:
    """
    Discover and load input backends using entry_points.
    """
    try:
        entry_points = importlib.metadata.entry_points(group="geniusrise.plugins.input")

        for entry_point in entry_points:
            try:
                register_func = entry_point.load()
                register_func()
                logger.info(f"Loaded input backend plugin: {entry_point.name}")
            except Exception as e:
                logger.error(f"Failed to load input backend plugin {entry_point.name}: {e}")
    except Exception as e:
        logger.debug(f"Error discovering input backends: {e}")

# Discover plugins on import
discover_input_backends()
```

## Update State Module

Update `geniusrise/core/state/__init__.py`:

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

from geniusrise.core.state.base import State
from geniusrise.core.state.memory import InMemoryState
from geniusrise.core.state.registry import (
    register_state_backend,
    STATE_BACKENDS,
    discover_state_backends
)

__all__ = [
    "State",
    "InMemoryState",
    "register_state_backend",
    "STATE_BACKENDS",
    "discover_state_backends"
]
```

## Update Data Module

Update `geniusrise/core/data/__init__.py`:

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

from geniusrise.core.data.input import Input
from geniusrise.core.data.output import Output
from geniusrise.core.data.input_registry import (
    register_input_backend,
    INPUT_BACKENDS,
    discover_input_backends
)
from geniusrise.core.data.output_registry import (
    register_output_backend,
    OUTPUT_BACKENDS,
    discover_output_backends
)

__all__ = [
    "Input",
    "Output",
    "register_input_backend",
    "INPUT_BACKENDS",
    "discover_input_backends",
    "register_output_backend",
    "OUTPUT_BACKENDS",
    "discover_output_backends"
]
```

## Update Task.py

Update `geniusrise/core/task.py` to use the plugin registries:

```python
# Inside Task.create method

# State management
if state_type == "none" or state_type == "memory":
    state_instance = InMemoryState(task_id=task_id)
elif state_type in STATE_BACKENDS:
    # Get the backend class from the registry
    state_class = STATE_BACKENDS[state_type]

    # Initialize with appropriate parameters based on state type
    if state_type == "redis":
        # Redis specific params
        redis_host = kwargs.get("redis_host", "localhost")
        redis_port = int(kwargs.get("redis_port", 6379))
        redis_db = int(kwargs.get("redis_db", 0))

        state_instance = state_class(
            task_id=task_id,
            host=redis_host,
            port=redis_port,
            db=redis_db,
        )
    elif state_type == "postgres":
        # Postgres specific params
        postgres_host = kwargs.get("postgres_host", "localhost")
        postgres_port = int(kwargs.get("postgres_port", 5432))
        postgres_user = kwargs.get("postgres_user", "postgres")
        postgres_password = kwargs.get("postgres_password", "")
        postgres_database = kwargs.get("postgres_database", "geniusrise")
        postgres_table = kwargs.get("postgres_table", "geniusrise_state")

        state_instance = state_class(
            task_id=task_id,
            host=postgres_host,
            port=postgres_port,
            user=postgres_user,
            password=postgres_password,
            database=postgres_database,
            table=postgres_table,
        )
    elif state_type == "dynamodb":
        # DynamoDB specific params
        table_name = kwargs.get("dynamodb_table_name", "geniusrise")
        region_name = kwargs.get("dynamodb_region_name", "us-east-1")

        state_instance = state_class(
            task_id=task_id,
            table_name=table_name,
            region_name=region_name,
        )
    else:
        # Generic initialization for custom backends
        state_instance = state_class(task_id=task_id, **kwargs)
else:
    raise ValueError(
        f"Invalid state type: {state_type}. Available types: {list(STATE_BACKENDS.keys())}"
    )

# Similar changes for input and output handling
```

## Update setup.py

Remove the extras_require sections for redis, postgres, dynamo, s3, kafka, and
update setup.py to use entry_points:

```python
setup(
    # ...
    entry_points={
        "console_scripts": [
            "geniusrise = geniusrise.cli.geniusctl:main",
            "genius = geniusrise.cli.geniusctl:main",
        ]
    },
    # ...
)
```

## Update dependencies

Update requirements-core.txt to include only core dependencies:

```
typing-extensions>=4.0.0
pydantic>=2.0.0
shortuuid>=1.0.0
emoji>=2.0.0
rich-argparse>=1.0.0
prometheus-client>=0.19.0
importlib-metadata>=6.0.0
```
