from typing import Dict, Optional

from geniusrise.core.state import StateManager


class InMemoryStateManager(StateManager):
    store: Dict[str, Dict]

    """
    A state manager that stores state in memory.
    """

    def __init__(self):
        """
        Initialize a new in-memory state manager.
        """
        self.store = {}

    def get_state(self, key: str) -> Optional[Dict]:
        """
        Get the state associated with a key.

        Args:
            key (str): The key to get the state for.

        Returns:
            str: The state associated with the key.
        """
        return self.store.get(key)

    def set_state(self, key: str, value: Dict) -> None:
        """
        Set the state associated with a key.

        Args:
            key (str): The key to set the state for.
            value (str): The state to set.
        """
        self.store[key] = value
