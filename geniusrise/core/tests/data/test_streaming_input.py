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


import pytest
from kafka import KafkaConsumer
from pyflink.table import DataTypes, TableSchema
from pyspark.sql import SparkSession
from streamz import Stream
import pandas as pd
import threading
import time

from geniusrise.core.data.streaming_input import StreamingInput

# Constants
KAFKA_CLUSTER_CONNECTION_STRING = "localhost:9094"
GROUP_ID = "geniusrise"
INPUT_TOPIC = "test_topic"

# Flink Table Schema
FLINK_TABLE_SCHEMA = TableSchema.builder().field("field1", DataTypes.STRING()).field("field2", DataTypes.INT()).build()

# Initialize Spark session for testing
spark_session = (
    SparkSession.builder.appName("GeniusRise")
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1")
    .getOrCreate()
)


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
        collected_data[0].reset_index(drop=True), pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]}).reset_index(drop=True)
    )
