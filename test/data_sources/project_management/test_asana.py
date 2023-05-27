import pytest
from geniusrise_cli.data_sources.project_management.asana import AsanaDataFetcher


@pytest.fixture
def fetcher():
    return AsanaDataFetcher()


def test_fetch_workspaces(fetcher):
    workspaces = fetcher.fetch_workspaces()
    assert isinstance(workspaces, list)
    for workspace in workspaces:
        assert "Workspace Name:" in workspace
        assert "Projects:" in workspace


def test_fetch_projects(fetcher):
    projects = fetcher.fetch_projects(1204690451108339)
    assert isinstance(projects, list)
    for project in projects:
        assert "Project Name:" in project
        assert "Tasks:" in project


def test_fetch_tasks(fetcher):
    tasks = fetcher.fetch_tasks(1204690393067637)
    assert isinstance(tasks, list)
    for task in tasks:
        assert "Task Name:" in task
        assert "Description:" in task
        assert "Due Date:" in task
        assert "Assignee:" in task
        assert "Subtasks:" in task
        assert "Comments:" in task
        assert "Attachments:" in task
