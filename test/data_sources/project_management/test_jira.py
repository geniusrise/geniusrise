from geniusrise_cli.data_sources.project_management.jira import JiraDataFetcher


def test_fetch_issues():
    issues = JiraDataFetcher().fetch_issues()
    assert isinstance(issues, list)
    assert len(issues) > 3
    assert issues[0][:10] == "Project Ke"


def test_fetch_projects():
    projects = JiraDataFetcher().fetch_projects()
    assert isinstance(projects, list)
    assert len(projects) > 0
    assert projects[0][:10] == "Project Ke"


def test_fetch_boards():
    boards = JiraDataFetcher().fetch_boards()
    assert isinstance(boards, list)
    assert len(boards) > 0
    assert boards[0][:10] == "Board Name"
