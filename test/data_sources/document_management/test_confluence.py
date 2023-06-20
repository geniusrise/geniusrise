from geniusrise_cli.data_sources.document_management.confluence import ConfluenceDataFetcher


def test_fetch_spaces(mocker):
    # Mock the Confluence API
    mocker.patch.object(ConfluenceDataFetcher, "confluence", autospec=True)
    ConfluenceDataFetcher.confluence.get_all_spaces.return_value = [
        {"key": "space1", "name": "Space 1"},
        {"key": "space2", "name": "Space 2"},
    ]
    ConfluenceDataFetcher.confluence.get_all_pages_from_space.return_value = [{"title": "Page 1"}, {"title": "Page 2"}]

    fetcher = ConfluenceDataFetcher()
    result = fetcher.fetch_spaces()

    assert len(result) == 2
    assert "Space Key: space1" in result[0]
    assert "Pages: Page 1, Page 2" in result[0]
    assert "Space Key: space2" in result[1]


def test_fetch_documents(mocker):
    # Mock the Confluence API
    mocker.patch.object(ConfluenceDataFetcher, "confluence", autospec=True)
    ConfluenceDataFetcher.confluence.get_all_pages_from_space.return_value = [
        {"id": "page1", "title": "Page 1"},
        {"id": "page2", "title": "Page 2"},
    ]
    ConfluenceDataFetcher.confluence.get_page_labels.return_value = ["label1", "label2"]
    ConfluenceDataFetcher.confluence.get_group_members.return_value = [
        {"displayName": "User 1"},
        {"displayName": "User 2"},
    ]
    ConfluenceDataFetcher.confluence.history.return_value = "history"

    fetcher = ConfluenceDataFetcher()
    result = fetcher.fetch_documents()

    assert len(result) == 2
    assert "Page ID: page1" in result[0]
    assert "Labels: label1, label2" in result[0]
    assert "Users: User 1, User 2" in result[0]
    assert "History: history" in result[0]
    assert "Page ID: page2" in result[1]
