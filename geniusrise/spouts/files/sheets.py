# geniusrise
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

import csv
from os.path import getmtime
from time import ctime
from typing import Any, Dict

import pyexcel_ods
from openpyxl import load_workbook

from geniusrise.spouts.files.base import TextExtractor


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
