from geniusrise_cli.data_sources.code_hosting.github import GithubDataFetcher


def test_fetch_code():
    fetcher = GithubDataFetcher(repo_name="rmccue/test-repository")
    code_files = fetcher.fetch_code()

    assert code_files[0][:10] == "File Name:"


def test_fetch_pull_requests():
    fetcher = GithubDataFetcher(repo_name="rmccue/test-repository")
    pull_requests = fetcher.fetch_pull_requests()

    assert pull_requests[0][:10] == "Title: fix"


def test_fetch_commits():
    fetcher = GithubDataFetcher(repo_name="rmccue/test-repository")
    commits = fetcher.fetch_commits()

    assert commits[0][:10] == "Commit Mes"


def test_fetch_issues():
    fetcher = GithubDataFetcher(repo_name="rmccue/test-repository")
    issues = fetcher.fetch_issues()

    assert issues[0][:10] == "Title: fix"


def test_fetch_repo_details():
    fetcher = GithubDataFetcher(repo_name="rmccue/test-repository")
    repo_details = fetcher.fetch_repo_details()

    assert repo_details[0][:10] == "Repo Name:"


def test_fetch_releases():
    fetcher = GithubDataFetcher(repo_name="rmccue/test-repository")
    releases = fetcher.fetch_releases()

    assert releases == []
