import logging
from datetime import datetime

import requests  # type: ignore
from github import Github, GithubException

from geniusrise.config import GITHUB_ACCESS_TOKEN
from geniusrise.core import Spout, BatchOutputConfig, InMemoryStateManager


class GithubIncremental(Spout):
    def __init__(
        self,
        output_config: BatchOutputConfig,
        state_manager: InMemoryStateManager,
        repo_name: str,
        github_access_token: str = GITHUB_ACCESS_TOKEN,
    ):
        """
        Initialize GithubResourceFetcher with repository name, output folder, and access token.

        :param repo_name: Name of the repository.
        :param github_access_token: GitHub access token.
        """
        super().__init__(output_config=output_config, state_manager=state_manager)
        self.github = Github(github_access_token)
        self.repo = self.github.get_repo(repo_name)
        self.output_folder = output_config.output_folder

        self.log = logging.getLogger(__name__)

    def fetch_pull_requests(self, start_date: datetime = None, end_date: datetime = None):
        """
        Fetch all pull requests and save each to a separate file.
        """
        try:
            for pr in self.repo.get_pulls(state="all"):
                if start_date and pr.created_at < start_date:
                    continue
                if end_date and pr.created_at > end_date:
                    continue
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

    def fetch_commits(self, start_date: datetime = None, end_date: datetime = None):
        """
        Fetch all commits and save each to a separate file.
        """
        try:
            for commit in self.repo.get_commits():
                if start_date and commit.commit.author.date < start_date:
                    continue
                if end_date and commit.commit.author.date > end_date:
                    continue
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

    def fetch_issues(self, start_date: datetime = None, end_date: datetime = None):
        """
        Fetch all issues and save each to a separate file.
        """
        try:
            for issue in self.repo.get_issues(state="all"):
                if start_date and issue.created_at < start_date:
                    continue
                if end_date and issue.created_at > end_date:
                    continue
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

    def fetch_releases(self, start_date: datetime = None, end_date: datetime = None):
        """
        Fetch all releases and save each to a separate file.
        """
        try:
            for release in self.repo.get_releases():
                if start_date and release.published_at < start_date:
                    continue
                if end_date and release.published_at > end_date:
                    continue
            for release in self.repo.get_releases():
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
