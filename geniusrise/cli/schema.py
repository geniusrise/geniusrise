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

from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Extra, validator


class ExtraKwargs(BaseModel):
    """
    This class is used to handle any extra arguments that are not explicitly defined in the schema.
    """

    class Config:
        extra = Extra.allow


class StateArgs(BaseModel):
    """
    This class defines the arguments for the state. Depending on the type of state (none, redis, postgres, dynamodb),
    different arguments are required.
    """

    redis_host: Optional[str] = "127.0.0.1"
    redis_port: Optional[int] = 6379
    redis_db: Optional[int] = 0
    postgres_host: Optional[str] = "127.0.0.1"
    postgres_port: Optional[int] = 5432
    postgres_user: Optional[str] = "postgres"
    postgres_password: Optional[str] = "password"
    postgres_database: Optional[str] = "geniusrise"
    postgres_table: Optional[str] = "geniusrise"
    dynamodb_table_name: Optional[str] = "geniusrise"
    dynamodb_region_name: Optional[str] = "us-east-1"

    class Config:
        extra = Extra.allow


class State(BaseModel):
    """
    This class defines the state of the spout or bolt. The state can be of type none, redis, postgres, or dynamodb.
    """

    type: str
    args: Optional[StateArgs] = None

    @validator("type")
    def validate_type(cls, v, values, **kwargs):
        if v not in ["none", "redis", "postgres", "dynamodb"]:
            raise ValueError("Invalid state type")
        return v

    @validator("args", pre=True, always=True)
    def validate_args(cls, v, values, **kwargs):
        if "type" in values:
            if values["type"] == "redis":
                if not v or "redis_db" not in v:
                    raise ValueError("Missing required fields for redis state type")
            elif values["type"] == "postgres":
                if not v or "postgres_table" not in v:
                    raise ValueError("Missing required fields for postgres state type")
            elif values["type"] == "dynamodb":
                if not v or "dynamodb_table_name" not in v:
                    raise ValueError("Missing required fields for dynamodb state type")
            elif values["type"] == "none":
                pass
            else:
                raise ValueError(f"Unknown type of state {values['type']}")
        else:
            raise ValueError("Missing the type of state")
        return v


class OutputArgs(BaseModel):
    """
    This class defines the arguments for the output. Depending on the type of output (batch, streaming),
    different arguments are required.
    """

    bucket: Optional[str] = None
    folder: Optional[str] = None
    output_topic: Optional[str] = None
    kafka_servers: Optional[str] = None
    buffer_size: Optional[int] = 1000

    class Config:
        extra = Extra.allow


class Output(BaseModel):
    """
    This class defines the output of the spout or bolt. The output can be of type batch or streaming.
    """

    type: str
    args: Optional[OutputArgs]

    @validator("type")
    def validate_type(cls, v, values, **kwargs):
        if v not in ["batch", "streaming"]:
            raise ValueError("Invalid output type")
        return v

    @validator("args", pre=True, always=True)
    def validate_args(cls, v, values, **kwargs):
        if "type" in values:
            if values["type"] == "batch":
                if not v or ("output_folder" not in v and ("bucket" not in v and "folder" not in v)):
                    raise ValueError("Missing required fields for batch output type")
            elif values["type"] == "streaming":
                if not v or "output_topic" not in v or "kafka_servers" not in v:
                    raise ValueError("Missing required fields for streaming output type")
            else:
                raise ValueError(f"Unknown type of output {values['type']}")
        else:
            raise ValueError("Missing the type of output")
        return v


class InputArgs(BaseModel):
    """
    This class defines the arguments for the input. Depending on the type of input (batch, streaming, spout, bolt),
    different arguments are required.
    """

    input_topic: Optional[str] = None
    kafka_servers: Optional[str] = None
    group_id: Optional[str] = None
    bucket: Optional[str] = None
    folder: Optional[str] = None
    name: Optional[str] = None
    buffer_size: Optional[int] = 1000

    class Config:
        extra = Extra.allow


class Input(BaseModel):
    """
    This class defines the input of the bolt. The input can be of type batch, streaming, spout, or bolt.
    """

    type: str
    args: Optional[InputArgs]

    @validator("type")
    def validate_type(cls, v, values, **kwargs):
        if v not in [
            "batch",
            "streaming",
            "spout",
            "bolt",
        ]:
            raise ValueError("Invalid input type")
        return v

    @validator("args", pre=True, always=True)
    def validate_args(cls, v, values, **kwargs):
        if "type" in values:
            if values["type"] == "batch":
                if not v or ("input_folder" not in v and ("bucket" not in v and "folder" not in v)):
                    raise ValueError("Missing required fields for batch input type")
            elif values["type"] == "streaming":
                if not v or "input_topic" not in v or "kafka_servers" not in v:
                    raise ValueError("Missing required fields for streaming input type")
            elif values["type"] in ["spout", "bolt"]:
                if not v or "name" not in v:
                    raise ValueError(f"Missing required fields for {values['type']} input type")
            else:
                raise ValueError(f"Unknown type of input {values['type']}")
        else:
            raise ValueError("Missing the type of input")
        return v


class DeployArgs(BaseModel):
    """
    This class defines the arguments for the deployment. Depending on the type of deployment (k8s, ecs, openstack-instance, openstack-autoscale),
    different arguments are required.
    """

    # k8s
    kind: Optional[str] = "deployment"
    name: Optional[str] = None
    replicas: Optional[int] = 1
    storage: Optional[str] = None
    gpu: Optional[str] = None
    kube_config_path: Optional[str] = "~/.kube/config"
    api_key: Optional[str] = None
    api_host: Optional[str] = None
    verify_ssl: Optional[bool] = False
    ssl_ca_cert: Optional[str] = None
    cluster_name: Optional[str] = None
    context_name: Optional[str] = None
    namespace: Optional[str] = None
    labels: Optional[Dict[str, str]] = {"created_by": "geniusrise"}
    annotations: Optional[Dict[str, str]] = {"created_by": "geniusrise"}
    port: Optional[int] = None
    target_port: Optional[int] = None
    schedule: Optional[str] = None

    # ecs
    account_id: Optional[str] = None
    cluster: Optional[str] = None
    subnet_ids: Optional[List[str]] = None
    security_group_ids: Optional[List[str]] = None
    log_group: Optional[str] = None

    # openstack-instance
    openstack_name: Optional[str] = None
    openstack_image: Optional[str] = None
    openstack_flavor: Optional[str] = None
    openstack_key_name: Optional[str] = None
    openstack_network: Optional[str] = None
    openstack_block_storage_size: Optional[int] = None
    openstack_open_ports: Optional[str] = None
    openstack_allocate_ip: Optional[bool] = False
    openstack_user_data: Optional[str] = None

    # openstack-autoscale
    openstack_min_instances: Optional[int] = 1
    openstack_max_instances: Optional[int] = 5
    openstack_desired_instances: Optional[int] = 2
    openstack_protocol: Optional[str] = "HTTP"
    openstack_scale_up_threshold: Optional[int] = 80
    openstack_scale_up_adjustment: Optional[int] = 1
    openstack_scale_down_threshold: Optional[int] = 20
    openstack_scale_down_adjustment: Optional[int] = -1
    openstack_alarm_period: Optional[int] = 60
    openstack_alarm_evaluation_periods: Optional[int] = 1

    # common
    image: Optional[str] = "geniusrise/geniusrise:latest"
    cpu: Optional[str] = None
    memory: Optional[str] = None
    env_vars: Optional[Dict[str, str]] = None

    class Config:
        extra = Extra.allow


class Deploy(BaseModel):
    """
    This class defines the deployment of the spout or bolt. The deployment can be of type k8s, ecs, openstack-instance, or openstack-autoscale.
    """

    type: str
    args: Optional[DeployArgs]

    @validator("type")
    def validate_type(cls, v, values, **kwargs):
        if v not in ["k8s", "ecs", "openstack-instance", "openstack-autoscale"]:
            raise ValueError("Invalid deploy type")
        return v

    @validator("args", pre=True, always=True)
    def validate_args(cls, v, values, **kwargs):
        if "type" in values:
            if values["type"] == "ecs":
                required_fields = [
                    "name",
                    "namespace",
                    "image",
                    "replicas",
                    "account_id",
                    "cluster",
                    "subnet_ids",
                    "security_group_ids",
                    "log_group",
                    "cpu",
                    "memory",
                ]
                for field in required_fields:
                    if not v or field not in v or not v[field]:
                        raise ValueError(f"Missing required field '{field}' for ecs deploy type")
            if values["type"] == "k8s":
                required_fields = [
                    "kind",
                    "name",
                    "context_name",
                    "namespace",
                    "image",
                ]
                for field in required_fields:
                    if not v or field not in v or not v[field]:
                        raise ValueError(f"Missing required field '{field}' for k8s deploy type")
            if values["type"] == "openstack-instance":
                required_fields = [
                    "openstack_name",
                    "openstack_image",
                    "openstack_flavor",
                    "openstack_network",
                ]
                for field in required_fields:
                    if not v or field not in v or not v[field]:
                        raise ValueError(f"Missing required field '{field}' for openstack-instance deploy type")
            if values["type"] == "openstack-autoscale":
                required_fields = [
                    "openstack_name",
                    "openstack_image",
                    "openstack_flavor",
                    "openstack_network",
                ]
                for field in required_fields:
                    if not v or field not in v or not v[field]:
                        raise ValueError(f"Missing required field '{field}' for openstack-autoscale deploy type")
            else:
                raise ValueError(f"Unknown type of deployment {values['type']}")
        else:
            raise ValueError("Missing the type of deployment")
        return v


class Spout(BaseModel):
    """
    This class defines a spout. A spout has a name, method, optional arguments, output, state, and deployment.
    """

    name: str
    method: str
    args: Optional[ExtraKwargs]
    output: Output
    state: Optional[State] = None
    deploy: Optional[Deploy] = None


class Bolt(BaseModel):
    """
    This class defines a bolt. A bolt has a name, method, optional arguments, input, output, state, and deployment.
    """

    name: str
    method: str
    args: Optional[ExtraKwargs]
    input: Input
    output: Output
    state: Optional[State] = None
    deploy: Optional[Deploy] = None


class Geniusfile(BaseModel):
    """
    This class defines the overall structure of the YAML file. It includes a version, spouts, and bolts.
    """

    version: Union[int, str, float]
    spouts: Dict[str, Spout] = {}
    bolts: Dict[str, Bolt] = {}

    @validator("version")
    def validate_version(cls, v, values, **kwargs):
        if v != "1" and v != 1 and v != 1.0:
            raise ValueError("Invalid version")
        return v
