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

import pytest
from kafka import KafkaProducer

from geniusrise.core.data import StreamingInputConfig

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
    producer.flush()

    # Consume from the Kafka topic and test that it works
    # Note: This assumes that there is data in the topic to consume
    for message in consumer:
        assert message.value == b'{"test": "lol"}'
        break  # Only consume one message for this test


# Test that the StreamingInputConfig can iterate over messages
def test_streaming_input_config_iterator(streaming_input_config):
    producer = KafkaProducer(bootstrap_servers=KAFKA_CLUSTER_CONNECTION_STRING)
    producer.send(INPUT_TOPIC, b'{"test": "lol"}')
    producer.flush()

    for message in streaming_input_config:
        assert message.value == b'{"test": "lol"}'
        break  # Only consume one message for this test


# Test that the StreamingInputConfig can filter messages
def test_streaming_input_config_filter_messages(streaming_input_config):
    producer = KafkaProducer(bootstrap_servers=KAFKA_CLUSTER_CONNECTION_STRING)
    producer.send(INPUT_TOPIC, b'{"test": "filter"}')
    producer.send(INPUT_TOPIC, b'{"test": "do not filter"}')
    producer.flush()

    def filter_func(message):
        return message.value == b'{"test": "filter"}'

    for message in streaming_input_config.filter_messages(filter_func):
        assert message.value == b'{"test": "filter"}'
        break  # Only consume one message for this test


# Test that the StreamingInputConfig can close the Kafka consumer
def test_streaming_input_config_close(streaming_input_config):
    streaming_input_config.close()
    assert streaming_input_config.consumer is None


# Test that the StreamingInputConfig can seek to a specific offset
def test_streaming_input_config_seek(streaming_input_config):
    partition = 0
    offset = 0
    streaming_input_config.seek(partition, offset)
    message = next(streaming_input_config)
    assert message.offset == offset


# Test that the StreamingInputConfig can commit offsets
def test_streaming_input_config_commit(streaming_input_config):
    streaming_input_config.commit()
    # This test is a bit tricky to implement because it depends on the state of the Kafka consumer
    # You might need to check the committed offsets for the consumer's current partitions
