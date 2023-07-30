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

import json
import logging
import os
from typing import Any

import gitlab

from geniusrise.config import GITLAB_ACCESS_TOKEN


class GitlabDataFetcher:
    def __init__(self, repo_id: str, output_folder: str):
        """
        Initialize GitlabDataFetcher with repository ID, output folder, and access token.

        :param repo_id: ID of the repository.
        :param output_folder: Folder to save the fetched data.
        :param access_token: GitLab access token.
        """
        self.gl = gitlab.Gitlab("https://gitlab.com", private_token=GITLAB_ACCESS_TOKEN)
        self.repo = self.gl.projects.get(repo_id)
        self.output_folder = output_folder

        self.log = logging.getLogger(__name__)

    def fetch_code(self):
        """
        Clone the repository to the output folder.
        """
        try:
            os.system(f"git clone {self.repo.http_url_to_repo} {self.output_folder}")
            self.log.info("Repository cloned successfully.")
        except Exception as e:
            self.log.error(f"Error cloning repository: {e}")

    def fetch_merge_requests(self):
        """
        Fetch all merge requests and save each to a separate file.
        """
        try:
            for mr in self.repo.mergerequests.list(all=True):
                mr_dict = {
                    "id": mr.id,
                    "title": mr.title,
                    "description": mr.description,
                    "state": mr.state,
                    "created_at": mr.created_at,
                    "updated_at": mr.updated_at,
                    "merged_at": mr.merged_at,
                    "closed_at": mr.closed_at,
                    "diff": [x["diff"] for i in mr.diffs.list() for x in mr.diffs.get(i.id).diffs],
                    "comments": [note.body for note in mr.notes.list(all=True)],
                }
                self.save_to_file(mr_dict, f"merge_request_{mr.id}.json")
            self.log.info("Merge requests fetched successfully.")
        except Exception as e:
            self.log.error(f"Error fetching merge requests: {e}")

    def fetch_commits(self):
        """
        Fetch all commits and save each to a separate file.
        """
        try:
            for commit in self.repo.commits.list(all=True):
                commit_dict = {
                    "id": commit.id,
                    "message": commit.message,
                    "title": commit.title,
                    "author_name": commit.author_name,
                    "authored_date": commit.authored_date,
                    "committed_date": commit.committed_date,
                    "diff": self.repo.commits.get(commit.id).diff(),
                }
                self.save_to_file(commit_dict, f"commit_{commit.id}.json")
            self.log.info("Commits fetched successfully.")
        except Exception as e:
            self.log.error(f"Error fetching commits: {e}")

    def fetch_issues(self):
        """
        Fetch all issues and save each to a separate file.
        """
        try:
            for issue in self.repo.issues.list(all=True):
                issue_dict = {
                    "id": issue.id,
                    "title": issue.title,
                    "description": issue.description,
                    "state": issue.state,
                    "created_at": issue.created_at,
                    "updated_at": issue.updated_at,
                    "closed_at": issue.closed_at,
                    "notes": [note.body for note in issue.notes.list(all=True)],
                }
                self.save_to_file(issue_dict, f"issue_{issue.id}.json")
            self.log.info("Issues fetched successfully.")
        except Exception as e:
            self.log.error(f"Error fetching issues: {e}")

    def fetch_releases(self):
        """
        Fetch all releases and save each to a separate file.
        """
        try:
            for release in self.repo.releases.list(all=True):
                release_dict = {
                    "name": release.name,
                    "tag_name": release.tag_name,
                    "description": release.description,
                    "created_at": release.created_at,
                    "released_at": release.released_at,
                }
                self.save_to_file(release_dict, f"release_{release.tag_name}.json")
            self.log.info("Releases fetched successfully.")
        except Exception as e:
            self.log.error(f"Error fetching releases: {e}")

    def fetch_repo_details(self):
        """
        Fetch repository details and save to a file.
        """
        try:
            self.fetch_code()
            with open(os.path.join(self.output_folder, "README.md"), "r") as readme_file:
                readme_content = readme_file.read()
            repo_details = {
                "id": self.repo.id,
                "name": self.repo.name,
                "description": self.repo.description,
                "default_branch": self.repo.default_branch,
                "visibility": self.repo.visibility,
                "created_at": self.repo.created_at,
                "last_activity_at": self.repo.last_activity_at,
                "readme": readme_content,
            }
            self.save_to_file(repo_details, "repo_details.json")
            self.log.info("Repository details fetched successfully.")
        except Exception as e:
            self.log.error(f"Error fetching repository details: {e}")

    def save_to_file(self, data: Any, filename: str):
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
