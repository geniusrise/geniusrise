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

import tempfile
from typing import Any, Optional
import uuid
import time

from geniusrise.core.data import BatchOutput, Output, StreamingOutput
from geniusrise.core.state import (
    DynamoDBState,
    InMemoryState,
    PostgresState,
    RedisState,
    State,
)
from geniusrise.core.task import Task
from geniusrise.logging import setup_logger


class Spout(Task):
    """
    Base class for all spouts.

    A spout is a component that emits new data.
    """

    def __init__(self, output: Output, state: State, id: Optional[str] = None, **kwargs) -> None:
        """
        The `Spout` class is a base class for all spouts in the given context.
        It inherits from the `Task` class and provides methods for executing tasks
        both locally and remotely, as well as managing their state, with state management
        options including in-memory, Redis, PostgreSQL, and DynamoDB,
        and output data for batch or streaming data.

        The `Spout` class uses the `Output` and `State` classes, which are abstract base
         classes for managing output data and states, respectively. The `Output` class
         has two subclasses: `StreamingOutput` and `BatchOutput`, which manage streaming and
         batch output data, respectively. The `State` class is used to get and set state,
         and it has several subclasses for different types of state managers.

        The `Spout` class also uses the `ECSManager` and `K8sManager` classes in the `execute_remote` method,
        which are used to manage tasks on Amazon ECS and Kubernetes, respectively.

        Usage:
            - Create an instance of the Spout class by providing an Output object and a State object.
            - The Output object specifies the output data for the spout.
            - The State object handles the management of the spout's state.

        Example:
            output = Output(...)
            state = State(...)
            spout = Spout(output, state)

        Args:
            output (Output): The output data.
            state (State): The state manager.
        """
        super().__init__(id=id)
        self.output = output
        self.state = state

        self.log = setup_logger(self.state)

    def __call__(self, method_name: str, *args, **kwargs) -> Any:
        """
        Execute a method locally and manage the state.

        Args:
            method_name (str): The name of the method to execute.
            *args: Positional arguments to pass to the method.
            **kwargs: Keyword arguments to pass to the method.
                Keyword Arguments:
                    - Additional keyword arguments specific to the method.

        Returns:
            Any: The result of the method.
        """
        try:
            # Save the current set of class variables to the state manager
            self.state.set_state("status", {"status": "running", "time": time.time()})

            # Execute the task's method
            result = self.execute(method_name, *args, **kwargs)

            # Flush the output
            self.output.flush()

            # Store the state as successful in the state manager
            self.state.set_state("status", {"status": "success", "time": time.time()})

            return result
        except Exception as e:
            self.state.set_state("status", {"status": "failed", "time": time.time()})
            self.log.exception(f"Failed to execute method '{method_name}': {e}")
            raise

    @staticmethod
    def create(
        klass: type,
        output_type: str,
        state_type: str,
        id: Optional[str] = None,
        **kwargs,
    ) -> "Spout":
        r"""
        Create a spout of a specific type.

        Args:
            klass (type): The Spout class to create.
            output_type (str): The type of output ("batch" or "streaming").
            state_type (str): The type of state manager ("none", "redis", "postgres", or "dynamodb").
            **kwargs: Additional keyword arguments for initializing the spout.
                ```
                Keyword Arguments:
                    Batch output:
                    - output_folder (str): The directory where output files should be stored temporarily.
                    - output_s3_bucket (str): The name of the S3 bucket for output storage.
                    - output_s3_folder (str): The S3 folder for output storage.
                    Streaming output:
                    - output_kafka_topic (str): Kafka output topic for streaming spouts.
                    - output_kafka_cluster_connection_string (str): Kafka connection string for streaming spouts.
                    Stream to Batch output:
                    - output_folder (str): The directory where output files should be stored temporarily.
                    - output_s3_bucket (str): The name of the S3 bucket for output storage.
                    - output_s3_folder (str): The S3 folder for output storage.
                    - buffer_size (int): Number of messages to buffer.
                    Redis state manager config:
                    - redis_host (str): The host address for the Redis server.
                    - redis_port (int): The port number for the Redis server.
                    - redis_db (int): The Redis database to be used.
                    Postgres state manager config:
                    - postgres_host (str): The host address for the PostgreSQL server.
                    - postgres_port (int): The port number for the PostgreSQL server.
                    - postgres_user (str): The username for the PostgreSQL server.
                    - postgres_password (str): The password for the PostgreSQL server.
                    - postgres_database (str): The PostgreSQL database to be used.
                    - postgres_table (str): The PostgreSQL table to be used.
                    DynamoDB state manager config:
                    - dynamodb_table_name (str): The name of the DynamoDB table.
                    - dynamodb_region_name (str): The AWS region for DynamoDB
                ```

        Returns:
            Spout: The created spout.

        Raises:
            ValueError: If an invalid output type or state type is provided.
        """
        id = id if id else f"{klass.__class__.__name__}--{str(uuid.uuid4())}"

        # Create the output
        output: BatchOutput | StreamingOutput
        if output_type == "batch":
            output = BatchOutput(
                output_folder=kwargs.get("output_folder", tempfile.mkdtemp()),
                bucket=kwargs.get("output_s3_bucket", "geniusrise"),
                s3_folder=kwargs.get("output_s3_folder", klass.__class__.__name__),
            )
        elif output_type == "streaming":
            output = StreamingOutput(
                output_topic=kwargs.get("output_kafka_topic", None),
                kafka_servers=kwargs.get("output_kafka_cluster_connection_string", None),
            )
        else:
            raise ValueError(f"Invalid output type: {output_type}")

        # Create the state manager
        state: State
        if state_type == "none":
            state = InMemoryState(
                task_id=id,
            )
        elif state_type == "redis":
            state = RedisState(
                task_id=id,
                host=kwargs["redis_host"] if "redis_host" in kwargs else None,
                port=kwargs["redis_port"] if "redis_port" in kwargs else None,
                db=kwargs["redis_db"] if "redis_db" in kwargs else None,
            )
        elif state_type == "postgres":
            state = PostgresState(
                task_id=id,
                host=kwargs["postgres_host"] if "postgres_host" in kwargs else None,
                port=kwargs["postgres_port"] if "postgres_port" in kwargs else None,
                user=kwargs["postgres_user"] if "postgres_user" in kwargs else None,
                password=kwargs["postgres_password"] if "postgres_password" in kwargs else None,
                database=kwargs["postgres_database"] if "postgres_database" in kwargs else None,
                table=kwargs["postgres_table"] if "postgres_table" in kwargs else None,
            )
        elif state_type == "dynamodb":
            state = DynamoDBState(
                task_id=id,
                table_name=kwargs["dynamodb_table_name"] if "dynamodb_table_name" in kwargs else None,
                region_name=kwargs["dynamodb_region_name"] if "dynamodb_region_name" in kwargs else None,
            )
        else:
            raise ValueError(f"Invalid state type: {state_type}")

        # Create the spout
        spout = klass(output=output, state=state, id=id, **kwargs)
        spout.state.set_state("status", {"status": "created", "time": time.time()})
        return spout
