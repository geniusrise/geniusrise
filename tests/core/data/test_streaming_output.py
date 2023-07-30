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

import json

import pytest
from kafka import KafkaConsumer

from geniusrise.core.data import StreamingOutputConfig

# Define your Kafka connection details as constants
KAFKA_SERVERS = "localhost:9094"
OUTPUT_TOPIC = "test_topic"
GROUP_ID = "test_group"


# Define a fixture for your StreamingOutputConfig
@pytest.fixture
def streaming_output_config():
    return StreamingOutputConfig(OUTPUT_TOPIC, KAFKA_SERVERS)


# Define a fixture for your KafkaConsumer
@pytest.fixture
def kafka_consumer():
    consumer = KafkaConsumer(OUTPUT_TOPIC, bootstrap_servers=KAFKA_SERVERS, group_id=GROUP_ID)
    consumer.commit()
    return consumer


# Test that the StreamingOutputConfig can save data to the Kafka topic
def test_streaming_output_config_save(streaming_output_config, kafka_consumer):
    data = {"test": "data"}
    streaming_output_config.save(data, "ignored_filename")

    # Consume from the Kafka topic and test that the data was saved
    for message in kafka_consumer:
        assert message.value == bytes(json.dumps(data).encode("utf-8"))
        break  # Only consume one message for this test


# Test that the StreamingOutputConfig can save data to a specific partition in the Kafka topic
def test_streaming_output_config_save_to_partition(streaming_output_config, kafka_consumer):
    data = {"test": "data"}
    partition = 0  # Replace with the number of a partition in your Kafka topic
    streaming_output_config.save_to_partition(data, partition)

    # Consume from the Kafka topic and test that the data was saved
    for message in kafka_consumer:
        if message.partition == partition:
            assert message.value == bytes(json.dumps(data).encode("utf-8"))
            break  # Only consume one message for this test


# Test that the StreamingOutputConfig can save data in bulk to the Kafka topic
def test_streaming_output_config_save_bulk(streaming_output_config, kafka_consumer):
    data = [{"test": "data1"}, {"test": "data2"}, {"test": "data3"}]
    streaming_output_config.save_bulk(data)

    # Consume from the Kafka topic and test that the data was saved
    for i, message in enumerate(kafka_consumer):
        assert message.value == bytes(json.dumps(data[i]).encode("utf-8"))
        if i == len(data) - 1:
            break  # Only consume the number of messages that were saved
