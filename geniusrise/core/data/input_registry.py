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
        try:
            # For Python 3.10+
            entry_points = importlib.metadata.entry_points(group="geniusrise.plugins.input")
        except TypeError:
            # For older Python versions
            entry_points = importlib.metadata.entry_points().get("geniusrise.plugins.input", [])

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
