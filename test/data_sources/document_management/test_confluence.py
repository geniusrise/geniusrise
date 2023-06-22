import os
import json
from geniusrise_cli.data_sources.document_management.confluence import ConfluenceDataFetcher

SPACE_KEY = "TT"


def test_fetch_pages(tmpdir):
    fetcher = ConfluenceDataFetcher(SPACE_KEY, tmpdir)

    # Test fetch_pages
    fetcher.fetch_pages()
    assert os.listdir(tmpdir), "No files were created by fetch_pages"

    with open(os.path.join(tmpdir, "page_425985.json")) as f:
        data = json.load(f)
    assert data == {
        "id": "425985",
        "title": "test",
        "type": "page",
        "status": "current",
        "comments": ["<p>erokom</p>", "<p>keno</p>", "<p>chorom</p>", "<p>ektu</p>"],
        "attachments": [],
    }


def test_fetch_blogs(tmpdir):
    fetcher = ConfluenceDataFetcher(SPACE_KEY, tmpdir)

    # Test fetch_blogs
    fetcher.fetch_blogs()
    assert os.listdir(tmpdir), "No files were created by fetch_blogs"

    with open(os.path.join(tmpdir, "page_1867790.json")) as f:
        data = json.load(f)
    assert data == {
        "id": "1867790",
        "title": "blug",
        "type": "blogpost",
        "status": "current",
        "comments": ["<p>lel</p>", "<p>kyu</p>", "<p>lasol</p>"],
        "attachments": [],
    }
