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
        try:
            # For Python 3.10+
            entry_points = importlib.metadata.entry_points(group="geniusrise.plugins.state")
        except TypeError:
            # For older Python versions
            entry_points = importlib.metadata.entry_points().get("geniusrise.plugins.state", [])

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
