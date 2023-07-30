# geniusrise
# Copyright (C) 2023  geniusrise.ai
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# from geniusrise.data_sources.code_hosting.bitbucket import BitbucketDataFetcher


# def test_fetch_code():
#     fetcher = BitbucketDataFetcher(repo_name="team-test", project_key="monoidspace", username="monoidspace-admin")
#     code_files = fetcher.fetch_code()

# assert code_files[0][:10] == "File Name:"


# def test_fetch_pull_requests():
#     fetcher = BitbucketDataFetcher(repo_name="team-test", project_key="monoidspace", username="monoidspace-admin")
#     pull_requests = fetcher.fetch_pull_requests()

#     assert pull_requests[0][:10] == "Title: "


# def test_fetch_commits():
#     fetcher = BitbucketDataFetcher(repo_name="team-test", project_key="monoidspace", username="monoidspace-admin")
#     commits = fetcher.fetch_commits()

#     assert commits[0][:10] == "Commit Mes"


# def test_fetch_issues():
#     fetcher = BitbucketDataFetcher(repo_name="team-test", project_key="monoidspace", username="monoidspace-admin")
#     issues = fetcher.fetch_issues()

#     assert issues[0][:10] == "Title: "


# def test_fetch_repo_details():
#     fetcher = BitbucketDataFetcher(repo_name="team-test", project_key="monoidspace", username="monoidspace-admin")
#     repo_details = fetcher.fetch_repo_details()

#     assert repo_details[0][:10] == "Repo Name:"


# def test_fetch_releases():
#     fetcher = BitbucketDataFetcher(repo_name="team-test", project_key="monoidspace", username="monoidspace-admin")
#     releases = fetcher.fetch_releases()

#     assert releases[0][:10] == "Release Na"
