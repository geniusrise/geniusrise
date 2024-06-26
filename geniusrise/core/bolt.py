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

from geniusrise.core.data import (
    BatchInput,
    BatchOutput,
    Input,
    Output,
    StreamingInput,
    StreamingOutput,
)
from geniusrise.core.state import (
    DynamoDBState,
    InMemoryState,
    PostgresState,
    RedisState,
    State,
)
from geniusrise.logging import setup_logger

from .task import Task


class Bolt(Task):
    """
    Base class for all bolts.

    A bolt is a component that consumes data, processes them, and possibly emits new data.
    """

    def __init__(
        self,
        input: Input,
        output: Output,
        state: State,
        id: Optional[str] = None,
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
        super().__init__(id=id)
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

            self.state.set_state("status", {"status": "getting_data", "time": time.time()})

            if type(self.input) is BatchInput:
                self.input.from_s3()

            self.state.set_state("status", {"status": "running", "time": time.time()})

            # Execute the task's method
            result = self.execute(method_name, *args, **kwargs)

            # Flush the output data
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
        input_type: str,
        output_type: str,
        state_type: str,
        id: Optional[str] = None,
        **kwargs,
    ) -> "Bolt":
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
                    Batch output config:
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
                ```

        Returns:
            Bolt: The created bolt.

        Raises:
            ValueError: If an invalid input type, output type, or state type is provided.
        """
        id = id if id else f"{klass.__class__.__name__}--{str(uuid.uuid4())}"

        # Create the input
        input: BatchInput | StreamingInput
        if input_type == "batch":
            input = BatchInput(
                input_folder=kwargs["input_folder"] if "input_folder" in kwargs else tempfile.mkdtemp(),
                bucket=kwargs["input_s3_bucket"] if "input_s3_bucket" in kwargs else None,
                s3_folder=kwargs["input_s3_folder"] if "input_s3_folder" in kwargs else None,
            )
        elif input_type == "streaming":
            input = StreamingInput(
                input_topic=kwargs["input_kafka_topic"] if "input_kafka_topic" in kwargs else None,  # type: ignore
                kafka_cluster_connection_string=(
                    kwargs["input_kafka_cluster_connection_string"]
                    if "input_kafka_cluster_connection_string" in kwargs
                    else None
                ),
                group_id=kwargs["input_kafka_consumer_group_id"] if "input_kafka_consumer_group_id" in kwargs else None,
            )
        else:
            raise ValueError(f"Invalid input type: {input_type}")

        # Create the output
        output: BatchOutput | StreamingOutput
        if output_type == "batch":
            output = BatchOutput(
                output_folder=kwargs["output_folder"] if "output_folder" in kwargs else tempfile.mkdtemp(),
                bucket=kwargs["output_s3_bucket"] if "output_s3_bucket" in kwargs else None,
                s3_folder=kwargs["output_s3_folder"] if "output_s3_folder" in kwargs else None,
            )
        elif output_type == "streaming":
            output = StreamingOutput(
                kwargs["output_kafka_topic"] if "output_kafka_topic" in kwargs else None,
                (
                    kwargs["output_kafka_cluster_connection_string"]
                    if "output_kafka_cluster_connection_string" in kwargs
                    else None
                ),
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

        # Create the bolt
        bolt = klass(
            input=input,
            output=output,
            state=state,
            id=id,
            **kwargs,
        )
        bolt.state.set_state("status", {"status": "created", "time": time.time()})
        return bolt
