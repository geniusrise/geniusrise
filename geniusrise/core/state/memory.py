# 🧠 Geniusrise
# Copyright (C) 2023  geniusrise.ai
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

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

    def __init__(self) -> None:
        """
        💥 Initialize a new in-memory state manager.
        """
        super().__init__()
        self.store = {}

    def get(self, key: str) -> Optional[Dict]:
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

    def set(self, key: str, value: Dict) -> None:
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
