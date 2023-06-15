<<<<<<< Updated upstream
from github import Github
from typing import List
import os

=======
import os
import json
from typing import Any, Dict
from github import Github
>>>>>>> Stashed changes
from geniusrise_cli.config import GITHUB_ACCESS_TOKEN
from geniusrise_cli.data_sources.code_hosting.static import valid_extensions
from task import Source


class GithubDataFetcher(Source):
    def __init__(self, repo_name: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.github = Github(GITHUB_ACCESS_TOKEN)
        self.repo = self.github.get_repo(repo_name)

    def fetch_code(self) -> str:
        contents = []
        for file in self.repo.get_contents(""):
            if file.type == "file" and any(file.name.endswith(ext) for ext in valid_extensions):
                contents.append(file.__dict__)
        return self.save_to_file(contents, "code.json")

    def fetch_pull_requests(self) -> str:
        pull_requests = []
        for pr in self.repo.get_pulls(state="all"):
            pull_requests.append(pr.__dict__)
        return self.save_to_file(pull_requests, "pull_requests.json")

    def fetch_commits(self) -> str:
        commits = []
        for commit in self.repo.get_commits():
            commits.append(commit.__dict__)
        return self.save_to_file(commits, "commits.json")

    def fetch_issues(self) -> str:
        issues = []
        for issue in self.repo.get_issues(state="all"):
            issues.append(issue.__dict__)
        return self.save_to_file(issues, "issues.json")

    def fetch_repo_details(self) -> str:
        contributors = [contributor.__dict__ for contributor in self.repo.get_contributors()]
        readme_content = self.repo.get_readme().__dict__
        file_structure = self._get_file_structure(self.repo.get_contents(""))
        repo_details = {
            "name": self.repo.name,
            "description": self.repo.description,
            "contributors": contributors,
            "readme": readme_content,
            "file_structure": file_structure,
        }
        return self.save_to_file(repo_details, "repo_details.json")

    def fetch_releases(self) -> str:
        releases = [release.__dict__ for release in self.repo.get_releases()]
        return self.save_to_file(releases, "releases.json")

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

    def read(self, what_to_read: str) -> Any:
        fetch_method = getattr(self, f"fetch_{what_to_read}", None)
        if not fetch_method:
            raise ValueError(f"Invalid read parameter: {what_to_read}")
        local_folder = fetch_method()
        self.sync_to_s3(local_folder)
        return local_folder

    def save_to_file(self, data: Dict[str, Any], filename: str) -> str:
        local_dir = os.path.join(self.output_folder, filename)
        with open(local_dir, "w") as f:
            json.dump(data, f)
        return local_dir
