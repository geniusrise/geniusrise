from unittest.mock import MagicMock
from github import Github
from geniusrise_cli.data_sources.code_hosting.github import GithubDataFetcher


def test_fetch_code():
    # Mock the Github instance and repo
    github_instance = MagicMock(spec=Github)
    repo = MagicMock()
    github_instance.get_repo.return_value = repo

    # Mock the repo's get_contents method
    file_content = MagicMock()
    file_content.decoded_content = b"test.py"
    repo.get_contents.return_value = [file_content]

    fetcher = GithubDataFetcher(repo_name="rmccue/test-repository")
    fetcher.github = github_instance
    code_files = fetcher.fetch_code()

    assert code_files[0][:5] == "<?php"


def test_fetch_pull_requests():
    # Mock the Github instance and repo
    github_instance = MagicMock(spec=Github)
    repo = MagicMock()
    github_instance.get_repo.return_value = repo

    # Mock the repo's get_pulls method
    pull_request = MagicMock()
    pull_request.title = "Test Pull Request"
    pull_request.body = "Test Pull Request Body"
    pull_request.get_commits.return_value = []
    pull_request.get_issue_comments.return_value = []
    repo.get_pulls.return_value = [pull_request]

    fetcher = GithubDataFetcher(repo_name="rmccue/test-repository")
    fetcher.github = github_instance
    pull_requests = fetcher.fetch_pull_requests()

    assert pull_requests[0][:10] == "fixing min"


def test_fetch_commits():
    # Mock the Github instance and repo
    github_instance = MagicMock(spec=Github)
    repo = MagicMock()
    github_instance.get_repo.return_value = repo

    # Mock the repo's get_commits method
    commit = MagicMock()
    commit.commit.message = "Test Commit"
    commit.files = []
    repo.get_commits.return_value = [commit]

    fetcher = GithubDataFetcher(repo_name="rmccue/test-repository")
    fetcher.github = github_instance
    commits = fetcher.fetch_commits()

    assert commits[0][:10] == "Adding OPM"


def test_fetch_issues():
    # Mock the Github instance and repo
    github_instance = MagicMock(spec=Github)
    repo = MagicMock()
    github_instance.get_repo.return_value = repo

    # Mock the repo's get_issues method
    issue = MagicMock()
    issue.title = "Test Issue"
    issue.body = "Test Issue Body"
    issue.pull_request = None
    issue.get_comments.return_value = []
    repo.get_issues.return_value = [issue]

    fetcher = GithubDataFetcher(repo_name="rmccue/test-repository")
    fetcher.github = github_instance
    issues = fetcher.fetch_issues()

    assert issues[0][:10] == "fixing min"
