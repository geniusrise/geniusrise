from github import Github
from typing import List
import os

from geniusrise_cli.config import GITHUB_ACCESS_TOKEN
from geniusrise_cli.data_sources.code_hosting.static import valid_extensions


class GithubDataFetcher:
    def __init__(self, repo_name: str):
        self.github = Github(GITHUB_ACCESS_TOKEN)
        self.repo = self.github.get_repo(repo_name)

    def fetch_code(self) -> List[str]:
        contents = []
        for file in self.repo.get_contents(""):  # type: ignore
            if file.type == "file" and any(
                file.name.endswith(ext) for ext in valid_extensions
            ):  # fetch only files with valid extensions
                contents.append(
                    f"File Name: {file.name}{os.linesep}Content:{os.linesep}{file.decoded_content.decode()}"
                )
        return contents

    def fetch_pull_requests(self) -> List[str]:
        pull_requests = []
        for pr in self.repo.get_pulls(state="all"):
            pr_data = [f"Title: {pr.title}", f"Body: {str(pr.body)}"]  # Convert pr.body to string
            pr_data += [f"Commit Message: {commit.commit.message}" for commit in pr.get_commits()]
            pr_data += [f"Comment: {comment.body}" for comment in pr.get_issue_comments()]
            pull_requests.append(os.linesep.join(pr_data))
        return pull_requests

    def fetch_commits(self) -> List[str]:
        commits = []
        for commit in self.repo.get_commits():
            commit_data = [f"Commit Message: {commit.commit.message}"]
            if commit.files:
                commit_data += [f"File Patch: {file.patch}" for file in commit.files if file.patch]
            commits.append(os.linesep.join(commit_data))
        return commits

    def fetch_issues(self) -> List[str]:
        issues = []
        for issue in self.repo.get_issues(state="all"):
            issue_data = [f"Title: {issue.title}", f"Body: {str(issue.body)}"]  # Convert issue.body to string
            issue_data += [f"Comment: {comment.body}" for comment in issue.get_comments()]
            if issue.pull_request:
                pr = self.repo.get_pull(issue.number)
                issue_data += [f"PR Body: {str(pr.body)}"]  # Convert pr.body to string
                issue_data += [f"Commit Message: {commit.commit.message}" for commit in pr.get_commits()]
                issue_data += [f"Comment: {comment.body}" for comment in pr.get_issue_comments()]
            issues.append(os.linesep.join(issue_data))
        return issues

    def fetch_repo_details(self) -> List[str]:
        contributors = self.repo.get_contributors()
        contributor_data = [f"Handle: {contributor.login}, Name: {contributor.name}" for contributor in contributors]
        readme_content = self.repo.get_readme().decoded_content.decode()
        file_structure = self._get_file_structure(self.repo.get_contents(""))
        repo_details = [
            f"Repo Name: {self.repo.name}{os.linesep}"
            f"Description: {self.repo.description}{os.linesep}"
            f"Contributors: {os.linesep.join(contributor_data)}{os.linesep}"
            f"Readme: {readme_content}{os.linesep}"
            f"File Structure: {os.linesep.join(file_structure)}"
        ]
        return repo_details

    def fetch_releases(self) -> List[str]:
        releases = self.repo.get_releases()
        release_data = [
            f"Release Name: {release.title}{os.linesep}"
            f"Release Notes: {release.body}{os.linesep}"
            f"Released At: {release.published_at}{os.linesep}"
            f"Version: {release.tag_name}{os.linesep}"
            f"Other Metadata: {release.raw_data}"
            for release in releases
        ]
        return release_data

    def _get_file_structure(self, contents) -> List[str]:
        structure = []
        for content in contents:
            if content.type == "dir":
                structure.append(
                    "Directory: "
                    + content.name
                    + "\n"
                    + "Contents: \n"
                    + "\n".join(self._get_file_structure(self.repo.get_contents(content.path)))
                )
            else:
                structure.append("File: " + content.name)
        return structure
