import json
import os
from geniusrise_cli.data_sources.code_hosting.github import GithubDataFetcher


def test_fetch_pull_requests(tmpdir):
    fetcher = GithubDataFetcher("zpqrtbnk/test-repo", tmpdir)
    fetcher.fetch_pull_requests()
    # Check that the 5th pull request contains the word "fix"
    with open(f"{tmpdir}/pull_request_123.json") as f:
        pr_data = json.load(f)
    assert "Add text document with hello message" in pr_data["body"]


def test_fetch_commits(tmpdir):
    fetcher = GithubDataFetcher("zpqrtbnk/test-repo", tmpdir)
    fetcher.fetch_commits()
    # Check that the 10th commit message contains the word "update"
    with open(f"{tmpdir}/commit_21c2a100246d498732557c67302bad1dd3c3c8d0.json") as f:
        commit_data = json.load(f)
    assert "wflow" in commit_data["commit"]["message"]


def test_fetch_issues(tmpdir):
    fetcher = GithubDataFetcher("zpqrtbnk/test-repo", tmpdir)
    fetcher.fetch_issues()
    # Check that the 3rd issue title contains the word "error"
    with open(f"{tmpdir}/issue_104.json") as f:
        issue_data = json.load(f)
    assert "update readme" in issue_data["title"]


def test_fetch_releases(tmpdir):
    fetcher = GithubDataFetcher("zpqrtbnk/test-repo", tmpdir)
    fetcher.fetch_releases()
    # Check that the 1st release tag name is "v2.26.0"
    with open(f"{tmpdir}/release_v4.5.6.json") as f:
        release_data = json.load(f)
    assert release_data["tag_name"] == "v4.5.6"


def test_fetch_repo_details(tmpdir):
    fetcher = GithubDataFetcher("zpqrtbnk/test-repo", tmpdir)
    fetcher.fetch_repo_details()
    # Check that the repository name is "requests"
    with open(f"{tmpdir}/repo_details.json") as f:
        repo_data = json.load(f)
    assert repo_data["name"] == "test-repo"


def test_fetch_code(tmpdir):
    fetcher = GithubDataFetcher("zpqrtbnk/test-repo", tmpdir)
    fetcher.fetch_code()
    # Check that the repository was cloned by checking if the .git directory exists
    assert os.path.isdir(f"{tmpdir}/.git")


def test_get_positive(tmpdir):
    fetcher = GithubDataFetcher("zpqrtbnk/test-repo", tmpdir)
    # Test the get method with a valid resource type
    status = fetcher.get("issues")
    assert status == "issues fetched successfully."


def test_get_negative(tmpdir):
    fetcher = GithubDataFetcher("zpqrtbnk/test-repo", tmpdir)
    # Test the get method with an invalid resource type
    status = fetcher.get("invalid_resource_type")
    assert status == "Invalid resource type: invalid_resource_type"
