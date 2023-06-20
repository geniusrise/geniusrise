from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2.credentials import Credentials
import io
import PyPDF2
from docx import Document
import pandas as pd
from typing import Optional


class GoogleDriveDataFetcher:
    def __init__(self, credentials: Credentials):
        self.drive_service = build("drive", "v3", credentials=credentials)

    def fetch_google_docs(self):
        return self._fetch_files_by_mime_type("application/vnd.google-apps.document", "text/plain")

    def fetch_google_sheets(self):
        return self._fetch_files_by_mime_type("application/vnd.google-apps.spreadsheet", "text/csv")

    def fetch_google_presentations(self):
        return self._fetch_files_by_mime_type("application/vnd.google-apps.presentation", "text/plain")

    def fetch_pdf_files(self):
        return self._fetch_files_by_mime_type("application/pdf")

    def fetch_word_files(self):
        return self._fetch_files_by_mime_type("application/vnd.openxmlformats-officedocument.wordprocessingml.document")

    def fetch_excel_files(self):
        return self._fetch_files_by_mime_type("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    def _fetch_files_by_mime_type(self, mime_type: str, export_mime_type: Optional[str] = None):
        try:
            results = (
                self.drive_service.files()
                .list(
                    q=f"mimeType='{mime_type}'",
                    fields="nextPageToken, files(id, name, mimeType, createdTime, modifiedTime, owners, lastModifyingUser, sharingUser, permissions)",
                )
                .execute()
            )
            items = results.get("files", [])
            for item in items:
                if export_mime_type:
                    content = self._export_file_content(item["id"], export_mime_type)
                else:
                    content = self._download_and_read_file_content(item["id"], mime_type)
                item["content"] = content
            return items
        except HttpError as error:
            print(f"An error occurred: {error}")
            return None

    def _export_file_content(self, file_id: str, mime_type: str):
        request = self.drive_service.files().export_media(fileId=file_id, mimeType=mime_type)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        return fh.getvalue().decode()

    def _download_and_read_file_content(self, file_id: str, mime_type: str):
        request = self.drive_service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()

        if mime_type == "application/pdf":
            reader = PyPDF2.PdfFileReader(fh)
            content = " ".join(page.extract_text() for page in reader.pages)
        elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = Document(fh)
            content = " ".join(paragraph.text for paragraph in doc.paragraphs)
        elif mime_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
            df = pd.read_excel(fh)
            content = df.to_string()
        else:
            content = None
        return content
