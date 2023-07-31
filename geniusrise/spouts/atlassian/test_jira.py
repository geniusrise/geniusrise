# 🧠 Geniusrise
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

import json

from geniusrise.data_sources.project_management.jira import JiraDataFetcher


def test_fetch_issues(tmpdir):
    jira_fetcher = JiraDataFetcher("TT", tmpdir)  # ATLAS is a project in Apache Jira
    jira_fetcher.fetch_issues()
    # Check that the first issue's fields contain the expected values
    with open(f"{tmpdir}/issue_TT-1.json", "r") as f:
        issue = json.load(f)

    assert issue == {
        "key": "TT-1",
        "summary": "test",
        "description": "totally a rad description",
        "comments": [],
        "reporter": "Russi Chatterjee",
        "assignee": "Russi Chatterjee",
        "created": "2023-05-24T23:47:03.149+0530",
        "updated": "2023-06-18T20:30:23.614+0530",
        "linked_confluence_pages": [
            {
                "title": "Wiki Page",
                "content": '<p>test </p><p /><div class="code panel pdl conf-macro output-block" data-hasbody="true" data-macro-id="a0bb434e-8fe5-4969-a186-255a7a4f5dae" data-macro-name="code" style="border-width: 1px;"><div class="codeContent panelContent pdl">\n<pre class="syntaxhighlighter-pre" data-syntaxhighlighter-params="brush: py; gutter: false; theme: Confluence" data-theme="Confluence">test</pre>\n</div></div><p />',
            }
        ],
        "linked_issues": [
            {"id": "10001", "type": "Blocks", "key": "TT-10", "title": "zxc", "description": None},
            {"id": "10000", "type": "Blocks", "key": "TT-5", "title": "afasdcsd s", "description": None},
            {"id": "10002", "type": "Cloners", "key": "TT-5", "title": "afasdcsd s", "description": None},
            {"id": "10003", "type": "Relates", "key": "TT-10", "title": "zxc", "description": None},
        ],
        "subtasks": [
            {"id": "10011", "key": "TT-12", "summary": "child 1"},
            {"id": "10012", "key": "TT-13", "summary": "child 2"},
        ],
        "parent_issue": None,
        "work_logs": [],
    }


def test_fetch_project_details(tmpdir):
    jira_fetcher = JiraDataFetcher("TT", tmpdir)
    jira_fetcher.fetch_project_details()
    # Check that the project's fields contain the expected values
    with open(f"{tmpdir}/project_details.json", "r") as f:
        project = json.load(f)

    assert project == {
        "name": "team-test",
        "description": "",
        "lead": "Russi Chatterjee",
        "projectTypeKey": "software",
        "projectCategory": None,
        "issueTypes": ["Story", "Task", "Bug", "Epic", "Subtask"],
        "components": [],
    }


def test_fetch_users(tmpdir):
    jira_fetcher = JiraDataFetcher("TT", tmpdir)
    jira_fetcher.fetch_users()
    # Check that the first user's fields contain the expected values
    with open(f"{tmpdir}/user_712020:31810d46-bc03-4755-86ab-41e36673e28f.json", "r") as f:
        user = json.load(f)

    assert user == {
        "name": "Russi Chatterjee",
        "emailAddress": "bitbucket@monoid.space",
        "active": True,
        "timeZone": "Asia/Kolkata",
    }


# TODO
# def test_fetch_attachments(tmpdir):
#     jira_fetcher = JiraDataFetcher("team-test", tmpdir)
#     jira_fetcher.fetch_attachments()
#     # Check that the first attachment's fields contain the expected values
#     with open(f"{tmpdir}/attachment_XXX.txt", "r") as f:
#         attachment = f.read()
#     assert "XXX" in attachment


def test_get_positive(tmpdir):
    jira_fetcher = JiraDataFetcher("team-test", tmpdir)
    # Test the get method with a valid resource type
    status = jira_fetcher.get("issues")
    assert status == "issues fetched successfully."


def test_get_negative(tmpdir):
    jira_fetcher = JiraDataFetcher("team-test", tmpdir)
    # Test the get method with an invalid resource type
    status = jira_fetcher.get("invalid_resource_type")
    assert status == "Invalid resource type: invalid_resource_type"
