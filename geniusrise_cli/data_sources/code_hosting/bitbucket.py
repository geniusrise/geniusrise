from atlassian import Bitbucket, Jira
from atlassian.bitbucket.cloud import Cloud
from typing import List
import os

from geniusrise_cli.config import BITBUCKET_ACCESS_TOKEN, BITBUCKET_URL, JIRA_ACCESS_TOKEN, JIRA_URL
from geniusrise_cli.data_sources.code_hosting.static import valid_extensions


class BitbucketDataFetcher:
    def __init__(self, repo_name: str, project_key: str, username: str, cloud=True):
        print("BITBUCKET_ACCESS_TOKEN", BITBUCKET_ACCESS_TOKEN)

        if not cloud:
            self.bitbucket = Bitbucket(url=BITBUCKET_URL, username=username, password=BITBUCKET_ACCESS_TOKEN)
            self.repo = self.bitbucket
        else:
            self.bitbucket = Cloud(cloud=True, access_token=BITBUCKET_ACCESS_TOKEN)
            self.workspace = self.bitbucket.workspaces.get(project_key)
            self.repo = self.workspace.repositories.get(repo_name)

        self.jira = Jira(url=JIRA_URL, username=username, password=JIRA_ACCESS_TOKEN)
        self.repo_name = repo_name
        self.project_key = project_key

    def fetch_code(self) -> List[str]:
        contents = []
        if isinstance(self.bitbucket, Bitbucket):
            branches = self.bitbucket.get_branches(self.project_key, self.repo_name)
            for branch in branches:
                commit = branch["latestCommit"]
                changes = self.bitbucket.get_changelog(self.project_key, self.repo_name, commit, commit)
                for change in changes:
                    if change["type"] == "MODIFY" and any(
                        change["path"]["toString"].endswith(ext) for ext in valid_extensions
                    ):
                        file_content = self.bitbucket.get_content_of_file(
                            self.project_key, self.repo_name, change["path"]["toString"]
                        )
                        contents.append(
                            f"File Name: {change['path']['toString']}{os.linesep}Content:{os.linesep}{file_content}"
                        )
        else:
            # Bitbucket Cloud does not support fetching code directly. You may need to use a different method.
            pass
        return contents

    def fetch_pull_requests(self) -> List[str]:
        pull_requests = []
        if isinstance(self.bitbucket, Bitbucket):
            prs = self.bitbucket.get_pull_requests(self.project_key, self.repo_name)
            for pr in prs:
                pr_data = [f"Title: {pr['title']}", f"Description: {pr['description']}"]
                pr_data += [
                    f"Commit Message: {commit['message']}"
                    for commit in self.bitbucket.get_pull_requests_commits(self.project_key, self.repo_name, pr["id"])
                ]
                pr_data += [
                    f"Comment: {comment['text']}"
                    for comment in self.bitbucket.get_pull_requests_activities(
                        self.project_key, self.repo_name, pr["id"]
                    )
                    if comment["action"] == "COMMENTED"
                ]
                pull_requests.append(os.linesep.join(pr_data))
        else:
            # Bitbucket Cloud does not support fetching pull requests directly. You may need to use a different method.
            pass
        return pull_requests

    def fetch_commits(self) -> List[str]:
        commits = []
        if isinstance(self.bitbucket, Bitbucket):
            commit_list = self.bitbucket.get_commits(self.project_key, self.repo_name)
            for commit in commit_list:
                commit_data = [f"Commit Message: {commit['message']}"]
                commits.append(os.linesep.join(commit_data))
        else:
            # Bitbucket Cloud does not support fetching commits directly. You may need to use a different method.
            pass
        return commits

    def fetch_issues(self) -> List[str]:
        issues = []
        if isinstance(self.bitbucket, Bitbucket):
            for issue in self.bitbucket.get_issues(self.project_key, self.repo_name):
                issue_data = [f"Title: {issue['title']}", f"Description: {issue['content']['raw']}"]
                issues.append(os.linesep.join(issue_data))
        else:
            for issue in self.repo.issues.each():
                issue_data = [f"Title: {issue['title']}", f"Description: {issue['content']['raw']}"]
                issues.append(os.linesep.join(issue_data))
        return issues

    def fetch_repo_details(self) -> List[str]:
        if isinstance(self.bitbucket, Bitbucket):
            contributors = self.jira.get_all_assignable_users_for_project(self.project_key)
            contributor_data = [
                f"Handle: {contributor['name']}, Name: {contributor['displayName']}" for contributor in contributors
            ]
            readme_content = self.bitbucket.get_content_of_file(self.project_key, self.repo_name, "README.md")
            repo_details = [
                f"Repo Name: {self.repo_name}{os.linesep}"
                f"Description: {self.bitbucket.get_project(self.project_key)['description']}{os.linesep}"
                f"Contributors: {os.linesep.join(contributor_data)}{os.linesep}"
                f"Readme: {readme_content}{os.linesep}"
            ]
        else:
            # Bitbucket Cloud does not support fetching repo details directly. You may need to use a different method.
            pass
        return repo_details

    def fetch_releases(self) -> List[str]:
        if isinstance(self.bitbucket, Bitbucket):
            releases = self.bitbucket.get_tags(self.project_key, self.repo_name)
            release_data = [
                f"Release Name: {release['displayId']}{os.linesep}"
                f"Commit Message: {release['latestChangeset']}{os.linesep}"
                f"Tag: {release['id']}{os.linesep}"
                for release in releases
            ]
        else:
            # Bitbucket Cloud does not support fetching releases directly. You may need to use a different method.
            pass
        return release_data
