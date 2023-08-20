import pytest
from pydantic import ValidationError

from geniusrise.cli.schema import Geniusfile

# Correct YAML data for testing
correct_yaml_data = {
    "version": "1",
    "spouts": {
        "github-batch": {
            "name": "GithubDump",
            "method": "fetch_pull_requests",
            "args": {"repo_name": "zpqrtbnk/test-repo", "github_access_token": "test"},
            "output": {
                "type": "batch",
                "args": {"bucket": "my-bucket", "folder": "my-s3-folder"},
            },
            "state": {"type": "in_memory"},
            "deploy": {
                "type": "k8s",
                "args": {
                    "name": "github-dump",
                    "namespace": "geniusrise",
                    "image": "geniusrise/geniusrise",
                    "replicas": 1,
                },
            },
        }
    },
    "bolts": {},
}

# Incorrect YAML data for testing
incorrect_yaml_data = {
    "version": "1",
    "spouts": {
        "github-batch": {
            "name": "GithubDump",
            "method": "fetch_pull_requests",
            "args": {"repo_name": "zpqrtbnk/test-repo"},
            "output": {"type": "batch", "args": {"bucket": "my-bucket"}},
            "state": {"type": "in_memory"},
            "deploy": {
                "type": "k8s",
                "args": {
                    "name": "github-dump",
                    "namespace": "geniusrise",
                    "image": "geniusrise/geniusrise",
                },
            },
        }
    },
    "bolts": {},
}

# Data with missing required fields
missing_fields_data = {
    "version": "1",
    "spouts": {
        "github-batch": {
            "name": "GithubDump",
            "method": "fetch_pull_requests",
            "output": {
                "type": "batch",
                "args": {"bucket": "my-bucket", "folder": "my-s3-folder"},
            },
            "state": {"type": "in_memory"},
        }
    },
    "bolts": {},
}

# Data with invalid field values
invalid_values_data = {
    "version": "1",
    "spouts": {
        "github-batch": {
            "name": "GithubDump",
            "method": "fetch_pull_requests",
            "args": {"repo_name": "zpqrtbnk/test-repo", "github_access_token": "test"},
            "output": {
                "type": "invalid_type",
                "args": {"bucket": "my-bucket", "folder": "my-s3-folder"},
            },
            "state": {"type": "in_memory"},
            "deploy": {
                "type": "k8s",
                "args": {
                    "name": "github-dump",
                    "namespace": "geniusrise",
                    "image": "geniusrise/geniusrise",
                    "replicas": 1,
                },
            },
        }
    },
    "bolts": {},
}

# Data with extra fields
extra_fields_data = {
    "version": "1",
    "spouts": {
        "github-batch": {
            "name": "GithubDump",
            "method": "fetch_pull_requests",
            "args": {
                "repo_name": "zpqrtbnk/test-repo",
                "github_access_token": "test",
                "extra_field": "extra_value",
            },
            "output": {
                "type": "batch",
                "args": {"bucket": "my-bucket", "folder": "my-s3-folder"},
            },
            "state": {"type": "in_memory"},
            "deploy": {
                "type": "k8s",
                "args": {
                    "name": "github-dump",
                    "namespace": "geniusrise",
                    "image": "geniusrise/geniusrise",
                    "replicas": 1,
                },
            },
        }
    },
    "bolts": {},
}


def test_correct_yaml_validation():
    """Test that the correct YAML data is validated without errors."""
    geniusfile = Geniusfile(**correct_yaml_data)
    assert geniusfile.version == "1"
    assert "github-batch" in geniusfile.spouts


def test_incorrect_yaml_validation():
    """Test that the incorrect YAML data raises a validation error."""
    with pytest.raises(ValidationError):
        Geniusfile(**incorrect_yaml_data)


def test_missing_fields_validation():
    """Test that the validation correctly identifies missing required fields."""
    with pytest.raises(ValidationError):
        Geniusfile(**missing_fields_data)


def test_invalid_values_validation():
    """Test that the validation correctly identifies invalid values for fields."""
    with pytest.raises(ValidationError):
        Geniusfile(**invalid_values_data)


def test_extra_fields_validation():
    """Test that the validation correctly handles extra fields."""
    geniusfile = Geniusfile(**extra_fields_data)
    assert geniusfile.spouts["github-batch"].args.extra_field == "extra_value"


def test_different_state_types_validation():
    """Test that the validation correctly identifies missing fields for different state types."""
    data = correct_yaml_data.copy()
    data["spouts"]["github-batch"]["state"]["type"] = "redis"

    with pytest.raises(ValidationError):
        Geniusfile(**data)
