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
import boto3
import pytest
from geniusrise.core.data import BatchOutput
from kafka import KafkaConsumer
import json


# Define your S3 bucket and folder details as constants
BUCKET = "geniusrise-test"
S3_FOLDER = "whatever"
KAFKA_CLUSTER_CONNECTION_STRING = "localhost:9094"
OUTPUT_TOPIC = "test_topic"


# Define a fixture for KafkaConsumer
@pytest.fixture
def kafka_consumer():
    consumer = KafkaConsumer(
        OUTPUT_TOPIC,
        bootstrap_servers=KAFKA_CLUSTER_CONNECTION_STRING,
        value_deserializer=lambda x: json.loads(x.decode("utf-8")),
    )
    yield consumer
    consumer.close()


# Define a fixture for your BatchOutput
@pytest.fixture
def batch_output(tmpdir):
    yield BatchOutput(str(tmpdir), BUCKET, S3_FOLDER)


# Test that the BatchOutput can be initialized
def test_batch_output_init(batch_output):
    assert batch_output.output_folder is not None


# Test that the BatchOutput can save data to a file
def test_batch_output_save(batch_output):
    data = {"test": "buffer"}
    filename = "test_file.json"
    batch_output.save(data, filename)

    # Check that the file was created in the output folder
    assert os.path.isfile(os.path.join(batch_output.output_folder, filename))


# Test that the BatchOutput can copy files to the S3 bucket
def test_batch_output_to_s3(batch_output):
    # First, save a file to the output folder
    data = {"test": "buffer"}
    filename = "test_file.json"
    batch_output.save(data, filename)

    # Then, copy the file to the S3 bucket
    batch_output.to_s3()

    # Check that the file was copied to the S3 bucket
    assert file_exists_in_s3(BUCKET, os.path.join(S3_FOLDER, filename))


# Test that the BatchOutput can flush the output folder to the S3 bucket
def test_batch_output_flush(batch_output):
    # First, save a file to the output folder
    data = {"test": "buffer"}
    filename = "test_file.json"
    batch_output.save(data, filename)

    # Then, flush the output folder to the S3 bucket
    batch_output.flush()

    # Check that the file was copied to the S3 bucket
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
        print(e)
        return False
    return True


# Test that the BatchOutput can produce messages to Kafka
def test_batch_output_to_kafka(batch_output, kafka_consumer):
    # First, save a file to the output folder
    data = {"test": "buffer"}
    batch_output.save(data)

    # Then, produce messages to Kafka
    batch_output.to_kafka(
        output_topic=OUTPUT_TOPIC,
        kafka_cluster_connection_string=KAFKA_CLUSTER_CONNECTION_STRING,
    )

    # # Consume the message from Kafka - TODO: consumer in different thread?
    # kafka_consumer.poll(1000)  # Wait for 1 second to get the message
    # consumed_data = next(kafka_consumer)
    # assert consumed_data.value == data
