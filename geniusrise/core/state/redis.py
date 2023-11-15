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

import jsonpickle  # type: ignore
import redis  # type: ignore
from typing import Dict, Optional, Any

from geniusrise.core.state import State


class RedisState(State):
    """
    RedisState: A state manager that stores state in Redis.

    This manager provides a fast, in-memory storage solution using Redis.

    Attributes:
        redis (redis.Redis): The Redis connection.
    """

    def __init__(self, task_id: str, host: str, port: int, db: int) -> None:
        """
        Initialize a new Redis state manager.

        Args:
            task_id (str): The task identifier.
            host (str): The host of the Redis server.
            port (int): The port of the Redis server.
            db (int): The database number to connect to.
        """
        super().__init__(task_id=task_id)
        self.redis = redis.Redis(host=host, port=port, db=db)
        self.log.info(f"Connected to Redis at {host}:{port}, DB: {db}")

    def get(self, task_id: str, key: str) -> Optional[Dict[str, Any]]:
        """
        Get the state associated with a task and key.

        Args:
            task_id (str): The task identifier.
            key (str): The key to get the state for.

        Returns:
            Optional[Dict[str, Any]]: The state associated with the task and key, if it exists.
        """
        redis_key = f"{task_id}:{key}"
        value = self.redis.get(redis_key)
        if not value:
            self.log.warning(f"Key '{redis_key}' not found in Redis.")
            return None
        else:
            return jsonpickle.decode(value.decode("utf-8"))

    def set(self, task_id: str, key: str, value: Dict[str, Any]) -> None:
        """
        Set the state associated with a task and key.

        Args:
            task_id (str): The task identifier.
            key (str): The key to set the state for.
            value (Dict[str, Any]): The state to set.
        """
        redis_key = f"{task_id}:{key}"
        try:
            self.redis.set(redis_key, jsonpickle.encode(value))
            self.log.info(f"State for key '{redis_key}' set in Redis.")
        except Exception as e:
            self.log.exception(f"Failed to set state in Redis: {e}")
            raise
