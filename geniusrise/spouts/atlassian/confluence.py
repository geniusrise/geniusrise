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

import base64
import json
import logging
import os
from io import BytesIO
from typing import Any, Dict, List

import pandas as pd
import PyPDF2
import requests
from docx import Document

from geniusrise.config import JIRA_ACCESS_TOKEN, JIRA_BASE_URL, JIRA_USERNAME


class ConfluenceDataFetcher:
    def __init__(self, space_key: str, output_folder: str):
        """
        Initialize ConfluenceDataFetcher with space key and output folder.

        :param space_key: Key of the Confluence space.
        :param output_folder: Folder to save the fetched data.
        """
        self.base_url = f"{JIRA_BASE_URL}"
        self.space_key = space_key
        self.output_folder = output_folder
        credentials = base64.b64encode(f"{JIRA_USERNAME}:{JIRA_ACCESS_TOKEN}".encode()).decode()
        self.headers = {
            "Authorization": f"Basic {credentials}",
            "Accept": "application/json",
        }

        self.log = logging.getLogger(__name__)

    def fetch_pages(self):
        return self.__fetch_content("page")

    def fetch_blogs(self):
        return self.__fetch_content("blogpost")

    def __fetch_content(self, content_type: str) -> None:
        """
        Fetch all content of a specific type in the space and save each to a separate file.

        :param content_type: Type of the content to fetch (e.g., 'page', 'blogpost').
        :raises: requests.exceptions.HTTPError if a request fails.
        """
        try:
            start_at = 0
            while True:
                response = requests.get(
                    f"{self.base_url}/wiki/rest/api/content?spaceKey={self.space_key}&start={start_at}&type={content_type}",
                    headers=self.headers,
                )
                print(response.text)
                response.raise_for_status()
                pages = response.json()["results"]
                if not pages:
                    break
                for page in pages:
                    # Fetch comments, attachments, linked Jira issues and link summaries
                    comments = self.__fetch_comments(page["id"])
                    attachments = self.__fetch_attachments(page["id"])

                    page_dict = {
                        "id": page["id"],
                        "title": page["title"],
                        "type": page["type"],
                        "status": page["status"],
                        "comments": comments,
                        "attachments": attachments,
                    }
                    self.save_to_file(page_dict, f"page_{page['id']}.json")
                start_at += len(pages)
            self.log.info("Content fetched successfully.")
        except Exception as e:
            self.log.error(f"Error fetching content: {e}")
            raise

    def __fetch_comments(self, page_id: str) -> List[str]:
        """
        Fetch all comments for a specific page.

        :param page_id: ID of the page.
        :return: List of comments.
        :raises: requests.exceptions.HTTPError if a request fails.
        """
        try:
            response = requests.get(
                f"{self.base_url}/wiki/rest/api/content/{page_id}/child/comment?expand=body.view&depth=all",
                headers=self.headers,
            )
            response.raise_for_status()
            comments = response.json()["results"]
            return [comment["body"]["view"]["value"] for comment in comments]
        except Exception as e:
            self.log.error(f"Error fetching comments: {e}")
            return []

    def __fetch_attachments(self, page_id: str) -> List[Dict[str, str]]:
        """
        Fetch attachments for a specific page.

        :param page_id: ID of the page.
        :return: List of attachments.
        :raises: requests.exceptions.HTTPError if a request fails.
        """
        try:
            response = requests.get(
                f"{self.base_url}/wiki/rest/api/content/{page_id}/child/attachment", headers=self.headers
            )
            response.raise_for_status()
            attachments = response.json()["results"]
            parsed_attachments = []
            for attachment in attachments:
                download_url = (
                    f"{self.base_url}/wiki/rest/api/content/{page_id}/child/attachment/{attachment['id']}/download"
                )
                attachment_response = requests.get(download_url, headers=self.headers)
                filename = attachment["title"]
                content = self.__parse_attachment(attachment_response.content, filename)
                parsed_attachments.append({"title": filename, "content": content})
            return parsed_attachments
        except Exception as e:
            self.log.error(f"Error fetching attachments: {e}")
            return []

    def __parse_attachment(self, content: bytes, filename: str) -> str:
        """
        Parse an attachment into text.

        :param content: Content of the attachment.
        :param filename: Name of the attachment file.
        :return: Text content of the attachment.
        """
        if filename.endswith(".docx"):
            return self.__parse_word_document(content)
        elif filename.endswith(".xlsx") or filename.endswith(".xls"):
            return self.__parse_excel_spreadsheet(content)
        elif filename.endswith(".pdf"):
            return self.__parse_pdf(content)
        else:
            return content.decode()

    def __parse_word_document(self, content: bytes) -> str:
        """
        Parse a Word document into text.

        :param content: Content of the Word document.
        :return: Text content of the Word document.
        """
        document = Document(BytesIO(content))
        return "\n".join([paragraph.text for paragraph in document.paragraphs])

    def __parse_excel_spreadsheet(self, content: bytes) -> str:
        """
        Parse an Excel spreadsheet into text.

        :param content: Content of the Excel spreadsheet.
        :return: Text content of the Excel spreadsheet.
        """
        df = pd.read_excel(BytesIO(content))
        return df.to_string()

    def __parse_pdf(self, content: bytes) -> str:
        """
        Parse a PDF into text.

        :param content: Content of the PDF.
        :return: Text content of the PDF.
        """
        reader = PyPDF2.PdfFileReader(BytesIO(content))
        return "\n".join([reader.getPage(i).extractText() for i in range(reader.getNumPages())])

    def save_to_file(self, data: Any, filename: str) -> None:
        """
        Save data to a file in the output folder.

        :param data: Data to save.
        :param filename: Name of the file to save the data.
        """
        try:
            local_dir = os.path.join(self.output_folder, filename)
            with open(local_dir, "w") as f:
                json.dump(data, f)
            self.log.info(f"Data saved to {filename}.")
        except Exception as e:
            self.log.error(f"Error saving data to file: {e}")
            raise
