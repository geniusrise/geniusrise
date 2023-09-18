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

import tempfile
from typing import Any

from geniusrise.core.data import (
    BatchOutput,
    Output,
    StreamingOutput,
    StreamToBatchOutput,
)
from geniusrise.core.state import (
    DynamoDBState,
    InMemoryState,
    PostgresState,
    RedisState,
    State,
    PrometheusState,
)
from geniusrise.core.task import Task
from geniusrise.logging import setup_logger


class Spout(Task):
    """
    Base class for all spouts.
    """

    def __init__(self, output: Output, state: State, **kwargs) -> None:
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
        super().__init__()
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
            # Get the type of state manager
            # state_type = self.state.get_state(self.id)

            # Save the current set of class variables to the state manager
            # self.state.set_state(self.id, {})

            # Execute the task's method
            result = self.execute(method_name, *args, **kwargs)

            # Flush the output
            self.output.flush()

            # Store the state as successful in the state manager
            state = {}
            state["status"] = "success"
            # self.state.set_state(self.id, state)

            return result
        except Exception as e:
            state = {}
            state["status"] = "failed"
            # self.state.set_state(self.id, state)
            self.log.exception(f"Failed to execute method '{method_name}': {e}")
            raise

    @staticmethod
    def create(klass: type, output_type: str, state_type: str, **kwargs) -> "Spout":
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
                    - dynamodb_region_name (str): The AWS region for DynamoDB.
                    Prometheus state manager config:
                    - prometheus_gateway (str): The push gateway for Prometheus metrics.
                ```

        Returns:
            Spout: The created spout.

        Raises:
            ValueError: If an invalid output type or state type is provided.
        """
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
        elif output_type == "stream_to_batch":
            output = StreamToBatchOutput(
                output_folder=kwargs.get("output_folder", tempfile.mkdtemp()),
                bucket=kwargs.get("output_s3_bucket", "geniusrise"),
                s3_folder=kwargs.get("output_s3_folder", klass.__class__.__name__),
                buffer_size=kwargs.get("buffer_size", 1000),
            )
        else:
            raise ValueError(f"Invalid output type: {output_type}")

        # Create the state manager
        state: State
        if state_type == "none":
            state = InMemoryState()
        elif state_type == "redis":
            state = RedisState(
                host=kwargs["redis_host"] if "redis_host" in kwargs else None,
                port=kwargs["redis_port"] if "redis_port" in kwargs else None,
                db=kwargs["redis_db"] if "redis_db" in kwargs else None,
            )
        elif state_type == "postgres":
            state = PostgresState(
                host=kwargs["postgres_host"] if "postgres_host" in kwargs else None,
                port=kwargs["postgres_port"] if "postgres_port" in kwargs else None,
                user=kwargs["postgres_user"] if "postgres_user" in kwargs else None,
                password=kwargs["postgres_password"] if "postgres_password" in kwargs else None,
                database=kwargs["postgres_database"] if "postgres_database" in kwargs else None,
                table=kwargs["postgres_table"] if "postgres_table" in kwargs else None,
            )
        elif state_type == "dynamodb":
            state = DynamoDBState(
                table_name=kwargs["dynamodb_table_name"] if "dynamodb_table_name" in kwargs else None,
                region_name=kwargs["dynamodb_region_name"] if "dynamodb_region_name" in kwargs else None,
            )
        elif state_type == "prometheus":
            state = PrometheusState(
                gateway=kwargs["prometheus_gateway"] if "prometheus_gateway" in kwargs else None,
            )
        else:
            raise ValueError(f"Invalid state type: {state_type}")

        # Create the spout
        spout = klass(output=output, state=state, **kwargs)
        return spout
