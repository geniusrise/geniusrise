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

import os

import boto3
import pytest

from geniusrise.core.data import BatchInputConfig

# Define your S3 bucket and folder details as constants
BUCKET = "geniusrise-test-bucket"
S3_FOLDER = "csv_to_json-6t7lqqpj"


# Define a fixture for your BatchInputConfig
@pytest.fixture
def batch_input_config(tmpdir):
    yield BatchInputConfig(tmpdir, BUCKET, S3_FOLDER)


# Test that the BatchInputConfig can be initialized
def test_batch_input_config_init(batch_input_config):
    assert batch_input_config.input_folder is not None
    assert batch_input_config.bucket == BUCKET
    assert batch_input_config.s3_folder == S3_FOLDER


# Test that the BatchInputConfig can get the input folder
def test_batch_input_config_get(batch_input_config):
    assert batch_input_config.get() == batch_input_config.input_folder


# Test that the BatchInputConfig can copy files from the S3 bucket
def test_batch_input_config_copy_from_remote(batch_input_config):
    batch_input_config.copy_from_remote()

    # Check that the files were copied to the input folder
    # Note: This assumes that there are files in the S3_FOLDER of the BUCKET
    print(batch_input_config.input_folder)
    assert list(os.listdir(batch_input_config.input_folder + "/")) == [S3_FOLDER]  # This should not be empty


# Test that the BatchInputConfig can list files in the input folder
def test_batch_input_config_list_files(batch_input_config):
    # Create a test file in the input folder
    with open(os.path.join(batch_input_config.input_folder, "test_file.txt"), "w") as f:
        f.write("test")

    files = batch_input_config.list_files()
    assert len(files) == 1
    assert "test_file.txt" in files[0]


# Test that the BatchInputConfig can read a file from the input folder
def test_batch_input_config_read_file(batch_input_config):
    # Create a test file in the input folder
    with open(os.path.join(batch_input_config.input_folder, "test_file.txt"), "w") as f:
        f.write("test")

    contents = batch_input_config.read_file("test_file.txt")
    assert contents == "test"


# Test that the BatchInputConfig can delete a file from the input folder
def test_batch_input_config_delete_file(batch_input_config):
    # Create a test file in the input folder
    with open(os.path.join(batch_input_config.input_folder, "test_file.txt"), "w") as f:
        f.write("test")

    batch_input_config.delete_file("test_file.txt")
    assert not os.path.exists(os.path.join(batch_input_config.input_folder, "test_file.txt"))


# Test that the BatchInputConfig can copy a file to an S3 bucket
def test_batch_input_config_copy_to_remote(batch_input_config):
    # Create a test file in the input folder
    with open(os.path.join(batch_input_config.input_folder, "test_file.txt"), "w") as f:
        f.write("test")

    batch_input_config.copy_to_remote("test_file.txt", BUCKET, S3_FOLDER)

    # Check that the file was copied to the S3 bucket
    s3 = boto3.resource("s3")
    obj = s3.Object(BUCKET, os.path.join(S3_FOLDER, "test_file.txt"))
    assert obj.get()["Body"].read().decode("utf-8") == "test"

    # Clean up the file in the S3 bucket
    obj.delete()
