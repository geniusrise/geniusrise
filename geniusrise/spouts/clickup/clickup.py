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

import os
from typing import List

import requests

from geniusrise.config import CLICKUP_API_TOKEN


class ClickUpDataFetcher:
    """
    A class used to fetch data from ClickUp using the ClickUp API.
    """

    def __init__(self, api_token: str = CLICKUP_API_TOKEN):
        """
        Initialize ClickUpDataFetcher with the provided API token.
        """
        self.api_token = api_token
        self.base_url = "https://api.clickup.com/api/v2/"
        self.headers = {"Authorization": self.api_token}

    def fetch_workspaces(self) -> List[str]:
        """
        Fetch all workspaces and return them as a list of formatted strings.
        """
        url = f"{self.base_url}team"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(f"HTTP error occurred: {err}")
            return []
        except Exception as err:
            print(f"An error occurred: {err}")
            return []

        workspaces = response.json()
        return [
            f"Workspace Name: {workspace['name']}, Workspace ID: {workspace['id']}, Members: {', '.join([w['user']['username'] for w in workspace['members']])}"
            for workspace in workspaces["teams"]
        ]

    def fetch_spaces(self, team_id: str) -> List[str]:
        """
        Fetch all spaces for a given team and return them as a list of formatted strings.
        """
        url = f"{self.base_url}team/{team_id}/space"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(f"HTTP error occurred: {err}")
            return []
        except Exception as err:
            print(f"An error occurred: {err}")
            return []

        spaces = response.json()
        return [f"Space Name: {space['name']}, Space ID: {space['id']}" for space in spaces]

    def fetch_folders(self, space_id: str) -> List[str]:
        """
        Fetch all folders for a given space and return them as a list of formatted strings.
        """
        url = f"{self.base_url}space/{space_id}/folder"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(f"HTTP error occurred: {err}")
            return []
        except Exception as err:
            print(f"An error occurred: {err}")
            return []

        folders = response.json()
        return [f"Folder Name: {folder['name']}, Folder ID: {folder['id']}" for folder in folders]

    def fetch_lists(self, folder_id: str) -> List[str]:
        """
        Fetch all lists for a given folder and return them as a list of formatted strings.
        """
        url = f"{self.base_url}folder/{folder_id}/list"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(f"HTTP error occurred: {err}")
            return []
        except Exception as err:
            print(f"An error occurred: {err}")
            return []

        lists = response.json()
        return [f"List Name: {ll['name']}, List ID: {ll['id']}" for ll in lists]

    def fetch_tasks(self, list_id: str) -> List[str]:
        """
        Fetch all tasks for a given list and return them as a list of formatted strings.
        """
        tasks = []
        page = 0
        while True:
            url = f"{self.base_url}list/{list_id}/task?page={page}"
            try:
                response = requests.get(url, headers=self.headers)
                response.raise_for_status()
            except requests.exceptions.HTTPError as err:
                print(f"HTTP error occurred: {err}")
                break
            except Exception as err:
                print(f"An error occurred: {err}")
                break

            task_data = response.json()
            if not task_data:
                break

            tasks.extend(
                [
                    f"Task Name: {task['name']}, Task ID: {task['id']}, Task Status: {task['status']['status']}"
                    for task in task_data
                ]
            )
            page += 1

        return tasks

    def fetch_subtasks(self, task_id: str) -> List[str]:
        """
        Fetch all subtasks for a given task and return them as a list of formatted strings.
        """
        url = f"{self.base_url}task/{task_id}"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(f"HTTP error occurred: {err}")
            return []
        except Exception as err:
            print(f"An error occurred: {err}")
            return []

        subtasks = response.json().get("subtasks", [])
        return [
            f"Subtask Name: {subtask['name']}, Subtask ID: {subtask['id']}, Subtask Status: {subtask['status']['status']}"
            for subtask in subtasks
        ]

    def fetch_checklists(self, task_id: str) -> List[str]:
        """
        Fetch all checklists for a given task and return them as a list of formatted strings.
        """
        url = f"{self.base_url}task/{task_id}"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(f"HTTP error occurred: {err}")
            return []
        except Exception as err:
            print(f"An error occurred: {err}")
            return []

        checklists = response.json().get("checklists", [])
        return [f"Checklist Name: {checklist['name']}, Checklist ID: {checklist['id']}" for checklist in checklists]

    def fetch_custom_fields(self, list_id: str) -> List[str]:
        """
        Fetch all custom fields for a given list and return them as a list of formatted strings.
        """
        url = f"{self.base_url}list/{list_id}/field"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(f"HTTP error occurred: {err}")
            return []
        except Exception as err:
            print(f"An error occurred: {err}")
            return []

        custom_fields = response.json()
        return [f"Custom Field Name: {field['name']}, Custom Field ID: {field['id']}" for field in custom_fields]

    def fetch_comments(self, task_id: str) -> List[str]:
        """
        Fetch all comments for a given task and return them as a list of formatted strings.
        """
        url = f"{self.base_url}task/{task_id}/comment"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(f"HTTP error occurred: {err}")
            return []
        except Exception as err:
            print(f"An error occurred: {err}")
            return []

        comments = response.json()
        return [f"Comment ID: {comment['id']}, Comment Text: {comment['comment']['text']}" for comment in comments]

    def fetch_attachments(self, task_id: str) -> List[str]:
        """
        Fetch all attachments for a given task and return them as a list of formatted strings.
        """
        url = f"{self.base_url}task/{task_id}/attachment"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(f"HTTP error occurred: {err}")
            return []
        except Exception as err:
            print(f"An error occurred: {err}")
            return []

        attachments = response.json()
        return [
            f"Attachment ID: {attachment['id']}, Attachment Filename: {attachment['filename']}"
            for attachment in attachments
        ]

    def fetch_all_data(self, team_id: str) -> List[str]:
        """
        Fetch all data for a given team and return it as a list of formatted strings.
        Each string includes the space, folder, list, task, subtasks, checklists, comments,
        and attachments for a given task.
        """
        all_data = []
        spaces = self.fetch_spaces(team_id)
        for space in spaces:
            space_id = space.split(": ")[1].split(",")[0]
            folders = self.fetch_folders(space_id)
            for folder in folders:
                folder_id = folder.split(": ")[1].split(",")[0]
                lists = self.fetch_lists(folder_id)
                for entry in lists:
                    list_id = entry.split(": ")[1].split(",")[0]
                    tasks = self.fetch_tasks(list_id)
                    for task in tasks:
                        task_id = task.split(": ")[1].split(",")[0]
                        subtasks = ", ".join(self.fetch_subtasks(task_id))
                        checklists = ", ".join(self.fetch_checklists(task_id))
                        comments = ", ".join(self.fetch_comments(task_id))
                        attachments = ", ".join(self.fetch_attachments(task_id))
                        all_data.append(
                            f"Space: {space}{os.linesep}"
                            f"Folder: {folder}{os.linesep}"
                            f"List: {entry}{os.linesep}"
                            f"Task: {task}{os.linesep}"
                            f"Subtasks: {subtasks}{os.linesep}"
                            f"Checklists: {checklists}{os.linesep}"
                            f"Comments: {comments}{os.linesep}"
                            f"Attachments: {attachments}{os.linesep}"
                        )
        return all_data
