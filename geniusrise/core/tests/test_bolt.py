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
from kafka import KafkaProducer  # type: ignore

from geniusrise.core import Bolt
from geniusrise.core.data import (
    BatchInput,
    BatchOutput,
    StreamingInput,
    StreamingOutput,
)
from geniusrise.core.state import (
    DynamoDBState,
    InMemoryState,
    PostgresState,
    RedisState,
)

# Define the parameters for the tests
bucket = "geniusrise-test"
s3_folder = "bolt-test"
input_topic = "test_topic"
kafka_cluster_connection_string = "localhost:9094"
group_id = "geniusrise-test-group"
output_topic = "test_topic"
kafka_servers = "localhost:9094"
redis_host = "localhost"
redis_port = 6379
redis_db = 0
postgres_host = "localhost"
postgres_port = 5432
postgres_user = "postgres"
postgres_password = "postgres"
postgres_database = "geniusrise"
postgres_table = "geniusrise_state"
dynamodb_table_name = "test_table"
dynamodb_region_name = "ap-south-1"
buffer_size = 1


class TestBolt(Bolt):
    def test_method(self, *args, input_folder=None, kafka_consumer=None, **kwargs):
        return sum(args) * sum(kwargs.values())


# Define a fixture for the input
@pytest.fixture(params=[BatchInput, StreamingInput])
def input(request, tmpdir):
    if request.param == BatchInput:
        return request.param(tmpdir, bucket, s3_folder)
    elif request.param == StreamingInput:
        return request.param(input_topic, kafka_cluster_connection_string, group_id)


# Define a fixture for the output
@pytest.fixture(params=[BatchOutput, StreamingOutput])
def output(request, tmpdir):
    if request.param == BatchOutput:
        return request.param(tmpdir, bucket, s3_folder)
    elif request.param == StreamingOutput:
        return request.param(output_topic, kafka_servers)


# Define a fixture for the state manager
@pytest.fixture(
    params=[
        InMemoryState,
        RedisState,
        PostgresState,
        DynamoDBState,
    ]
)
def state(request):
    if request.param == InMemoryState:
        return request.param(task_id="test")
    elif request.param == RedisState:
        return request.param(host=redis_host, port=redis_port, db=redis_db, task_id="test")
    elif request.param == PostgresState:
        return request.param(
            host=postgres_host,
            port=postgres_port,
            user=postgres_user,
            password=postgres_password,
            database=postgres_database,
            task_id="test",
        )
    elif request.param == DynamoDBState:
        return request.param(
            table_name=dynamodb_table_name,
            region_name=dynamodb_region_name,
            task_id="test",
        )


def test_bolt_init(input, output, state):
    bolt = TestBolt(input, output, state)
    assert bolt.input == input
    assert bolt.output == output
    assert bolt.state == state


def test_bolt_call(input, output, state):
    producer = KafkaProducer(bootstrap_servers=kafka_cluster_connection_string)
    for _ in range(2):
        producer.send(input_topic, value=json.dumps({"test": "buffer"}).encode("utf-8"))
        producer.flush()

    bolt = TestBolt(input, output, state)
    method_name = "test_method"
    args = (1, 2, 3)
    kwargs = {"a": 4, "b": 5, "c": 6}
    result = bolt(method_name, *args, **kwargs)
    assert result == 6 * (4 + 5 + 6)


@pytest.fixture(params=["batch", "streaming"])
def input_type(request):
    return request.param


@pytest.fixture(params=["batch", "streaming"])
def output_type(request):
    return request.param


@pytest.fixture(params=["none", "redis", "postgres", "dynamodb"])
def state_type(request):
    return request.param


def test_bolt_create(input_type, output_type, state_type, tmpdir):
    kwargs = {
        "input_folder": tmpdir,
        "input_s3_bucket": bucket,
        "input_s3_folder": s3_folder,
        "output_folder": tmpdir,
        "output_s3_bucket": bucket,
        "output_s3_folder": s3_folder,
        "input_kafka_cluster_connection_string": kafka_cluster_connection_string,
        "input_kafka_topic": input_topic,
        "input_kafka_consumer_group_id": group_id,
        "output_kafka_cluster_connection_string": kafka_cluster_connection_string,
        "output_kafka_topic": output_topic,
        "redis_host": redis_host,
        "redis_port": redis_port,
        "redis_db": redis_db,
        "postgres_host": postgres_host,
        "postgres_port": postgres_port,
        "postgres_user": postgres_user,
        "postgres_password": postgres_password,
        "postgres_database": postgres_database,
        "postgres_table": postgres_table,
        "dynamodb_table_name": dynamodb_table_name,
        "dynamodb_region_name": dynamodb_region_name,
    }

    bolt = Bolt.create(klass=TestBolt, input_type=input_type, output_type=output_type, state_type=state_type, **kwargs)

    assert isinstance(bolt, Bolt)

    if input_type == "batch":
        assert isinstance(bolt.input, BatchInput)
    elif input_type == "streaming":
        assert isinstance(bolt.input, StreamingInput)

    if output_type == "batch":
        assert isinstance(bolt.output, BatchOutput)
    elif output_type == "streaming":
        assert isinstance(bolt.output, StreamingOutput)

    if state_type == "none":
        assert isinstance(bolt.state, InMemoryState)
    elif state_type == "redis":
        assert isinstance(bolt.state, RedisState)
    elif state_type == "postgres":
        assert isinstance(bolt.state, PostgresState)
    elif state_type == "dynamodb":
        assert isinstance(bolt.state, DynamoDBState)


def test_bolt_call_with_types(input_type, output_type, state_type, tmpdir):
    kwargs = {
        "input_folder": tmpdir,
        "input_s3_bucket": bucket,
        "input_s3_folder": s3_folder,
        "output_folder": tmpdir,
        "output_s3_bucket": bucket,
        "output_s3_folder": s3_folder,
        "input_kafka_cluster_connection_string": kafka_cluster_connection_string,
        "input_kafka_topic": input_topic,
        "input_kafka_consumer_group_id": group_id,
        "output_kafka_cluster_connection_string": kafka_cluster_connection_string,
        "output_kafka_topic": output_topic,
        "redis_host": redis_host,
        "redis_port": redis_port,
        "redis_db": redis_db,
        "postgres_host": postgres_host,
        "postgres_port": postgres_port,
        "postgres_user": postgres_user,
        "postgres_password": postgres_password,
        "postgres_database": postgres_database,
        "postgres_table": postgres_table,
        "dynamodb_table_name": dynamodb_table_name,
        "dynamodb_region_name": dynamodb_region_name,
    }

    producer = KafkaProducer(bootstrap_servers=kafka_cluster_connection_string)
    for _ in range(2):
        producer.send(input_topic, value=json.dumps({"test": "buffer"}).encode("utf-8"))
        producer.flush()

    bolt = Bolt.create(klass=TestBolt, input_type=input_type, output_type=output_type, state_type=state_type, **kwargs)

    method_name = "test_method"
    args = (1, 2, 3)
    kwargs_for_method = {"a": 4, "b": 5, "c": 6}
    result = bolt(method_name, *args, **kwargs_for_method)

    assert result == 6 * (4 + 5 + 6)
