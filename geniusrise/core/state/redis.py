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
