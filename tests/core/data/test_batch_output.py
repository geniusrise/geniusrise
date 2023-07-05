import pytest
import os
import boto3
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
