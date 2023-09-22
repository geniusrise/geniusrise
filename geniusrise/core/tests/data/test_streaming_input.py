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

import json

import pytest
from kafka import KafkaConsumer, KafkaProducer

from geniusrise.core.data import StreamingInput

# Constants
KAFKA_CLUSTER_CONNECTION_STRING = "localhost:9094"
GROUP_ID = "geniusrise"
INPUT_TOPIC = "test_topic"


# Fixture for StreamingInput
@pytest.fixture
def streaming_input_config():
    si = StreamingInput(INPUT_TOPIC, KAFKA_CLUSTER_CONNECTION_STRING, GROUP_ID)
    yield si
    si.close()


# Test Initialization
def test_streaming_input_config_init(streaming_input_config):
    assert streaming_input_config.input_topic == INPUT_TOPIC
    assert isinstance(streaming_input_config.consumer, KafkaConsumer)


# Test Get Consumer
def test_streaming_input_config_get(streaming_input_config):
    consumer = streaming_input_config.get()
    assert consumer is not None


# Test Iterator
def test_streaming_input_config_iterator(streaming_input_config):
    producer = KafkaProducer(bootstrap_servers=KAFKA_CLUSTER_CONNECTION_STRING)
    producer.send(INPUT_TOPIC, value=json.dumps({"test": "buffer"}).encode("utf-8"))
    producer.flush()

    consumer = streaming_input_config.get()

    # NOTE: this shit is done for testing only cause we produce first and then consume
    retries = 3
    for _ in range(retries):
        msg_poll = consumer.poll(timeout_ms=1000)
        if msg_poll:
            for _, messages in msg_poll.items():
                for message in messages:
                    assert json.loads(message.value.decode("utf-8")) == {"test": "buffer"}
                    return
        else:
            print("Retrying...")
    consumer.unsubscribe()


# Test Acknowledge
def test_streaming_input_config_ack(streaming_input_config):
    try:
        streaming_input_config.ack()
    except Exception:
        pytest.fail("Failed to acknowledge message")


# Test Close Consumer
def test_streaming_input_config_close(streaming_input_config):
    try:
        streaming_input_config.close()
    except Exception:
        pytest.fail("Failed to close Kafka consumer")


# Test Seek
def test_streaming_input_config_seek(streaming_input_config):
    itr = streaming_input_config.get()
    itr.poll(0)
    try:
        streaming_input_config.seek(0)
    except Exception:
        pytest.fail("Failed to seek Kafka consumer")


# Test Commit Offsets
def test_streaming_input_config_commit(streaming_input_config):
    try:
        streaming_input_config.commit()
    except Exception:
        pytest.fail("Failed to commit offsets")


# # Test Filter Messages
# def test_streaming_input_config_filter_messages(streaming_input_config):
#     try:
#         producer = KafkaProducer(bootstrap_servers=KAFKA_CLUSTER_CONNECTION_STRING)
#         producer.send(INPUT_TOPIC, value=json.dumps({"test": "filter"}).encode("utf-8"))
#         producer.flush()

#         consumer = streaming_input_config.get()
#         consumer.poll(timeout_ms=1000)  # Poll to get messages
#         streaming_input_config.seek(0)

#         def filter_func(message):
#             return json.loads(message.value.decode("utf-8")) == {"test": "filter"}

#         for message in consumer:
#             if filter_func(message):
#                 break

#         consumer.unsubscribe()
#     except Exception:
#         consumer.unsubscribe()
#         pytest.fail("Failed in filter_messages test")


# Test Collect Metrics
def test_streaming_input_config_collect_metrics(streaming_input_config):
    try:
        metrics = streaming_input_config.collect_metrics()
        assert "request_latency_avg" in metrics
        assert "request_latency_max" in metrics
    except Exception:
        pytest.fail("Failed to collect metrics")
