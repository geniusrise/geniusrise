import os
import pytest
from kafka import KafkaConsumer
import boto3

from geniusrise.core.data import StreamToBatchOutput

# Constants
KAFKA_SERVERS = "localhost:9094"
OUTPUT_TOPIC = "test_batch_to_streaming_topic"
GROUP_ID = "test_group"
BUCKET = "geniusrise-test-bucket"
S3_FOLDER = "whatever"
BUFFER_SIZE = 10


# Fixtures
@pytest.fixture
def stream_to_batch_output_config(tmpdir):
    return StreamToBatchOutput(OUTPUT_TOPIC, KAFKA_SERVERS, tmpdir, BUCKET, S3_FOLDER, BUFFER_SIZE)


@pytest.fixture
def kafka_consumer():
    consumer = KafkaConsumer(OUTPUT_TOPIC, bootstrap_servers=KAFKA_SERVERS, group_id=GROUP_ID)
    consumer.commit()
    return consumer


# Helper function
def file_exists_in_s3(bucket, key):
    s3 = boto3.resource("s3")
    try:
        s3.Object(bucket, key).load()
    except Exception as e:
        return False
    return True


# Tests
def test_stream_to_batch_output_init(stream_to_batch_output_config):
    assert stream_to_batch_output_config.buffer_size == BUFFER_SIZE


def test_stream_to_batch_output_save(stream_to_batch_output_config):
    data = {"test": "data"}
    for _ in range(BUFFER_SIZE):
        stream_to_batch_output_config.save(data)

    files = os.listdir(stream_to_batch_output_config.output_folder)
    assert any(file_exists_in_s3(BUCKET, os.path.join(S3_FOLDER, f)) for f in files)


def test_stream_to_batch_output_flush(stream_to_batch_output_config):
    data = {"test": "data"}
    for _ in range(BUFFER_SIZE - 1):
        stream_to_batch_output_config.save(data)

    stream_to_batch_output_config.flush()
    assert len(stream_to_batch_output_config.buffered_messages) == 0
