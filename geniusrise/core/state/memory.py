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

from typing import Dict, Optional

from geniusrise.core.state import State


class InMemoryState(State):
    """
    🧠 **InMemoryState**: A state manager that stores state in memory.

    This manager is useful for temporary storage or testing purposes. Since it's in-memory, the data will be lost once the application stops.

    ## Attributes:
    - `store` (Dict[str, Dict]): The in-memory store for states.

    ## Usage:
    ```python
    manager = InMemoryState()
    manager.set_state("user123", {"status": "active"})
    state = manager.get_state("user123")
    print(state)  # Outputs: {"status": "active"}
    ```

    Remember, this is an in-memory store. Do not use it for persistent storage!
    """

    store: Dict[str, Dict]

    def __init__(self, task_id: str) -> None:
        """
        💥 Initialize a new in-memory state manager.
        """
        super().__init__(task_id=task_id)
        self.store = {}

    def get(self, task_id: Optional[str], key: str) -> Optional[Dict]:
        """
        📖 Get the state associated with a key.

        Args:
            key (str): The key to get the state for.

        Returns:
            Dict: The state associated with the key, or None if not found.
        """
        state = self.store.get(key)
        if state:
            self.log.debug(f"✅ Retrieved state for key: {key}")
        else:
            self.log.warning(f"🚫 No state found for key: {key}")
        return state

    def set(self, task_id: Optional[str], key: str, value: Dict) -> None:
        """
        📝 Set the state associated with a key.

        Args:
            key (str): The key to set the state for.
            value (Dict): The state to set.

        Example:
        ```python
        manager.set_state("user123", {"status": "active"})
        ```
        """
        self.store[key] = value
        self.log.debug(f"✅ Set state for key: {key}")
