from geniusrise_cli.data_sources.code_hosting.gitlab import GitlabDataFetcher


def test_fetch_code():
    fetcher = GitlabDataFetcher(repo_id="14136772")
    code_files = fetcher.fetch_code()

    assert code_files[0][:10] == "File Name:"


def test_fetch_merge_requests():
    fetcher = GitlabDataFetcher(repo_id="14136772")
    merge_requests = fetcher.fetch_merge_requests()

    assert merge_requests[0][:10] == "Title: Add"


def test_fetch_commits():
    fetcher = GitlabDataFetcher(repo_id="14136772")
    commits = fetcher.fetch_commits()

    assert commits[0][:10] == "Commit Mes"


def test_fetch_issues():
    fetcher = GitlabDataFetcher(repo_id="14136772")
    issues = fetcher.fetch_issues()

    assert issues[0][:10] == "Title: lel"


def test_fetch_repo_details():
    fetcher = GitlabDataFetcher(repo_id="14136772")
    repo_details = fetcher.fetch_repo_details()

    assert repo_details[0][:10] == "Repo Name:"


def test_fetch_releases():
    fetcher = GitlabDataFetcher(repo_id="14136772")
    releases = fetcher.fetch_releases()

    assert releases[0][:10] == "Release Na"
