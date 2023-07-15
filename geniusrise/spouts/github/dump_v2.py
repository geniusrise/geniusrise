import logging
import os
from typing import List

import requests  # type: ignore
from github import Github, GithubException, PaginatedList
from github.Commit import Commit
from github.ContentFile import ContentFile
from github.GitRelease import GitRelease
from github.Issue import Issue
from github.PullRequest import PullRequest

from geniusrise.config import GITHUB_ACCESS_TOKEN
from geniusrise.core import BatchOutputConfig, InMemoryStateManager, Spout


class GithubDumpV2(Spout):
    def __init__(
        self,
        output_config: BatchOutputConfig,
        repo_name: str,
        state_manager: InMemoryStateManager = InMemoryStateManager(),
        github_access_token: str = GITHUB_ACCESS_TOKEN,
    ):
        """
        Initialize GithubDump with repository name, output folder, and access token.

        :param output_config: Configuration for output.
        :param repo_name: Name of the repository.
        :param state_manager: State manager to handle incremental fetching.
        :param github_access_token: Github access token.
        """
        super().__init__(output_config=output_config, state_manager=state_manager)
        self.github = Github(github_access_token)
        self.repo = self.github.get_repo(repo_name)
        self.output_folder = output_config.output_folder

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

    def fetch_pull_requests(self) -> None:
        """
        Fetch all pull requests and save each to a separate file.
        """
        self._fetch_and_save(self.repo.get_pulls(state="all"), self._pr_to_dict, "pull_request")

    def fetch_commits(self) -> None:
        """
        Fetch all commits and save each to a separate file.
        """
        self._fetch_and_save(self.repo.get_commits(), self._commit_to_dict, "commit")

    def fetch_issues(self) -> None:
        """
        Fetch all issues and save each to a separate file.
        """
        self._fetch_and_save(self.repo.get_issues(state="all"), self._issue_to_dict, "issue")

    def fetch_releases(self) -> None:
        """
        Fetch all releases and save each to a separate file.
        """
        self._fetch_and_save(self.repo.get_releases(), self._release_to_dict, "release")

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

    def _fetch_and_save(self, paginated_list: PaginatedList.PaginatedList, to_dict, prefix: str) -> None:
        """
        Fetch all items from paginated list, convert to dict and save each to a separate file.

        :param paginated_list: Paginated list of items.
        :param to_dict: Function to convert item to dict.
        :param prefix: Prefix for output file name.
        """
        try:
            for item in paginated_list:
                self.output_config.save(to_dict(item), f"{prefix}_{item.id}.json")
            self.log.info(f"{prefix.capitalize()}s fetched successfully.")
        except GithubException as e:
            self.log.error(f"Error fetching {prefix}s: {e}")
        except requests.exceptions.RequestException as e:
            self.log.error(f"Error fetching diff or patch data: {e}")

    @staticmethod
    def _pr_to_dict(pr: PullRequest) -> dict:
        """
        Convert pull request to dict.

        :param pr: Pull request.
        :return: Dict representation of pull request.
        """
        return {
            "number": pr.number,
            "title": pr.title,
            "body": pr.body,
            "comments": [comment.body for comment in pr.get_comments()],
            "diff": requests.get(pr.diff_url).text,
            "patch": requests.get(pr.patch_url).text,
        }

    @staticmethod
    def _commit_to_dict(commit: Commit) -> dict:
        """
        Convert commit to dict.

        :param commit: Commit.
        :return: Dict representation of commit.
        """
        diff_url = (
            f"https://github.com/{commit.repository.owner.login}/{commit.repository.name}/commit/{commit.sha}.diff"
        )
        patch_url = (
            f"https://github.com/{commit.repository.owner.login}/{commit.repository.name}/commit/{commit.sha}.patch"
        )
        return {
            "sha": commit.sha,
            "message": commit.commit.message,
            "author": commit.commit.author.name,
            "date": commit.commit.author.date.isoformat(),
            "files_changed": [f.filename for f in commit.files],
            "diff": requests.get(diff_url).text,
            "patch": requests.get(patch_url).text,
        }

    @staticmethod
    def _issue_to_dict(issue: Issue) -> dict:
        """
        Convert issue to dict.

        :param issue: Issue.
        :return: Dict representation of issue.
        """
        return {
            "number": issue.number,
            "title": issue.title,
            "body": issue.body,
            "comments": [comment.body for comment in issue.get_comments()],
            "state": issue.state,
        }

    @staticmethod
    def _release_to_dict(release: GitRelease) -> dict:
        """
        Convert release to dict.

        :param release: Release.
        :return: Dict representation of release.
        """
        return {
            "tag_name": release.tag_name,
            "name": release.title,
            "body": release.body,
            "published_at": release.published_at.isoformat(),
        }
