import requests  # type: ignore
from typing import Dict, Optional, Any, List


# Create a function to authenticate a user using a personal access token.
def authenticate(token: str) -> Dict[str, str]:
    headers = {"Authorization": f"token {token}"}
    return headers


# Create a function to create a new repository.
def create_repository(
    token: str, name: str, description: Optional[str] = None, private: Optional[bool] = False
) -> Dict[str, Any]:
    url = "https://api.github.com/user/repos"
    headers = authenticate(token)
    data = {"name": name, "description": description, "private": private}
    response = requests.post(url, headers=headers, json=data)
    return response.json()


# Create a function to get details of a specific repository.
def get_repository(token: str, owner: str, repo: str) -> Dict[str, Any]:
    url = f"https://api.github.com/repos/{owner}/{repo}"
    headers = authenticate(token)
    response = requests.get(url, headers=headers)
    return response.json()


# Create a function to update a repository's details.
def update_repository(
    token: str,
    owner: str,
    repo: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    private: Optional[bool] = None,
) -> Dict[str, Any]:
    url = f"https://api.github.com/repos/{owner}/{repo}"
    headers = authenticate(token)
    data = {"name": name, "description": description, "private": private}
    response = requests.patch(url, headers=headers, json=data)
    return response.json()


# Create a function to delete a repository.
def delete_repository(token: str, owner: str, repo: str) -> int:
    url = f"https://api.github.com/repos/{owner}/{repo}"
    headers = authenticate(token)
    response = requests.delete(url, headers=headers)
    return response.status_code  # Returns 204 on success


# Create a function to create a new issue.
def create_issue(token: str, owner: str, repo: str, title: str, body: Optional[str] = None) -> Dict[str, Any]:
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    headers = authenticate(token)
    data = {"title": title, "body": body}
    response = requests.post(url, headers=headers, json=data)
    return response.json()


# Create a function to get details of a specific issue.
def get_issue(token: str, owner: str, repo: str, issue_number: int) -> Dict[str, Any]:
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}"
    headers = authenticate(token)
    response = requests.get(url, headers=headers)
    return response.json()


# Create a function to update an issue's details.
def update_issue(
    token: str,
    owner: str,
    repo: str,
    issue_number: int,
    title: Optional[str] = None,
    body: Optional[str] = None,
    state: Optional[str] = None,
) -> Dict[str, Any]:
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}"
    headers = authenticate(token)
    data = {"title": title, "body": body, "state": state}
    response = requests.patch(url, headers=headers, json=data)
    return response.json()


# Create a function to close an issue.
def close_issue(token: str, owner: str, repo: str, issue_number: int) -> Dict[str, Any]:
    return update_issue(token, owner, repo, issue_number, state="closed")


# Create a function to create a new pull request.
def create_pull_request(
    token: str, owner: str, repo: str, title: str, head: str, base: str, body: Optional[str] = None
) -> Dict[str, Any]:
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    headers = authenticate(token)
    data = {"title": title, "head": head, "base": base, "body": body}
    response = requests.post(url, headers=headers, json=data)
    return response.json()


# Create a function to get details of a specific pull request.
def get_pull_request(token: str, owner: str, repo: str, pull_number: int) -> Dict[str, Any]:
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}"
    headers = authenticate(token)
    response = requests.get(url, headers=headers)
    return response.json()


# Create a function to update a pull request's details.
def update_pull_request(
    token: str,
    owner: str,
    repo: str,
    pull_number: int,
    title: Optional[str] = None,
    body: Optional[str] = None,
    state: Optional[str] = None,
) -> Dict[str, Any]:
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}"
    headers = authenticate(token)
    data = {"title": title, "body": body, "state": state}
    response = requests.patch(url, headers=headers, json=data)
    return response.json()


# Create a function to close a pull request.
def close_pull_request(token: str, owner: str, repo: str, pull_number: int) -> Dict[str, Any]:
    return update_pull_request(token, owner, repo, pull_number, state="closed")


# Create a function to comment on a pull request.
def comment_pull_request(token: str, owner: str, repo: str, pull_number: int, body: str) -> Dict[str, Any]:
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pull_number}/comments"
    headers = authenticate(token)
    data = {"body": body}
    response = requests.post(url, headers=headers, json=data)
    return response.json()


# Create a function to approve a pull request.
# Note: GitHub API does not provide a direct way to approve a pull request. You can only create a review comment with an "APPROVE" event.
def approve_pull_request(
    token: str, owner: str, repo: str, pull_number: int, body: Optional[str] = None
) -> Dict[str, Any]:
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/reviews"
    headers = authenticate(token)
    data = {"body": body, "event": "APPROVE"}
    response = requests.post(url, headers=headers, json=data)
    return response.json()


# Create a function to request changes on a pull request.
# Note: GitHub API does not provide a direct way to request changes on a pull request. You can only create a review comment with a "REQUEST_CHANGES" event.
def request_changes_pull_request(token: str, owner: str, repo: str, pull_number: int, body: str) -> Dict[str, Any]:
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/reviews"
    headers = authenticate(token)
    data = {"body": body, "event": "REQUEST_CHANGES"}
    response = requests.post(url, headers=headers, json=data)
    return response.json()


# Create a function to get details of a specific commit.
def get_commit(token: str, owner: str, repo: str, sha: str) -> Dict[str, Any]:
    url = f"https://api.github.com/repos/{owner}/{repo}/commits/{sha}"
    headers = authenticate(token)
    response = requests.get(url, headers=headers)
    return response.json()


# Create a function to compare two commits.
def compare_commits(token: str, owner: str, repo: str, base: str, head: str) -> Dict[str, Any]:
    url = f"https://api.github.com/repos/{owner}/{repo}/compare/{base}...{head}"
    headers = authenticate(token)
    response = requests.get(url, headers=headers)
    return response.json()


# Create a function to create a new branch.
# Note: GitHub API does not provide a direct way to create a branch. You can only create a reference which can be used as a branch.
def create_branch(token: str, owner: str, repo: str, branch: str, sha: str) -> Dict[str, Any]:
    url = f"https://api.github.com/repos/{owner}/{repo}/git/refs"
    headers = authenticate(token)
    data = {"ref": f"refs/heads/{branch}", "sha": sha}
    response = requests.post(url, headers=headers, json=data)
    return response.json()


# Create a function to get details of a specific branch.
def get_branch(token: str, owner: str, repo: str, branch: str) -> Dict[str, Any]:
    url = f"https://api.github.com/repos/{owner}/{repo}/branches/{branch}"
    headers = authenticate(token)
    response = requests.get(url, headers=headers)
    return response.json()


# Create a function to update a branch's details.
# Note: GitHub API does not provide a direct way to update a branch. You can only update a branch's protection rules.
def update_branch_protection(
    token: str,
    owner: str,
    repo: str,
    branch: str,
    enforce_admins: Optional[bool] = None,
    required_status_checks: Optional[Dict[str, Any]] = None,
    required_pull_request_reviews: Optional[Dict[str, Any]] = None,
    restrictions: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    url = f"https://api.github.com/repos/{owner}/{repo}/branches/{branch}/protection"
    headers = authenticate(token)
    data = {
        "enforce_admins": enforce_admins,
        "required_status_checks": required_status_checks,
        "required_pull_request_reviews": required_pull_request_reviews,
        "restrictions": restrictions,
    }
    response = requests.put(url, headers=headers, json=data)
    return response.json()


# Create a function to delete a branch.
# Note: GitHub API does not provide a direct way to delete a branch. You can only delete a reference which can be used as a branch.
def delete_branch(token: str, owner: str, repo: str, branch: str) -> int:
    url = f"https://api.github.com/repos/{owner}/{repo}/git/refs/heads/{branch}"
    headers = authenticate(token)
    response = requests.delete(url, headers=headers)
    return response.status_code  # Returns 204 on success


# Create a function to fork a repository.
def fork_repository(token: str, owner: str, repo: str) -> Dict[str, Any]:
    url = f"https://api.github.com/repos/{owner}/{repo}/forks"
    headers = authenticate(token)
    response = requests.post(url, headers=headers)
    return response.json()


# Create a function to list all forks of a repository.
def list_forks(token: str, owner: str, repo: str) -> List[Dict[str, Any]]:
    url = f"https://api.github.com/repos/{owner}/{repo}/forks"
    headers = authenticate(token)
    response = requests.get(url, headers=headers)
    return response.json()


# Create a function to star a repository.
def star_repository(token: str, owner: str, repo: str) -> int:
    url = f"https://api.github.com/user/starred/{owner}/{repo}"
    headers = authenticate(token)
    response = requests.put(url, headers=headers)
    return response.status_code  # Returns 204 on success


# Create a function to unstar a repository.
def unstar_repository(token: str, owner: str, repo: str) -> int:
    url = f"https://api.github.com/user/starred/{owner}/{repo}"
    headers = authenticate(token)
    response = requests.delete(url, headers=headers)
    return response.status_code  # Returns 204 on success


# Create a function to list all starred repositories of a user.
def list_starred_repositories(token: str) -> List[Dict[str, Any]]:
    url = "https://api.github.com/user/starred"
    headers = authenticate(token)
    response = requests.get(url, headers=headers)
    return response.json()


# Create a function to watch a repository.
def watch_repository(token: str, owner: str, repo: str) -> Dict[str, Any]:
    url = f"https://api.github.com/repos/{owner}/{repo}/subscription"
    headers = authenticate(token)
    data = {"subscribed": True}
    response = requests.put(url, headers=headers, json=data)
    return response.json()


# Create a function to unwatch a repository.
def unwatch_repository(token: str, owner: str, repo: str) -> int:
    url = f"https://api.github.com/repos/{owner}/{repo}/subscription"
    headers = authenticate(token)
    response = requests.delete(url, headers=headers)
    return response.status_code  # Returns 204 on success


# Create a function to list all watched repositories of a user.
def list_watched_repositories(token: str) -> List[Dict[str, Any]]:
    url = "https://api.github.com/user/subscriptions"
    headers = authenticate(token)
    response = requests.get(url, headers=headers)
    return response.json()


# Gist Management


# Create a function to create a new gist.
def create_gist(token: str, files: Dict[str, Dict[str, str]], description: str, public: bool) -> Dict[str, Any]:
    url = "https://api.github.com/gists"
    headers = authenticate(token)
    data = {"files": files, "description": description, "public": public}
    response = requests.post(url, headers=headers, json=data)
    return response.json()


# Create a function to get details of a specific gist.
def get_gist(token: str, gist_id: str) -> Dict[str, Any]:
    url = f"https://api.github.com/gists/{gist_id}"
    headers = authenticate(token)
    response = requests.get(url, headers=headers)
    return response.json()


# Create a function to update a gist's details.
def update_gist(token: str, gist_id: str, files: Dict[str, Dict[str, str]], description: str) -> Dict[str, Any]:
    url = f"https://api.github.com/gists/{gist_id}"
    headers = authenticate(token)
    data = {"files": files, "description": description}
    response = requests.patch(url, headers=headers, json=data)
    return response.json()


# Create a function to delete a gist.
def delete_gist(token: str, gist_id: str) -> int:
    url = f"https://api.github.com/gists/{gist_id}"
    headers = authenticate(token)
    response = requests.delete(url, headers=headers)
    return response.status_code  # Returns 204 on success


# Team Management


# Create a function to create a new team within an organization.
def create_team(token: str, org: str, name: str, description: str, privacy: str) -> Dict[str, Any]:
    url = f"https://api.github.com/orgs/{org}/teams"
    headers = authenticate(token)
    data = {"name": name, "description": description, "privacy": privacy}
    response = requests.post(url, headers=headers, json=data)
    return response.json()


# Create a function to get details of a specific team.
def get_team(token: str, team_id: str) -> Dict[str, Any]:
    url = f"https://api.github.com/teams/{team_id}"
    headers = authenticate(token)
    response = requests.get(url, headers=headers)
    return response.json()


# Create a function to update a team's details.
def update_team(token: str, team_id: str, name: str, description: str, privacy: str) -> Dict[str, Any]:
    url = f"https://api.github.com/teams/{team_id}"
    headers = authenticate(token)
    data = {"name": name, "description": description, "privacy": privacy}
    response = requests.patch(url, headers=headers, json=data)
    return response.json()


# Create a function to delete a team.
def delete_team(token: str, team_id: str) -> int:
    url = f"https://api.github.com/teams/{team_id}"
    headers = authenticate(token)
    response = requests.delete(url, headers=headers)
    return response.status_code  # Returns 204 on success


# Member Management


# Create a function to add a member to an organization or team.
def add_member_to_org(token: str, org: str, username: str) -> Dict[str, Any]:
    url = f"https://api.github.com/orgs/{org}/memberships/{username}"
    headers = authenticate(token)
    response = requests.put(url, headers=headers)
    return response.json()


def add_member_to_team(token: str, team_id: str, username: str) -> Dict[str, Any]:
    url = f"https://api.github.com/teams/{team_id}/memberships/{username}"
    headers = authenticate(token)
    response = requests.put(url, headers=headers)
    return response.json()


# Create a function to remove a member from an organization or team.
def remove_member_from_org(token: str, org: str, username: str) -> int:
    url = f"https://api.github.com/orgs/{org}/memberships/{username}"
    headers = authenticate(token)
    response = requests.delete(url, headers=headers)
    return response.status_code  # Returns 204 on success


def remove_member_from_team(token: str, team_id: str, username: str) -> int:
    url = f"https://api.github.com/teams/{team_id}/memberships/{username}"
    headers = authenticate(token)
    response = requests.delete(url, headers=headers)
    return response.status_code  # Returns 204 on success


# Create a function to list all members of an organization or team.
def list_org_members(token: str, org: str) -> List[Dict[str, Any]]:
    url = f"https://api.github.com/orgs/{org}/members"
    headers = authenticate(token)
    response = requests.get(url, headers=headers)
    return response.json()


def list_team_members(token: str, team_id: str) -> List[Dict[str, Any]]:
    url = f"https://api.github.com/teams/{team_id}/members"
    headers = authenticate(token)
    response = requests.get(url, headers=headers)
    return response.json()


# Webhook Management


# Create a function to create a new webhook.
def create_webhook(token: str, repo: str, config: Dict[str, Any], events: List[str], active: bool) -> Dict[str, Any]:
    url = f"https://api.github.com/repos/{repo}/hooks"
    headers = authenticate(token)
    data = {"config": config, "events": events, "active": active}
    response = requests.post(url, headers=headers, json=data)
    return response.json()


# Create a function to get details of a specific webhook.
def get_webhook(token: str, repo: str, hook_id: str) -> Dict[str, Any]:
    url = f"https://api.github.com/repos/{repo}/hooks/{hook_id}"
    headers = authenticate(token)
    response = requests.get(url, headers=headers)
    return response.json()


# Create a function to update a webhook's details.
def update_webhook(
    token: str, repo: str, hook_id: str, config: Dict[str, Any], events: List[str], active: bool
) -> Dict[str, Any]:
    url = f"https://api.github.com/repos/{repo}/hooks/{hook_id}"
    headers = authenticate(token)
    data = {"config": config, "events": events, "active": active}
    response = requests.patch(url, headers=headers, json=data)
    return response.json()


# Create a function to delete a webhook.
def delete_webhook(token: str, repo: str, hook_id: str) -> int:
    url = f"https://api.github.com/repos/{repo}/hooks/{hook_id}"
    headers = authenticate(token)
    response = requests.delete(url, headers=headers)
    return response.status_code  # Returns 204 on success


# Release Management


# Create a function to create a new release.
def create_release(
    token: str, repo: str, tag_name: str, target_commitish: str, name: str, body: str, draft: bool, prerelease: bool
) -> Dict[str, Any]:
    url = f"https://api.github.com/repos/{repo}/releases"
    headers = authenticate(token)
    data = {
        "tag_name": tag_name,
        "target_commitish": target_commitish,
        "name": name,
        "body": body,
        "draft": draft,
        "prerelease": prerelease,
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()


# Create a function to get details of a specific release.
def get_release(token: str, repo: str, release_id: str) -> Dict[str, Any]:
    url = f"https://api.github.com/repos/{repo}/releases/{release_id}"
    headers = authenticate(token)
    response = requests.get(url, headers=headers)
    return response.json()


# Create a function to update a release's details.
def update_release(
    token: str,
    repo: str,
    release_id: str,
    tag_name: str,
    target_commitish: str,
    name: str,
    body: str,
    draft: bool,
    prerelease: bool,
) -> Dict[str, Any]:
    url = f"https://api.github.com/repos/{repo}/releases/{release_id}"
    headers = authenticate(token)
    data = {
        "tag_name": tag_name,
        "target_commitish": target_commitish,
        "name": name,
        "body": body,
        "draft": draft,
        "prerelease": prerelease,
    }
    response = requests.patch(url, headers=headers, json=data)
    return response.json()


# Create a function to delete a release.
def delete_release(token: str, repo: str, release_id: str) -> int:
    url = f"https://api.github.com/repos/{repo}/releases/{release_id}"
    headers = authenticate(token)
    response = requests.delete(url, headers=headers)
    return response.status_code  # Returns 204 on success


# Label Management


# Create a function to create a new label.
def create_label(token: str, repo: str, name: str, color: str, description: Optional[str] = None) -> Dict[str, Any]:
    url = f"https://api.github.com/repos/{repo}/labels"
    headers = authenticate(token)
    data = {"name": name, "color": color, "description": description}
    response = requests.post(url, headers=headers, json=data)
    return response.json()


# Create a function to get details of a specific label.
def get_label(token: str, repo: str, name: str) -> Dict[str, Any]:
    url = f"https://api.github.com/repos/{repo}/labels/{name}"
    headers = authenticate(token)
    response = requests.get(url, headers=headers)
    return response.json()


# Create a function to update a label's details.
def update_label(
    token: str, repo: str, name: str, new_name: str, color: str, description: Optional[str] = None
) -> Dict[str, Any]:
    url = f"https://api.github.com/repos/{repo}/labels/{name}"
    headers = authenticate(token)
    data = {"name": new_name, "color": color, "description": description}
    response = requests.patch(url, headers=headers, json=data)
    return response.json()


# Create a function to delete a label.
def delete_label(token: str, repo: str, name: str) -> int:
    url = f"https://api.github.com/repos/{repo}/labels/{name}"
    headers = authenticate(token)
    response = requests.delete(url, headers=headers)
    return response.status_code  # Returns 204 on success


# Milestone Management


# Create a function to create a new milestone.
def create_milestone(
    token: str, repo: str, title: str, state: str, description: Optional[str] = None, due_on: Optional[str] = None
) -> Dict[str, Any]:
    url = f"https://api.github.com/repos/{repo}/milestones"
    headers = authenticate(token)
    data = {"title": title, "state": state, "description": description, "due_on": due_on}
    response = requests.post(url, headers=headers, json=data)
    return response.json()


# Create a function to get details of a specific milestone.
def get_milestone(token: str, repo: str, number: int) -> Dict[str, Any]:
    url = f"https://api.github.com/repos/{repo}/milestones/{number}"
    headers = authenticate(token)
    response = requests.get(url, headers=headers)
    return response.json()


# Create a function to update a milestone's details.
def update_milestone(
    token: str,
    repo: str,
    number: int,
    title: str,
    state: str,
    description: Optional[str] = None,
    due_on: Optional[str] = None,
) -> Dict[str, Any]:
    url = f"https://api.github.com/repos/{repo}/milestones/{number}"
    headers = authenticate(token)
    data = {"title": title, "state": state, "description": description, "due_on": due_on}
    response = requests.patch(url, headers=headers, json=data)
    return response.json()


# Create a function to delete a milestone.
def delete_milestone(token: str, repo: str, number: int) -> int:
    url = f"https://api.github.com/repos/{repo}/milestones/{number}"
    headers = authenticate(token)
    response = requests.delete(url, headers=headers)
    return response.status_code  # Returns 204 on success


# Project Management


# Create a function to create a new project.
def create_project(token: str, org: str, name: str, body: Optional[str] = None) -> Dict[str, Any]:
    url = f"https://api.github.com/orgs/{org}/projects"
    headers = authenticate(token)
    headers["Accept"] = "application/vnd.github.inertia-preview+json"
    data = {"name": name, "body": body}
    response = requests.post(url, headers=headers, json=data)
    return response.json()


# Create a function to get details of a specific project.
def get_project(token: str, project_id: int) -> Dict[str, Any]:
    url = f"https://api.github.com/projects/{project_id}"
    headers = authenticate(token)
    headers["Accept"] = "application/vnd.github.inertia-preview+json"
    response = requests.get(url, headers=headers)
    return response.json()


# Create a function to update a project's details.
def update_project(
    token: str, project_id: int, name: str, body: Optional[str] = None, state: Optional[str] = None
) -> Dict[str, Any]:
    url = f"https://api.github.com/projects/{project_id}"
    headers = authenticate(token)
    headers["Accept"] = "application/vnd.github.inertia-preview+json"
    data = {"name": name, "body": body, "state": state}
    response = requests.patch(url, headers=headers, json=data)
    return response.json()


# Create a function to delete a project.
def delete_project(token: str, project_id: int) -> int:
    url = f"https://api.github.com/projects/{project_id}"
    headers = authenticate(token)
    headers["Accept"] = "application/vnd.github.inertia-preview+json"
    response = requests.delete(url, headers=headers)
    return response.status_code  # Returns 204 on success


def get_license(token: str, owner: str, repo: str) -> Dict[str, Any]:
    url = f"https://api.github.com/repos/{owner}/{repo}/license"
    headers = authenticate(token)
    response = requests.get(url, headers=headers)
    return response.json()


def get_traffic(token: str, owner: str, repo: str) -> Dict[str, Any]:
    url = f"https://api.github.com/repos/{owner}/{repo}/traffic/views"
    headers = authenticate(token)
    response = requests.get(url, headers=headers)
    return response.json()


def list_workflows(token: str, owner: str, repo: str) -> Dict[str, Any]:
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows"
    headers = authenticate(token)
    response = requests.get(url, headers=headers)
    return response.json()


def list_packages(token: str, owner: str, repo: str) -> Dict[str, Any]:
    url = f"https://api.github.com/repos/{owner}/{repo}/packages"
    headers = authenticate(token)
    response = requests.get(url, headers=headers)
    return response.json()


def list_security_advisories(token: str, owner: str, repo: str) -> Dict[str, Any]:
    url = f"https://api.github.com/repos/{owner}/{repo}/security/advisories"
    headers = authenticate(token)
    response = requests.get(url, headers=headers)
    return response.json()


def list_sponsors(token: str, username: str) -> Dict[str, Any]:
    url = f"https://api.github.com/users/{username}/sponsorships"
    headers = authenticate(token)
    response = requests.get(url, headers=headers)
    return response.json()
