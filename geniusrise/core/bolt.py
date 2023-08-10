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

import logging
import tempfile
from typing import Any

from geniusrise.core.data import (
    BatchInputConfig,
    BatchOutputConfig,
    InputConfig,
    OutputConfig,
    StreamingInputConfig,
    StreamingOutputConfig,
)
from geniusrise.core.state import (
    DynamoDBStateManager,
    InMemoryStateManager,
    PostgresStateManager,
    RedisStateManager,
    StateManager,
)

from .task import Task


class Bolt(Task):
    """
    Base class for all bolts.

    A bolt is a component that consumes streams of data, processes them, and possibly emits new data streams.
    """

    def __init__(
        self, input_config: InputConfig, output_config: OutputConfig, state_manager: StateManager, **kwargs
    ) -> None:
        """
        The `Bolt` class is a base class for all bolts in the given context.
        It inherits from the `Task` class and provides methods for executing tasks
        both locally and remotely, as well as managing their state, with state management
        options including in-memory, Redis, PostgreSQL, and DynamoDB,
        and input and output configurations for batch or streaming data.

        The `Bolt` class uses the `InputConfig`, `OutputConfig` and `StateManager` classes, which are abstract base
        classes for managing input configurations, output configurations and states, respectively. The `InputConfig` and
        `OutputConfig` classes each have two subclasses: `StreamingInputConfig`, `BatchInputConfig`, `StreamingOutputConfig`
        and `BatchOutputConfig`, which manage streaming and batch input and output configurations, respectively.
        The `StateManager` class is used to get and set state, and it has several subclasses for different types of state managers.

        The `Bolt` class also uses the `ECSManager` and `K8sManager` classes in the `execute_remote` method,
        which are used to manage tasks on Amazon ECS and Kubernetes, respectively.

        Usage:
            - Create an instance of the Bolt class by providing an InputConfig object, an OutputConfig object and a StateManager object.
            - The InputConfig object specifies the input configuration for the bolt.
            - The OutputConfig object specifies the output configuration for the bolt.
            - The StateManager object handles the management of the bolt's state.

        Example:
            input_config = InputConfig(...)
            output_config = OutputConfig(...)
            state_manager = StateManager(...)
            bolt = Bolt(input_config, output_config, state_manager)

        Args:
            input_config (InputConfig): The input configuration.
            output_config (OutputConfig): The output configuration.
            state_manager (StateManager): The state manager.
        """
        super().__init__()
        self.input_config = input_config
        self.output_config = output_config
        self.state_manager = state_manager

        self.log = logging.getLogger(self.__class__.__name__)

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
            state_type = self.state_manager.get_state(self.id)

            # Save the current set of class variables to the state manager
            self.state_manager.set_state(self.id, {})

            # Copy input data to local or connect to kafka and pass on the details
            if type(self.input_config) is BatchInputConfig:
                self.input_config.copy_from_remote()
                input_folder = self.input_config.get()
                kwargs["input_folder"] = input_folder
            elif type(self.input_config) is StreamingInputConfig:
                kafka_consumer = self.input_config.get()
                kwargs["kafka_consumer"] = kafka_consumer

            # Execute the task's method
            result = self.execute(method_name, *args, **kwargs)

            # Flush the output config
            self.output_config.flush()

            # Store the state as successful in the state manager
            state = {}
            state["status"] = "success"
            self.state_manager.set_state(self.id, state)

            return result
        except Exception as e:
            self.log.error(f"Failed to execute method '{method_name}': {e}")
            state = {}
            state["status"] = "failed"
            self.state_manager.set_state(self.id, state)
            raise

    @staticmethod
    def create(klass: type, input_type: str, output_type: str, state_type: str, **kwargs) -> "Bolt":
        """
        Create a bolt of a specific type.

        This static method is used to create a bolt of a specific type. It takes in an input type,
        an output type, a state type, and additional keyword arguments for initializing the bolt.

        The method creates the input config, output config, and state manager based on the provided types,
        and then creates and returns a bolt using these configurations.

        Args:
            klass (type): The Bolt class to create.
            input_type (str): The type of input config ("batch" or "streaming").
            output_type (str): The type of output config ("batch" or "streaming").
            state_type (str): The type of state manager ("in_memory", "redis", "postgres", or "dynamodb").
            **kwargs: Additional keyword arguments for initializing the bolt.
                Keyword Arguments:
                    Batch input config:
                    - input_folder (str): The input folder argument.
                    - input_bucket (str): The input bucket argument.
                    - input_s3_folder (str): The input S3 folder argument.
                    Batch outupt config:
                    - output_folder (str): The output folder argument.
                    - output_bucket (str): The output bucket argument.
                    - output_s3_folder (str): The output S3 folder argument.
                    Streaming input config:
                    - input_kafka_cluster_connection_string (str): The input Kafka servers argument.
                    - input_kafka_topic (str): The input kafka topic argument.
                    - input_kafka_consumer_group_id (str): The Kafka consumer group id.
                    Streaming output config:
                    - output_kafka_cluster_connection_string (str): The output Kafka servers argument.
                    - output_kafka_topic (str): The output kafka topic argument.
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

        Returns:
            Bolt: The created bolt.

        Raises:
            ValueError: If an invalid input type, output type, or state type is provided.
        """
        # Create the input config
        input_config: BatchInputConfig | StreamingInputConfig
        if input_type == "batch":
            input_config = BatchInputConfig(
                input_folder=kwargs["input_folder"] if "input_folder" in kwargs else tempfile.mkdtemp(),
                bucket=kwargs["input_bucket"] if "input_bucket" in kwargs else None,
                s3_folder=kwargs["input_s3_folder"] if "input_s3_folder" in kwargs else None,
            )
        elif input_type == "streaming":
            input_config = StreamingInputConfig(
                input_topic=kwargs["input_kafka_topic"] if "input_kafka_topic" in kwargs else None,
                kafka_cluster_connection_string=kwargs["input_kafka_cluster_connection_string"]
                if "input_kafka_cluster_connection_string" in kwargs
                else None,
                group_id=kwargs["input_kafka_consumer_group_id"] if "input_kafka_consumer_group_id" in kwargs else None,
            )
        else:
            raise ValueError(f"Invalid input type: {input_type}")

        # Create the output config
        output_config: BatchOutputConfig | StreamingOutputConfig
        if output_type == "batch":
            output_config = BatchOutputConfig(
                output_folder=kwargs["output_folder"] if "output_folder" in kwargs else tempfile.mkdtemp(),
                bucket=kwargs["output_bucket"] if "output_bucket" in kwargs else tempfile.mkdtemp(),
                s3_folder=kwargs["output_s3_folder"] if "output_s3_folder" in kwargs else tempfile.mkdtemp(),
            )
        elif output_type == "streaming":
            output_config = StreamingOutputConfig(
                kwargs["output_kafka_topic"] if "output_kafka_topic" in kwargs else None,
                kwargs["output_kafka_cluster_connection_string"]
                if "output_kafka_cluster_connection_string" in kwargs
                else None,
            )
        else:
            raise ValueError(f"Invalid output type: {output_type}")

        # Create the state manager
        state_manager: StateManager
        if state_type == "in_memory":
            state_manager = InMemoryStateManager()
        elif state_type == "redis":
            state_manager = RedisStateManager(
                host=kwargs["redis_host"] if "redis_host" in kwargs else None,
                port=kwargs["redis_port"] if "redis_port" in kwargs else None,
                db=kwargs["redis_db"] if "redis_db" in kwargs else None,
            )
        elif state_type == "postgres":
            state_manager = PostgresStateManager(
                host=kwargs["postgres_host"] if "postgres_host" in kwargs else None,
                port=kwargs["postgres_port"] if "postgres_port" in kwargs else None,
                user=kwargs["postgres_user"] if "postgres_user" in kwargs else None,
                password=kwargs["postgres_password"] if "postgres_password" in kwargs else None,
                database=kwargs["postgres_database"] if "postgres_database" in kwargs else None,
                table=kwargs["postgres_table"] if "postgres_table" in kwargs else None,
            )
        elif state_type == "dynamodb":
            state_manager = DynamoDBStateManager(
                table_name=kwargs["dynamodb_table_name"] if "dynamodb_table_name" in kwargs else None,
                region_name=kwargs["dynamodb_region_name"] if "dynamodb_region_name" in kwargs else None,
            )
        else:
            raise ValueError(f"Invalid state type: {state_type}")

        # Create the bolt
        bolt = klass(input_config=input_config, output_config=output_config, state_manager=state_manager, **kwargs)
        return bolt
