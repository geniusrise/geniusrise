import pytest
import argparse
import os
from geniusrise.cli.spoutctl import SpoutCtl
from geniusrise.cli.discover import Discover
from geniusrise.core import Spout


@pytest.fixture
def discovered_spout():
    discover = Discover(directory=os.path.dirname(os.path.abspath(__file__)) + "/test_spout")
    classes = discover.scan_directory()
    return classes.get("TestSpoutCtlSpout")


@pytest.fixture
def spoutctl(discovered_spout):
    return SpoutCtl(discovered_spout)


def test_spoutctl_init(discovered_spout):
    spoutctl = SpoutCtl(discovered_spout)
    assert spoutctl.discovered_spout == discovered_spout


# fmt: off
def test_spoutctl_run(spoutctl):
    parser = argparse.ArgumentParser()
    spoutctl.create_parser(parser)
    args = parser.parse_args([
        "run",
        "batch",
        "in_memory",
        "test_method",
        "--output_kafka_topic", "test_topic",
        "--output_kafka_cluster_connection_string", "localhost:9092",
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
        "--output_bucket", "geniusrise-test-bucket",
        "--output_s3_folder", "csv_to_json-6t7lqqpj"
    ])
    spoutctl.run(args)
    assert isinstance(spoutctl.spout, Spout)
# fmt: on


@pytest.mark.parametrize(
    "output_type,state_type",
    [
        ("batch", "in_memory"),
        ("batch", "redis"),
        ("batch", "postgres"),
        ("batch", "dynamodb"),
        ("streaming", "in_memory"),
        ("streaming", "redis"),
        ("streaming", "postgres"),
        ("streaming", "dynamodb"),
    ],
)
def test_spoutctl_create_spout(spoutctl, output_type, state_type, tmpdir):
    kwargs = {
        "output_folder": tmpdir,
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
        "output_bucket": "geniusrise-test-bucket",
        "output_s3_folder": "csv_to_json-6t7lqqpj",
    }

    spout = spoutctl.create_spout(output_type, state_type, **kwargs)
    assert isinstance(spout, Spout)


def test_spoutctl_execute_spout(spoutctl, tmpdir):
    spout = spoutctl.create_spout(
        "batch", "in_memory", output_folder=tmpdir, output_bucket="geniusrise-test-bucket", output_s3_folder="whatever"
    )
    result = spoutctl.execute_spout(spout, "test_method", 1, 2, 3, a=4, b=5, c=6)
    assert result == 6 * (4 + 5 + 6)
