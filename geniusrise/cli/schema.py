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

from typing import Dict, List, Optional

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

    redis_host: Optional[str] = None
    redis_port: Optional[int] = None
    redis_db: Optional[int] = None
    postgres_host: Optional[str] = None
    postgres_port: Optional[int] = None
    postgres_user: Optional[str] = None
    postgres_password: Optional[str] = None
    postgres_database: Optional[str] = None
    postgres_table: Optional[str] = None
    dynamodb_table_name: Optional[str] = None
    dynamodb_region_name: Optional[str] = None
    prometheus_gateway: Optional[str] = None

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
        if v not in ["none", "redis", "postgres", "dynamodb", "prometheus"]:
            raise ValueError("Invalid state type")
        return v

    @validator("args", pre=True, always=True)
    def validate_args(cls, v, values, **kwargs):
        if "type" in values:
            if values["type"] == "redis":
                if not v or "redis_host" not in v or "redis_port" not in v or "redis_db" not in v:
                    raise ValueError("Missing required fields for redis state type")
            elif values["type"] == "postgres":
                if (
                    not v
                    or "postgres_host" not in v
                    or "postgres_port" not in v
                    or "postgres_user" not in v
                    or "postgres_password" not in v
                    or "postgres_database" not in v
                    or "postgres_table" not in v
                ):
                    raise ValueError("Missing required fields for postgres state type")
            elif values["type"] == "dynamodb":
                if not v or "dynamodb_table_name" not in v or "dynamodb_region_name" not in v:
                    raise ValueError("Missing required fields for dynamodb state type")
            elif values["type"] == "none":
                pass
            elif values["type"] == "prometheus":
                if not v or "prometheus_gateway" not in v:
                    raise ValueError("Missing required fields for prometheus state type")
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
    buffer_size: Optional[int] = 1

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
        if v not in ["batch", "streaming", "stream_to_batch"]:
            raise ValueError("Invalid output type")
        return v

    @validator("args", pre=True, always=True)
    def validate_args(cls, v, values, **kwargs):
        if "type" in values:
            if values["type"] == "batch":
                if not v or "bucket" not in v or "folder" not in v:
                    raise ValueError("Missing required fields for batch output type")
            elif values["type"] == "streaming":
                if not v or "output_topic" not in v or "kafka_servers" not in v:
                    raise ValueError("Missing required fields for streaming output type")
            elif values["type"] == "stream_to_batch":
                if not v or "bucket" not in v or "folder" not in v or "buffer_size" not in v:
                    raise ValueError("Missing required fields for stream_to_batch output type")
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
    buffer_size: Optional[int] = 1

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
            "batch_to_stream",
            "stream_to_batch",
            "spout",
            "bolt",
        ]:
            raise ValueError("Invalid input type")
        return v

    @validator("args", pre=True, always=True)
    def validate_args(cls, v, values, **kwargs):
        if "type" in values:
            if values["type"] == "batch":
                if not v or "bucket" not in v or "folder" not in v:
                    raise ValueError("Missing required fields for batch input type")
            elif values["type"] == "streaming":
                if not v or "input_topic" not in v or "kafka_servers" not in v:
                    raise ValueError("Missing required fields for streaming input type")
            elif values["type"] == "batch_to_stream":
                if not v or "bucket" not in v or "folder" not in v:
                    raise ValueError("Missing required fields for batch_to_stream input type")
            elif values["type"] == "stream_to_batch":
                if not v or "input_topic" not in v or "kafka_servers" not in v or "buffer_size" not in v:
                    raise ValueError("Missing required fields for stream_to_batch input type")
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
    This class defines the arguments for the deployment. Depending on the type of deployment (k8s, ecs),
    different arguments are required.
    """

    # k8s
    kind: Optional[str] = None
    name: Optional[str] = None
    cluster_name: Optional[str] = None
    context_name: Optional[str] = None
    namespace: Optional[str] = None
    replicas: Optional[int] = None
    labels: Optional[str] = None
    annotations: Optional[str] = None
    api_key: Optional[str] = None
    api_host: Optional[str] = None
    verify_ssl: Optional[str] = None
    ssl_ca_cert: Optional[str] = None
    storage: Optional[str] = None
    gpu: Optional[str] = None
    port: Optional[str] = None
    target_port: Optional[str] = None
    schedule: Optional[str] = None

    # ecs
    account_id: Optional[str] = None
    cluster: Optional[str] = None
    subnet_ids: Optional[List[str]] = None
    security_group_ids: Optional[List[str]] = None
    log_group: Optional[str] = None

    # common
    image: Optional[str] = None
    command: Optional[str] = None
    cpu: Optional[int] = None
    memory: Optional[int] = None
    env_vars: Optional[str] = None

    class Config:
        extra = Extra.allow


class Deploy(BaseModel):
    """
    This class defines the deployment of the spout or bolt. The deployment can be of type k8s or ecs.
    """

    type: str
    args: Optional[DeployArgs]

    @validator("type")
    def validate_type(cls, v, values, **kwargs):
        if v not in ["k8s", "ecs"]:
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
                    "cluster_name",
                    "context_name",
                    "namespace",
                    "image",
                    "command",
                ]
                for field in required_fields:
                    if not v or field not in v or not v[field]:
                        raise ValueError(f"Missing required field '{field}' for k8s deploy type")
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
    state: State
    deploy: Deploy


class Bolt(BaseModel):
    """
    This class defines a bolt. A bolt has a name, method, optional arguments, input, output, state, and deployment.
    """

    name: str
    method: str
    args: Optional[ExtraKwargs]
    input: Input
    output: Output
    state: State
    deploy: Deploy


class Geniusfile(BaseModel):
    """
    This class defines the overall structure of the YAML file. It includes a version, spouts, and bolts.
    """

    version: str
    spouts: Dict[str, Spout]
    bolts: Dict[str, Bolt]

    @validator("version")
    def validate_version(cls, v, values, **kwargs):
        if v != "1":
            raise ValueError("Invalid version")
        return v
