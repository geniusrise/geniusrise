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

from geniusrise.core import Spout
from geniusrise.core.data import BatchOutput, StreamingOutput
from geniusrise.core.state import (
    DynamoDBState,
    InMemoryState,
    PostgresState,
    RedisState,
)

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
s3_bucket = "geniusrise-test"
s3_folder = "whatever"


class TestSpout(Spout):
    def test_method(self, *args, **kwargs):
        return sum(args) * sum(kwargs.values())


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


# Define a fixture for the output
@pytest.fixture(params=[BatchOutput, StreamingOutput])  # Add StreamToBatchOutput
def output(request, tmpdir):
    if request.param == BatchOutput:
        return request.param(tmpdir, s3_bucket, s3_folder)
    elif request.param == StreamingOutput:
        return request.param(output_topic, kafka_servers)


def test_spout_init(output, state):
    spout = TestSpout(output, state)
    assert spout.output == output
    assert spout.state == state


def test_spout_call(output, state):
    spout = TestSpout(output, state)
    method_name = "test_method"
    args = (1, 2, 3)
    kwargs = {"a": 4, "b": 5, "c": 6}
    result = spout(method_name, *args, **kwargs)
    assert result == 6 * (4 + 5 + 6)


@pytest.fixture(params=["batch", "streaming"])
def output_type(request):
    return request.param


@pytest.fixture(params=["none", "redis", "postgres", "dynamodb"])
def state_type(request):
    return request.param


def test_spout_create(output_type, state_type, tmpdir):
    kwargs = {
        "output_folder": tmpdir,
        "output_s3_bucket": s3_bucket,
        "output_s3_folder": s3_folder,
        "output_kafka_topic": output_topic,
        "output_kafka_cluster_connection_string": kafka_servers,
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
        "buffer_size": 1,
    }

    spout = Spout.create(TestSpout, output_type, state_type, **kwargs)

    assert isinstance(spout, TestSpout)

    if output_type == "batch":
        assert isinstance(spout.output, BatchOutput)
    elif output_type == "streaming":
        assert isinstance(spout.output, StreamingOutput)

    if state_type == "none":
        assert isinstance(spout.state, InMemoryState)
    elif state_type == "redis":
        assert isinstance(spout.state, RedisState)
    elif state_type == "postgres":
        assert isinstance(spout.state, PostgresState)
    elif state_type == "dynamodb":
        assert isinstance(spout.state, DynamoDBState)


def test_spout_run(output_type, state_type, tmpdir):
    kwargs = {
        "output_folder": tmpdir,
        "output_s3_bucket": s3_bucket,
        "output_s3_folder": s3_folder,
        "output_kafka_topic": output_topic,
        "output_kafka_cluster_connection_string": kafka_servers,
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

    spout = Spout.create(TestSpout, output_type, state_type, **kwargs)
    method_name = "test_method"
    args = (1, 2, 3)
    kwargs_for_method = {"a": 4, "b": 5, "c": 6}

    # Running the spout
    result = spout.__call__(method_name, *args, **kwargs_for_method)

    # Verifying the result
    assert result == 6 * (4 + 5 + 6)
