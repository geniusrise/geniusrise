from atlassian import Jira
from typing import List
import os

from geniusrise_cli.config import JIRA_URL, JIRA_USERNAME, JIRA_ACCESS_TOKEN


class JiraDataFetcher:
    def __init__(self, url: str = JIRA_URL, username: str = JIRA_USERNAME, password: str = JIRA_ACCESS_TOKEN):
        self.jira = Jira(url=url, username=username, password=password)

    def fetch_issues(self) -> List[str]:
        projects = self.jira.get_all_projects()

        all_issue_data = []
        for project in projects:
            issues = self.jira.jql(f"project={project['key']}")
            for issue in issues["issues"]:
                changelog = self.jira.get_issue_changelog(issue["id"])
                status_changes = [
                    change for change in changelog["histories"] if "status" in change["items"][0]["field"]
                ]
                status_change_data = [
                    f"From: {change['items'][0]['fromString']}, To: {change['items'][0]['toString']}, Date: {change['created']}"
                    for change in status_changes
                ]
                story_points = issue["fields"].get("customfield_10004")
                issue_data = (
                    f"Project Key: {project['key']}{os.linesep}"
                    f"Issue Key: {issue['key']}{os.linesep}"
                    f"Summary: {issue['fields']['summary']}{os.linesep}"
                    f"Story Points: {story_points}{os.linesep}"
                    f"Status Changes: {', '.join(status_change_data)}"
                )
                all_issue_data.append(issue_data)
        return all_issue_data

    def fetch_projects(self) -> List[str]:
        projects = self.jira.projects()
        project_data = []
        for project in projects:
            print(project)
            project_data.append(
                f"Project Key: {project['key']}{os.linesep}"
                f"Project Name: {project['name']}{os.linesep}"
                f"Project Components: {', '.join(self.__fetch_project_components(project['key']))}{os.linesep}"
                f"Project Versions: {', '.join(self.__fetch_project_versions(project['key']))}{os.linesep}"
                f"Assignable Users: {', '.join(self.__fetch_assignable_users_for_project(project['key']))}"
            )
        return project_data

    def __fetch_project_components(self, key: str) -> List[str]:
        components = self.jira.get_project_components(key)
        return [component["name"] for component in components]

    def __fetch_project_versions(self, key: str) -> List[str]:
        versions = self.jira.get_project_versions(key)
        return [version["name"] for version in versions]

    def __fetch_assignable_users_for_project(self, project_key: str) -> List[str]:
        users = self.jira.get_all_assignable_users_for_project(project_key)
        return [user["displayName"] for user in users]

    def fetch_boards(self):
        all_details = []

        # Fetch all boards
        boards = self.jira.get_all_agile_boards()
        for board in boards["values"]:
            board_name = board["name"]
            board_owner = board["location"]["projectName"]

            # Fetch all sprints for the current board
            sprints = self.jira.get_all_sprint(board["id"])
            for sprint in sprints["values"]:
                sprint_name = sprint["name"]
                sprint_start_date = sprint["startDate"]
                sprint_end_date = sprint["endDate"]
                sprint_goal = sprint["goal"]

                # Fetch all issues for the current sprint
                issues = self.jira.get_sprint_issues(sprint["id"], start=0, limit=1000)
                issue_data = []
                for issue in issues["issues"]:
                    issue_key = issue["key"]
                    issue_summary = issue["fields"]["summary"]
                    issue_story_points = issue["fields"]["customfield_10004"]
                    issue_data.append(
                        f"Issue Key: {issue_key}, Summary: {issue_summary}, Story Points: {issue_story_points}"
                    )

                sprint_details = (
                    f"Board Name: {board_name}{os.linesep}"
                    f"Board Owner: {board_owner}{os.linesep}"
                    f"Sprint Name: {sprint_name}{os.linesep}"
                    f"Sprint Start Date: {sprint_start_date}{os.linesep}"
                    f"Sprint End Date: {sprint_end_date}{os.linesep}"
                    f"Sprint Goal: {sprint_goal}{os.linesep}"
                    f"Issues: {', '.join(issue_data)}"
                )
                all_details.append(sprint_details)

        return all_details
