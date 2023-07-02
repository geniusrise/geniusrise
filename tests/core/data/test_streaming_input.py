import pytest
from geniusrise.core.data import StreamingInputConfig
from kafka import KafkaProducer

# Define your Kafka connection details as constants
KAFKA_CLUSTER_CONNECTION_STRING = "localhost:9094"
GROUP_ID = "test_group_1"
INPUT_TOPIC = "test_topic"


# Define a fixture for your StreamingInputConfig
@pytest.fixture
def streaming_input_config():
    return StreamingInputConfig(INPUT_TOPIC, KAFKA_CLUSTER_CONNECTION_STRING, GROUP_ID)


# Test that the StreamingInputConfig can be initialized
def test_streaming_input_config_init(streaming_input_config):
    assert streaming_input_config.input_topic == INPUT_TOPIC
    assert streaming_input_config.consumer is not None


# Test that the StreamingInputConfig can get data from the Kafka topic
def test_streaming_input_config_get(streaming_input_config):
    consumer = streaming_input_config.get()
    assert consumer is not None

    producer = KafkaProducer(bootstrap_servers=KAFKA_CLUSTER_CONNECTION_STRING)
    producer.send(INPUT_TOPIC, b'{"test": "lol"}')

    # Consume from the Kafka topic and test that it works
    # Note: This assumes that there is data in the topic to consume
    for message in consumer:
        assert message.value == b'{"test": "lol"}'
        break  # Only consume one message for this test
