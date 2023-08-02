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

from os.path import getmtime
from time import ctime
from typing import Any, Dict

from PyPDF2 import PdfFileReader

from geniusrise.spouts.files.base import TextExtractor

# from pyth.plugins.plaintext.writer import PlaintextWriter
# from pyth.plugins.rtf15.reader import Rtf15Reader


class PDFExtractor(TextExtractor):
    """Text extractor for PDF files."""

    def extract(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Extract text and metadata from a PDF file."""
        with open(file_path, "rb") as file:
            pdf = PdfFileReader(file)
            text = ""
            for page in range(pdf.getNumPages()):
                text += pdf.getPage(page).extractText()
            return {"text": text, "metadata": pdf.getDocumentInfo(), "created_at": ctime(getmtime(file_path))}


class TXTExtractor(TextExtractor):
    """Text extractor for text files."""

    def extract(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Extract text from a text file."""
        with open(file_path, "r") as file:
            text = file.read()
        return {"text": text, "created_at": ctime(getmtime(file_path))}


# class RTFExtractor(TextExtractor):
#     """Text extractor for RTF files."""

#     def extract(self, file_path: str, **kwargs) -> Dict[str, Any]:
#         """Extract text from an RTF file."""
#         doc = Rtf15Reader.read(open(file_path, "rb"))
#         text = PlaintextWriter.write(doc).getvalue()
#         return {"text": text, "created_at": ctime(getmtime(file_path))}
