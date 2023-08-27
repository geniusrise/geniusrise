import pytest
import json
import os
from kafka import KafkaProducer

from geniusrise.core.data import StreamToBatchInput

# Constants
KAFKA_CLUSTER_CONNECTION_STRING = "localhost:9094"
GROUP_ID = "test_group_1"
INPUT_TOPIC = "test_topic"
BUFFER_SIZE = 10
BUCKET = "geniusrise-test-bucket"
S3_FOLDER = "whatever"


# Fixture for StreamToBatchInput
@pytest.fixture
def stream_to_batch_input_config(tmpdir):
    return StreamToBatchInput(
        input_topic=INPUT_TOPIC,
        kafka_cluster_connection_string=KAFKA_CLUSTER_CONNECTION_STRING,
        buffer_size=BUFFER_SIZE,
        group_id=GROUP_ID,
        input_folder=str(tmpdir),
        bucket=BUCKET,
        s3_folder=S3_FOLDER,
    )


# Test Initialization
def test_stream_to_batch_input_config_init(stream_to_batch_input_config):
    assert stream_to_batch_input_config.input_topic == INPUT_TOPIC
    assert stream_to_batch_input_config.buffer_size == BUFFER_SIZE
    assert os.path.exists(stream_to_batch_input_config.temp_folder)


# Test Buffer Messages
def test_stream_to_batch_input_config_buffer_messages(stream_to_batch_input_config):
    producer = KafkaProducer(bootstrap_servers=KAFKA_CLUSTER_CONNECTION_STRING)
    for _ in range(BUFFER_SIZE):
        producer.send(INPUT_TOPIC, value=json.dumps({"test": "buffer"}).encode("utf-8"))
    producer.flush()

    buffered_messages = stream_to_batch_input_config.buffer_messages()
    stream_to_batch_input_config.consumer.unsubscribe()
    assert len(buffered_messages) == BUFFER_SIZE


# Test Store to Temp
def test_stream_to_batch_input_config_store_to_temp(stream_to_batch_input_config):
    messages = [{"value": {"test": i}} for i in range(BUFFER_SIZE)]
    stream_to_batch_input_config.store_to_temp(messages)

    stored_files = os.listdir(stream_to_batch_input_config.temp_folder)
    assert len(stored_files) == BUFFER_SIZE


# Test Get (Buffer and Store)
def test_stream_to_batch_input_config_get(stream_to_batch_input_config):
    producer = KafkaProducer(bootstrap_servers=KAFKA_CLUSTER_CONNECTION_STRING)
    for _ in range(BUFFER_SIZE):
        producer.send(INPUT_TOPIC, value=json.dumps({"test": "buffer"}).encode("utf-8"))
    producer.flush()

    temp_folder = stream_to_batch_input_config.get()
    stream_to_batch_input_config.consumer.unsubscribe()

    assert os.path.exists(temp_folder)
    stored_files = os.listdir(temp_folder)
    assert len(stored_files) == BUFFER_SIZE


# Test Close
def test_stream_to_batch_input_config_close(stream_to_batch_input_config):
    try:
        stream_to_batch_input_config.close()
    except Exception:
        pytest.fail("Failed to close resources")
