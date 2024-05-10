# 🧠 Geniusrise
# Copyright (C) 2023  geniusrise.ai
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import json
import time

import boto3
import pytest
from kafka import KafkaProducer
from pyspark.sql import SparkSession, Row

from geniusrise.core.data.batch_input import BatchInput

# Define your S3 bucket and folder details as constants
BUCKET = "geniusrise-test"
S3_FOLDER = "whatever"
KAFKA_CLUSTER_CONNECTION_STRING = "localhost:9094"
GROUP_ID = "geniusrise"
INPUT_TOPIC = "test_topic"


# Initialize Spark session for testing
spark = SparkSession.builder.master("local[1]").appName("GeniusRise").getOrCreate()


# Define a fixture for BatchInput
@pytest.fixture
def batch_input(tmpdir):
    yield BatchInput(str(tmpdir), BUCKET, S3_FOLDER)


# Test that the BatchInput can be initialized
def test_batch_input_init(batch_input):
    assert batch_input.input_folder is not None
    assert batch_input.bucket == BUCKET
    assert batch_input.s3_folder == S3_FOLDER


# Test that the BatchInput can get the input folder
def test_batch_input_get(batch_input):
    assert batch_input.get() == batch_input.input_folder


# Test that the BatchInput can save from a Spark DataFrame
def test_batch_input_from_spark(batch_input):
    # Create a Spark DataFrame
    data = [
        Row(filename="test1.json", content=json.dumps({"key": "value1"})),
        Row(filename="test2.json", content=json.dumps({"key": "value2"})),
    ]
    df = spark.createDataFrame(data)

    # Save DataFrame to input folder
    batch_input.from_spark(df)

    # Verify that the files were saved
    saved_files = os.listdir(batch_input.input_folder)
    assert "test1.json" in saved_files
    assert "test2.json" in saved_files


# Test that the BatchInput can save from a Spark DataFrame with partitioning
def test_batch_input_from_spark_with_partition(batch_input):
    batch_input.partition_scheme = "%Y/%m/%d"

    # Create a Spark DataFrame
    data = [
        Row(filename="test_partition1.json", content=json.dumps({"key": "value1"})),
        Row(filename="test_partition2.json", content=json.dumps({"key": "value2"})),
    ]
    df = spark.createDataFrame(data)

    # Save DataFrame to input folder with partitioning
    batch_input.from_spark(df)

    # Verify that the files were saved in a partitioned manner
    partition_folder = time.strftime("%Y/%m/%d")
    saved_files = os.listdir(os.path.join(batch_input.input_folder, os.path.join(S3_FOLDER, partition_folder)))
    assert "test_partition1.json" in saved_files
    assert "test_partition2.json" in saved_files


# Test composing multiple BatchInput instances
def test_batch_input_compose(batch_input, tmpdir):
    another_input = BatchInput(str(tmpdir.mkdir("another")), BUCKET, S3_FOLDER)
    test_file = "test_compose.txt"
    with open(os.path.join(another_input.input_folder, test_file), "w") as f:
        f.write("compose test")
    assert batch_input.compose(another_input)
    assert os.path.exists(os.path.join(batch_input.input_folder, test_file))


# Test collecting metrics
def test_batch_input_collect_metrics(batch_input):
    metrics = batch_input.collect_metrics()
    assert isinstance(metrics, dict)


# Test _get_partitioned_key
def test_batch_input_get_partitioned_key(batch_input):
    batch_input.partition_scheme = "%Y/%m/%d"
    partitioned_key = batch_input._get_partitioned_key(S3_FOLDER)
    assert partitioned_key.startswith(S3_FOLDER)


# Test that the BatchInput can copy files from the S3 bucket
def test_batch_input_from_s3(batch_input):
    # Upload a test file to the S3 bucket
    s3 = boto3.client("s3")
    s3.put_object(Body="test content", Bucket=BUCKET, Key=f"{S3_FOLDER}/test_file_from_s3.txt")

    # Run the from_s3 method
    batch_input.from_s3()

    # Check that the files were copied to the input folder
    copied_files = os.listdir(os.path.join(batch_input.input_folder, S3_FOLDER))
    assert "test_file_from_s3.txt" in copied_files

    # Clean up the test file from the S3 bucket
    s3.delete_object(Bucket=BUCKET, Key=f"{S3_FOLDER}/test_file_from_s3.txt")


def test_batch_input_from_kafka(batch_input):
    producer = KafkaProducer(bootstrap_servers=KAFKA_CLUSTER_CONNECTION_STRING)
    for _ in range(10):
        producer.send(INPUT_TOPIC, value=json.dumps({"test": "buffer"}).encode("utf-8"))
        producer.flush()

    # Run the from_kafka method
    input_folder = batch_input.from_kafka(
        input_topic=INPUT_TOPIC,
        kafka_cluster_connection_string=KAFKA_CLUSTER_CONNECTION_STRING,
        nr_messages=2,
        group_id=GROUP_ID,
    )

    # Check that the messages were saved to the input folder
    saved_files = os.listdir(input_folder)
    assert "message_0.json" in saved_files
    assert "message_1.json" in saved_files

    # Validate the content of the saved files
    with open(os.path.join(input_folder, "message_0.json"), "r") as f:
        content = json.load(f)
    # Replace the following line with the actual content you expect
    assert content == {"test": "buffer"}

    with open(os.path.join(input_folder, "message_1.json"), "r") as f:
        content = json.load(f)
    # Replace the following line with the actual content you expect
    assert content == {"test": "buffer"}
