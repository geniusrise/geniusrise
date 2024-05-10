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


import pytest
from kafka import KafkaConsumer
from streamz import Stream
import pandas as pd
import threading
import time
import csv
import os

from geniusrise.core.data.streaming_input import StreamingInput

# Constants
KAFKA_CLUSTER_CONNECTION_STRING = "localhost:9094"
GROUP_ID = "geniusrise"
INPUT_TOPIC = "test_topic"


# Fixture for StreamingInput
@pytest.fixture
def streaming_input():
    si = StreamingInput(INPUT_TOPIC, KAFKA_CLUSTER_CONNECTION_STRING, GROUP_ID)
    yield si
    si.close()


# Test Initialization
def test_streaming_input_init(streaming_input):
    assert streaming_input.input_topic == INPUT_TOPIC
    assert isinstance(streaming_input.consumer, KafkaConsumer)


# Test Get Consumer
def test_streaming_input_get(streaming_input):
    consumer = streaming_input.get()
    assert consumer is not None


# Test Close Consumer
def test_streaming_input_close(streaming_input):
    try:
        streaming_input.close()
    except Exception:
        pytest.fail("Failed to close Kafka consumer")


# Test Seek
def test_streaming_input_seek(streaming_input):
    itr = streaming_input.get()
    itr.poll(0)
    try:
        streaming_input.seek(0)
    except Exception:
        pytest.fail("Failed to seek Kafka consumer")


# Test Commit Offsets
def test_streaming_input_commit(streaming_input):
    try:
        streaming_input.commit()
    except Exception:
        pytest.fail("Failed to commit offsets")


# Test Collect Metrics
def test_streaming_input_collect_metrics(streaming_input):
    try:
        metrics = streaming_input.collect_metrics()
        assert "request_latency_avg" in metrics
        assert "request_latency_max" in metrics
    except Exception:
        pytest.fail("Failed to collect metrics")


# Test for compose method
def test_streaming_input_compose(streaming_input):
    # Create another StreamingInput instance for composition
    another_input = StreamingInput("another_topic", KAFKA_CLUSTER_CONNECTION_STRING, GROUP_ID)
    result = streaming_input.compose(another_input)
    assert result is True


# Test for from_streamz method
def test_streaming_input_from_streamz(streaming_input):
    # Create a stream and a streamz DataFrame
    source = Stream()
    example = pd.DataFrame({"x": [], "y": []})
    sdf = source.map(pd.DataFrame).to_dataframe(example=example)

    # Function to emit data
    def emit_data():
        time.sleep(1)  # Wait for a short time to ensure the generator is ready
        new_data = {"x": [1, 2, 3], "y": [4, 5, 6]}
        source.emit(new_data)
        sentinel = pd.DataFrame({"x": [-1], "y": [-1]})
        source.emit(sentinel)

    # Start a thread to emit data
    emit_thread = threading.Thread(target=emit_data)
    emit_thread.start()

    # Create a generator from the from_streamz method
    sentinel = pd.DataFrame({"x": [-1], "y": [-1]})
    row_gen = streaming_input.from_streamz(sdf, sentinel=sentinel)

    # Collect emitted data from the generator
    collected_data = []
    for _ in range(1):  # We emitted 1 chunk of data
        collected_data.append(next(row_gen))

    # Wait for the emit thread to finish
    emit_thread.join()

    # Validate the collected data
    pd.testing.assert_frame_equal(
        collected_data[0].reset_index(drop=True),
        pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]}).reset_index(drop=True),
    )


def create_test_csv(dir_path):
    csv_file_path = os.path.join(dir_path, "test.csv")
    with open(csv_file_path, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["x", "y"])
        writer.writerow([1, 2])
        writer.writerow([3, 4])
        writer.writerow([5, 6])
    return csv_file_path


def map_func(row):
    return row["x"] + row["y"]
