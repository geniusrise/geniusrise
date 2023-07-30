# geniusrise
# Copyright (C) 2023  geniusrise.ai
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import pytest

from geniusrise.data_sources.project_management.asana import AsanaDataFetcher


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
