from github import Github
from typing import List

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
                contents.append(file.decoded_content.decode())
        return contents

    def fetch_pull_requests(self) -> List[str]:
        pull_requests = []
        for pr in self.repo.get_pulls(state="all"):
            pr_data = [pr.title, str(pr.body)]  # Convert pr.body to string
            pr_data += [commit.commit.message for commit in pr.get_commits()]
            pr_data += [comment.body for comment in pr.get_issue_comments()]
            pull_requests.append("\n".join(pr_data))
        return pull_requests

    def fetch_commits(self) -> List[str]:
        commits = []
        for commit in self.repo.get_commits():
            commit_data = [commit.commit.message]
            if commit.files:
                commit_data += [file.patch for file in commit.files if file.patch]
            commits.append("\n".join(commit_data))
        return commits

    def fetch_issues(self) -> List[str]:
        issues = []
        for issue in self.repo.get_issues(state="all"):
            issue_data = [issue.title, str(issue.body)]  # Convert issue.body to string
            issue_data += [comment.body for comment in issue.get_comments()]
            if issue.pull_request:
                pr = self.repo.get_pull(issue.number)
                issue_data += [str(pr.body)]  # Convert pr.body to string
                issue_data += [commit.commit.message for commit in pr.get_commits()]
                issue_data += [comment.body for comment in pr.get_issue_comments()]
            issues.append("\n".join(issue_data))
        return issues

    def get_all_data(self) -> dict:
        return {
            "code": self.fetch_code(),
            "pull_requests": self.fetch_pull_requests(),
            "commits": self.fetch_commits(),
            "issues": self.fetch_issues(),
        }
