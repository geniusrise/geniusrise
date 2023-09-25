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
from pyspark.sql import SparkSession
from geniusrise.core.data.batch_input import BatchInput, FileNotExistError

# Define your S3 bucket and folder details as constants
BUCKET = "geniusrise-test-bucket"
S3_FOLDER = "whatever"

# Initialize Spark session for testing
spark = SparkSession.builder.master("local[1]").appName("GeniusRise").getOrCreate()


# Define a fixture for BatchInput
@pytest.fixture
def batch_input_config(tmpdir):
    yield BatchInput(str(tmpdir), BUCKET, S3_FOLDER)


# Test that the BatchInput can be initialized
def test_batch_input_config_init(batch_input_config):
    assert batch_input_config.input_folder is not None
    assert batch_input_config.bucket == BUCKET
    assert batch_input_config.s3_folder == S3_FOLDER


# Test that the BatchInput can get the input folder
def test_batch_input_config_get(batch_input_config):
    assert batch_input_config.get() == batch_input_config.input_folder


def test_batch_input_config_validate_file(batch_input_config):
    test_file = "test_file.txt"
    with open(os.path.join(batch_input_config.input_folder, test_file), "w") as f:
        f.write("test")
    assert batch_input_config._validate_file(test_file)  # Method is now private
    assert not batch_input_config._validate_file("nonexistent.txt")


# Test that the BatchInput can list files in the input folder
def test_batch_input_config_list_files(batch_input_config):
    test_file = "test_file.txt"
    with open(os.path.join(batch_input_config.input_folder, test_file), "w") as f:
        f.write("test")
    files = list(batch_input_config.list_files())
    assert len(files) == 1
    assert test_file in files[0]


# Test that the BatchInput can read a file from the input folder
def test_batch_input_config_read_file(batch_input_config):
    test_file = "test_file.txt"
    with open(os.path.join(batch_input_config.input_folder, test_file), "w") as f:
        f.write("test")
    contents = batch_input_config.read_file(test_file)
    assert contents == "test"


# Test that the BatchInput can delete a file from the input folder
def test_batch_input_config_delete_file(batch_input_config):
    test_file = "test_file.txt"
    with open(os.path.join(batch_input_config.input_folder, test_file), "w") as f:
        f.write("test")
    batch_input_config.delete_file(test_file)
    assert not os.path.exists(os.path.join(batch_input_config.input_folder, test_file))


# Test Spark DataFrame creation
def test_batch_input_config_spark_df(batch_input_config):
    test_file = "test_spark.txt"
    with open(os.path.join(batch_input_config.input_folder, test_file), "w") as f:
        f.write("spark test")
    df = batch_input_config.spark_df(spark)
    assert df.count() == 1
    assert df.first().content == "spark test"


# Test composing multiple BatchInput instances
def test_batch_input_config_compose(batch_input_config, tmpdir):
    another_input = BatchInput(str(tmpdir.mkdir("another")), BUCKET, S3_FOLDER)
    test_file = "test_compose.txt"
    with open(os.path.join(another_input.input_folder, test_file), "w") as f:
        f.write("compose test")
    assert batch_input_config.compose(another_input)
    assert os.path.exists(os.path.join(batch_input_config.input_folder, test_file))


# Test collecting metrics
def test_batch_input_config_collect_metrics(batch_input_config):
    metrics = batch_input_config.collect_metrics()
    assert isinstance(metrics, dict)


# Test _get_partitioned_key
def test_batch_input_config_get_partitioned_key(batch_input_config):
    batch_input_config.partition_scheme = "%Y/%m/%d"
    partitioned_key = batch_input_config._get_partitioned_key(S3_FOLDER)
    assert partitioned_key.startswith(S3_FOLDER)


# Test FileNotExistError in spark_df
def test_batch_input_config_spark_df_error():
    with pytest.raises(FileNotExistError):
        batch_input = BatchInput("nonexistent_folder", BUCKET, S3_FOLDER)
        batch_input.spark_df(spark)


# Test that the BatchInput can copy files from the S3 bucket
def test_batch_input_config_copy_from_remote(batch_input_config):
    # Upload a test file to the S3 bucket
    s3 = boto3.client("s3")
    s3.put_object(Body="test content", Bucket=BUCKET, Key=f"{S3_FOLDER}/test_file_from_s3.txt")

    # Run the copy_from_remote method
    batch_input_config.copy_from_remote()

    # Check that the files were copied to the input folder
    copied_files = os.listdir(os.path.join(batch_input_config.input_folder, S3_FOLDER))
    assert "test_file_from_s3.txt" in copied_files

    # Clean up the test file from the S3 bucket
    s3.delete_object(Bucket=BUCKET, Key=f"{S3_FOLDER}/test_file_from_s3.txt")
