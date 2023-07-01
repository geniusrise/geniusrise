import redis  # type: ignore
from typing import Dict, Optional
import json

from .state_manager import StateManager


class RedisStateManager(StateManager):
    """
    A state manager that stores state in Redis.
    """

    def __init__(self, host: str, port: int, db: int):
        """
        Initialize a new Redis state manager.

        Args:
            host (str): The host of the Redis server.
            port (int): The port of the Redis server.
            db (int): The database number to connect to.
        """
        super().__init__()
        self.redis = redis.Redis(host=host, port=port, db=db)

    def get_state(self, key: str) -> Optional[Dict]:
        """
        Get the state associated with a key.

        Args:
            key (str): The key to get the state for.

        Returns:
            Dict: The state associated with the key.
        """
        value = self.redis.get(key)
        if not value:
            return None
        else:
            return json.loads(str(value))

    def set_state(self, key: str, value: Dict):
        """
        Set the state associated with a key.

        Args:
            key (str): The key to set the state for.
            value (Dict): The state to set.
        """
        self.redis.set(key, json.dumps(value))
