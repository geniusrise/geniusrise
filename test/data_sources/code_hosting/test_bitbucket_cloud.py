from unittest.mock import patch

from geniusrise_cli.data_sources.code_hosting.bitbucket_cloud import BitbucketCloudDataFetcher


def test_fetch_code():
    fetcher = BitbucketCloudDataFetcher(repo_name="team-test", workspace="monoidspace", username="monoidspace-admin")
    code_files = fetcher.fetch_code()

    assert code_files[0][:10] == "File Name:"


def test_fetch_pull_requests_real():
    fetcher = BitbucketCloudDataFetcher(repo_name="team-test", workspace="monoidspace", username="monoidspace-admin")
    pull_requests = fetcher.fetch_pull_requests()

    assert pull_requests[0][:6] == "Title:"


def test_fetch_commits_real():
    fetcher = BitbucketCloudDataFetcher(repo_name="team-test", workspace="monoidspace", username="monoidspace-admin")
    commits = fetcher.fetch_commits()

    assert commits[0][:8] == "Message:"


def test_fetch_issues_real():
    fetcher = BitbucketCloudDataFetcher(repo_name="team-test", workspace="monoidspace", username="monoidspace-admin")
    issues = fetcher.fetch_issues()

    assert issues[0][:6] == "Title:"


def test_fetch_repo_details_real():
    fetcher = BitbucketCloudDataFetcher(repo_name="team-test", workspace="monoidspace", username="monoidspace-admin")
    repo_details = fetcher.fetch_repo_details()

    assert repo_details[0][:10] == "Repo Name:"


def test_fetch_releases_real():
    fetcher = BitbucketCloudDataFetcher(repo_name="team-test", workspace="monoidspace", username="monoidspace-admin")
    releases = fetcher.fetch_releases()

    assert releases == []


# Mocked


@patch("requests.get")
def test_fetch_pull_requests(mock_get):
    mock_get.return_value.json.return_value = {
        "values": [
            {"title": "PR1", "description": "PR1 description"},
            {"title": "PR2", "description": "PR2 description"},
        ]
    }

    fetcher = BitbucketCloudDataFetcher(repo_name="team-test", workspace="monoidspace", username="monoidspace-admin")
    pull_requests = fetcher.fetch_pull_requests()

    assert len(pull_requests) == 2
    assert pull_requests[0] == "Title: PR1\nDescription: PR1 description"
    assert pull_requests[1] == "Title: PR2\nDescription: PR2 description"


@patch("requests.get")
def test_fetch_commits(mock_get):
    mock_get.return_value.json.return_value = {
        "values": [
            {"message": "Commit1"},
            {"message": "Commit2"},
        ]
    }

    fetcher = BitbucketCloudDataFetcher(repo_name="team-test", workspace="monoidspace", username="monoidspace-admin")
    commits = fetcher.fetch_commits()

    assert len(commits) == 2
    assert commits[0] == "Message: Commit1"
    assert commits[1] == "Message: Commit2"


@patch("requests.get")
def test_fetch_issues(mock_get):
    mock_get.return_value.json.return_value = {
        "values": [
            {"title": "Issue1", "content": {"raw": "Issue1 description"}},
            {"title": "Issue2", "content": {"raw": "Issue2 description"}},
        ]
    }

    fetcher = BitbucketCloudDataFetcher(repo_name="team-test", workspace="monoidspace", username="monoidspace-admin")
    issues = fetcher.fetch_issues()

    assert len(issues) == 2
    assert issues[0] == "Title: Issue1\nDescription: Issue1 description"
    assert issues[1] == "Title: Issue2\nDescription: Issue2 description"


@patch("requests.get")
def test_fetch_repo_details(mock_get):
    mock_get.return_value.json.return_value = {
        "name": "Repo1",
        "description": "Repo1 description",
        "language": "Python",
        "created_on": "2023-01-01T00:00:00Z",
        "updated_on": "2023-01-02T00:00:00Z",
        "size": 123456,
        "is_private": True,
        "has_wiki": True,
        "has_issues": True,
        "watchers": {"count": 10},
        "forks": {"count": 5},
    }

    fetcher = BitbucketCloudDataFetcher(repo_name="team-test", workspace="monoidspace", username="monoidspace-admin")
    repo_details = fetcher.fetch_repo_details()

    assert len(repo_details) == 1
    assert (
        repo_details[0] == "Repo Name: Repo1\n"
        "Description: Repo1 description\n"
        "Language: Python\n"
        "Created on: 2023-01-01T00:00:00Z\n"
        "Updated on: 2023-01-02T00:00:00Z\n"
        "Size: 123456\n"
        "Is private: True\n"
        "Has wiki: True\n"
        "Has issues: True\n"
    )


@patch("requests.get")
def test_fetch_releases(mock_get):
    mock_get.return_value.json.return_value = {
        "values": [
            {"name": "Release1", "target": {"hash": "abc123"}},
            {"name": "Release2", "target": {"hash": "def456"}},
        ]
    }

    fetcher = BitbucketCloudDataFetcher(repo_name="team-test", workspace="monoidspace", username="monoidspace-admin")
    releases = fetcher.fetch_releases()

    assert len(releases) == 2
    assert releases[0] == "Name: Release1\nTarget hash: abc123"
    assert releases[1] == "Name: Release2\nTarget hash: def456"
