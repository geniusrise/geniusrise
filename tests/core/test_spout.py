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

import pytest

from geniusrise.core import Spout
from geniusrise.core.data import BatchOutputConfig, StreamingOutputConfig
from geniusrise.core.state import DynamoDBStateManager, InMemoryStateManager, PostgresStateManager, RedisStateManager

output_topic = "test_topic"
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
s3_bucket = "geniusrise-test-bucket"
s3_folder = "csv_to_json-6t7lqqpj"


class TestSpout(Spout):
    def test_method(self, *args, **kwargs):
        return sum(args) * sum(kwargs.values())


# Define a fixture for the state manager
@pytest.fixture(params=[InMemoryStateManager, RedisStateManager, PostgresStateManager, DynamoDBStateManager])
def state_manager(request):
    if request.param == InMemoryStateManager:
        return request.param()
    elif request.param == RedisStateManager:
        return request.param(redis_host, redis_port, redis_db)
    elif request.param == PostgresStateManager:
        return request.param(postgres_host, postgres_port, postgres_user, postgres_password, postgres_database)
    elif request.param == DynamoDBStateManager:
        return request.param(dynamodb_table_name, dynamodb_region_name)


# Define a fixture for the output config
@pytest.fixture(params=[BatchOutputConfig, StreamingOutputConfig])
def output_config(request, tmpdir):
    if request.param == BatchOutputConfig:
        return request.param(tmpdir, s3_bucket, s3_folder)
    elif request.param == StreamingOutputConfig:
        return request.param(output_topic, kafka_servers)


def test_spout_init(output_config, state_manager):
    spout = TestSpout(output_config, state_manager)
    assert spout.output_config == output_config
    assert spout.state_manager == state_manager


def test_spout_call(output_config, state_manager):
    spout = TestSpout(output_config, state_manager)
    method_name = "test_method"
    args = (1, 2, 3)
    kwargs = {"a": 4, "b": 5, "c": 6}
    result = spout(method_name, *args, **kwargs)
    assert result == 6 * (4 + 5 + 6)


@pytest.fixture(params=["batch", "streaming"])
def output_type(request):
    return request.param


@pytest.fixture(params=["in_memory", "redis", "postgres", "dynamodb"])
def state_type(request):
    return request.param


def test_spout_create(output_type, state_type, tmpdir):
    kwargs = {
        "output_folder": tmpdir,
        "bucket": s3_bucket,
        "s3_folder": s3_folder,
        "output_topic": output_topic,
        "kafka_servers": kafka_servers,
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

    spout = Spout.create(Spout, output_type, state_type, **kwargs)

    assert isinstance(spout, Spout)

    if output_type == "batch":
        assert isinstance(spout.output_config, BatchOutputConfig)
    elif output_type == "streaming":
        assert isinstance(spout.output_config, StreamingOutputConfig)

    if state_type == "in_memory":
        assert isinstance(spout.state_manager, InMemoryStateManager)
    elif state_type == "redis":
        assert isinstance(spout.state_manager, RedisStateManager)
    elif state_type == "postgres":
        assert isinstance(spout.state_manager, PostgresStateManager)
    elif state_type == "dynamodb":
        assert isinstance(spout.state_manager, DynamoDBStateManager)
