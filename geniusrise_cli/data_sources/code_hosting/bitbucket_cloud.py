import os
import json
import logging
import requests
import base64
from typing import Any


class BitbucketDataFetcher:
    def __init__(self, workspace: str, repo_slug: str, username: str, password: str, output_folder: str):
        """
        Initialize BitbucketDataFetcher with workspace, repository slug, username, password, and output folder.

        :param workspace: Bitbucket workspace.
        :param repo_slug: Slug of the repository.
        :param username: Bitbucket username.
        :param password: Bitbucket password.
        :param output_folder: Folder to save the fetched data.
        """
        self.base_url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}"
        self.auth = (username, password)
        self.output_folder = output_folder
        self.headers = {
            "Authorization": f"Basic {base64.b64encode(f'{username}:{password}'.encode()).decode()}",
        }

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def fetch_code(self):
        """
        Clone the repository to the output folder.
        """
        try:
            repo_url = f"{self.base_url}"
            response = requests.get(repo_url, auth=self.auth)
            response.raise_for_status()
            clone_url = response.json()["links"]["clone"][0]["href"]
            os.system(f"git clone {clone_url} {self.output_folder}")
            self.logger.info("Repository cloned successfully.")
        except Exception as e:
            self.logger.error(f"Error cloning repository: {e}")

    def fetch_pull_requests(self):
        """
        Fetch all pull requests and save each to a separate file.
        """
        try:
            pr_url = f"{self.base_url}/pullrequests"
            response = requests.get(pr_url, headers=self.headers)
            response.raise_for_status()
            for pr in response.json()["values"]:
                self.save_to_file(pr, f"pull_request_{pr['id']}.json")
            self.logger.info("Pull requests fetched successfully.")
        except Exception as e:
            self.logger.error(f"Error fetching pull requests: {e}")

    def fetch_commits(self):
        """
        Fetch all commits and save each to a separate file.
        """
        try:
            commits_url = f"{self.base_url}/commits"
            response = requests.get(commits_url, headers=self.headers)
            response.raise_for_status()
            for commit in response.json()["values"]:
                self.save_to_file(commit, f"commit_{commit['hash']}.json")
            self.logger.info("Commits fetched successfully.")
        except Exception as e:
            self.logger.error(f"Error fetching commits: {e}")

    def fetch_issues(self):
        """
        Fetch all issues and save each to a separate file.
        """
        try:
            issues_url = f"{self.base_url}/issues"
            response = requests.get(issues_url, headers=self.headers)
            response.raise_for_status()
            for issue in response.json()["values"]:
                self.save_to_file(issue, f"issue_{issue['id']}.json")
            self.logger.info("Issues fetched successfully.")
        except Exception as e:
            self.logger.error(f"Error fetching issues: {e}")

    def fetch_releases(self):
        """
        Fetch all releases and save each to a separate file.
        """
        try:
            releases_url = f"{self.base_url}/refs/tags"
            response = requests.get(releases_url, headers=self.headers)
            response.raise_for_status()
            for release in response.json()["values"]:
                self.save_tofile(release, f"release_{release['name']}.json")
            self.logger.info("Releases fetched successfully.")
        except Exception as e:
            self.logger.error(f"Error fetching releases: {e}")

    def fetch_repo_details(self):
        """
        Fetch repository details and save to a file.
        """
        try:
            repo_url = f"{self.base_url}"
            response = requests.get(repo_url, headers=self.headers)
            response.raise_for_status()
            self.save_to_file(response.json(), "repo_details.json")
            self.logger.info("Repository details fetched successfully.")
        except Exception as e:
            self.logger.error(f"Error fetching repository details: {e}")

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
            self.logger.info(f"Data saved to {filename}.")
        except Exception as e:
            self.logger.error(f"Error saving data to file: {e}")

    def get(self, resource_type: str) -> str:
        """
        Call the appropriate function based on the resource type, save the data, and return the status.

        :param resource_type: Type of the resource to fetch.
        :return: Status message.
        """
        fetch_method = getattr(self, f"fetch_{resource_type}", None)
        if not fetch_method:
            self.logger.error(f"Invalid resource type: {resource_type}")
            return f"Invalid resource type: {resource_type}"
        try:
            fetch_method()
            return f"{resource_type} fetched successfully."
        except Exception as e:
            self.logger.error(f"Error fetching {resource_type}: {e}")
            return f"Error fetching {resource_type}: {e}"
