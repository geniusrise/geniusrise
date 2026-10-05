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

from .base import State
from .memory import InMemoryState
from .registry import (
    register_state_backend,
    STATE_BACKENDS,
    discover_state_backends
)

# For backwards compatibility
class RedisState:
    def __new__(cls, *args, **kwargs):
        raise ImportError(
            "Redis state backend is not installed. Install with: pip install geniusrise-state-redis"
        )

class PostgresState:
    def __new__(cls, *args, **kwargs):
        raise ImportError(
            "Postgres state backend is not installed. Install with: pip install geniusrise-state-postgres"
        )

class DynamoDBState:
    def __new__(cls, *args, **kwargs):
        raise ImportError(
            "DynamoDB state backend is not installed. Install with: pip install geniusrise-state-dynamo"
        )

__all__ = [
    "State",
    "InMemoryState",
    "RedisState",
    "PostgresState",
    "DynamoDBState",
    "register_state_backend",
    "STATE_BACKENDS",
    "discover_state_backends"
]
