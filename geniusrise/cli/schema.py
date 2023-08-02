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


class SpoutKwargs(BaseModel):
    class Config:
        extra = Extra.allow


class StateArgs(BaseModel):
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
    type: str
    args: Optional[StateArgs]

    @validator("type")
    def validate_type(cls, v, values, **kwargs):
        if v not in ["in_memory", "redis", "postgres", "dynamodb"]:
            raise ValueError("Invalid state type")
        return v

    @validator("args", pre=True)
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
    output_folder: Optional[str]
    bucket: Optional[str]
    s3_folder: Optional[str]
    output_topic: Optional[str]
    kafka_servers: Optional[str]

    class Config:
        extra = Extra.allow


class Output(BaseModel):
    type: str
    args: Optional[OutputArgs]

    @validator("type")
    def validate_type(cls, v, values, **kwargs):
        if v not in ["batch", "streaming"]:
            raise ValueError("Invalid output type")
        return v

    @validator("args", pre=True)
    def validate_args(cls, v, values, **kwargs):
        if "type" in values:
            if values["type"] == "batch":
                if not v or "output_folder" not in v or "bucket" not in v or "s3_folder" not in v:
                    raise ValueError("Missing required fields for batch output type")
            elif values["type"] == "streaming":
                if not v or "output_topic" not in v or "kafka_servers" not in v:
                    raise ValueError("Missing required fields for streaming output type")
        return v


class DeployArgs(BaseModel):
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
    type: str
    args: Optional[DeployArgs]

    @validator("type")
    def validate_type(cls, v, values, **kwargs):
        if v not in ["k8s", "ecs"]:
            raise ValueError("Invalid deploy type")
        return v


class Spout(BaseModel):
    name: str
    method: str
    output: Output
    state: State
    other: SpoutKwargs
    deploy: Deploy


class SpoutConfig(BaseModel):
    version: str
    spouts: Dict[str, Spout]

    @validator("version")
    def validate_version(cls, v, values, **kwargs):
        if v != "1":
            raise ValueError("Invalid version")
        return v
