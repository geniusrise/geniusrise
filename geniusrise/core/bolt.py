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
    BatchInput,
    BatchOutput,
    BatchToStreamingInput,
    Input,
    Output,
    StreamingInput,
    StreamingOutput,
    StreamToBatchInput,
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
from geniusrise.logging import setup_logger

from .task import Task


class Bolt(Task):
    """
    Base class for all bolts.

    A bolt is a component that consumes streams of data, processes them, and possibly emits new data streams.
    """

    def __init__(
        self,
        input: Input,
        output: Output,
        state: State,
        **kwargs,
    ) -> None:
        """
        The `Bolt` class is a base class for all bolts in the given context.
        It inherits from the `Task` class and provides methods for executing tasks
        both locally and remotely, as well as managing their state, with state management
        options including in-memory, Redis, PostgreSQL, and DynamoDB,
        and input and output data for  batch, streaming, stream-to-batch, and batch-to-streaming.

        The `Bolt` class uses the `Input`, `Output` and `State` classes, which are abstract base
        classes for managing input data, output data and states, respectively. The `Input` and
        `Output` classes each have two subclasses: `StreamingInput`, `BatchInput`, `StreamingOutput`
        and `BatchOutput`, which manage streaming and batch input and output data, respectively.
        The `State` class is used to get and set state, and it has several subclasses for different types of state managers.

        The `Bolt` class also uses the `ECSManager` and `K8sManager` classes in the `execute_remote` method,
        which are used to manage tasks on Amazon ECS and Kubernetes, respectively.

        Usage:
            - Create an instance of the Bolt class by providing an Input object, an Output object and a State object.
            - The Input object specifies the input data for the bolt.
            - The Output object specifies the output data for the bolt.
            - The State object handles the management of the bolt's state.

        Example:
            input = Input(...)
            output = Output(...)
            state = State(...)
            bolt = Bolt(input, output, state)

        Args:
            input (Input): The input data.
            output (Output): The output data.
            state (State): The state manager.
        """
        super().__init__()
        self.input = input
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

            # Copy input data to local or connect to kafka and pass on the details
            if type(self.input) is BatchInput:
                self.input.copy_from_remote()
                input_folder = self.input.get()
                kwargs["input_folder"] = input_folder
            elif type(self.input) is StreamingInput:
                kafka_consumer = self.input.get()
                kwargs["kafka_consumer"] = kafka_consumer
            elif isinstance(self.input, StreamToBatchInput):
                temp_folder = self.input.get()
                kwargs["input_folder"] = temp_folder
            elif isinstance(self.input, BatchToStreamingInput):
                self.input.copy_from_remote()
                iterator = self.input.iterator()
                kwargs["kafka_consumer"] = iterator

            # Execute the task's method
            result = self.execute(method_name, *args, **kwargs)

            # Flush the output data
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
    def create(klass: type, input_type: str, output_type: str, state_type: str, **kwargs) -> "Bolt":
        r"""
        Create a bolt of a specific type.

        This static method is used to create a bolt of a specific type. It takes in an input type,
        an output type, a state type, and additional keyword arguments for initializing the bolt.

        The method creates the input, output, and state manager based on the provided types,
        and then creates and returns a bolt using these configurations.

        Args:
            klass (type): The Bolt class to create.
            input_type (str): The type of input ("batch" or "streaming").
            output_type (str): The type of output ("batch" or "streaming").
            state_type (str): The type of state manager ("none", "redis", "postgres", or "dynamodb").
            **kwargs: Additional keyword arguments for initializing the bolt.
                ```
                Keyword Arguments:
                    Batch input:
                    - input_folder (str): The input folder argument.
                    - input_s3_bucket (str): The input bucket argument.
                    - input_s3_folder (str): The input S3 folder argument.
                    Batch outupt config:
                    - output_folder (str): The output folder argument.
                    - output_s3_bucket (str): The output bucket argument.
                    - output_s3_folder (str): The output S3 folder argument.
                    Streaming input:
                    - input_kafka_cluster_connection_string (str): The input Kafka servers argument.
                    - input_kafka_topic (str): The input kafka topic argument.
                    - input_kafka_consumer_group_id (str): The Kafka consumer group id.
                    Streaming output:
                    - output_kafka_cluster_connection_string (str): The output Kafka servers argument.
                    - output_kafka_topic (str): The output kafka topic argument.
                    Stream-to-Batch input:
                    - buffer_size (int): Number of messages to buffer.
                    - input_kafka_cluster_connection_string (str): The input Kafka servers argument.
                    - input_kafka_topic (str): The input kafka topic argument.
                    - input_kafka_consumer_group_id (str): The Kafka consumer group id.
                    Batch-to-Streaming input:
                    - buffer_size (int): Number of messages to buffer.
                    - input_folder (str): The input folder argument.
                    - input_s3_bucket (str): The input bucket argument.
                    - input_s3_folder (str): The input S3 folder argument.
                    Stream-to-Batch output:
                    - buffer_size (int): Number of messages to buffer.
                    - output_folder (str): The output folder argument.
                    - output_s3_bucket (str): The output bucket argument.
                    - output_s3_folder (str): The output S3 folder argument.
                    Redis state manager config:
                    - redis_host (str): The Redis host argument.
                    - redis_port (str): The Redis port argument.
                    - redis_db (str): The Redis database argument.
                    Postgres state manager config:
                    - postgres_host (str): The PostgreSQL host argument.
                    - postgres_port (str): The PostgreSQL port argument.
                    - postgres_user (str): The PostgreSQL user argument.
                    - postgres_password (str): The PostgreSQL password argument.
                    - postgres_database (str): The PostgreSQL database argument.
                    - postgres_table (str): The PostgreSQL table argument.
                    DynamoDB state manager config:
                    - dynamodb_table_name (str): The DynamoDB table name argument.
                    - dynamodb_region_name (str): The DynamoDB region name argument.
                    Prometheus state manager config:
                    - prometheus_gateway (str): The push gateway for Prometheus metrics.
                ```

        Returns:
            Bolt: The created bolt.

        Raises:
            ValueError: If an invalid input type, output type, or state type is provided.
        """
        # Create the input
        input: BatchInput | StreamingInput | StreamToBatchInput | BatchToStreamingInput
        if input_type == "batch":
            input = BatchInput(
                input_folder=kwargs["input_folder"] if "input_folder" in kwargs else tempfile.mkdtemp(),
                bucket=kwargs["input_s3_bucket"] if "input_s3_bucket" in kwargs else None,
                s3_folder=kwargs["input_s3_folder"] if "input_s3_folder" in kwargs else None,
            )
        elif input_type == "streaming":
            input = StreamingInput(
                input_topic=kwargs["input_kafka_topic"] if "input_kafka_topic" in kwargs else None,
                kafka_cluster_connection_string=kwargs["input_kafka_cluster_connection_string"]
                if "input_kafka_cluster_connection_string" in kwargs
                else None,
                group_id=kwargs["input_kafka_consumer_group_id"] if "input_kafka_consumer_group_id" in kwargs else None,
            )
        elif input_type == "stream_to_batch":
            input = StreamToBatchInput(
                input_topic=kwargs["input_kafka_topic"] if "input_kafka_topic" in kwargs else None,
                kafka_cluster_connection_string=kwargs["input_kafka_cluster_connection_string"]
                if "input_kafka_cluster_connection_string" in kwargs
                else None,
                buffer_size=int(kwargs.get("buffer_size", 1000)) if "buffer_size" in kwargs else 1,
                group_id=kwargs["input_kafka_consumer_group_id"] if "input_kafka_consumer_group_id" in kwargs else None,
            )
        elif input_type == "batch_to_stream":
            input = BatchToStreamingInput(
                input_folder=kwargs["input_folder"] if "input_folder" in kwargs else tempfile.mkdtemp(),
                bucket=kwargs["input_s3_bucket"] if "input_s3_bucket" in kwargs else None,
                s3_folder=kwargs["input_s3_folder"] if "input_s3_folder" in kwargs else None,
            )
        else:
            raise ValueError(f"Invalid input type: {input_type}")

        # Create the output
        output: BatchOutput | StreamingOutput | StreamToBatchOutput
        if output_type == "batch":
            output = BatchOutput(
                output_folder=kwargs["output_folder"] if "output_folder" in kwargs else tempfile.mkdtemp(),
                bucket=kwargs["output_s3_bucket"] if "output_s3_bucket" in kwargs else None,
                s3_folder=kwargs["output_s3_folder"] if "output_s3_folder" in kwargs else None,
            )
        elif output_type == "streaming":
            output = StreamingOutput(
                kwargs["output_kafka_topic"] if "output_kafka_topic" in kwargs else None,
                kwargs["output_kafka_cluster_connection_string"]
                if "output_kafka_cluster_connection_string" in kwargs
                else None,
            )
        elif output_type == "stream_to_batch":
            output = StreamToBatchOutput(
                output_folder=kwargs["output_folder"] if "output_folder" in kwargs else tempfile.mkdtemp(),
                bucket=kwargs["output_s3_bucket"] if "output_s3_bucket" in kwargs else None,
                s3_folder=kwargs["output_s3_folder"] if "output_s3_folder" in kwargs else None,
                buffer_size=int(kwargs.get("buffer_size", 1000)) if "buffer_size" in kwargs else 1,
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

        # Create the bolt
        bolt = klass(
            input=input,
            output=output,
            state=state,
            **kwargs,
        )
        return bolt
