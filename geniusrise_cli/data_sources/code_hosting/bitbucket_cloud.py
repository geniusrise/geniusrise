import requests
from typing import List
import os
import git
import tempfile
import subprocess
import base64

from geniusrise_cli.config import BITBUCKET_ACCESS_TOKEN
from geniusrise_cli.data_sources.code_hosting.static import valid_extensions


class BitbucketCloudDataFetcher:
    def __init__(self, repo_name: str, workspace: str, username: str):
        print("BITBUCKET_ACCESS_TOKEN", BITBUCKET_ACCESS_TOKEN)

        self.base_url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_name}"
        self.headers = {
            "Authorization": f"Basic {base64.b64encode(f'{username}:{BITBUCKET_ACCESS_TOKEN}'.encode()).decode()}",
        }
        self.workspace = workspace
        self.repo_name = repo_name
        self.username = username

    def fetch_code(self) -> List[str]:
        contents = []

        # Create a temporary directory
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Clone the repository to the temporary directory
            subprocess.run(
                [
                    "git",
                    "clone",
                    "--quiet",  # Suppress output
                    f"https://{self.username}:{BITBUCKET_ACCESS_TOKEN}@bitbucket.org/{self.workspace}/{self.repo_name}.git",
                    tmp_dir,
                ],
                check=True,  # Raise an exception if the command fails
            )

            # Walk through the repository directory, read the files
            for root, dirs, files in os.walk(tmp_dir):
                for file in files:
                    if any(file.endswith(ext) for ext in valid_extensions):
                        with open(os.path.join(root, file)) as f:
                            content = f.read()
                            contents.append(
                                f"File Name: {os.path.relpath(os.path.join(root, file), tmp_dir)}{os.linesep}Content:{os.linesep}{content}"
                            )

        return contents

    def fetch_pull_requests(self) -> List[str]:
        response = requests.get(f"{self.base_url}/pullrequests", headers=self.headers)
        response.raise_for_status()
        pull_requests = response.json()["values"]
        pr_data = []
        for pr in pull_requests:
            pr_data.append(f"Title: {pr['title']}\nDescription: {pr['description']}")
        return pr_data

    def fetch_commits(self) -> List[str]:
        response = requests.get(f"{self.base_url}/commits", headers=self.headers)
        response.raise_for_status()
        commits = response.json()["values"]
        commit_data = []
        for commit in commits:
            commit_data.append(f"Message: {commit['message']}")
        return commit_data

    def fetch_issues(self) -> List[str]:
        response = requests.get(f"{self.base_url}/issues", headers=self.headers)
        response.raise_for_status()
        issues = response.json()["values"]
        issue_data = []
        for issue in issues:
            issue_data.append(f"Title: {issue['title']}\nDescription: {issue['content']['raw']}")
        return issue_data

    def fetch_repo_details(self) -> List[str]:
        response = requests.get(self.base_url, headers=self.headers)
        response.raise_for_status()
        repo = response.json()
        repo_details = [
            f"Repo Name: {repo['name']}\n"
            f"Description: {repo['description']}\n"
            f"Language: {repo['language']}\n"
            f"Created on: {repo['created_on']}\n"
            f"Updated on: {repo['updated_on']}\n"
            f"Size: {repo['size']}\n"
            f"Is private: {repo['is_private']}\n"
            f"Has wiki: {repo['has_wiki']}\n"
            f"Has issues: {repo['has_issues']}\n"
        ]
        return repo_details

    def fetch_releases(self) -> List[str]:
        response = requests.get(f"{self.base_url}/refs/tags", headers=self.headers)
        response.raise_for_status()
        releases = response.json()["values"]
        release_data = []
        for release in releases:
            release_data.append(f"Name: {release['name']}\nTarget hash: {release['target']['hash']}")
        return release_data
