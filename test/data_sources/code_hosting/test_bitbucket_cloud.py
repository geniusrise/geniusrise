import os
import json
from geniusrise_cli.data_sources.code_hosting.bitbucket_cloud import BitbucketDataFetcher


def test_fetch_code(tmpdir):
    fetcher = BitbucketDataFetcher("fargo3d", "public", "monoidspace-admin", tmpdir)
    fetcher.fetch_code()
    assert os.path.exists(tmpdir)  # Check that the repository was cloned

    with open(os.path.join(tmpdir, "README.md")) as f:
        pr_data = f.read()
        assert "FARGO3D" in pr_data


def test_fetch_pull_requests(tmpdir):
    fetcher = BitbucketDataFetcher("fargo3d", "public", "monoidspace-admin", tmpdir)
    fetcher.fetch_pull_requests()

    # Check that the pull request files exist
    for i in range(1, 6):  # Assume there are 5 pull requests
        assert os.path.exists(os.path.join(tmpdir, f"pull_request_{i}.json"))

    # Check that the pull request data is correct
    with open(os.path.join(tmpdir, "pull_request_5.json")) as f:
        data = json.load(f)
        assert "Feature multifluid merged" in data["description"]


def test_fetch_commits(tmpdir):
    fetcher = BitbucketDataFetcher("fargo3d", "public", "monoidspace-admin", tmpdir)
    fetcher.fetch_commits()

    with open(os.path.join(tmpdir, "commit_7835cac96444a4bd68f1bf0567e35e7d986bd99c.json")) as f:
        data = json.load(f)
        assert "Merged in hotfix/radialmesh" in data["message"]


# def test_fetch_issues(tmpdir):
#     fetcher = BitbucketDataFetcher("fargo3d", "public", "monoidspace-admin", tmpdir)
#     fetcher.fetch_issues()


def test_fetch_releases(tmpdir):
    fetcher = BitbucketDataFetcher("fargo3d", "public", "monoidspace-admin", tmpdir)
    fetcher.fetch_releases()

    with open(os.path.join(tmpdir, "release_1.3.json")) as f:
        data = json.load(f)
        assert "fargo3d 1.3" in data["target"]["message"]


def test_fetch_repo_details(tmpdir):
    fetcher = BitbucketDataFetcher("fargo3d", "public", "monoidspace-admin", tmpdir)
    fetcher.fetch_repo_details()

    with open(os.path.join(tmpdir, "repo_details.json")) as f:
        data = json.load(f)
        assert "public" in data["name"]


def test_get(tmpdir):
    fetcher = BitbucketDataFetcher("fargo3d", "public", "monoidspace-admin", tmpdir)
    assert fetcher.get("code").lower() == "Code fetched successfully.".lower()
    assert fetcher.get("pull_requests").lower() == "Pull_requests fetched successfully.".lower()
    assert fetcher.get("commits").lower() == "Commits fetched successfully.".lower()
    # assert fetcher.get("issues").lower() == "Issues fetched successfully.".lower()
    assert fetcher.get("releases").lower() == "Releases fetched successfully.".lower()
    assert fetcher.get("repo_details").lower() == "Repo_details fetched successfully.".lower()
    assert fetcher.get("invalid").lower() == "Invalid resource type: invalid".lower()
