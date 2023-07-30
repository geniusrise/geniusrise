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

import inspect
import json
import logging
import os
import uuid
from abc import ABC
from typing import Any, Callable, Optional

from geniusrise.core.state import InMemoryStateManager, StateManager


class BatchDataFetcher(ABC):
    """
    An abstract base class for batch data fetchers.
    """

    output_folder: str
    state_manager: StateManager

    def __init__(self, state_manager: StateManager = InMemoryStateManager(), handler: Optional[Callable] = None):
        """
        Initialize the batch data fetcher.

        :param state_manager: A state manager instance for saving and retrieving state.
        :param handler: An optional callable to handle the fetched data.
        """
        self.log = logging.getLogger(__name__)
        self.handler = handler
        self.id = str(uuid.uuid4())
        self.state_manager = state_manager
        self.state_key = f"{self.__class__.__name__}-{self.id}"
        self.state = self.state_manager.get_state(self.state_key)
        if not self.state:
            self.state = {"last_run": None, "status": None}
            self.state_manager.save_state(self.state_key, self.state)  # type: ignore
        self.save_state()

    def __repr__(self) -> str:
        """
        Return a string representation of the batch data fetcher.

        :return: A string representation of the batch data fetcher.
        """
        return f"Batch data fetcher: {self.__class__.__name__}"

    def get(self, resource_type: str) -> str:
        """
        Call the appropriate function based on the resource type, save the data, and return the status.

        :param resource_type: Type of the resource to fetch.
        :return: Status message.
        """
        fetch_method = getattr(self, f"fetch_{resource_type}", None)
        if not fetch_method:
            self.log.error(f"Invalid resource type: {resource_type}")
            return f"Invalid resource type: {resource_type}"
        try:
            fetch_method()
            self.update_state("success")
            return f"{resource_type} fetched successfully."
        except Exception as e:
            self.log.error(f"Error fetching {resource_type}: {e}")
            self.update_state("failure")
            return f"Error fetching {resource_type}: {e}"

    def fetch_all(self):
        """
        Call all fetch methods in the class.
        """
        for name, _ in inspect.getmembers(self, predicate=inspect.ismethod):
            if name.startswith("fetch_"):
                self.get(name[6:])

    def save(self, data: Any, filename: str):
        """
        Save data to a file in the output folder or pass it to the handler.

        :param data: Data to save.
        :param filename: Name of the file to save the data.
        """
        if self.handler:
            self.handler(data)
        else:
            self.save_to_file(data, filename)

    def save_to_file(self, data: Any, filename: str):
        """
        Save data to a file in the output folder.

        :param data: Data to save.
        :param filename: Name of the file to save the data.
        """
        try:
            local_dir = os.path.join(self.output_folder, filename)
            with open(local_dir, "w") as f:
                json.dump(data, f)
            self.log.info(f"Data saved to {filename}.")
        except Exception as e:
            self.log.error(f"Error saving data to file: {e}")

    def save_state(self):
        """
        Save the state of the inherited class's class variables.
        """
        class_variables = inspect.getmembers(self, lambda a: not (inspect.isroutine(a)))
        state = self.state.copy()

        for name, value in class_variables:
            if not name.startswith("__"):
                state[name] = value
        self.state_manager.set_state(self.state_key, json.dumps(state))

    def update_state(self, status: str):
        """
        Update the state with the status of the fetch operation.

        :param status: Status of the fetch operation ('success' or 'failure').
        """
        state = self.state_manager.get_state(self.state_key)
        if state:
            self.state["status"] = status  # type: ignore
            state["status"] = status
            self.state_manager.set_state(self.state_key, json.dumps(state))  # type: ignore
