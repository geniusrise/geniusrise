# 🧠 Geniusrise
# Copyright (C) 2023  geniusrise.ai
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

"""
Simple in-memory state for testing purposes only.
Not for production use - use PostgresState instead.
"""

from typing import Any, Dict, Optional
from geniusrise.core.state.base import State


class InMemoryState(State):
    """
    Simple in-memory state storage for testing.
    Data is lost when the process terminates.

    For production, use PostgresState instead.
    """

    def __init__(self, id: str = "test", **kwargs):
        super().__init__(id)
        self.data: Dict[str, Dict[str, Any]] = {}

    def get_state(self, key: str) -> Optional[Dict[str, Any]]:
        """Get state by key."""
        full_key = f"{self.id}:{key}"
        return self.data.get(full_key)

    def set_state(self, key: str, value: Dict[str, Any]) -> None:
        """Set state by key."""
        full_key = f"{self.id}:{key}"
        self.data[full_key] = value

    def flush(self) -> None:
        """No-op for in-memory state."""
        pass
