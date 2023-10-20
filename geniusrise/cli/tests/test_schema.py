# 🧠 Geniusrise
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

import copy

import pytest
from pydantic import ValidationError

from geniusrise.cli.schema import Geniusfile

# Base YAML data for testing
base_yaml_data = {
    "version": "1",
    "spouts": {
        "github-batch": {
            "name": "GithubDump",
            "method": "fetch_pull_requests",
            "args": {"repo_name": "zpqrtbnk/test-repo", "github_access_token": "test"},
            "output": {
                "type": "batch",
                "args": {"bucket": "geniusrise-test", "folder": "my-s3-folder"},
            },
            "state": {"type": "none", "args": {}},
            "deploy": {
                "type": "k8s",
                "args": {
                    "kind": "deployment",
                    "context_name": "arn:aws:eks:us-east-1:143601010266:cluster/geniusrise-dev",
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
    geniusfile = Geniusfile(**base_yaml_data)
    assert geniusfile.version == "1"
    assert "github-batch" in geniusfile.spouts


def test_invalid_version():
    """Test that an invalid version raises a validation error."""
    data = copy.deepcopy(base_yaml_data)
    data["version"] = "2"
    with pytest.raises(ValidationError):
        Geniusfile(**data)


def test_missing_required_fields():
    """Test that missing required fields raises a validation error."""
    data = copy.deepcopy(base_yaml_data)
    del data["spouts"]["github-batch"]["name"]
    with pytest.raises(ValidationError):
        Geniusfile(**data)


def test_invalid_state_type():
    """Test that an invalid state type raises a validation error."""
    data = copy.deepcopy(base_yaml_data)
    data["spouts"]["github-batch"]["state"]["type"] = "invalid_type"
    with pytest.raises(ValidationError):
        Geniusfile(**data)


def test_invalid_output_type():
    """Test that an invalid output type raises a validation error."""
    data = copy.deepcopy(base_yaml_data)
    data["spouts"]["github-batch"]["output"]["type"] = "invalid_type"
    with pytest.raises(ValidationError):
        Geniusfile(**data)


def test_extra_fields():
    """Test that extra fields are allowed and do not raise a validation error."""
    data = copy.deepcopy(base_yaml_data)
    data["spouts"]["github-batch"]["args"]["extra_field"] = "extra_value"
    geniusfile = Geniusfile(**data)
    assert geniusfile.spouts["github-batch"].args.extra_field == "extra_value"


def test_invalid_deploy_type():
    """Test that an invalid deploy type raises a validation error."""
    data = copy.deepcopy(base_yaml_data)
    data["spouts"]["github-batch"]["deploy"]["type"] = "invalid_type"
    with pytest.raises(ValidationError):
        Geniusfile(**data)


def test_missing_state_args_for_redis():
    """Test that missing required fields for Redis state type raises a validation error."""
    data = copy.deepcopy(base_yaml_data)
    data["spouts"]["github-batch"]["state"]["type"] = "redis"
    with pytest.raises(ValidationError):
        Geniusfile(**data)


def test_missing_output_args_for_streaming():
    """Test that missing required fields for streaming output type raises a validation error."""
    data = copy.deepcopy(base_yaml_data)
    data["spouts"]["github-batch"]["output"]["type"] = "streaming"
    with pytest.raises(ValidationError):
        Geniusfile(**data)


def test_missing_deploy_args_for_ecs():
    """Test that missing required fields for ECS deploy type raises a validation error."""
    data = copy.deepcopy(base_yaml_data)
    data["spouts"]["github-batch"]["deploy"]["type"] = "ecs"
    with pytest.raises(ValidationError):
        Geniusfile(**data)
