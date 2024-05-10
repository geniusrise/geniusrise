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

import argparse
import json
import os

import pytest
from kafka import KafkaProducer  # type: ignore

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
    deploy:
      type: k8s
      args:
        kind: deployment
        name: my_fine_tuner
        context_name: arn:aws:eks:us-east-1:genius-dev:cluster/geniusrise-dev
        namespace: geniusrise
        image: geniusrise/geniusrise
        kube_config_path: ~/.kube/config
    output:
      type: "{output_type}"
      args:
        bucket: "geniusrise-test"
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
    deploy:
      type: k8s
      args:
        kind: deployment
        name: my_fine_tuner
        context_name: arn:aws:eks:us-east-1:genius-dev:cluster/geniusrise-dev
        namespace: geniusrise
        image: geniusrise/geniusrise
        kube_config_path: ~/.kube/config
    input:
      type: "{input_type}"
      args:
        bucket: "geniusrise-test"
        folder: "{tmpdir}"
        kafka_servers: "localhost:9094"
        input_topic: "test_topic"
        name: "{spout_name}"
        buffer_size: 1
    output:
      type: "{output_type}"
      args:
        bucket: "geniusrise-test"
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
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "streaming", "none"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "streaming", "redis"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "streaming", "postgres"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "streaming", "dynamodb"),

        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "batch", "none"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "batch", "redis"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "batch", "postgres"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "batch", "dynamodb"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "streaming", "none"),
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
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "streaming", "none"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "streaming", "redis"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "streaming", "postgres"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "batch", "streaming", "dynamodb"),

        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "batch", "none"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "batch", "redis"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "batch", "postgres"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "batch", "dynamodb"),
        ("TestSpoutCtlSpout", "TestBoltCtlBolt", "streaming", "streaming", "none"),
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

    producer = KafkaProducer(bootstrap_servers=kafka_cluster_connection_string)
    for _ in range(2):
        producer.send(test_topic, value=json.dumps({"test": "buffer"}).encode("utf-8"))
        producer.flush()

    # Create an instance of argparse.Namespace with the necessary attributes
    args = argparse.Namespace(bolt="all", spout=None, file=geniusfile_path)

    # Call the run method with the created args
    yamlctl.run(args)
