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

from geniusrise.core.data.streaming_input import KafkaConnectionError, StreamingInput

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


# Test for streamz_df method
def test_streaming_input_streamz_df(streaming_input):
    sdf = streaming_input.streamz_df()
    assert sdf is not None


# Test for spark_df method
@pytest.mark.skipif(not spark_session, reason="SparkSession not available.")
def test_streaming_input_spark_df(streaming_input):
    try:
        df = streaming_input.spark_df(spark_session)
        assert df is not None
    except KafkaConnectionError:
        pytest.fail("Failed to create Spark DataFrame")


# Test Flink Table
def test_streaming_input_flink_table(streaming_input):
    try:
        flink_table = streaming_input.flink_table(FLINK_TABLE_SCHEMA)
        assert flink_table is not None
    except KafkaConnectionError:
        pytest.fail("Failed to create Flink table")


# Test for compose method
def test_streaming_input_compose(streaming_input):
    # Create another StreamingInput instance for composition
    another_input = StreamingInput("another_topic", KAFKA_CLUSTER_CONNECTION_STRING, GROUP_ID)
    result = streaming_input.compose(another_input)
    assert result is True
