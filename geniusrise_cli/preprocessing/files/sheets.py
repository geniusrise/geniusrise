import csv
from os.path import getmtime
from time import ctime
from typing import Any, Dict

import pyexcel_ods
from openpyxl import load_workbook

from geniusrise_cli.data_sources.files.base import TextExtractor


class CSVExtractor(TextExtractor):
    """Text extractor for CSV files."""

    def extract(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Extract text from a CSV file."""
        with open(file_path, "r") as file:
            reader = csv.reader(file)
            text = " ".join([" ".join(row) for row in reader])
            return {"text": text, "created_at": ctime(getmtime(file_path))}


class ExcelExtractor(TextExtractor):
    """Text extractor for Excel files."""

    def extract(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Extract text from an Excel file."""
        wb = load_workbook(filename=file_path, read_only=True)
        text = ""
        for sheet in wb:
            for row in sheet:
                for cell in row:
                    text += str(cell.value) + " "
        return {"text": text, "created_at": ctime(getmtime(file_path))}


class ODSExtractor(TextExtractor):
    def process(self, file_path: str, **kwargs) -> Dict[str, Any]:
        data = pyexcel_ods.get_data(file_path)
        text = " ".join(str(val) for sublist in data.values() for val in sublist)
        return {"text": text, "created_at": ctime(getmtime(file_path))}
