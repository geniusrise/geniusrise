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
from pyspark.sql import SparkSession
from streamz import Stream
import pandas as pd
import threading
import time
import tempfile
import csv
import os
from pyspark.sql.types import StructType, StructField, IntegerType

from geniusrise.core.data.streaming_input import StreamingInput

# Constants
KAFKA_CLUSTER_CONNECTION_STRING = "localhost:9094"
GROUP_ID = "geniusrise"
INPUT_TOPIC = "test_topic"


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


def test_from_spark_streaming(streaming_input):
    # Create a temporary directory and CSV file
    with tempfile.TemporaryDirectory() as tmpdirname:
        create_test_csv(tmpdirname)

        # Create a streaming DataFrame
        schema = StructType([StructField("x", IntegerType()), StructField("y", IntegerType())])
        streaming_df = spark_session.readStream.schema(schema).csv(tmpdirname)

        query = streaming_input.from_spark(streaming_df, map_func)

        assert query.isActive


def test_from_spark_batch(streaming_input):
    # Create a batch DataFrame
    data = [(1, 2), (3, 4), (5, 6)]

    # spark_session.sparkContext.addPyFile("./geniusrise/core/tests/data/test_streaming_input.py")
    batch_df = spark_session.createDataFrame(data, ["x", "y"])

    rdd = streaming_input.from_spark(batch_df, lambda row: row["x"] + row["y"])

    # Collect the results and check
    results = rdd.collect()
    assert results == [3, 7, 11]
