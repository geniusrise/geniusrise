# Github Spouts

This repository contains two classes, `GithubBatchSpout` and `GithubDump`, which
are designed to fetch data from Github repositories and save them in a
structured format. These classes are part of a larger data pipeline and are used
to fetch data from Github for further processing or analysis.

## GithubBatchSpout

`GithubBatchSpout` is a class that fetches data from a Github repository in
batches. It fetches data such as commits, pull requests, issues, and releases.
The fetched data is then saved in a structured format for further processing or
analysis.

The class takes the following parameters:

- `output_config`: An instance of `BatchOutputConfig` that specifies the
  configuration for output.
- `repo_name`: The name of the Github repository to fetch data from.
- `state_manager`: An instance of `InMemoryStateManager` that manages the state
  of the data fetching process. This is optional and defaults to
  `InMemoryStateManager()`.
- `github_access_token`: The Github access token to use for fetching data. This
  is optional and defaults to `GITHUB_ACCESS_TOKEN`.

## GithubDump

`GithubDump` is a class that fetches all data from a Github repository and saves
it in a structured format. It fetches data such as commits, pull requests,
issues, releases, and repository details. The fetched data is then saved in a
structured format for further processing or analysis.

The class takes the following parameters:

- `output_config`: An instance of `BatchOutputConfig` that specifies the
  configuration for output.
- `repo_name`: The name of the Github repository to fetch data from.
- `state_manager`: An instance of `InMemoryStateManager` that manages the state
  of the data fetching process. This is optional and defaults to
  `InMemoryStateManager()`.
- `github_access_token`: The Github access token to use for fetching data. This
  is optional and defaults to `GITHUB_ACCESS_TOKEN`.

## Usage

To use these classes, you need to create an instance of the class and then call
the appropriate method to fetch the data you need. For example, to fetch all
commits from a repository, you would do the following:

```python
from geniusrise.core import BatchOutputConfig
from geniusrise.github import GithubBatchSpout

output_config = BatchOutputConfig(output_folder="output")
spout = GithubBatchSpout(output_config, "octocat/Hello-World")
spout.fetch_commits()
```

This will fetch all commits from the `octocat/Hello-World` repository and save
them in the `output` folder.

## Requirements

To use these classes, you need to have the following installed:

- Python 3.6 or later
- `PyGithub` library
- `requests` library

You also need to have a Github access token, which you can get by following the
instructions
[here](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token).

## Contributing

Contributions are welcome! Please feel free to submit a pull request.

## License

This project is licensed under the MIT License.
