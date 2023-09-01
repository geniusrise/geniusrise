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

import jsonpickle
import redis  # type: ignore

from geniusrise.core.state import State


class RedisState(State):
    """
    🗄️ **RedisState**: A state manager that stores state in Redis.

    This manager provides a fast, in-memory storage solution using Redis.

    ## Attributes:
    - `redis` (redis.Redis): The Redis connection.

    ## Usage:
    ```python
    manager = RedisState(host="localhost", port=6379, db=0)
    manager.set_state("user123", {"status": "active"})
    state = manager.get_state("user123")
    print(state)  # Outputs: {"status": "active"}
    ```

    Ensure Redis is accessible and running.
    """

    def __init__(self, host: str, port: int, db: int) -> None:
        """
        💥 Initialize a new Redis state manager.

        Args:
            host (str): The host of the Redis server.
            port (int): The port of the Redis server.
            db (int): The database number to connect to.
        """
        super().__init__()
        self.redis = redis.Redis(host=host, port=port, db=db)
        self.log.info(f"🔌 Connected to Redis at {host}:{port}, DB: {db}")

    def get(self, key: str) -> Optional[Dict]:
        """
        📖 Get the state associated with a key.

        Args:
            key (str): The key to get the state for.

        Returns:
            Dict: The state associated with the key, or None if not found.

        Raises:
            Exception: If there's an error accessing Redis.
        """
        value = self.redis.get(key)
        if not value:
            self.log.warning(f"🔍 Key '{key}' not found in Redis.")
            return None
        else:
            return jsonpickle.decode(value.decode("utf-8"))

    def set(self, key: str, value: Dict) -> None:
        """
        📝 Set the state associated with a key.

        Args:
            key (str): The key to set the state for.
            value (Dict): The state to set.

        Raises:
            Exception: If there's an error accessing Redis.
        """
        try:
            self.redis.set(key, jsonpickle.encode(value))
            self.log.info(f"✅ State for key '{key}' set in Redis.")
        except Exception as e:
            self.log.exception(f"🚫 Failed to set state in Redis: {e}")
            raise
