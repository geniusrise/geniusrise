# 🧠 Geniusrise
# Copyright (C) 2023-2025  geniusrise.ai
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
import time
import uuid
from logging import Logger
from typing import Any, Callable, Dict, Optional, Type, TypeVar, Union, cast

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

# Type variable for the Task class and its subclasses
T = TypeVar("T", bound="Task")


class Task:
    """
    Unified class for all tasks in Geniusrise.

    A task is a component that can consume data, process it, generate data, or both.
    This provides a flexible way to define components with different input/output needs.
    """

    def __init__(
        self,
        input: Optional[Input] = None,
        output: Optional[Output] = None,
        state: Optional[State] = None,
        id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Initialize a Task.

        Args:
            input: The input data source. Can be None for tasks that generate data.
            output: The output data destination. Can be None for tasks that only consume data.
            state: The state manager. If None, will use InMemoryState.
            id: Unique identifier for the task. If None, a UUID will be generated.
            **kwargs: Additional keyword arguments for specific task implementations.
        """
        self.id: str = id if id else f"{self.__class__.__name__}--{str(uuid.uuid4())}"
        self.input: Optional[Input] = input
        self.output: Optional[Output] = output
        self.state: State = state if state else InMemoryState(task_id=self.id)
        self.log: Logger = setup_logger(self.state)

    def execute(self, method_name: str, *args: Any, **kwargs: Any) -> Any:
        """
        Execute a method by name.

        Args:
            method_name: The name of the method to execute.
            *args: Positional arguments to pass to the method.
            **kwargs: Keyword arguments to pass to the method.

        Returns:
            The result of the method.

        Raises:
            AttributeError: If the method does not exist.
        """
        method: Callable[..., Any] = getattr(self, method_name)
        return method(*args, **kwargs)

    def __call__(self, method_name: str, *args: Any, **kwargs: Any) -> Any:
        """
        Execute a method locally and manage the state.

        Args:
            method_name: The name of the method to execute.
            *args: Positional arguments to pass to the method.
            **kwargs: Keyword arguments to pass to the method.

        Returns:
            The result of the method.
        """
        try:
            self.state.set_state("status", {"status": "getting_data", "time": time.time()})

            # Handle input data if available
            if self.input:
                if isinstance(self.input, BatchInput):
                    self.input.from_s3()

            self.state.set_state("status", {"status": "running", "time": time.time()})

            # Execute the task's method
            result = self.execute(method_name, *args, **kwargs)

            # Flush output data if available
            if self.output:
                self.output.flush()

            # Store the state as successful in the state manager
            self.state.set_state("status", {"status": "success", "time": time.time()})

            return result
        except Exception as e:
            self.state.set_state("status", {"status": "failed", "time": time.time()})
            self.log.exception(f"Failed to execute method '{method_name}': {e}")
            raise

    @classmethod
    def create(
        cls,
        klass: Type[T],
        input_type: Optional[str] = None,
        output_type: Optional[str] = None,
        state_type: str = "none",
        id: Optional[str] = None,
        **kwargs: Any,
    ) -> T:
        """
        Create a task of a specific type.

        Args:
            klass: The Task class to create.
            input_type: The type of input (e.g., "batch" or "streaming"). None for no input.
            output_type: The type of output (e.g., "batch" or "streaming"). None for no output.
            state_type: The type of state manager (e.g., "memory", "redis", "postgres", or "dynamodb").
            id: Unique identifier for the task. If None, a UUID will be generated.
            **kwargs: Additional keyword arguments for task initialization.

        Returns:
            The created task instance.

        Raises:
            ValueError: If an invalid input type, output type, or state type is provided.
            ImportError: If a required plugin for a specific backend is not installed.
        """
        # Import registries that contain available backends
        from geniusrise.core.data.input_registry import INPUT_BACKENDS
        from geniusrise.core.data.output_registry import OUTPUT_BACKENDS
        from geniusrise.core.state.registry import STATE_BACKENDS

        task_id: str = id if id else f"{klass.__name__}--{str(uuid.uuid4())}"
        log = setup_logger()

        # Create the input if specified
        input_instance: Optional[Input] = None
        if input_type:
            if input_type not in INPUT_BACKENDS:
                raise ImportError(
                    f"Input type '{input_type}' is not available. "
                    f"Install required plugin with: pip install geniusrise-data-{input_type}"
                )

            # Get the input class from the registry
            input_class = INPUT_BACKENDS[input_type]

            # Initialize based on input type
            if input_type == "batch":
                # Extract parameters for batch input
                input_folder: str = tempfile.mkdtemp()
                if "input_folder" in kwargs and kwargs["input_folder"] is not None:
                    input_folder = str(kwargs["input_folder"])

                bucket: str = ""
                if "input_s3_bucket" in kwargs and kwargs["input_s3_bucket"] is not None:
                    bucket = str(kwargs["input_s3_bucket"])

                s3_folder: Optional[str] = None
                if "input_s3_folder" in kwargs and kwargs["input_s3_folder"] is not None:
                    s3_folder = str(kwargs["input_s3_folder"])

                try:
                    input_instance = input_class(
                        input_folder=input_folder,
                        bucket=bucket,
                        s3_folder=s3_folder if s3_folder else "geniusrise",
                    )
                except Exception as e:
                    log.error(f"Failed to create {input_type} input: {e}.")
                    raise

            elif input_type == "streaming":
                # Extract parameters for streaming input
                input_topic: str = ""
                if "input_kafka_topic" in kwargs and kwargs["input_kafka_topic"] is not None:
                    input_topic = str(kwargs["input_kafka_topic"])

                kafka_conn: str = ""
                if (
                    "input_kafka_cluster_connection_string" in kwargs
                    and kwargs["input_kafka_cluster_connection_string"] is not None
                ):
                    kafka_conn = str(kwargs["input_kafka_cluster_connection_string"])

                group_id: str = "geniusrise"
                if "input_kafka_consumer_group_id" in kwargs and kwargs["input_kafka_consumer_group_id"] is not None:
                    group_id = str(kwargs["input_kafka_consumer_group_id"])

                try:
                    input_instance = input_class(
                        input_topic=input_topic,
                        kafka_cluster_connection_string=kafka_conn,
                        group_id=group_id,
                    )
                except Exception as e:
                    log.error(f"Failed to create {input_type} input: {e}.")
                    raise
            else:
                # For custom input types, pass all kwargs
                try:
                    input_instance = input_class(**kwargs)
                except Exception as e:
                    log.error(f"Failed to create {input_type} input: {e}.")
                    raise

        # Create the output if specified
        output_instance: Optional[Output] = None
        if output_type:
            if output_type not in OUTPUT_BACKENDS:
                raise ImportError(
                    f"Output type '{output_type}' is not available. "
                    f"Install required plugin with: pip install geniusrise-data-{output_type}"
                )

            # Get the output class from the registry
            output_class = OUTPUT_BACKENDS[output_type]

            # Initialize based on output type
            if output_type == "batch":
                # Extract parameters for batch output
                output_folder: str = tempfile.mkdtemp()
                if "output_folder" in kwargs and kwargs["output_folder"] is not None:
                    output_folder = str(kwargs["output_folder"])

                bucket: str = ""
                if "output_s3_bucket" in kwargs and kwargs["output_s3_bucket"] is not None:
                    bucket = str(kwargs["output_s3_bucket"])

                s3_folder: Optional[str] = None
                if "output_s3_folder" in kwargs and kwargs["output_s3_folder"] is not None:
                    s3_folder = str(kwargs["output_s3_folder"])

                try:
                    output_instance = output_class(
                        output_folder=output_folder,
                        bucket=bucket,
                        s3_folder=s3_folder if s3_folder else "geniusrise",
                    )
                except Exception as e:
                    log.error(f"Failed to create {output_type} output: {e}.")
                    raise

            elif output_type == "streaming":
                # Extract parameters for streaming output
                output_topic: str = ""
                if "output_kafka_topic" in kwargs and kwargs["output_kafka_topic"] is not None:
                    output_topic = str(kwargs["output_kafka_topic"])

                kafka_conn: str = ""
                if (
                    "output_kafka_cluster_connection_string" in kwargs
                    and kwargs["output_kafka_cluster_connection_string"] is not None
                ):
                    kafka_conn = str(kwargs["output_kafka_cluster_connection_string"])

                try:
                    output_instance = output_class(
                        output_topic=output_topic,
                        kafka_servers=kafka_conn,
                    )
                except Exception as e:
                    log.error(f"Failed to create {output_type} output: {e}.")
                    raise
            else:
                # For custom output types, pass all kwargs
                try:
                    output_instance = output_class(**kwargs)
                except Exception as e:
                    log.error(f"Failed to create {output_type} output: {e}.")
                    raise

        # Create the state manager with proper type handling
        state_instance: State

        # Handle state types
        if state_type == "none" or state_type == "memory":
            # Default to in-memory state
            state_instance = InMemoryState(task_id=task_id)
        elif state_type in STATE_BACKENDS:
            # Get the state backend class from the registry
            state_class = STATE_BACKENDS[state_type]

            # Initialize based on state type
            if state_type == "redis":
                # Extract Redis parameters
                redis_host: str = kwargs.get("redis_host", "localhost")
                redis_port: int = int(kwargs.get("redis_port", 6379))
                redis_db: int = int(kwargs.get("redis_db", 0))

                try:
                    state_instance = state_class(
                        task_id=task_id,
                        host=redis_host,
                        port=redis_port,
                        db=redis_db,
                    )
                except Exception as e:
                    log.error(f"Failed to create {state_type} state: {e}.")
                    raise

            elif state_type == "postgres":
                # Extract PostgreSQL parameters
                postgres_host: str = kwargs.get("postgres_host", "localhost")
                postgres_port: int = int(kwargs.get("postgres_port", 5432))
                postgres_user: str = kwargs.get("postgres_user", "postgres")
                postgres_password: str = kwargs.get("postgres_password", "")
                postgres_database: str = kwargs.get("postgres_database", "geniusrise")
                postgres_table: str = kwargs.get("postgres_table", "geniusrise_state")

                try:
                    state_instance = state_class(
                        task_id=task_id,
                        host=postgres_host,
                        port=postgres_port,
                        user=postgres_user,
                        password=postgres_password,
                        database=postgres_database,
                        table=postgres_table,
                    )
                except Exception as e:
                    log.error(f"Failed to create {state_type} state: {e}.")
                    raise

            elif state_type == "dynamodb":
                # Extract DynamoDB parameters
                table_name: str = kwargs.get("dynamodb_table_name", "geniusrise")
                region_name: str = kwargs.get("dynamodb_region_name", "us-east-1")

                try:
                    state_instance = state_class(
                        task_id=task_id,
                        table_name=table_name,
                        region_name=region_name,
                    )
                except Exception as e:
                    log.error(f"Failed to create {state_type} state: {e}.")
                    raise
            else:
                # For custom state types, pass task_id and kwargs
                try:
                    state_instance = state_class(task_id=task_id, **kwargs)
                except Exception as e:
                    log.error(f"Failed to create {state_type} state: {e}.")
                    raise
        else:
            available_types = list(STATE_BACKENDS.keys())
            raise ValueError(
                f"Invalid state type: {state_type}. Available types: {available_types}"
            )

        # Create the task
        task = klass(
            input=input_instance,
            output=output_instance,
            state=state_instance,
            id=task_id,
            **kwargs,
        )
        task.state.set_state("status", {"status": "created", "time": time.time()})
        return task
