import argparse
import os

import pytest

from geniusrise.cli.boltctl import BoltCtl
from geniusrise.cli.discover import Discover
from geniusrise.cli.spoutctl import SpoutCtl
from geniusrise.cli.yamlctl import YamlCtl

# from geniusrise.core import Spout, Bolt


@pytest.fixture
def sample_geniusfile(tmpdir):
    def _geniusfile(spout_name, bolt_name, input_type, output_type, state_type):
        return f"""
version: "1"
spouts:
  {spout_name}:
    name: "{spout_name}"
    method: "test_method"
    args:
      a: 4
      b: 5
      c: 6
    state:
      type: "{state_type}"
      args:
        redis_host: "localhost"
        redis_port: 6379
        redis_db: 0
        postgres_host: "localhost"
        postgres_port: 5432
        postgres_user: "postgres"
        postgres_password: "postgres"
        postgres_database: "geniusrise"
        postgres_table: "geniusrise_state"
        dynamodb_table_name: "test_table"
        dynamodb_region_name: "ap-south-1"
    deploy:
      type: "k8s"
      args:
        name: "sample_spout_deploy"
        namespace: "default"
        image: "sample_spout_image"
        replicas: 1
    output:
      type: "{output_type}"
      args:
        bucket: "geniusrise-test-bucket"
        folder: "{tmpdir}"
        kafka_servers: "localhost:9092"
        output_topic: "test_topic"
bolts:
  {bolt_name}:
    name: "{bolt_name}"
    method: "test_method"
    args:
      a: 4
      b: 5
      c: 6
    state:
      type: "{state_type}"
      args:
        redis_host: "localhost"
        redis_port: 6379
        redis_db: 0
        postgres_host: "localhost"
        postgres_port: 5432
        postgres_user: "postgres"
        postgres_password: "postgres"
        postgres_database: "geniusrise"
        postgres_table: "geniusrise_state"
        dynamodb_table_name: "test_table"
        dynamodb_region_name: "ap-south-1"
    deploy:
      type: "k8s"
      args:
        name: "sample_bolt_deploy"
        namespace: "default"
        image: "sample_bolt_image"
        replicas: 1
    input:
      type: "{input_type}"
      args:
        bucket: "geniusrise-test-bucket"
        folder: "{tmpdir}"
        kafka_servers: "localhost:9092"
        input_topic: "test_topic"
        name: "{spout_name}"
    output:
      type: "{output_type}"
      args:
        bucket: "geniusrise-test-bucket"
        folder: "{tmpdir}"
        kafka_servers: "localhost:9092"
        output_topic: "test_topic"
"""

    return _geniusfile


@pytest.fixture
def discovered_spout():
    discover = Discover(directory=os.path.dirname(os.path.abspath(__file__)) + "/test_spout")
    classes = discover.scan_directory()
    return {"TestSpoutCtlSpout": SpoutCtl(classes.get("TestSpoutCtlSpout"))}


@pytest.fixture
def discovered_bolt():
    discover = Discover(directory=os.path.dirname(os.path.abspath(__file__)) + "/test_bolt")
    classes = discover.scan_directory()
    return {"TestBoltCtlBolt": BoltCtl(classes.get("TestBoltCtlBolt"))}


@pytest.fixture
def yamlctl(discovered_spout, discovered_bolt):
    return YamlCtl(discovered_spout, discovered_bolt)


def test_yamlctl_init(yamlctl):
    assert isinstance(yamlctl, YamlCtl)


@pytest.mark.parametrize(
    "spout_name,bolt_name,input_type,output_type,state_type",
    [
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "batch", "in_memory"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "batch", "redis"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "batch", "postgres"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "batch", "dynamodb"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "streaming", "in_memory"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "streaming", "redis"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "streaming", "postgres"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "streaming", "dynamodb"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "batch", "in_memory"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "batch", "redis"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "batch", "postgres"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "batch", "dynamodb"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "streaming", "in_memory"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "streaming", "redis"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "streaming", "postgres"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "streaming", "dynamodb"),
    ],
)
def test_yamlctl_run(
    yamlctl,
    sample_geniusfile,
    spout_name,
    bolt_name,
    input_type,
    output_type,
    state_type,
    tmpdir,
):
    geniusfile_content = sample_geniusfile(spout_name, bolt_name, input_type, output_type, state_type)
    with open(tmpdir + "/geniusrise.yaml", "w") as f:
        f.write(geniusfile_content)

    geniusfile_path = os.path.join(tmpdir, "geniusrise.yaml")
    # Create an instance of argparse.Namespace with the necessary attributes
    args = argparse.Namespace(
        spout="all", bolt=None, file=geniusfile_path
    )  # This will run all spouts. Adjust as needed.

    # Call the run method with the created args
    yamlctl.run(args)


@pytest.mark.parametrize(
    "spout_name,bolt_name,input_type,output_type,state_type",
    [
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "batch", "in_memory"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "batch", "redis"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "batch", "postgres"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "batch", "dynamodb"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "streaming", "in_memory"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "streaming", "redis"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "streaming", "postgres"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "streaming", "dynamodb"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "batch", "in_memory"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "batch", "redis"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "batch", "postgres"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "batch", "dynamodb"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "streaming", "in_memory"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "streaming", "redis"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "streaming", "postgres"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "streaming", "dynamodb"),
    ],
)
def test_yamlctl_run_2(
    yamlctl,
    sample_geniusfile,
    spout_name,
    bolt_name,
    input_type,
    output_type,
    state_type,
    tmpdir,
):
    geniusfile_content = sample_geniusfile(spout_name, bolt_name, input_type, output_type, state_type)
    with open(tmpdir + "/geniusrise.yaml", "w") as f:
        f.write(geniusfile_content)
    geniusfile_path = os.path.join(tmpdir, "geniusrise.yaml")

    # Create an instance of argparse.Namespace with the necessary attributes
    args = argparse.Namespace(bolt="all", spout=None, file=geniusfile_path)

    # Call the run method with the created args
    yamlctl.run(args)
