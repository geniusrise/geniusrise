import pytest
import os
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
def test_batch_input_config_copy_from_s3(batch_input_config):
    batch_input_config.copy_from_s3()

    # Check that the files were copied to the input folder
    # Note: This assumes that there are files in the S3_FOLDER of the BUCKET
    print(batch_input_config.input_folder)
    assert list(os.listdir(batch_input_config.input_folder + "/")) == [S3_FOLDER]  # This should not be empty
