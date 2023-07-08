from os.path import getmtime
from time import ctime
from typing import Any, Dict

from PyPDF2 import PdfFileReader

from geniusrise.preprocessing.files.base import TextExtractor

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
