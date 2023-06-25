import os
from typing import List

import asana

from geniusrise_cli.config import ASANA_PERSONAL_ACCESS_TOKEN


class AsanaDataFetcher:
    def __init__(self, personal_access_token: str = ASANA_PERSONAL_ACCESS_TOKEN):
        """
        Initialize the AsanaDataFetcher with a personal access token.
        """
        self.client = asana.Client.access_token(personal_access_token)

    def fetch_workspaces(self) -> List[str]:
        """
        Fetch all workspaces and their associated projects.
        """
        workspaces = list(self.client.workspaces.find_all())
        workspace_data = []
        print(workspaces)
        for workspace in workspaces:
            try:
                projects = self.fetch_projects(workspace["gid"])
                workspace_data.append(
                    f"Workspace Name: {workspace['name']}{os.linesep}" f"Projects: {'{os.linesep}'.join(projects)}"
                )
            except asana.error.AsanaError as e:
                print(f"An error occurred while fetching projects for workspace {workspace['name']}: {e}")
        return workspace_data

    def fetch_projects(self, workspace_gid: str) -> List[str]:
        """
        Fetch all projects and their associated tasks within a workspace.
        """
        projects = list(self.client.projects.find_all({"workspace": workspace_gid}, iterator_type=None))
        project_data = []
        for project in projects:
            try:
                tasks = self.fetch_tasks(project["gid"])
                project_data.append(
                    f"Project Name: {project['name']}{os.linesep}" f"Tasks: {'{os.linesep}'.join(tasks)}"
                )
            except asana.error.AsanaError as e:
                print(f"An error occurred while fetching tasks for project {project['name']}: {e}")
        return project_data

    def fetch_tasks(self, project_gid: str) -> List[str]:
        """
        Fetch all tasks and their associated subtasks, comments, and attachments within a project.
        """
        tasks = list(self.client.tasks.find_all({"project": project_gid}, iterator_type=None))
        task_data = []
        for task in tasks:
            try:
                task = self.client.tasks.get_task(task_gid=task["gid"])
                subtasks = self.fetch_subtasks(task["gid"])
                comments = self.fetch_comments(task["gid"])
                attachments = self.fetch_attachments(task["gid"])
                task_data.append(
                    f"Task Name: {task['name']}{os.linesep}"
                    f"Description: {task.get('notes', 'No description provided')}{os.linesep}"
                    f"Due Date: {task['due_on']}{os.linesep}"
                    f"Assignee: {(task['assignee']['name'] if task['assignee'] else 'None')}{os.linesep}"
                    f"Subtasks: {'{os.linesep}'.join(subtasks)}{os.linesep}"
                    f"Comments: {'{os.linesep}'.join(comments)}{os.linesep}"
                    f"Attachments: {'{os.linesep}'.join(attachments)}"
                )
            except asana.error.AsanaError as e:
                print(f"An error occurred while fetching details for task {task['name']}: {e}")
        return task_data

    def fetch_subtasks(self, task_gid: str) -> List[str]:
        """
        Fetch all subtasks within a task.
        """
        subtasks = list(self.client.tasks.subtasks(task_gid))
        return [
            f"Subtask Name: {subtask['name']}, Description: {subtask['notes']}, Due Date: {subtask['due_on']}"
            for subtask in subtasks
        ]

    def fetch_comments(self, task_gid: str) -> List[str]:
        """
        Fetch all comments within a task.
        """
        comments = list(self.client.tasks.stories(task_gid))
        return [f"Comment: {comment['text']}, Created At: {comment['created_at']}" for comment in comments]

    def fetch_attachments(self, task_gid: str) -> List[str]:
        """
        Fetch all attachments within a task.
        """
        attachments = list(self.client.attachments.find_by_task(task_gid))
        return [
            f"Attachment: {attachment['name']}, Created At: {attachment['created_at']}" for attachment in attachments
        ]
