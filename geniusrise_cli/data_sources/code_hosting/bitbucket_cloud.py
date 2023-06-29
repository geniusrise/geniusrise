import base64
import json
import logging
import os
from typing import Any, List

import requests

from geniusrise_cli.config import BITBUCKET_ACCESS_TOKEN


class BitbucketDataFetcher:
    def __init__(self, workspace: str, repo_slug: str, username: str, output_folder: str):
        """
        Initialize BitbucketDataFetcher with workspace, repository slug, username, password, and output folder.

        :param workspace: Bitbucket workspace.
        :param repo_slug: Slug of the repository.
        :param username: Bitbucket username.
        :param password: Bitbucket password.
        :param output_folder: Folder to save the fetched data.
        """
        self.base_url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}"
        self.auth = (username, BITBUCKET_ACCESS_TOKEN)
        self.output_folder = output_folder
        self.repo_slug = repo_slug
        self.headers = {
            "Authorization": f"Basic {base64.b64encode(f'{username}:{BITBUCKET_ACCESS_TOKEN}'.encode()).decode()}",
        }

        self.log = logging.getLogger(__name__)

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
            self.log.info("Repository cloned successfully.")
        except Exception as e:
            self.log.error(f"Error cloning repository: {e}")

    def fetch_pull_requests(self):
        """
        Fetch all pull requests and save each to a separate file.
        """
        try:
            next_url = f"{self.base_url}/pullrequests?state=OPEN,MERGED,DECLINED"
            while next_url:
                response = requests.get(next_url, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                pull_requests = data["values"]
                for pr in pull_requests:
                    pr_dict = {
                        "id": pr["id"],
                        "title": pr["title"],
                        "description": pr["description"],
                        "state": pr["state"],
                        "created_on": pr["created_on"],
                        "updated_on": pr["updated_on"],
                        "diff": self.__fetch_diff(pr["links"]["diff"]["href"]),
                        "comments": self.__fetch_comments(pr["links"]["comments"]["href"]),
                    }
                    self.save_to_file(pr_dict, f"pull_request_{pr['id']}.json")
                next_url = data.get("next", None)  # Get the URL for the next page of results, if it exists
            self.log.info("Pull requests fetched successfully.")
        except Exception as e:
            self.log.error(f"Error fetching pull requests: {e}")

    def __fetch_diff(self, diff_url: str) -> str:
        """
        Fetch the diff for a pull request.

        :param diff_url: The URL to fetch the diff from.
        :return: The diff as a string.
        """
        try:
            response = requests.get(diff_url, headers=self.headers)
            response.raise_for_status()
            return response.text
        except Exception as e:
            self.log.error(f"Error fetching diff: {e}")
            return ""

    def __fetch_comments(self, comments_url: str) -> List[str]:
        """
        Fetch the comments for a pull request.

        :param comments_url: The URL to fetch the comments from.
        :return: A list of comments.
        """
        try:
            response = requests.get(comments_url, headers=self.headers)
            response.raise_for_status()
            comments_data = response.json()["values"]
            return [comment["content"]["raw"] for comment in comments_data]
        except Exception as e:
            self.log.error(f"Error fetching comments: {e}")
            return []

    def fetch_commits(self):
        """
        Fetch all commits and save each to a separate file.
        """
        try:
            next_url = f"{self.base_url}/commits"
            while next_url:
                response = requests.get(next_url, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                commits = data["values"]
                for commit in commits:
                    commit_dict = {
                        "id": commit["hash"],
                        "message": commit["message"],
                        "repository": self.repo_slug,
                        "author": commit["author"]["raw"],
                        "date": commit["date"],
                        "parents": [parent["hash"] for parent in commit["parents"]],
                        "diff": self.__fetch_diff(f"{self.base_url}/diff/{commit['hash']}"),
                    }
                    self.save_to_file(commit_dict, f"commit_{commit['hash']}.json")
                next_url = data.get("next", None)  # Get the URL for the next page of results, if it exists
            self.log.info("Commits fetched successfully.")
        except Exception as e:
            self.log.error(f"Error fetching commits: {e}")

    def fetch_issues(self):
        """
        Fetch all issues and save each to a separate file.
        """
        try:
            next_url = f"{self.base_url}/issues"
            while next_url:
                response = requests.get(next_url, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                issues = data["values"]
                for issue in issues:
                    issue_dict = {
                        "id": issue["id"],
                        "title": issue["title"],
                        "content": issue["content"]["raw"],
                        "state": issue["state"],
                        "priority": issue["priority"],
                        "kind": issue["kind"],
                        "repository": self.repo_name,
                        "created_on": issue["created_on"],
                        "updated_on": issue["updated_on"],
                        "reporter": issue["reporter"]["display_name"],
                        "assignee": issue["assignee"]["display_name"] if issue["assignee"] else None,
                        "comments": self.__fetch_comments(issue["links"]["comments"]["href"]),
                    }
                    self.save_to_file(issue_dict, f"issue_{issue['id']}.json")
                next_url = data.get("next", None)  # Get the URL for the next page of results, if it exists
            self.log.info("Issues fetched successfully.")
        except Exception as e:
            self.log.error(f"Error fetching issues: {e}")

    def fetch_releases(self):
        """
        Fetch all releases (tags) and save each to a separate file.
        """
        try:
            next_url = f"{self.base_url}/refs/tags"
            while next_url:
                response = requests.get(next_url, headers=self.headers)
                response.raise_for_status()
                data = response.json()
                tags = data["values"]
                for tag in tags:
                    commit_hash = tag["target"]["hash"]
                    commit_response = requests.get(f"{self.base_url}/commit/{commit_hash}", headers=self.headers)
                    commit_response.raise_for_status()
                    commit_data = commit_response.json()
                    tag_dict = {
                        "name": tag["name"],
                        "repository": self.repo_slug,
                        "target": {
                            "hash": commit_hash,
                            "message": commit_data["message"],
                            "diff": self.__fetch_diff(f"{self.base_url}/diff/{commit_hash}"),
                        },
                    }
                    self.save_to_file(tag_dict, f"release_{tag['name']}.json")
                next_url = data.get("next", None)  # Get the URL for the next page of results, if it exists
            self.log.info("Releases (tags) fetched successfully.")
        except Exception as e:
            self.log.error(f"Error fetching releases (tags): {e}")

    def fetch_repo_details(self):
        """
        Fetch repository details and save to a file.
        """
        try:
            repo_url = f"{self.base_url}"
            response = requests.get(repo_url, headers=self.headers)
            response.raise_for_status()
            repo_data = response.json()

            self.fetch_code()
            with open(os.path.join(self.output_folder, "README.md"), "r") as readme_file:
                readme_content = readme_file.read()

            repo_details = {
                "name": repo_data["name"],
                "full_name": repo_data["full_name"],
                "uuid": repo_data["uuid"],
                "language": repo_data["language"],
                "created_on": repo_data["created_on"],
                "updated_on": repo_data["updated_on"],
                "size": repo_data["size"],
                "is_private": repo_data["is_private"],
                "has_issues": repo_data["has_issues"],
                "has_wiki": repo_data["has_wiki"],
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
