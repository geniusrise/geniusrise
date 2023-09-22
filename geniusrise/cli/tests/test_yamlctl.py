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

import argparse
import os

import pytest
from kafka import KafkaProducer
import json

from geniusrise.cli.boltctl import BoltCtl
from geniusrise.cli.discover import Discover
from geniusrise.cli.spoutctl import SpoutCtl
from geniusrise.cli.yamlctl import YamlCtl

# fmt: off

test_topic = "test_topic"
kafka_cluster_connection_string = "localhost:9094"


@pytest.fixture
def sample_geniusfile(tmpdir):
    def _geniusfile(spout_name, bolt_name, input_type, output_type, state_type):
        return f"""version: "1"
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
        prometheus_gateway: "http://localhost:9091"
    deploy:
      type: "k8s"
      args:
        kube_config_path: ""
        cluster_name: "geniusrise"
        context_name: "eks"
        namespace: "geniusrise_k8s_test"
        labels: {"tag1": "lol", "tag2": "lel"}
        annotations: {"tag1": "lol", "tag2": "lel"}
        api_key:
        api_host: localhost
        verify_ssl: true
        ssl_ca_cert:
        cpu:
        memory:
        storage:
        gpu:
        env_vars:
    output:
      type: "{output_type}"
      args:
        bucket: "geniusrise-test-bucket"
        folder: "{tmpdir}"
        kafka_servers: "localhost:9094"
        output_topic: "test_topic"
        input_kafka_consumer_group_id: "geniusrise"
        buffer_size: 1
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
        prometheus_gateway: "http://localhost:9091"
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
        kafka_servers: "localhost:9094"
        input_topic: "test_topic"
        name: "{spout_name}"
        buffer_size: 1
    output:
      type: "{output_type}"
      args:
        bucket: "geniusrise-test-bucket"
        folder: "{tmpdir}"
        kafka_servers: "localhost:9094"
        output_topic: "test_topic"
        buffer_size: 1
"""

    return _geniusfile


@pytest.fixture
def discovered_spout():
    discover = Discover(directory=".")
    classes = discover.scan_directory()
    return {"TestSpoutCtlSpout": SpoutCtl(classes.get("TestSpoutCtlSpout"))}


@pytest.fixture
def discovered_bolt():
    discover = Discover(directory=".")
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
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "batch", "none"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "batch", "redis"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "batch", "postgres"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "batch", "dynamodb"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "batch", "prometheus"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "streaming", "none"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "streaming", "redis"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "streaming", "postgres"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "streaming", "dynamodb"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "streaming", "prometheus"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "stream_to_batch", "none"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "stream_to_batch", "redis"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "stream_to_batch", "postgres"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "stream_to_batch", "dynamodb"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "stream_to_batch", "prometheus"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "stream_to_batch", "none"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "stream_to_batch", "redis"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "stream_to_batch", "postgres"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "stream_to_batch", "dynamodb"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "stream_to_batch", "prometheus"),

        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "batch", "none"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "batch", "redis"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "batch", "postgres"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "batch", "dynamodb"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "batch", "prometheus"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "streaming", "none"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "streaming", "redis"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "streaming", "postgres"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "streaming", "dynamodb"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "streaming", "prometheus"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "stream_to_batch", "none"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "stream_to_batch", "redis"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "stream_to_batch", "postgres"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "stream_to_batch", "dynamodb"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "stream_to_batch", "prometheus"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "stream_to_batch", "none"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "stream_to_batch", "redis"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "stream_to_batch", "postgres"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "stream_to_batch", "dynamodb"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "stream_to_batch", "prometheus"),

        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "stream_to_batch", "batch", "none"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "stream_to_batch", "batch", "redis"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "stream_to_batch", "batch", "postgres"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "stream_to_batch", "batch", "dynamodb"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "stream_to_batch", "batch", "prometheus"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "stream_to_batch", "streaming", "none"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "stream_to_batch", "streaming", "redis"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "stream_to_batch", "streaming", "postgres"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "stream_to_batch", "streaming", "dynamodb"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "stream_to_batch", "streaming", "prometheus"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "stream_to_batch", "stream_to_batch", "none"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "stream_to_batch", "stream_to_batch", "redis"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "stream_to_batch", "stream_to_batch", "postgres"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "stream_to_batch", "stream_to_batch", "dynamodb"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "stream_to_batch", "stream_to_batch", "prometheus"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "stream_to_batch", "stream_to_batch", "none"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "stream_to_batch", "stream_to_batch", "redis"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "stream_to_batch", "stream_to_batch", "postgres"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "stream_to_batch", "stream_to_batch", "dynamodb"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "stream_to_batch", "stream_to_batch", "prometheus"),
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

    producer = KafkaProducer(bootstrap_servers=kafka_cluster_connection_string)
    for _ in range(2):
        producer.send(test_topic, value=json.dumps({"test": "buffer"}).encode("utf-8"))
        producer.flush()

    geniusfile_path = os.path.join(tmpdir, "geniusrise.yaml")
    # Create an instance of argparse.Namespace with the necessary attributes
    args = argparse.Namespace(spout="all", bolt=None, file=geniusfile_path)  # This will run all spouts. Adjust as needed.

    # Call the run method with the created args
    yamlctl.run(args)


@pytest.mark.parametrize(
    "spout_name,bolt_name,input_type,output_type,state_type",
    [
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "batch", "none"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "batch", "redis"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "batch", "postgres"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "batch", "dynamodb"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "batch", "prometheus"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "streaming", "none"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "streaming", "redis"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "streaming", "postgres"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "streaming", "dynamodb"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "streaming", "prometheus"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "stream_to_batch", "none"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "stream_to_batch", "redis"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "stream_to_batch", "postgres"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "stream_to_batch", "dynamodb"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "stream_to_batch", "prometheus"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "stream_to_batch", "none"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "stream_to_batch", "redis"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "stream_to_batch", "postgres"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "stream_to_batch", "dynamodb"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "stream_to_batch", "prometheus"),

        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "batch", "none"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "batch", "redis"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "batch", "postgres"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "batch", "dynamodb"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "batch", "prometheus"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "streaming", "none"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "streaming", "redis"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "streaming", "postgres"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "streaming", "dynamodb"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "streaming", "prometheus"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "stream_to_batch", "none"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "stream_to_batch", "redis"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "stream_to_batch", "postgres"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "stream_to_batch", "dynamodb"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "stream_to_batch", "prometheus"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "stream_to_batch", "none"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "stream_to_batch", "redis"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "stream_to_batch", "postgres"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "stream_to_batch", "dynamodb"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "stream_to_batch", "prometheus"),

        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "stream_to_batch", "batch", "none"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "stream_to_batch", "batch", "redis"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "stream_to_batch", "batch", "postgres"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "stream_to_batch", "batch", "dynamodb"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "stream_to_batch", "batch", "prometheus"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "stream_to_batch", "streaming", "none"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "stream_to_batch", "streaming", "redis"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "stream_to_batch", "streaming", "postgres"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "stream_to_batch", "streaming", "dynamodb"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "stream_to_batch", "streaming", "prometheus"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "stream_to_batch", "stream_to_batch", "none"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "stream_to_batch", "stream_to_batch", "redis"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "stream_to_batch", "stream_to_batch", "postgres"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "stream_to_batch", "stream_to_batch", "dynamodb"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "stream_to_batch", "stream_to_batch", "prometheus"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "stream_to_batch", "stream_to_batch", "none"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "stream_to_batch", "stream_to_batch", "redis"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "stream_to_batch", "stream_to_batch", "postgres"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "stream_to_batch", "stream_to_batch", "dynamodb"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "stream_to_batch", "stream_to_batch", "prometheus"),
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

    producer = KafkaProducer(bootstrap_servers=kafka_cluster_connection_string)
    for _ in range(2):
        producer.send(test_topic, value=json.dumps({"test": "buffer"}).encode("utf-8"))
        producer.flush()

    # Create an instance of argparse.Namespace with the necessary attributes
    args = argparse.Namespace(bolt="all", spout=None, file=geniusfile_path)

    # Call the run method with the created args
    yamlctl.run(args)
