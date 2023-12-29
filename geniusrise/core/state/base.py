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

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class State(ABC):
    """
    Abstract base class for a state manager.

    This class is responsible for managing task states.
    It provides an interface for state management and captures task-related metrics.

    Attributes:
        buffer (Dict[str, Any]): Buffer for state data.
        log (logging.Logger): Logger for capturing logs.
        task_id (str): Identifier for the task.
    """

    def __init__(self, task_id: str) -> None:
        self.log = logging.getLogger(self.__class__.__name__)
        self.buffer: Dict[str, Any] = {}
        self.task_id = task_id

    @abstractmethod
    def get(self, task_id: str, key: str) -> Optional[Dict[str, Any]]:
        """
        Abstract method to get the state associated with a task and key.

        Args:
            task_id (str): The task identifier.
            key (str): The key to get the state for.

        Returns:
            Optional[Dict[str, Any]]: The state associated with the task and key, if it exists.
        """
        pass

    @abstractmethod
    def set(self, task_id: str, key: str, value: Dict[str, Any]) -> None:
        """
        Abstract method to set the state associated with a task and key.

        Args:
            task_id (str): The task identifier.
            key (str): The key to set the state for.
            value (Dict[str, Any]): The state to set.
        """
        pass

    def get_state(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get the state associated with a key from the buffer or underlying storage.

        Args:
            key (str): The key to get the state for.

        Returns:
            Optional[Dict[str, Any]]: The state associated with the key.
        """
        if key in self.buffer:
            return self.buffer[key]
        value = self.get(task_id=self.task_id, key=key)
        self.buffer[key] = value
        return value

    def set_state(self, key: str, value: Dict[str, Any]) -> None:
        """
        Set the state associated with a key in the buffer.

        Args:
            key (str): The key to set the state for.
            value (Dict[str, Any]): The state to set.
        """
        self.buffer[key] = value
        self.set(task_id=self.task_id, key=key, value=value)

    def flush(self) -> None:
        """
        Flush the buffer to the state storage.

        This method is responsible for writing the buffered state data to the underlying storage mechanism.
        """
        if hasattr(self, "buffer"):
            for key, value in self.buffer.items():
                self.set(task_id=self.task_id, key=key, value=value)

    def __del__(self) -> None:
        """
        Destructor to flush the buffer before object deletion.

        This ensures that any buffered state data is not lost when the object is deleted.
        """
        try:
            self.flush()
        except Exception:
            self.log.debug("Could not flush output")
