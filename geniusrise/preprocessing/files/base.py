from abc import ABC, abstractmethod
from os.path import getmtime
from time import ctime
from typing import Any, Dict


class TextExtractor(ABC):
    """Abstract base class for text extractors."""

    def __init__(self, extension: str):
        self.extension = extension

    @abstractmethod
    def extract(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Process a file and extract text and metadata.

        This method must be overridden by subclasses.

        :param file_path: The path to the file to process.
        :return: A dictionary containing the extracted text and metadata.
        """
        raise NotImplementedError()


class ThirdPartyExtractor(TextExtractor, ABC):
    """Abstract base class for extractors that require an API call to an external service to make sense of them."""

    @abstractmethod
    def make_sense(self, file_path: str, **kwargs) -> str:
        """Make an API call to convert the file into text.

        This method should be implemented by each subclass to make the
        appropriate API call.

        :param file_path: The path to the file to process.
        :return: The text extracted from the file.
        """
        raise NotImplementedError()

    def process(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Process a file by making an API call to convert it into text."""
        text = self.make_sense(file_path, **kwargs)
        return {"text": text, "created_at": ctime(getmtime(file_path))}
