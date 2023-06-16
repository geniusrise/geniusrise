import json
import tempfile
import os
from geniusrise_cli.data_sources.code_hosting.github import GithubDataFetcher

# Initialize GithubResourceFetcher with the public repository "requests/requests"
output_folder = tempfile.mkdtemp()
fetcher = GithubDataFetcher("zpqrtbnk/test-repo", output_folder)


def test_fetch_pull_requests():
    fetcher.fetch_pull_requests()
    # Check that the 5th pull request contains the word "fix"
    with open(f"{output_folder}/pull_request_123.json") as f:
        pr_data = json.load(f)
    assert "Add text document with hello message" in pr_data["body"]


def test_fetch_commits():
    fetcher.fetch_commits()
    # Check that the 10th commit message contains the word "update"
    with open(f"{output_folder}/commit_21c2a100246d498732557c67302bad1dd3c3c8d0.json") as f:
        commit_data = json.load(f)
    assert "wflow" in commit_data["commit"]["message"]


def test_fetch_issues():
    fetcher.fetch_issues()
    # Check that the 3rd issue title contains the word "error"
    with open(f"{output_folder}/issue_104.json") as f:
        issue_data = json.load(f)
    assert "update readme" in issue_data["title"]


def test_fetch_releases():
    fetcher.fetch_releases()
    # Check that the 1st release tag name is "v2.26.0"
    with open(f"{output_folder}/release_v4.5.6.json") as f:
        release_data = json.load(f)
    assert release_data["tag_name"] == "v4.5.6"


def test_fetch_repo_details():
    fetcher.fetch_repo_details()
    # Check that the repository name is "requests"
    with open(f"{output_folder}/repo_details.json") as f:
        repo_data = json.load(f)
    assert repo_data["name"] == "test-repo"


def test_fetch_code():
    fetcher.fetch_code()
    # Check that the repository was cloned by checking if the .git directory exists
    assert os.path.isdir(f"{output_folder}/.git")


def test_get_positive():
    # Test the get method with a valid resource type
    status = fetcher.get("issues")
    assert status == "issues fetched successfully."


def test_get_negative():
    # Test the get method with an invalid resource type
    status = fetcher.get("invalid_resource_type")
    assert status == "Invalid resource type: invalid_resource_type"
