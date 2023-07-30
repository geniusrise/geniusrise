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

import json
import logging
import os
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Callable, Optional

from geniusrise.data_sources.state import InMemoryStateManager, StateManager


class StreamingDataFetcher(ABC):
    """
    An abstract base class for streaming data fetchers.
    """

    output_folder: str
    state_manager: StateManager

    def __init__(self, handler: Optional[Callable] = None, state_manager: StateManager = InMemoryStateManager()):
        """
        Initialize the streaming data fetcher.

        :param handler: An optional callable to handle the fetched data.
        :param state_manager: A state manager instance for saving and retrieving state.
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

    def __repr__(self) -> str:
        """
        Return a string representation of the streaming data fetcher.

        :return: A string representation of the streaming data fetcher.
        """
        return f"Streaming data fetcher: {self.__class__.__name__}"

    @abstractmethod
    def listen(self):
        """
        Start listening for data. This method should be implemented in subclasses to handle specific data sources.
        """
        pass

    def update_state(self, status: str):
        """
        Update the state of the fetcher.

        :param status: Status to update.
        """
        self.state["last_run"] = datetime.now().isoformat()
        self.state["status"] = status
        self.state_manager.set_state(self.state_key, self.state)

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
