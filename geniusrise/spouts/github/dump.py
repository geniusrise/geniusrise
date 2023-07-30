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

import logging
import os
from typing import List

import requests  # type: ignore
from github import Github, GithubException
from github.ContentFile import ContentFile
from github.PaginatedList import PaginatedList

from geniusrise.config import GITHUB_ACCESS_TOKEN
from geniusrise.core import BatchOutputConfig, InMemoryStateManager, Spout


class GithubDump(Spout):
    def __init__(
        self,
        output_config: BatchOutputConfig,
        repo_name: str,
        state_manager: InMemoryStateManager = InMemoryStateManager(),
        github_access_token: str = GITHUB_ACCESS_TOKEN,
    ):
        """
        Initialize GithubResourceFetcher with repository name, output folder, and access token.

        :param output_config: Configuration for output.
        :param repo_name: Name of the repository.
        :param state_manager: Manager for state.
        :param github_access_token: Github access token.
        """
        super().__init__(output_config=output_config, state_manager=state_manager)
        self.github = Github(github_access_token)
        self.repo = self.github.get_repo(repo_name)
        self.output_folder = output_config.output_folder

        self.log = logging.getLogger(__name__)

    def fetch_code(self) -> None:
        """
        Clone the repository to the output folder.
        """
        try:
            os.system(f"git clone {self.repo.clone_url} {self.output_folder}")
            self.log.info("Repository cloned successfully.")
        except Exception as e:
            self.log.error(f"Error cloning repository: {e}")

    def fetch_pull_requests(self) -> None:
        """
        Fetch all pull requests and save each to a separate file.
        """
        try:
            pulls: PaginatedList = self.repo.get_pulls(state="all")
            for pr in pulls:
                diff_data = requests.get(pr.diff_url).text
                patch_data = requests.get(pr.patch_url).text
                pr_dict = {
                    "number": pr.number,
                    "title": pr.title,
                    "body": pr.body,
                    "comments": [comment.body for comment in pr.get_comments()],
                    "diff": diff_data,
                    "patch": patch_data,
                }
                self.output_config.save(pr_dict, f"pull_request_{pr.number}.json")
            self.log.info("Pull requests fetched successfully.")
        except GithubException as e:
            self.log.error(f"Error fetching pull requests: {e}")
        except requests.exceptions.RequestException as e:
            self.log.error(f"Error fetching diff or patch data: {e}")

    def fetch_commits(self) -> None:
        """
        Fetch all commits and save each to a separate file.
        """
        try:
            commits: PaginatedList = self.repo.get_commits()
            for commit in commits:
                diff_url = f"https://github.com/{self.repo.owner.login}/{self.repo.name}/commit/{commit.sha}.diff"
                patch_url = f"https://github.com/{self.repo.owner.login}/{self.repo.name}/commit/{commit.sha}.patch"
                diff_data = requests.get(diff_url).text
                patch_data = requests.get(patch_url).text
                commit_dict = {
                    "sha": commit.sha,
                    "message": commit.commit.message,
                    "author": commit.commit.author.name,
                    "date": commit.commit.author.date.isoformat(),
                    "files_changed": [f.filename for f in commit.files],
                    "diff": diff_data,
                    "patch": patch_data,
                }
                self.output_config.save(commit_dict, f"commit_{commit.sha}.json")
            self.log.info("Commits fetched successfully.")
        except GithubException as e:
            self.log.error(f"Error fetching commits: {e}")
        except requests.exceptions.RequestException as e:
            self.log.error(f"Error fetching diff or patch data: {e}")

    def fetch_issues(self) -> None:
        """
        Fetch all issues and save each to a separate file.
        """
        try:
            issues: PaginatedList = self.repo.get_issues(state="all")
            for issue in issues:
                issue_dict = {
                    "number": issue.number,
                    "title": issue.title,
                    "body": issue.body,
                    "comments": [comment.body for comment in issue.get_comments()],
                    "state": issue.state,
                }
                self.output_config.save(issue_dict, f"issue_{issue.number}.json")
            self.log.info("Issues fetched successfully.")
        except GithubException as e:
            self.log.error(f"Error fetching issues: {e}")

    def fetch_releases(self) -> None:
        """
        Fetch all releases and save each to a separate file.
        """
        try:
            releases: PaginatedList = self.repo.get_releases()
            for release in releases:
                release_dict = {
                    "tag_name": release.tag_name,
                    "name": release.title,
                    "body": release.body,
                    "published_at": release.published_at.isoformat(),
                }
                self.output_config.save(release_dict, f"release_{release.tag_name}.json")
            self.log.info("Releases fetched successfully.")
        except GithubException as e:
            self.log.error(f"Error fetching releases: {e}")

    def fetch_repo_details(self) -> None:
        """
        Fetch repository details and save to a file.
        """
        try:
            repo_details = {
                "name": self.repo.name,
                "description": self.repo.description,
                "contributors": [contributor.login for contributor in self.repo.get_contributors()],
                "readme": self.repo.get_readme().decoded_content.decode(),
                "file_structure": self._get_file_structure(self.repo.get_contents("")),
            }
            self.output_config.save(repo_details, "repo_details.json")
            self.log.info("Repository details fetched successfully.")
        except GithubException as e:
            self.log.error(f"Error fetching repository details: {e}")

    def _get_file_structure(self, contents: List[ContentFile]) -> List[str]:
        """
        Get the file structure of the repository.

        :param contents: List of repository contents.
        :return: List of file and directory names.
        """
        structure = []
        for content in contents:
            if content.type == "dir":
                structure.append(
                    "Directory: "
                    + content.name
                    + "\n"
                    + "Contents: \n"
                    + "\n".join(self._get_file_structure(self.repo.get_contents(content.path)))  # type: ignore
                )
            else:
                structure.append("File: " + content.name)
        return structure
