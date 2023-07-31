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

import base64
import json
import logging
import os
import re
from io import BytesIO
from typing import Any, List

import pandas as pd
import PyPDF2
import requests
from docx import Document

from geniusrise.config import JIRA_ACCESS_TOKEN, JIRA_BASE_URL, JIRA_USERNAME


class JiraDataFetcher:
    def __init__(self, project_key: str, output_folder: str):
        """
        Initialize JiraDataFetcher with project key and output folder.

        :param project_key: Key of the Jira project.
        :param output_folder: Folder to save the fetched data.
        """
        self.base_url = JIRA_BASE_URL
        self.project_key = project_key
        self.output_folder = output_folder

        credentials = base64.b64encode(f"{JIRA_USERNAME}:{JIRA_ACCESS_TOKEN}".encode("utf-8")).decode("utf-8")
        self.headers = {
            "Authorization": f"Basic {credentials}",
            "Accept": "application/json",
        }

        self.log = logging.getLogger(__name__)

    def fetch_issues(self):
        """
        Fetch all issues in the project and save each to a separate file.
        """
        try:
            start_at = 0
            while True:
                response = requests.get(
                    f"{self.base_url}/rest/api/3/search?jql=project={self.project_key}&fields=*all&startAt={start_at}",
                    headers=self.headers,
                )
                response.raise_for_status()
                issues = response.json()["issues"]
                if not issues:
                    break
                for issue in issues:
                    # Fetch linked Confluence documents
                    linked_pages = self.__fetch_linked_confluence_pages(issue["key"])

                    # Fetch linked issues, subtasks, and parent issue
                    linked_issues = self.__fetch_linked_issues(issue["key"])
                    subtasks = self.__fetch_subtasks(issue["key"])
                    parent_issue = self.__fetch_parent_issue(issue["key"])
                    work_logs = self.__fetch_work_logs(issue["key"])

                    issue_dict = {
                        "key": issue["key"],
                        "summary": issue["fields"]["summary"],
                        "description": issue["fields"]["description"]["content"][0]["content"][0]["text"]
                        if issue["fields"]["description"]
                        else None,
                        "comments": [
                            comment["body"]["content"][0]["content"][0]["text"]
                            for comment in issue["fields"]["comment"]["comments"]
                        ],
                        "reporter": issue["fields"]["reporter"]["displayName"],
                        "assignee": issue["fields"]["assignee"]["displayName"] if issue["fields"]["assignee"] else None,
                        "created": issue["fields"]["created"],
                        "updated": issue["fields"]["updated"],
                        "linked_confluence_pages": linked_pages,
                        "linked_issues": linked_issues,
                        "subtasks": subtasks,
                        "parent_issue": parent_issue,
                        "work_logs": work_logs,
                    }

                    self.save_to_file(issue_dict, f"issue_{issue['key']}.json")
                start_at += len(issues)
            self.log.info("Issues fetched successfully.")
        except Exception as e:
            self.log.error(f"Error fetching issues: {e}")
            raise

    def __fetch_linked_issues(self, issue_key: str):
        """
        Fetch all linked issues for a specific issue and save to a separate file.
        """
        try:
            response = requests.get(f"{self.base_url}/rest/api/3/issue/{issue_key}", headers=self.headers)
            response.raise_for_status()
            issue = response.json()
            linked_issues = issue["fields"]["issuelinks"]
            linked_issues_list = []
            for linked_issue in linked_issues:
                linked_issue_key = linked_issue.get("inwardIssue", {}).get("key") or linked_issue.get(
                    "outwardIssue", {}
                ).get("key")
                if linked_issue_key:
                    linked_issue_response = requests.get(
                        f"{self.base_url}/rest/api/3/issue/{linked_issue_key}", headers=self.headers
                    )
                    linked_issue_response.raise_for_status()
                    linked_issue_details = linked_issue_response.json()
                    linked_issue_dict = {
                        "id": linked_issue["id"],
                        "type": linked_issue["type"]["name"],
                        "key": linked_issue_key,
                        "title": linked_issue_details["fields"]["summary"],
                        "description": linked_issue_details["fields"]["description"]["content"][0]["content"][0]["text"]
                        if linked_issue_details["fields"]["description"]
                        else None,
                    }
                    linked_issues_list.append(linked_issue_dict)
            return linked_issues_list
        except Exception as e:
            self.log.error(f"Error fetching linked issues: {e}")
            return []

    def __fetch_subtasks(self, issue_key: str):
        """
        Fetch all subtasks for a specific issue.

        :param issue_key: Key of the issue.
        :return: List of subtasks.
        """
        try:
            response = requests.get(f"{self.base_url}/rest/api/3/issue/{issue_key}", headers=self.headers)
            response.raise_for_status()
            issue = response.json()
            subtasks = issue["fields"]["subtasks"]
            subtasks_list = []
            for subtask in subtasks:
                subtask_dict = {
                    "id": subtask["id"],
                    "key": subtask["key"],
                    "summary": subtask["fields"]["summary"],
                }
                subtasks_list.append(subtask_dict)
            return subtasks_list
        except Exception as e:
            self.log.error(f"Error fetching subtasks: {e}")
            return []

    def __fetch_parent_issue(self, issue_key: str):
        """
        Fetch the parent issue for a specific issue.

        :param issue_key: Key of the issue.
        :return: Parent issue.
        """
        try:
            response = requests.get(f"{self.base_url}/rest/api/3/issue/{issue_key}", headers=self.headers)
            response.raise_for_status()
            issue = response.json()
            parent_issue = issue["fields"].get("parent")
            if parent_issue:
                parent_issue_dict = {
                    "id": parent_issue["id"],
                    "key": parent_issue["key"],
                    "summary": parent_issue["fields"]["summary"],
                }
                return parent_issue_dict
            return None
        except Exception as e:
            self.log.error(f"Error fetching parent issue: {e}")
            return None

    def __fetch_linked_confluence_pages(self, issue_key: str):
        """
        Fetch linked Confluence pages for a specific issue.

        :param issue_key: Key of the issue.
        :return: List of linked Confluence pages.
        """
        try:
            response = requests.get(f"{self.base_url}/rest/api/3/issue/{issue_key}/remotelink", headers=self.headers)
            response.raise_for_status()
            remote_links = response.json()
            confluence_pages = []
            for link in remote_links:
                if "application" in link and link["application"]["type"] == "com.atlassian.confluence":
                    url = link["object"]["url"]
                    match = re.search(r"pageId=(\d+)", url)
                    if match:
                        page_id = match.group(1)
                        page_response = requests.get(
                            f"{self.base_url}/wiki/rest/api/content/{page_id}?expand=body.view",
                            headers=self.headers,
                        )
                        page_response.raise_for_status()
                        page_content = page_response.json()["body"]["view"]["value"]
                        confluence_pages.append({"title": link["object"]["title"], "content": page_content})
            return confluence_pages
        except Exception as e:
            self.log.error(f"Error fetching linked Confluence pages: {e}")
            return []

    def fetch_project_details(self) -> None:
        """
        Fetch project details and save to a file.
        """
        try:
            response = requests.get(f"{self.base_url}/rest/api/3/project/{self.project_key}", headers=self.headers)
            response.raise_for_status()
            project = response.json()

            # Format the raw response
            project_dict = {
                "name": project.get("name"),
                "description": project.get("description"),
                "lead": project.get("lead", {}).get("displayName"),
                "projectTypeKey": project.get("projectTypeKey"),
                "projectCategory": project.get("projectCategory", {}).get("name"),
                "issueTypes": [issue_type.get("name") for issue_type in project.get("issueTypes", [])],
                "components": [component.get("name") for component in project.get("components", [])],
            }

            self.save_to_file(project_dict, "project_details.json")
            self.log.info("Project details fetched successfully.")
        except Exception as e:
            self.log.error(f"Error fetching project details: {e}")
            raise

    def fetch_users(self) -> None:
        """
        Fetch all users that can be assigned to issues in the project and save to a file.
        """
        try:
            response = requests.get(
                f"{self.base_url}/rest/api/3/user/assignable/search?project={self.project_key}", headers=self.headers
            )
            response.raise_for_status()
            users = response.json()
            for user in users:
                user_dict = {
                    "name": user["displayName"],
                    "emailAddress": user["emailAddress"],
                    "active": user["active"],
                    "timeZone": user["timeZone"],
                }
                self.save_to_file(user_dict, f"user_{user['accountId']}.json")
            self.log.info("Assignable users fetched successfully.")
        except Exception as e:
            self.log.error(f"Error fetching assignable users: {e}")
            raise

    def __fetch_work_logs(self, issue_key: str) -> List[dict]:
        """
        Fetch all work logs for a specific issue and save to a separate file.

        :param issue_key: The key of the issue for which to fetch work logs.
        """
        try:
            response = requests.get(f"{self.base_url}/rest/api/3/issue/{issue_key}/worklog", headers=self.headers)
            response.raise_for_status()
            work_logs = response.json()["worklogs"]
            work_log_dicts = []
            for work_log in work_logs:
                work_log_dict = {
                    "author": work_log["author"]["displayName"],
                    "time_spent": work_log["timeSpent"],
                    "created": work_log["created"],
                    "comment": work_log["comment"],
                }
                work_log_dicts.append(work_log_dict)
            self.log.info("Work logs fetched successfully.")
            return work_log_dicts
        except Exception as e:
            self.log.error(f"Error fetching work logs: {e}")
            return []

    def fetch_attachments(self):
        """
        Fetch all attachments in the project and save each to a separate file.
        """
        try:
            start_at = 0
            while True:
                response = requests.get(
                    f"{self.base_url}/rest/api/3/search?jql=project={self.project_key}&fields=attachment&startAt={start_at}",
                    headers=self.headers,
                )
                response.raise_for_status()
                issues = response.json()["issues"]
                if not issues:
                    break
                for issue in issues:
                    for attachment in issue["fields"]["attachment"]:
                        attachment_response = requests.get(attachment["content"], headers=self.headers)
                        filename = attachment["filename"]
                        content = self.__parse_attachment(attachment_response.content, filename)
                        self.save_to_file(content, f"attachment_{attachment['id']}.txt")
                start_at += len(issues)
            self.log.info("Attachments fetched successfully.")
        except Exception as e:
            self.log.error(f"Error fetching attachments: {e}")
            raise

    def __parse_attachment(self, content: bytes, filename: str) -> str:
        """
        Parse an attachment into text.

        :param content: Content of the attachment.
        :param filename: Name of the attachment file.
        :return: Text content of the attachment.
        """
        if filename.endswith(".docx"):
            return self.__parse_word_document(content)
        elif filename.endswith(".xlsx") or filename.endswith(".xls"):
            return self.__parse_excel_spreadsheet(content)
        elif filename.endswith(".pdf"):
            return self.__parse_pdf(content)
        else:
            return content.decode()

    def __parse_word_document(self, content: bytes) -> str:
        """
        Parse a Word document into text.

        :param content: Content of the Word document.
        :return: Text content of the Word document.
        """
        document = Document(BytesIO(content))
        return "\n".join([paragraph.text for paragraph in document.paragraphs])

    def __parse_excel_spreadsheet(self, content: bytes) -> str:
        """
        Parse an Excel spreadsheet into text.

        :param content: Content of the Excel spreadsheet.
        :return: Text content of the Excel spreadsheet.
        """
        df = pd.read_excel(BytesIO(content))
        return df.to_string()

    def __parse_pdf(self, content: bytes) -> str:
        """
        Parse a PDF into text.

        :param content: Content of the PDF.
        :return: Text content of the PDF.
        """
        reader = PyPDF2.PdfFileReader(BytesIO(content))
        return "\n".join([reader.getPage(i).extractText() for i in range(reader.getNumPages())])

    def save_to_file(self, data: Any, filename: str) -> None:
        """
        Save data to a file in the output folder.

        :param data: Data to save.
        :param filename: Name of the file to save the data.
        """
        try:
            local_dir = os.path.join(self.output_folder, filename)
            with open(local_dir, "w") as f:
                json.dump(data, f)
            self.log.info(f"Data saved to {filename}.")
        except Exception as e:
            self.log.error(f"Error saving data to file: {e}")
            raise

    def get(self, resource_type: str) -> str:
        """
        Call the appropriate function based on the resource type, save the data, and return the status.

        :param resource_type: Type of the resource to fetch.
        :return: Status message.
        """
        fetch_method = getattr(self, f"fetch_{resource_type}", None)
        if not fetch_method:
            self.log.error(f"Invalid resource type: {resource_type}")
            return f"Invalid resource type: {resource_type}"
        try:
            fetch_method()
            return f"{resource_type} fetched successfully."
        except Exception as e:
            self.log.error(f"Error fetching {resource_type}: {e}")
            return f"Error fetching {resource_type}: {e}"
