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

import json
import os

import boto3
import pytest

from geniusrise.core.data import BatchOutputConfig

# Define your S3 bucket and folder details as constants
BUCKET = "geniusrise-test-bucket"
S3_FOLDER = "csv_to_json-6t7lqqpj"


# Define a fixture for your BatchOutputConfig
@pytest.fixture
def batch_output_config(tmpdir):
    yield BatchOutputConfig(tmpdir, BUCKET, S3_FOLDER)


# Test that the BatchOutputConfig can be initialized
def test_batch_output_config_init(batch_output_config):
    assert batch_output_config.output_folder is not None


# Test that the BatchOutputConfig can save data to a file
def test_batch_output_config_save(batch_output_config):
    data = {"test": "data"}
    filename = "test_file.json"
    batch_output_config.save(data, filename)

    # Check that the file was created in the output folder
    assert os.path.isfile(os.path.join(batch_output_config.output_folder, filename))


# Test that the BatchOutputConfig can copy files to the S3 bucket
def test_batch_output_config_copy_to_remote(batch_output_config):
    # First, save a file to the output folder
    data = {"test": "data"}
    filename = "test_file.json"
    batch_output_config.save(data, filename)

    # Then, copy the file to the S3 bucket
    batch_output_config.copy_to_remote()

    # Check that the file was copied to the S3 bucket
    # Note: This assumes that you have a way to check the contents of the S3 bucket
    # You might need to use the boto3 library or the AWS CLI to do this
    assert file_exists_in_s3(BUCKET, os.path.join(S3_FOLDER, filename))


# Test that the BatchOutputConfig can flush the output folder to the S3 bucket
def test_batch_output_config_flush(batch_output_config):
    # First, save a file to the output folder
    data = {"test": "data"}
    filename = "test_file.json"
    batch_output_config.save(data, filename)

    # Then, flush the output folder to the S3 bucket
    batch_output_config.flush()

    # Check that the file was copied to the S3 bucket
    # Note: This assumes that you have a way to check the contents of the S3 bucket
    # You might need to use the boto3 library or the AWS CLI to do this
    assert file_exists_in_s3(BUCKET, os.path.join(S3_FOLDER, filename))


def file_exists_in_s3(bucket, key):
    """
    Check if a file exists in an S3 bucket.

    Args:
        bucket (str): The name of the S3 bucket.
        key (str): The key of the file in the S3 bucket.

    Returns:
        bool: True if the file exists, False otherwise.
    """
    s3 = boto3.resource("s3")
    try:
        s3.Object(bucket, key).load()
    except Exception as e:
        return False
    return True


# Test that the BatchOutputConfig can list files in the output folder
def test_batch_output_config_list_files(batch_output_config):
    # First, save a file to the output folder
    data = {"test": "data"}
    filename = "test_file.json"
    batch_output_config.save(data, filename)

    # Then, list the files in the output folder
    files = batch_output_config.list_files()

    # Check that the list contains the file that was saved
    assert os.path.join(batch_output_config.output_folder, filename) in files


# Test that the BatchOutputConfig can read a file from the output folder
def test_batch_output_config_read_file(batch_output_config):
    # First, save a file to the output folder
    data = {"test": "data"}
    filename = "test_file.json"
    batch_output_config.save(data, filename)

    # Then, read the file from the output folder
    contents = batch_output_config.read_file(filename)

    # Check that the contents of the file match the data that was saved
    assert json.loads(contents) == data


# Test that the BatchOutputConfig can delete a file from the output folder
def test_batch_output_config_delete_file(batch_output_config):
    # First, save a file to the output folder
    data = {"test": "data"}
    filename = "test_file.json"
    batch_output_config.save(data, filename)

    # Then, delete the file from the output folder
    batch_output_config.delete_file(filename)

    # Check that the file no longer exists in the output folder
    assert not os.path.isfile(os.path.join(batch_output_config.output_folder, filename))


# Test that the BatchOutputConfig can copy a specific file to the S3 bucket
def test_batch_output_config_copy_file_to_remote(batch_output_config):
    # First, save a file to the output folder
    data = {"test": "data"}
    filename = "test_file.json"
    batch_output_config.save(data, filename)

    # Then, copy the file to the S3 bucket
    batch_output_config.copy_file_to_remote(filename)

    # Check that the file was copied to the S3 bucket
    assert file_exists_in_s3(BUCKET, os.path.join(S3_FOLDER, filename))
