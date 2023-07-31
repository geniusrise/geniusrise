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
import os

from geniusrise.data_sources.document_management.confluence import ConfluenceDataFetcher

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
