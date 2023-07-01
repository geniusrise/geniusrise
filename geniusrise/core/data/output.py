from abc import ABC, abstractmethod
from typing import Any


class OutputConfig(ABC):
    """
    Abstract base class for managing output configurations.
    """

    @abstractmethod
    def save(self, data: Any, filename: str):
        """
        Save data to a file or ingest it into a Kafka topic.

        Args:
            data (Any): The data to save or ingest.
            filename (str): The filename to use when saving the data to a file.
        """
        pass

    @abstractmethod
    def flush(self):
        """
        Flush the output. This method should be implemented by subclasses.
        """
        pass
