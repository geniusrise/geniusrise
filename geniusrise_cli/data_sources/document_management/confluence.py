from atlassian import Confluence
from typing import List

from geniusrise_cli.config import CONFLUENCE_URL, CONFLUENCE_USERNAME, CONFLUENCE_ACCESS_TOKEN


class ConfluenceDataFetcher:
    def __init__(
        self, url: str = CONFLUENCE_URL, username: str = CONFLUENCE_USERNAME, password: str = CONFLUENCE_ACCESS_TOKEN
    ):
        self.confluence = Confluence(url=url, username=username, password=password)

    def fetch_spaces(self) -> List[str]:
        # Fetch all spaces
        spaces = self.confluence.get_all_spaces(start=0, limit=500, expand=None)
        space_data = []
        for space in spaces:
            # Fetch all pages from the current space
            pages = self.confluence.get_all_pages_from_space(
                space, start=0, limit=100, status=None, expand=None, content_type="page"
            )
            page_titles = [page["title"] for page in pages]
            space_data.append(
                f"Space Key: {space['key']}\n" f"Space Name: {space['name']}\n" f"Pages: {', '.join(page_titles)}"
            )
        return space_data

    def fetch_documents(self) -> List[str]:
        page_data = []
        spaces = self.confluence.get_all_spaces(start=0, limit=500, expand=None)
        for space in spaces:
            # Fetch all pages from a space
            pages = self.confluence.get_all_pages_from_space(
                space, start=0, limit=100, status=None, expand=None, content_type="page"
            )

            for page in pages:
                # Fetch all labels on the current page
                labels = self.confluence.get_page_labels(page["id"], prefix=None, start=None, limit=None)
                # Fetch page history
                history = self.confluence.history(page["id"])
                page_data.append(
                    f"Space: {space['name']}\n"
                    f"Page ID: {page['id']}\n"
                    f"Page Title: {page['title']}\n"
                    f"Labels: {', '.join(labels)}\n"
                    f"History: {history}"
                )

        return page_data
