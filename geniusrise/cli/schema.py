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
    This class defines the arguments for the state. Depending on the type of state (in_memory, redis, postgres, dynamodb),
    different arguments are required.
    """

    redis_host: Optional[str]
    redis_port: Optional[int]
    redis_db: Optional[int]
    postgres_host: Optional[str]
    postgres_port: Optional[int]
    postgres_user: Optional[str]
    postgres_password: Optional[str]
    postgres_database: Optional[str]
    postgres_table: Optional[str]
    dynamodb_table_name: Optional[str]
    dynamodb_region_name: Optional[str]

    class Config:
        extra = Extra.allow


class State(BaseModel):
    """
    This class defines the state of the spout or bolt. The state can be of type in_memory, redis, postgres, or dynamodb.
    """

    type: str
    args: Optional[StateArgs]

    @validator("type")
    def validate_type(cls, v, values, **kwargs):
        if v not in ["in_memory", "redis", "postgres", "dynamodb"]:
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
        return v


class OutputArgs(BaseModel):
    """
    This class defines the arguments for the output. Depending on the type of output (batch, streaming),
    different arguments are required.
    """

    bucket: Optional[str]
    folder: Optional[str]
    output_topic: Optional[str]
    kafka_servers: Optional[str]

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
                if not v or "bucket" not in v or "folder" not in v:
                    raise ValueError("Missing required fields for batch output type")
            elif values["type"] == "streaming":
                if not v or "output_topic" not in v or "kafka_servers" not in v:
                    raise ValueError("Missing required fields for streaming output type")
        return v


class InputArgs(BaseModel):
    """
    This class defines the arguments for the input. Depending on the type of input (batch, streaming, spout, bolt),
    different arguments are required.
    """

    input_topic: Optional[str]
    kafka_servers: Optional[str]
    output_folder: Optional[str]
    bucket: Optional[str]
    folder: Optional[str]
    name: Optional[str]

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
        if v not in ["batch", "streaming", "spout", "bolt"]:
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
            elif values["type"] in ["spout", "bolt"]:
                if not v or "name" not in v:
                    raise ValueError(f"Missing required fields for {values['type']} input type")
        return v


class DeployArgs(BaseModel):
    """
    This class defines the arguments for the deployment. Depending on the type of deployment (k8s, ecs),
    different arguments are required.
    """

    name: Optional[str]
    namespace: Optional[str]
    image: Optional[str]
    replicas: Optional[int]
    account_id: Optional[str]
    cluster: Optional[str]
    subnet_ids: Optional[List[str]]
    security_group_ids: Optional[List[str]]
    log_group: Optional[str]
    cpu: Optional[int]
    memory: Optional[int]

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
            elif values["type"] == "k8s":
                required_fields = ["name", "namespace", "image", "replicas"]
                for field in required_fields:
                    if not v or field not in v or not v[field]:
                        raise ValueError(f"Missing required field '{field}' for k8s deploy type")
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
