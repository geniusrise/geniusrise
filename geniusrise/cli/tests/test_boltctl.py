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
import argparse
import os
from geniusrise.cli.boltctl import BoltCtl
from geniusrise.cli.discover import Discover
from geniusrise.core import Bolt


@pytest.fixture
def discovered_bolt():
    discover = Discover(directory=os.path.dirname(os.path.abspath(__file__)) + "/test_bolt")
    classes = discover.scan_directory()
    return classes.get("TestBoltCtlBolt")


@pytest.fixture
def boltctl(discovered_bolt):
    return BoltCtl(discovered_bolt)


def test_boltctl_init(discovered_bolt):
    boltctl = BoltCtl(discovered_bolt)
    assert boltctl.discovered_bolt == discovered_bolt


# fmt: off
@pytest.mark.parametrize(
    "input_type,output_type,state_type",
    [
        ("batch", "batch", "in_memory"),
        ("batch", "batch", "redis"),
        ("batch", "batch", "postgres"),
        ("batch", "batch", "dynamodb"),
        ("batch", "streaming", "in_memory"),
        ("batch", "streaming", "redis"),
        ("batch", "streaming", "postgres"),
        ("batch", "streaming", "dynamodb"),
        ("streaming", "batch", "in_memory"),
        ("streaming", "batch", "redis"),
        ("streaming", "batch", "postgres"),
        ("streaming", "batch", "dynamodb"),
        ("streaming", "streaming", "in_memory"),
        ("streaming", "streaming", "redis"),
        ("streaming", "streaming", "postgres"),
        ("streaming", "streaming", "dynamodb"),
    ],
)
def test_boltctl_run(boltctl, input_type, output_type, state_type, tmpdir):
    parser = argparse.ArgumentParser()
    boltctl.create_parser(parser)
    args = parser.parse_args([
        "run",
        input_type,
        "--input_folder", str(tmpdir),
        "--input_s3_bucket", "geniusrise-test-bucket",
        "--input_s3_folder", "input_s3_folder_path",
        "--input_kafka_topic", "test_topic",
        "--input_kafka_cluster_connection_string", "localhost:9092",
        output_type,
        "--output_folder", str(tmpdir),
        "--output_s3_bucket", "geniusrise-test-bucket",
        "--output_s3_folder", "whatever",
        "--output_kafka_topic", "test_topic",
        "--output_kafka_cluster_connection_string", "localhost:9092",
        state_type,
        "--redis_host", "localhost",
        "--redis_port", "6379",
        "--redis_db", "0",
        "--postgres_host", "localhost",
        "--postgres_port", "5432",
        "--postgres_user", "postgres",
        "--postgres_password", "postgres",
        "--postgres_database", "geniusrise",
        "--postgres_table", "geniusrise_state",
        "--dynamodb_table_name", "test_table",
        "--dynamodb_region_name", "ap-south-1",
        "test_method",
        "--args", "1", "2", "3", "a=4", "b=5", "c=6"
    ])
    result = boltctl.run(args)
    assert result == 90
    assert isinstance(boltctl.bolt, Bolt)
# fmt: on


def test_boltctl_execute_bolt(boltctl, tmpdir):
    bolt = boltctl.create_bolt(
        "batch",
        "batch",
        "in_memory",
        input_folder=tmpdir,
        input_s3_bucket="geniusrise-test-bucket",
        input_s3_folder="input_s3_folder_path",
        output_folder=tmpdir,
        output_s3_bucket="geniusrise-test-bucket",
        output_s3_folder="whatever",
    )
    result = boltctl.execute_bolt(bolt, "test_method", 1, 2, 3, a=4, b=5, c=6)
    assert result == 6 * (4 + 5 + 6)


@pytest.mark.parametrize(
    "input_type,output_type,state_type",
    [
        ("batch", "batch", "in_memory"),
        ("batch", "batch", "redis"),
        ("batch", "batch", "postgres"),
        ("batch", "batch", "dynamodb"),
        ("batch", "streaming", "in_memory"),
        ("batch", "streaming", "redis"),
        ("batch", "streaming", "postgres"),
        ("batch", "streaming", "dynamodb"),
        ("streaming", "batch", "in_memory"),
        ("streaming", "batch", "redis"),
        ("streaming", "batch", "postgres"),
        ("streaming", "batch", "dynamodb"),
        ("streaming", "streaming", "in_memory"),
        ("streaming", "streaming", "redis"),
        ("streaming", "streaming", "postgres"),
        ("streaming", "streaming", "dynamodb"),
    ],
)
def test_boltctl_create_bolt(boltctl, input_type, output_type, state_type, tmpdir):
    kwargs = {
        "input_folder": tmpdir,
        "input_s3_bucket": "geniusrise-test-bucket",
        "input_s3_folder": "input_s3_folder_path",
        "input_kafka_topic": "test_topic",
        "input_kafka_cluster_connection_string": "localhost:9092",
        "output_folder": tmpdir,
        "output_s3_bucket": "geniusrise-test-bucket",
        "output_s3_folder": "whatever",
        "output_kafka_topic": "test_topic",
        "output_kafka_cluster_connection_string": "localhost:9092",
        "redis_host": "localhost",
        "redis_port": 6379,
        "redis_db": 0,
        "postgres_host": "localhost",
        "postgres_port": 5432,
        "postgres_user": "postgres",
        "postgres_password": "postgres",
        "postgres_database": "geniusrise",
        "postgres_table": "geniusrise_state",
        "dynamodb_table_name": "test_table",
        "dynamodb_region_name": "ap-south-1",
    }

    bolt = boltctl.create_bolt(input_type, output_type, state_type, **kwargs)
    assert isinstance(bolt, Bolt)
