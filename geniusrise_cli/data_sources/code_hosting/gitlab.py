import gitlab
import os
from typing import List

from geniusrise_cli.config import GITLAB_ACCESS_TOKEN
from geniusrise_cli.data_sources.code_hosting.static import valid_extensions


class GitlabDataFetcher:
    def __init__(self, repo_id: str):
        self.gitlab = gitlab.Gitlab("https://gitlab.com", private_token=GITLAB_ACCESS_TOKEN)
        self.repo = self.gitlab.projects.get(repo_id)

    def fetch_code(self) -> List[str]:
        contents = []
        items = self.repo.repository_tree(ref="master")
        for item in items:
            if item["type"] == "blob" and any(item["name"].endswith(ext) for ext in valid_extensions):
                file_content = self.repo.files.raw(file_path=item["path"], ref="master")
                if isinstance(file_content, bytes):
                    contents.append(f"File Name: {item['name']}{os.linesep}Content:{os.linesep}{file_content.decode()}")
        return contents

    def fetch_merge_requests(self) -> List[str]:
        merge_requests = []
        for mr in self.repo.mergerequests.list(all=True):
            mr_data = [f"Title: {mr.title}", f"Description: {mr.description}"]
            mr_data += [f"Commit Message: {commit.message}" for commit in mr.commits()]
            mr_data += [f"Comment: {note.body}" for note in mr.notes.list()]
            merge_requests.append(os.linesep.join(mr_data))
        return merge_requests

    def fetch_commits(self) -> List[str]:
        commits = []
        for commit in self.repo.commits.list(all=True):
            commit_data = [f"Commit Message: {commit.message}"]
            commits.append(os.linesep.join(commit_data))
        return commits

    def fetch_issues(self) -> List[str]:
        issues = []
        for issue in self.repo.issues.list(all=True):
            issue_data = [f"Title: {issue.title}", f"Description: {issue.description}"]
            issue_data += [f"Comment: {note.body}" for note in issue.notes.list()]
            issues.append(os.linesep.join(issue_data))
        return issues

    def fetch_repo_details(self) -> List[str]:
        contributors = self.repo.members.list(all=True)
        contributor_data = [f"Handle: {contributor.username}, Name: {contributor.name}" for contributor in contributors]
        readme_content_raw = self.repo.files.raw(file_path="README.md", ref="master")
        readme_content = readme_content_raw.decode() if isinstance(readme_content_raw, bytes) else ""
        file_structure = self._get_file_structure(self.repo.repository_tree(ref="master"))
        repo_details = [
            f"Repo Name: {self.repo.name}{os.linesep}"
            f"Description: {self.repo.description}{os.linesep}"
            f"Contributors: {os.linesep.join(contributor_data)}{os.linesep}"
            f"Readme: {readme_content}{os.linesep}"
            f"File Structure: {os.linesep.join(file_structure)}"
        ]
        return repo_details

    def fetch_releases(self) -> List[str]:
        releases = self.repo.releases.list()
        release_data = [
            f"Release Name: {release.name}{os.linesep}"
            f"Release Notes: {release.description}{os.linesep}"
            f"Released At: {release.released_at}{os.linesep}"
            f"Tag: {release.tag_name}{os.linesep}"
            for release in releases
        ]
        return release_data

    def _get_file_structure(self, items) -> List[str]:
        structure = []
        for item in items:
            if item["type"] == "tree":  # this is a directory
                structure.append(
                    "Directory: "
                    + item["name"]
                    + "\n"
                    + "Contents: \n"
                    + "\n".join(self._get_file_structure(self.repo.repository_tree(path=item["path"], ref="master")))
                )
            else:  # this is a file
                structure.append("File: " + item["name"])
        return structure
