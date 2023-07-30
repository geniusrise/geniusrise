# geniusrise
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

from geniusrise.core.state import StateManager


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
            return jsonpickle.decode(value.decode("utf-8"))

    def set_state(self, key: str, value: Dict):
        """
        Set the state associated with a key.

        Args:
            key (str): The key to set the state for.
            value (Dict): The state to set.
        """
        self.redis.set(key, jsonpickle.encode(value))
