import mimetypes
import os
from typing import Any, Dict

from geniusrise.preprocessing.files.binary import ELFExtractor
from geniusrise.preprocessing.files.code import HTMLExtractor, JSONExtractor, MarkdownExtractor, XMLExtractor
from geniusrise.preprocessing.files.documents import PDFExtractor, TXTExtractor
from geniusrise.preprocessing.files.office import DocExtractor, ODTExtractor, PPTExtractor
from geniusrise.preprocessing.files.sheets import CSVExtractor, ExcelExtractor, ODSExtractor


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
        # ".rtf": RTFExtractor,
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
