from abc import ABC, abstractmethod
from typing import Dict, Any
from os.path import getmtime
from time import ctime
import mimetypes
import os

from geniusrise_cli.data_sources.files.office import DocExtractor, PPTExtractor, ODTExtractor
from geniusrise_cli.data_sources.files.documents import PDFExtractor, TXTExtractor, RTFExtractor
from geniusrise_cli.data_sources.files.sheets import CSVExtractor, ExcelExtractor, ODSExtractor
from geniusrise_cli.data_sources.files.code import JSONExtractor, XMLExtractor, HTMLExtractor, MarkdownExtractor
from geniusrise_cli.data_sources.files.binary import ELFExtractor


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


def extract(file_path: str) -> Dict[str, Any]:
    """Extract text from a file.

    This function determines the appropriate extractor class based on the file
    extension, creates an instance of that class, and then processes the file
    to extract the text.

    :param file_path: The path to the file to process.
    :return: A dictionary with the original file path and the extracted data.
    """
    # Get the MIME type of the file
    mime_type, _ = mimetypes.guess_type(file_path)
    # Get the file extension
    extension = os.path.splitext(file_path)[1]

    # Map file extensions to extractor classes
    extractor_map = {
        ".pdf": PDFExtractor,
        ".csv": CSVExtractor,
        ".xlsx": ExcelExtractor,
        ".xls": ExcelExtractor,
        ".doc": DocExtractor,
        ".docx": DocExtractor,
        ".json": JSONExtractor,
        ".xml": XMLExtractor,
        ".ppt": PPTExtractor,
        ".pptx": PPTExtractor,
        ".rtf": RTFExtractor,
        ".html": HTMLExtractor,
        ".md": MarkdownExtractor,
        ".txt": TXTExtractor,
        ".ods": ODSExtractor,
        ".odt": ODTExtractor,
        ".elf": ELFExtractor,
    }

    # Default to TXTExtractor for text files and unknown file extensions
    extractor_class = TXTExtractor

    # If the file extension is in the map, use the corresponding extractor
    if extension in extractor_map:
        extractor_class = extractor_map[extension]  # type: ignore
    else:
        # Check if the file is an ELF file
        with open(file_path, "rb") as file:
            magic_number = file.read(4)
        if magic_number == b"\x7fELF":
            extractor_class = ELFExtractor  # type: ignore

    # Create an instance of the extractor class and process the file
    extractor = extractor_class(extension)
    extracted_data = extractor.extract(file_path)

    # Return both the original and extracted data
    return {"original": file_path, "extracted": extracted_data}
