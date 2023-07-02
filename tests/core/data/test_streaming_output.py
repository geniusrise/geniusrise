import pytest
from geniusrise.core.data import StreamingOutputConfig
from kafka import KafkaConsumer
import json

# Define your Kafka connection details as constants
KAFKA_SERVERS = "localhost:9094"
OUTPUT_TOPIC = "test_topic"
GROUP_ID = "test_group"


# Define a fixture for your StreamingOutputConfig
@pytest.fixture
def streaming_output_config():
    return StreamingOutputConfig(OUTPUT_TOPIC, KAFKA_SERVERS)


# Test that the StreamingOutputConfig can be initialized
def test_streaming_output_config_init(streaming_output_config):
    assert streaming_output_config.output_topic == OUTPUT_TOPIC
    assert streaming_output_config.producer is not None


# Test that the StreamingOutputConfig can save data to the Kafka topic
def test_streaming_output_config_save(streaming_output_config):
    data = {"test": "data"}
    streaming_output_config.save(data, "ignored_filename")

    # Consume from the Kafka topic and test that the data was saved
    # Note: This assumes that you have a KafkaConsumer configured to consume from the test_topic
    consumer = KafkaConsumer(OUTPUT_TOPIC, bootstrap_servers=KAFKA_SERVERS, group_id=GROUP_ID)
    for message in consumer:
        assert message.value == bytes(json.dumps(data).encode("utf-8"))
        break  # Only consume one message for this test


# Test that the StreamingOutputConfig can flush the Kafka producer
def test_streaming_output_config_flush(streaming_output_config):
    # This test just checks that the flush method doesn't raise an exception
    # It doesn't check that the data is actually flushed, because that would require
    # inspecting the internal state of the Kafka producer
    try:
        streaming_output_config.flush()
    except Exception:
        pytest.fail("StreamingOutputConfig.flush() raised an exception")
