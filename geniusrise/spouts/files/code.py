# 🧠 Geniusrise
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
from os.path import getmtime
from time import ctime
from typing import Any, Dict
from xml.etree import ElementTree

from bs4 import BeautifulSoup

from geniusrise.spouts.files.base import TextExtractor


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
