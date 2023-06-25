from abc import ABC
import logging
from typing import Any, Callable
import os
import json


class BatchDataFetcher(ABC):
    output_folder: str

    def __init__(self, handler: Callable | None = None):
        self.log = logging.getLogger(__name__)
        if handler:
            self.handler = handler

    def __repr__(self) -> str:
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
            return f"{resource_type} fetched successfully."
        except Exception as e:
            self.log.error(f"Error fetching {resource_type}: {e}")
            return f"Error fetching {resource_type}: {e}"

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
