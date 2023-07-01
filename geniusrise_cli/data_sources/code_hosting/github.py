import json
import logging
import os
from typing import Any, List

import requests
from github import Github, GithubException
from github.ContentFile import ContentFile

from geniusrise_cli.config import GITHUB_ACCESS_TOKEN


class GithubDataFetcher:
    def __init__(self, repo_name: str, output_folder: str):
        """
        Initialize GithubResourceFetcher with repository name, output folder, and access token.

        :param repo_name: Name of the repository.
        :param output_folder: Folder to save the fetched data.
        """
        self.github = Github(GITHUB_ACCESS_TOKEN)
        self.repo = self.github.get_repo(repo_name)
        self.output_folder = output_folder

        self.log = logging.getLogger(__name__)

    def fetch_code(self):
        """
        Clone the repository to the output folder.
        """
        try:
            os.system(f"git clone {self.repo.clone_url} {self.output_folder}")
            self.log.info("Repository cloned successfully.")
        except Exception as e:
            self.log.error(f"Error cloning repository: {e}")

    def fetch_pull_requests(self):
        """
        Fetch all pull requests and save each to a separate file.
        """
        try:
            for pr in self.repo.get_pulls(state="all"):
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
                self.save_to_file(pr_dict, f"pull_request_{pr.number}.json")
            self.log.info("Pull requests fetched successfully.")
        except GithubException as e:
            self.log.error(f"Error fetching pull requests: {e}")
        except requests.exceptions.RequestException as e:
            self.log.error(f"Error fetching diff or patch data: {e}")

    def fetch_commits(self):
        """
        Fetch all commits and save each to a separate file.
        """
        try:
            for commit in self.repo.get_commits():
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
                self.save_to_file(commit_dict, f"commit_{commit.sha}.json")
            self.log.info("Commits fetched successfully.")
        except GithubException as e:
            self.log.error(f"Error fetching commits: {e}")
        except requests.exceptions.RequestException as e:
            self.log.error(f"Error fetching diff or patch data: {e}")

    def fetch_issues(self):
        """
        Fetch all issues and save each to a separate file.
        """
        try:
            for issue in self.repo.get_issues(state="all"):
                issue_dict = {
                    "number": issue.number,
                    "title": issue.title,
                    "body": issue.body,
                    "comments": [comment.body for comment in issue.get_comments()],
                    "state": issue.state,
                }
                self.save_to_file(issue_dict, f"issue_{issue.number}.json")
            self.log.info("Issues fetched successfully.")
        except GithubException as e:
            self.log.error(f"Error fetching issues: {e}")

    def fetch_releases(self):
        """
        Fetch all releases and save each to a separate file.
        """
        try:
            for release in self.repo.get_releases():
                release_dict = {
                    "tag_name": release.tag_name,
                    "name": release.title,
                    "body": release.body,
                    "published_at": release.published_at.isoformat(),
                }
                self.save_to_file(release_dict, f"release_{release.tag_name}.json")
            self.log.info("Releases fetched successfully.")
        except GithubException as e:
            self.log.error(f"Error fetching releases: {e}")

    def fetch_repo_details(self):
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
            self.save_to_file(repo_details, "repo_details.json")
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
