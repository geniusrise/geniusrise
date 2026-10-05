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

import argparse
import importlib
import inspect
import logging
import warnings
from typing import Any, Dict, Optional

import emoji  # type: ignore
from rich_argparse import RichHelpFormatter  # type: ignore

from geniusrise.cli.discover import DiscoveredTask
from geniusrise.core import Task


class TaskCtl:
    """
    Command-line interface for managing tasks.

    The TaskCtl class provides methods to run the methods of a task.
    """

    def __init__(self, discovered_task: DiscoveredTask):
        """
        Initialize a TaskCtl instance.

        Args:
            discovered_task (DiscoveredTask): The discovered task to control.
        """
        self.discovered_task = discovered_task
        self.log = logging.getLogger(self.__class__.__name__)

    def create_parser(self, parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
        """
        Create a command-line parser with arguments for managing tasks.

        Args:
            parser (argparse.ArgumentParser): The parser to add arguments to.

        Returns:
            argparse.ArgumentParser: The parser with added arguments.
        """
        parser.formatter_class = RichHelpFormatter
        parser.description = f"Task: {self.discovered_task.name}"

        # Add a subparser for each method in the task
        methods = [
            m
            for m in dir(self.discovered_task.klass)
            if not m.startswith("_") and callable(getattr(self.discovered_task.klass, m))
        ]
        if not methods:
            self.log.warn(f"Task {self.discovered_task.name} has no methods.")
            return parser

        method_subparsers = parser.add_subparsers(dest="method")
        for method_name in methods:
            method_parser = method_subparsers.add_parser(
                method_name,
                help=f"Run the {method_name} method of task {self.discovered_task.name}.",
                formatter_class=RichHelpFormatter,
            )

            # Add arguments for the method
            method = getattr(self.discovered_task.klass, method_name)
            if hasattr(method, "__annotations__"):
                for param_name, param_type in method.__annotations__.items():
                    if param_name != "return":
                        method_parser.add_argument(
                            f"--{param_name}",
                            dest=param_name,
                            help=f"The {param_name} parameter of type {param_type}.",
                            required=True,
                        )

            # Add arguments for configuring the batch input
            input_group = method_parser.add_argument_group("Input Arguments")
            input_type_group = input_group.add_mutually_exclusive_group()
            input_type_group.add_argument(
                "--batch-input",
                action="store_true",
                help="Use batch input.",
            )
            input_type_group.add_argument(
                "--streaming-input",
                action="store_true",
                help="Use streaming input.",
            )
            input_group.add_argument(
                "--input-folder",
                help="Input folder for batch input.",
                default=None,
            )
            input_group.add_argument(
                "--input-s3-bucket",
                help="Input S3 bucket for batch input.",
                default=None,
            )
            input_group.add_argument(
                "--input-s3-folder",
                help="Input S3 folder for batch input.",
                default=None,
            )
            input_group.add_argument(
                "--input-kafka-topic",
                help="Input Kafka topic for streaming input.",
                default=None,
            )
            input_group.add_argument(
                "--input-kafka-cluster-connection-string",
                help="Input Kafka cluster connection string for streaming input.",
                default=None,
            )
            input_group.add_argument(
                "--input-kafka-consumer-group-id",
                help="Input Kafka consumer group ID for streaming input.",
                default=None,
            )

            # Add arguments for configuring the batch output
            output_group = method_parser.add_argument_group("Output Arguments")
            output_type_group = output_group.add_mutually_exclusive_group()
            output_type_group.add_argument(
                "--batch-output",
                action="store_true",
                help="Use batch output.",
            )
            output_type_group.add_argument(
                "--streaming-output",
                action="store_true",
                help="Use streaming output.",
            )
            output_group.add_argument(
                "--output-folder",
                help="Output folder for batch output.",
                default=None,
            )
            output_group.add_argument(
                "--output-s3-bucket",
                help="Output S3 bucket for batch output.",
                default=None,
            )
            output_group.add_argument(
                "--output-s3-folder",
                help="Output S3 folder for batch output.",
                default=None,
            )
            output_group.add_argument(
                "--output-kafka-topic",
                help="Output Kafka topic for streaming output.",
                default=None,
            )
            output_group.add_argument(
                "--output-kafka-cluster-connection-string",
                help="Output Kafka cluster connection string for streaming output.",
                default=None,
            )

            # Add arguments for configuring the state
            state_group = method_parser.add_argument_group("State Arguments")
            state_type_group = state_group.add_mutually_exclusive_group()
            state_type_group.add_argument(
                "--in-memory-state",
                action="store_true",
                help="Use in-memory state.",
            )
            state_type_group.add_argument(
                "--redis-state",
                action="store_true",
                help="Use Redis state.",
            )
            state_type_group.add_argument(
                "--postgres-state",
                action="store_true",
                help="Use Postgres state.",
            )
            state_type_group.add_argument(
                "--dynamodb-state",
                action="store_true",
                help="Use DynamoDB state.",
            )
            state_group.add_argument(
                "--redis-host",
                help="Redis host for Redis state.",
                default=None,
            )
            state_group.add_argument(
                "--redis-port",
                help="Redis port for Redis state.",
                default=None,
            )
            state_group.add_argument(
                "--redis-db",
                help="Redis database for Redis state.",
                default=None,
            )
            state_group.add_argument(
                "--postgres-host",
                help="Postgres host for Postgres state.",
                default=None,
            )
            state_group.add_argument(
                "--postgres-port",
                help="Postgres port for Postgres state.",
                default=None,
            )
            state_group.add_argument(
                "--postgres-user",
                help="Postgres user for Postgres state.",
                default=None,
            )
            state_group.add_argument(
                "--postgres-password",
                help="Postgres password for Postgres state.",
                default=None,
            )
            state_group.add_argument(
                "--postgres-database",
                help="Postgres database for Postgres state.",
                default=None,
            )
            state_group.add_argument(
                "--postgres-table",
                help="Postgres table for Postgres state.",
                default=None,
            )
            state_group.add_argument(
                "--dynamodb-table-name",
                help="DynamoDB table name for DynamoDB state.",
                default=None,
            )
            state_group.add_argument(
                "--dynamodb-region-name",
                help="DynamoDB region name for DynamoDB state.",
                default=None,
            )

            # Add a flag for the task ID
            method_parser.add_argument(
                "--id",
                help="A unique identifier for the task.",
                default=None,
            )

        return parser

    def run(self, args: argparse.Namespace) -> Any:
        """
        Run the task.

        Args:
            args (argparse.Namespace): The parsed command-line arguments.

        Returns:
            Any: The result of the task.
        """
        if not hasattr(args, "method") or not args.method:
            self.log.error("No method specified.")
            return

        self.log.info(emoji.emojize(f":rocket: Running task {self.discovered_task.name} method {args.method}"))

        # Determine the input type
        input_type = None
        if hasattr(args, "batch_input") and args.batch_input:
            input_type = "batch"
        elif hasattr(args, "streaming_input") and args.streaming_input:
            input_type = "streaming"

        # Determine the output type
        output_type = None
        if hasattr(args, "batch_output") and args.batch_output:
            output_type = "batch"
        elif hasattr(args, "streaming_output") and args.streaming_output:
            output_type = "streaming"

        # Determine the state type
        state_type = "none"
        if hasattr(args, "in_memory_state") and args.in_memory_state:
            state_type = "none"  # InMemoryState is the default for "none" state_type
        elif hasattr(args, "redis_state") and args.redis_state:
            state_type = "redis"
        elif hasattr(args, "postgres_state") and args.postgres_state:
            state_type = "postgres"
        elif hasattr(args, "dynamodb_state") and args.dynamodb_state:
            state_type = "dynamodb"

        # Create a dictionary of arguments for the task
        task_args = {}
        for arg_name, arg_value in vars(args).items():
            if arg_name not in [
                "method",
                "batch_input",
                "streaming_input",
                "batch_output",
                "streaming_output",
                "in_memory_state",
                "redis_state",
                "postgres_state",
                "dynamodb_state",
                "id",
                "top_level_command",
            ]:
                if arg_value is not None:
                    task_args[arg_name] = arg_value

        # Create the task
        task_id = args.id if hasattr(args, "id") else None
        task: Any = Task.create(
            klass=self.discovered_task.klass,
            input_type=input_type,
            output_type=output_type,
            state_type=state_type,
            id=task_id,
            **task_args,
        )

        # Run the task
        self.log.info(emoji.emojize(f":rocket: Running method {args.method}"))

        # Extract method-specific arguments
        method_kwargs = {}

        # Check if the target method has annotations to identify expected parameters
        method = getattr(self.discovered_task.klass, args.method, None)
        if method and hasattr(method, "__annotations__"):
            for param_name in method.__annotations__:
                if param_name != "return" and hasattr(args, param_name):
                    method_kwargs[param_name] = getattr(args, param_name)

        result = task(args.method, **method_kwargs)

        return result
