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

from geniusrise.core import Bolt
from geniusrise.core.data import (
    BatchInputConfig,
    BatchOutputConfig,
    StreamingInputConfig,
    StreamingOutputConfig,
)
from geniusrise.core.state import (
    DynamoDBStateManager,
    InMemoryStateManager,
    PostgresStateManager,
    RedisStateManager,
)

# Define the parameters for the tests
bucket = "geniusrise-test-bucket"
s3_folder = "bolt-test"
input_topic = "input_topic"
kafka_cluster_connection_string = "localhost:9092"
group_id = "geniusrise-test-group"
output_topic = "output_topic"
kafka_servers = "localhost:9092"
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


class TestBolt(Bolt):
    def test_method(self, *args, input_folder=None, kafka_consumer=None, **kwargs):
        return sum(args) * sum(kwargs.values())


# Define a fixture for the input config
@pytest.fixture(params=[BatchInputConfig, StreamingInputConfig])
def input_config(request, tmpdir):
    if request.param == BatchInputConfig:
        return request.param(tmpdir, bucket, s3_folder)
    elif request.param == StreamingInputConfig:
        return request.param(input_topic, kafka_cluster_connection_string, group_id)


# Define a fixture for the output config
@pytest.fixture(params=[BatchOutputConfig, StreamingOutputConfig])
def output_config(request, tmpdir):
    if request.param == BatchOutputConfig:
        return request.param(tmpdir, bucket, s3_folder)
    elif request.param == StreamingOutputConfig:
        return request.param(output_topic, kafka_servers)


# Define a fixture for the state manager
@pytest.fixture(
    params=[
        InMemoryStateManager,
        RedisStateManager,
        PostgresStateManager,
        DynamoDBStateManager,
    ]
)
def state_manager(request):
    if request.param == InMemoryStateManager:
        return request.param()
    elif request.param == RedisStateManager:
        return request.param(redis_host, redis_port, redis_db)
    elif request.param == PostgresStateManager:
        return request.param(
            postgres_host,
            postgres_port,
            postgres_user,
            postgres_password,
            postgres_database,
            postgres_table,
        )
    elif request.param == DynamoDBStateManager:
        return request.param(dynamodb_table_name, dynamodb_region_name)


def test_bolt_init(input_config, output_config, state_manager):
    bolt = TestBolt(input_config, output_config, state_manager)
    assert bolt.input_config == input_config
    assert bolt.output_config == output_config
    assert bolt.state_manager == state_manager


def test_bolt_call(input_config, output_config, state_manager):
    bolt = TestBolt(input_config, output_config, state_manager)
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


@pytest.fixture(params=["in_memory", "redis", "postgres", "dynamodb"])
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
        assert isinstance(bolt.input_config, BatchInputConfig)
    elif input_type == "streaming":
        assert isinstance(bolt.input_config, StreamingInputConfig)

    if output_type == "batch":
        assert isinstance(bolt.output_config, BatchOutputConfig)
    elif output_type == "streaming":
        assert isinstance(bolt.output_config, StreamingOutputConfig)

    if state_type == "in_memory":
        assert isinstance(bolt.state_manager, InMemoryStateManager)
    elif state_type == "redis":
        assert isinstance(bolt.state_manager, RedisStateManager)
    elif state_type == "postgres":
        assert isinstance(bolt.state_manager, PostgresStateManager)
    elif state_type == "dynamodb":
        assert isinstance(bolt.state_manager, DynamoDBStateManager)


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

    bolt = Bolt.create(klass=TestBolt, input_type=input_type, output_type=output_type, state_type=state_type, **kwargs)

    method_name = "test_method"
    args = (1, 2, 3)
    kwargs_for_method = {"a": 4, "b": 5, "c": 6}
    result = bolt(method_name, *args, **kwargs_for_method)

    assert result == 6 * (4 + 5 + 6)
