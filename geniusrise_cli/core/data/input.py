import logging
from abc import ABC, abstractmethod

log = logging.getLogger(__name__)


class InputConfig(ABC):
    """
    Abstract class for managing input configurations.
    """

    @abstractmethod
    def get(self):
        """
        Abstract method to get data from the input source.

        Returns:
            The data from the input source.
        """
        pass
