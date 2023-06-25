import os
import json
from geniusrise_cli.data_sources.code_hosting.gitlab import GitlabDataFetcher


def test_fetch_code(tmpdir):
    fetcher = GitlabDataFetcher("gitlab-org/gitlab-test", tmpdir)
    fetcher.fetch_code()
    assert os.path.exists(f"{tmpdir}/foo")  # Check that the repository was cloned


def test_fetch_merge_requests(tmpdir):
    fetcher = GitlabDataFetcher("gitlab-org/gitlab-test", tmpdir)
    fetcher.fetch_merge_requests()

    # Check that the merge request data is correct
    with open(os.path.join(tmpdir, "merge_request_204423908.json")) as f:
        data = json.load(f)
        assert "Signed-off-by" in data["description"]


def test_fetch_commits(tmpdir):
    fetcher = GitlabDataFetcher("gitlab-org/gitlab-test", tmpdir)
    fetcher.fetch_commits()

    # Check that the commit files exist
    assert os.path.exists(os.path.join(tmpdir, "commit_c1c67abbaf91f624347bb3ae96eabe3a1b742478.json"))

    with open(os.path.join(tmpdir, "commit_c1c67abbaf91f624347bb3ae96eabe3a1b742478.json")) as f:
        data = json.load(f)
        assert "Add file with a _flattable_" in data["message"]


def test_fetch_issues(tmpdir):
    fetcher = GitlabDataFetcher("gitlab-org/editor-extensions/gitlab-jetbrains-plugin", tmpdir)
    fetcher.fetch_issues()

    with open(os.path.join(tmpdir, "issue_129039368.json")) as f:
        data = json.load(f)
        assert "Code Suggestions" in data["title"]


def test_fetch_releases(tmpdir):
    fetcher = GitlabDataFetcher("gitlab-org/gitlab-test", tmpdir)
    fetcher.fetch_releases()

    with open(os.path.join(tmpdir, "release_v9.9.json")) as f:
        data = json.load(f)
        assert "Test" in data["description"]


def test_fetch_repo_details(tmpdir):
    fetcher = GitlabDataFetcher("gitlab-org/gitlab-test", tmpdir)
    fetcher.fetch_repo_details()
    # Check that the repo details file exists
    assert os.path.exists(os.path.join(tmpdir, "repo_details.json"))


def test_get(tmpdir):
    fetcher = GitlabDataFetcher("gitlab-org/gitlab-test", tmpdir)
    assert fetcher.get("code").lower() == "Code fetched successfully.".lower()
    assert fetcher.get("merge_requests").lower() == "Merge_requests fetched successfully.".lower()
    assert fetcher.get("commits").lower() == "Commits fetched successfully.".lower()
    assert fetcher.get("issues").lower() == "Issues fetched successfully.".lower()
    assert fetcher.get("releases").lower() == "Releases fetched successfully.".lower()
    assert fetcher.get("repo_details").lower() == "repo_details fetched successfully.".lower()
    assert fetcher.get("invalid").lower() == "Invalid resource type: invalid".lower()
