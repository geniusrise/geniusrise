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

import importlib.util
import logging
from typing import Dict, Type, Any, List

# Basic components that are always available
from geniusrise.core.data import (
    Input, Output,
    BatchInput, BatchOutput, StreamingInput, StreamingOutput,
    INPUT_BACKENDS, OUTPUT_BACKENDS,
    register_input_backend, register_output_backend
)
from geniusrise.core.state import (
    State, InMemoryState,
    RedisState, PostgresState, DynamoDBState,
    STATE_BACKENDS, register_state_backend
)
from geniusrise.core.task import Task

# Logger for import messages
logger = logging.getLogger(__name__)

# Dictionaries to track available components
AVAILABLE_DATA_INPUTS = INPUT_BACKENDS
AVAILABLE_DATA_OUTPUTS = OUTPUT_BACKENDS
AVAILABLE_STATE_BACKENDS = STATE_BACKENDS
AVAILABLE_RUNNERS = {}

# Function to register external runners via plugins
def register_runner(name: str, runner_class: type) -> None:
    """
    Register an external runner to the Geniusrise ecosystem.

    Args:
        name: The name for the runner
        runner_class: The runner class to register
    """
    AVAILABLE_RUNNERS[name] = runner_class

# Function to discover all available plugins
def discover_all_plugins() -> Dict[str, List[str]]:
    """
    Discover and load all available plugins.

    Returns:
        Dict with information about discovered plugins
    """
    from geniusrise.core.state.registry import discover_state_backends
    from geniusrise.core.data.input_registry import discover_input_backends
    from geniusrise.core.data.output_registry import discover_output_backends

    # Rediscover plugins (in case new ones were installed)
    discover_state_backends()
    discover_input_backends()
    discover_output_backends()

    # Discover runner plugins
    try:
        try:
            # Python 3.10+
            entry_points = importlib.metadata.entry_points(group="geniusrise.plugins.runner")
        except TypeError:
            # Older Python versions
            entry_points = importlib.metadata.entry_points().get("geniusrise.plugins.runner", [])

        for entry_point in entry_points:
            try:
                register_func = entry_point.load()
                register_func()
                logger.info(f"Loaded runner plugin: {entry_point.name}")
            except Exception as e:
                logger.error(f"Failed to load runner plugin {entry_point.name}: {e}")
    except Exception as e:
        logger.debug(f"Error discovering runner plugins: {e}")

    return {
        "state_backends": list(STATE_BACKENDS.keys()),
        "input_backends": list(INPUT_BACKENDS.keys()),
        "output_backends": list(OUTPUT_BACKENDS.keys()),
        "runners": list(AVAILABLE_RUNNERS.keys())
    }

# Show all available components
def show_available_components() -> Dict[str, List[str]]:
    """
    Get a dictionary of all available components in the current installation.

    Returns:
        Dict with lists of available components by category
    """
    return discover_all_plugins()

# Define exports
__all__ = [
    # Core components
    "Task", "Input", "Output", "State", "InMemoryState",

    # Placeholder compatibility classes
    "BatchInput", "BatchOutput", "StreamingInput", "StreamingOutput",
    "RedisState", "PostgresState", "DynamoDBState",

    # Registry functions
    "register_state_backend", "register_input_backend", "register_output_backend",
    "register_runner", "discover_all_plugins", "show_available_components",

    # Available component dictionaries
    "AVAILABLE_DATA_INPUTS", "AVAILABLE_DATA_OUTPUTS",
    "AVAILABLE_STATE_BACKENDS", "AVAILABLE_RUNNERS",
]

# Auto-discover plugins on import
discover_all_plugins()
