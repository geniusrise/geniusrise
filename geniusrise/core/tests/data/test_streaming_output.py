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

import json

import pytest
from kafka import KafkaConsumer

from geniusrise.core.data import StreamingOutput

# Define your Kafka connection details as constants
KAFKA_SERVERS = "localhost:9094"
OUTPUT_TOPIC = "test_topic"
GROUP_ID = "test_group"


# Define a fixture for your StreamingOutput
@pytest.fixture
def streaming_output():
    return StreamingOutput(OUTPUT_TOPIC, KAFKA_SERVERS)


# Define a fixture for your KafkaConsumer
@pytest.fixture
def kafka_consumer():
    consumer = KafkaConsumer(OUTPUT_TOPIC, bootstrap_servers=KAFKA_SERVERS, group_id=GROUP_ID)
    consumer.commit()
    return consumer


# Test that the StreamingOutput can save data to the Kafka topic
def test_streaming_output_save(streaming_output, kafka_consumer):
    data = {"test": "buffer"}
    for _ in range(10):
        streaming_output.save(data)

    # Consume from the Kafka topic and test that the data was saved
    for message in kafka_consumer:
        assert message.value == bytes(json.dumps(data).encode("utf-8"))
        kafka_consumer.unsubscribe()
        break  # Only consume one message for this test


# Test that the StreamingOutput can save data to a specific partition in the Kafka topic
def test_streaming_output_save_to_partition(streaming_output, kafka_consumer):
    data = {"test": "buffer"}
    partition = 0  # Replace with the number of a partition in your Kafka topic
    streaming_output.save_to_partition(data, partition)

    # Consume from the Kafka topic and test that the data was saved
    for message in kafka_consumer:
        if message.partition == partition:
            assert message.value == bytes(json.dumps(data).encode("utf-8"))
            break  # Only consume one message for this test
    kafka_consumer.unsubscribe()
