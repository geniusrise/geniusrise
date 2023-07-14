import json
import os
from datetime import datetime

from .incremental import GithubIncremental
from geniusrise.core import BatchOutputConfig, InMemoryStateManager


def test_fetch_pull_requests(tmpdir):
    output_config = BatchOutputConfig(
        output_folder=str(tmpdir), bucket="geniusrise-test-bucket", s3_folder="csv_to_json-6t7lqqpj"
    )
    state_manager = InMemoryStateManager()
    fetcher = GithubIncremental(
        output_config=output_config, state_manager=state_manager, repo_name="zpqrtbnk/test-repo"
    )
    fetcher.fetch_pull_requests(start_date=datetime(2023, 1, 1), end_date=datetime(2023, 12, 31))
    # Check that the 5th pull request contains the word "fix"
    with open(f"{tmpdir}/pull_request_123.json") as f:
        pr_data = json.load(f)
    assert pr_data == {
        "number": 123,
        "title": "Add hello.txt",
        "body": "Add text document with hello message. Fixes #87 .",
        "comments": [],
        "diff": "diff --git a/hello.txt b/hello.txt\nnew file mode 100644\nindex 0000000000..273b45e905\n--- /dev/null\n+++ b/hello.txt\n@@ -0,0 +1 @@\n+Hello GitHub!\n\\ No newline at end of file\n",
        "patch": "From 31e1913bfd75844da882457c2ee1be6302b7e081 Mon Sep 17 00:00:00 2001\nFrom: bonzi9 <sanshams@gmail.com>\nDate: Wed, 26 Oct 2023 19:44:46 +0200\nSubject: [PATCH] Add hello.txt\n\nAdd text document with hello message\n---\n hello.txt | 1 +\n 1 file changed, 1 insertion(+)\n create mode 100644 hello.txt\n\ndiff --git a/hello.txt b/hello.txt\nnew file mode 100644\nindex 0000000000..273b45e905\n--- /dev/null\n+++ b/hello.txt\n@@ -0,0 +1 @@\n+Hello GitHub!\n\\ No newline at end of file\n",
    }


def test_fetch_commits(tmpdir):
    output_config = BatchOutputConfig(
        output_folder=str(tmpdir), bucket="geniusrise-test-bucket", s3_folder="csv_to_json-6t7lqqpj"
    )
    state_manager = InMemoryStateManager()
    fetcher = GithubIncremental(
        output_config=output_config, state_manager=state_manager, repo_name="zpqrtbnk/test-repo"
    )
    fetcher.fetch_commits(start_date=datetime(2023, 1, 1), end_date=datetime(2023, 12, 31))
    # Check that the 10th commit message contains the word "update"
    with open(f"{tmpdir}/commit_21c2a100246d498732557c67302bad1dd3c3c8d0.json") as f:
        commit_data = json.load(f)
    assert commit_data == {
        "sha": "21c2a100246d498732557c67302bad1dd3c3c8d0",
        "message": "wflow",
        "author": "Stephan",
        "date": "2023-12-02T13:15:54",
        "files_changed": [".github/workflows/pull-request-target.yml"],
        "diff": "diff --git a/.github/workflows/pull-request-target.yml b/.github/workflows/pull-request-target.yml\nindex c5975f35ad..d1f1e181bf 100644\n--- a/.github/workflows/pull-request-target.yml\n+++ b/.github/workflows/pull-request-target.yml\n@@ -44,7 +44,7 @@ jobs:\n       - name: Report\n         shell: bash\n         run: |\n-          git l | head -n 12\n+          git log --graph --pretty=format':%h%d %s %an, %ar' | head -n 12\n \n   build-pr-call:\n \n",
        "patch": "From 21c2a100246d498732557c67302bad1dd3c3c8d0 Mon Sep 17 00:00:00 2001\nFrom: Stephan <stephane.gay@hazelcast.com>\nDate: Fri, 2 Dec 2023 14:15:54 +0100\nSubject: [PATCH] wflow\n\n---\n .github/workflows/pull-request-target.yml | 2 +-\n 1 file changed, 1 insertion(+), 1 deletion(-)\n\ndiff --git a/.github/workflows/pull-request-target.yml b/.github/workflows/pull-request-target.yml\nindex c5975f35ad..d1f1e181bf 100644\n--- a/.github/workflows/pull-request-target.yml\n+++ b/.github/workflows/pull-request-target.yml\n@@ -44,7 +44,7 @@ jobs:\n       - name: Report\n         shell: bash\n         run: |\n-          git l | head -n 12\n+          git log --graph --pretty=format':%h%d %s %an, %ar' | head -n 12\n \n   build-pr-call:\n \n",
    }


def test_fetch_issues(tmpdir):
    output_config = BatchOutputConfig(
        output_folder=str(tmpdir), bucket="geniusrise-test-bucket", s3_folder="csv_to_json-6t7lqqpj"
    )
    fetcher = GithubIncremental(output_config, InMemoryStateManager(), "zpqrtbnk/test-repo")
    fetcher.fetch_issues(start_date=datetime(2023, 1, 1), end_date=datetime(2023, 12, 31))
    # Check that the 3rd issue title contains the word "error"
    with open(f"{tmpdir}/issue_104.json") as f:
        issue_data = json.load(f)
    assert issue_data == {
        "number": 104,
        "title": "update readme",
        "body": None,
        "comments": [
            "Hey,\r\nThanks for this test PR. Let's pretend I don't merge it, OK?\r\nNo bad feelings ;)\r\nPS: if you *really* wanted to test something specific, let me know"
        ],
        "state": "closed",
    }


def test_fetch_releases(tmpdir):
    output_config = BatchOutputConfig(
        output_folder=str(tmpdir), bucket="geniusrise-test-bucket", s3_folder="csv_to_json-6t7lqqpj"
    )
    state_manager = InMemoryStateManager()
    fetcher = GithubIncremental(
        output_config=output_config, state_manager=state_manager, repo_name="zpqrtbnk/test-repo"
    )
    fetcher.fetch_releases(start_date=datetime(2022, 1, 1), end_date=datetime(2022, 12, 31))
    # Check that the 1st release tag name is "v2.26.0"
    with open(f"{tmpdir}/release_v4.5.6.json") as f:
        release_data = json.load(f)
    assert release_data == {
        "tag_name": "v4.5.6",
        "name": "Test release tag",
        "body": "Meh",
        "published_at": "2021-12-10T14:39:08",
    }


def test_fetch_repo_details(tmpdir):
    output_config = BatchOutputConfig(
        output_folder=str(tmpdir), bucket="geniusrise-test-bucket", s3_folder="csv_to_json-6t7lqqpj"
    )
    fetcher = GithubIncremental(output_config, InMemoryStateManager(), "zpqrtbnk/test-repo", tmpdir)
    fetcher.fetch_repo_details()
    # Check that the repository name is "requests"
    with open(f"{tmpdir}/repo_details.json") as f:
        repo_data = json.load(f)
    assert repo_data == {
        "name": "test-repo",
        "description": "Test Repository",
        "contributors": ["zpqrtbnk", "erictho", "M0stafa-Fawzy", "benyanke", "bonzi9"],
        "readme": '# A Git(Hub) Test Repository\n\nHey! This is my personal Git(Hub) Test Repository where I experiment with Git and GitHub. \n\nIf you are new to Git and GitHub and found this repository through Google: feel free to clone the repository and experiment with it! You will not be able to push back to the repository, as it is *my* repository and I cannot let everybody push to it. The right way to do it on GitHub is: \n\n1. fork the repository in your own account, \n2. make changes and push them in a branch of your own fork, \n3. create a Pull Request in my repository. \n\nI will get notified, will review the changes that you propose, and eventually will either merge the changes, or reject them. This *may* take some time as I am not actively monitoring nor maintaining this repository, as you can guess, but I try to be helpful ;)\n\n> NOTE\n> If you want your PR to have a chance to get merged, please propose additions or changes to neutral files such as text files or small images. If you propose changes to the GitHub workflow files, to `.gitignore`, etc. they will quite probably be rejected.\n\nDon\'t expect to find anything meaningful nor useful in the repository. Also, I happen to force-push a reset of everything from time to time. This means that I reset all history, including changes that you may have submitted. In theory, noone ever does this to a repository. But hey, this is a *test* repository after all.\n\nThe rest of this README file is mostly random stuff.\n\nClone the repository with: `git clone https://github.com/zpqrtbnk/test-repo.git .`\n\nWe have test GitHUb pages (from the `gh-pages` branch) at: http://zpqrtbnk.github.io/test-repo/ \n\nWe have an image in the README (markdown)\n![Image](https://raw.github.com/zpqrtbnk/test-repo/master/wtf.jpg)\n\nWe have an image in the README (html)\n<img src="./wtf.jpg" />\n\nWe have an image in the README (more html)\n<p align="center" style="background:#000;padding:5px;color:#fff;font-size:150%;margin-bottom:64px">\n    <img src="./wtf.jpg" />\n    <span style="margin-left:48px;">wubble</span>\n</p>\n\n',
        "file_structure": [
            "Directory: .github\nContents: \nDirectory: actions\nContents: \nDirectory: test-action\nContents: \nFile: action.yml\nDirectory: dist\nContents: \nFile: index.js\nFile: index.js\nFile: package-lock.json\nFile: package.json\nDirectory: workflows.not\nContents: \nFile: assign-milestones.js\nFile: assign-milestones.yml\nFile: assign-to-project.yml\nFile: build-pr.yml\nFile: exp.yml\nFile: publish-release.js\nFile: publish-release.yml\nFile: rest-description.yml\nFile: symlink-test.yml\nFile: test-push.yml\nDirectory: workflows\nContents: \nFile: branch.yml\nFile: callme.yml\nFile: mmerge.yml\nFile: pull-request-target.yml\nFile: pull-request.yml\nFile: test-ssh.yml",
            "File: .gitignore",
            "File: README.md",
            "File: hello.txt",
            "File: wtf.jpg",
        ],
    }


def test_fetch_code(tmpdir):
    output_config = BatchOutputConfig(
        output_folder=str(tmpdir), bucket="geniusrise-test-bucket", s3_folder="csv_to_json-6t7lqqpj"
    )
    fetcher = GithubIncremental(output_config, InMemoryStateManager(), "zpqrtbnk/test-repo", tmpdir)
    fetcher.fetch_code()
    # Check that the repository was cloned by checking if the .git directory exists
    assert os.path.isdir(f"{tmpdir}/.git")
