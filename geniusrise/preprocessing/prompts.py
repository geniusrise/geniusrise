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


def prompt_generate_prompts(x: str):
    return f"""
generate 10 prompts to generate this {x} (that i intend to use to fine tune a model to be able to generate this {x} when prompted by those prompts):

"""


def prompt_summarize_pdf(text: str) -> str:
    return f"Summarize and clean the following text extracted from a PDF document, dont output anything else except the summary: \n{text}"


def prompt_summarize_csv_table(text: str) -> str:
    return f"Construct tables from the following CSV data, dont output anything else except the tables: \n{text}"


def prompt_summarize_csv(text: str) -> str:
    return f"Summarize and clean the following text extracted from a CSV file, dont output anything else except the summary: \n{text}"


def prompt_summarize_excel_table(text: str) -> str:
    return f"Construct tables from the following Excel data, dont output anything else except the tables: \n{text}"


def prompt_summarize_excel(text: str) -> str:
    return f"Summarize and clean the following text extracted from an Excel file, dont output anything else except the summary: \n{text}"


def prompt_summarize_word(text: str) -> str:
    return f"Summarize and clean the following text extracted from a Word document, dont output anything else except the summary: \n{text}"


def prompt_summarize_json(text: str) -> str:
    return f"Summarize and clean the following text extracted from a JSON file, dont output anything else except the summary: \n{text}"


def prompt_summarize_xml(text: str) -> str:
    return f"Summarize and clean the following text extracted from an XML file, dont output anything else except the summary: \n{text}"


def prompt_summarize_ppt(text: str) -> str:
    return f"Summarize and clean the following text extracted from a presentation, dont output anything else except the summary: \n{text}"


def prompt_summarize_txt(text: str) -> str:
    return f"Summarize and clean the following text extracted from a text file, dont output anything else except the summary: \n{text}"


def prompt_summarize_html(text: str) -> str:
    return f"Summarize and clean the following text extracted from a HTML file, dont output anything else except the summary: \n{text}"


def prompt_summarize_md(text: str) -> str:
    return f"Summarize and clean the following text extracted from a Markdown file, dont output anything else except the summary: \n{text}"
