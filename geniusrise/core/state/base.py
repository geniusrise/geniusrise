from abc import ABC, abstractmethod
from typing import Dict, Optional


class StateManager(ABC):
    """
    Abstract base class for a state manager.

    A state manager is responsible for getting and setting state.
    """

    @abstractmethod
    def get_state(self, key: str) -> Optional[Dict]:
        """
        Get the state associated with a key.

        Args:
            key (str): The key to get the state for.

        Returns:
            Dict: The state associated with the key.
        """
        pass

    @abstractmethod
    def set_state(self, key: str, value: Dict):
        """
        Set the state associated with a key.

        Args:
            key (str): The key to set the state for.
            value (Dict): The state to set.
        """
        pass
