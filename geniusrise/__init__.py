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
from typing import Any, Dict, Optional, List

# Version
__version__ = "0.2.0"

# Configure logging
logger = logging.getLogger(__name__)

# Import core components - these will always be available
from geniusrise.core import (
    Task,
    Input,
    Output,
    State,
    InMemoryState,
    register_runner,
    AVAILABLE_DATA_INPUTS,
    AVAILABLE_DATA_OUTPUTS,
    AVAILABLE_STATE_BACKENDS,
    AVAILABLE_RUNNERS,
)

# Base exports
__all__ = [
    "Task",           # Unified task concept
    "Input",          # Data input base class
    "Output",         # Data output base class
    "State",          # State management base class
    "InMemoryState",  # In-memory state
    "register_runner",# Runner registration API
    "AVAILABLE_DATA_INPUTS",   # Available data input backends
    "AVAILABLE_DATA_OUTPUTS",  # Available data output backends
    "AVAILABLE_STATE_BACKENDS",# Available state backends
    "AVAILABLE_RUNNERS",       # Available runners
    "__version__",    # Version information
]

# Try to import optional components - these might fail if dependencies aren't installed
# Data components
try:
    from geniusrise.core import (
        BatchInput,
        BatchOutput,
        StreamingInput,
        StreamingOutput,
    )
    __all__.extend([
        "BatchInput",     # Batch data input
        "BatchOutput",    # Batch data output
        "StreamingInput", # Streaming data input
        "StreamingOutput",# Streaming data output
    ])
except ImportError as e:
    logger.debug(f"Some data components could not be imported: {e}")

# State backends
try:
    from geniusrise.core import (
        RedisState,
        PostgresState,
        DynamoDBState,
    )
    __all__.extend([
        "RedisState",     # Redis state
        "PostgresState",  # PostgreSQL state
        "DynamoDBState",  # DynamoDB state
    ])
except ImportError as e:
    logger.debug(f"Some state backends could not be imported: {e}")

# Runners
try:
    from geniusrise.core import K8sRunner
    __all__.append("K8sRunner")
except ImportError:
    pass

try:
    from geniusrise.core import DockerRunner
    __all__.append("DockerRunner")
except ImportError:
    pass

try:
    from geniusrise.core import OpenstackRunner
    __all__.append("OpenstackRunner")
except ImportError:
    pass

# Helper function to show all available components
def show_available_components() -> Dict[str, List[str]]:
    """
    Get a dictionary of all available components in the current installation.

    Returns:
        Dict with lists of available components by category
    """
    return {
        "data_inputs": list(AVAILABLE_DATA_INPUTS.keys()),
        "data_outputs": list(AVAILABLE_DATA_OUTPUTS.keys()),
        "state_backends": list(AVAILABLE_STATE_BACKENDS.keys()),
        "runners": list(AVAILABLE_RUNNERS.keys()),
    }

__all__.append("show_available_components")
