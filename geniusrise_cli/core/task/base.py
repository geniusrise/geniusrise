import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict

from geniusrise_cli.core.data import InputConfig, OutputConfig


class Task(ABC):
    input_config: InputConfig
    output_config: OutputConfig

    """
    Class for managing tasks.

    Attributes:
        id (uuid.UUID): Unique identifier for the task.
        input_config (InputConfig): Configuration for input data.
        output_config (OutputConfig): Configuration for output data.
    """

    def __init__(self):
        """
        Initialize a new task.

        Args:
            input_config (InputConfig): Configuration for input data.
            output_config (OutputConfig): Configuration for output data.
        """
        self.id = uuid.uuid4()

    @abstractmethod
    def run(self) -> None:
        """
        Run the task. This method should be implemented by subclasses.
        """
        raise NotImplementedError

    @abstractmethod
    def destroy(self) -> None:
        """
        Destroy the task. This method should be implemented by subclasses.
        """
        raise NotImplementedError

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """
        Get the status of the task. This method should be implemented by subclasses.

        Returns:
            Dict[str, Any]: The status of the task.
        """
        raise NotImplementedError

    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get the statistics of the task. This method should be implemented by subclasses.

        Returns:
            Dict[str, Any]: The statistics of the task.
        """
        raise NotImplementedError

    @abstractmethod
    def get_logs(self) -> Dict[str, Any]:
        """
        Get the logs of the task. This method should be implemented by subclasses.

        Returns:
            Dict[str, Any]: The logs of the task.
        """
        raise NotImplementedError

    def __repr__(self):
        """
        Return a string representation of the task.

        Returns:
            str: A string representation of the task.
        """
        return f"Task(id={self.id}, input_config={self.input_config}, output_config={self.output_config})"
