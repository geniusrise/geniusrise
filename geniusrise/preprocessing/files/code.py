import json
from os.path import getmtime
from time import ctime
from typing import Any, Dict
from xml.etree import ElementTree

from bs4 import BeautifulSoup

from geniusrise.data_sources.files.base import TextExtractor


class JSONExtractor(TextExtractor):
    """Text extractor for JSON files."""

    def extract(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Extract text from a JSON file."""
        with open(file_path, "r") as file:
            data = json.load(file)
            text = json.dumps(data)
            return {"text": text, "created_at": ctime(getmtime(file_path))}


class XMLExtractor(TextExtractor):
    """Text extractor for XML files."""

    def extract(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Extract text from an XML file."""
        tree = ElementTree.parse(file_path)
        root = tree.getroot()
        text = ElementTree.tostring(root, encoding="utf8").decode("utf8")
        return {"text": text, "created_at": ctime(getmtime(file_path))}


class HTMLExtractor(TextExtractor):
    """Text extractor for HTML files."""

    def extract(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Extract text from an HTML file."""
        with open(file_path, "r") as file:
            soup = BeautifulSoup(file.read(), "html.parser")
            text = soup.get_text()
        return {"text": text, "created_at": ctime(getmtime(file_path))}


class MarkdownExtractor(TextExtractor):
    """Text extractor for Markdown files."""

    def extract(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Extract text from a Markdown file."""
        with open(file_path, "r") as file:
            text = file.read()
        return {"text": text, "created_at": ctime(getmtime(file_path))}
