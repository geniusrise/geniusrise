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
import json
import logging
import sys
import typing
import warnings
from concurrent.futures import ProcessPoolExecutor, wait
from multiprocessing import get_context
from typing import Dict, List, Any, Optional

import emoji  # type: ignore
import yaml  # type: ignore
from rich_argparse import RichHelpFormatter

from geniusrise.cli.schema import Geniusfile, Task
from geniusrise.cli.taskctl import TaskCtl
from geniusrise.cli.discover import DiscoveredTask


class YamlCtl:
    r"""
    Command-line interface for managing tasks based on a YAML configuration.

    The YamlCtl class provides methods to run specific or all tasks defined in a YAML file.
    The YAML file's structure is defined by the Geniusfile schema.

    Example YAML structure:

    ```yaml
    version: 1

    tasks:
      my_task:
        name: MyTask
        method: process
        input:
          type: batch
          args:
            input_folder: ./input
        output:
          type: batch
          args:
            output_folder: ./output
        state:
          type: none
        args:
          param1: value1
          param2: value2
    ```
    """

    def __init__(self, task_ctls: Dict[str, TaskCtl]):
        """
        Initialize YamlCtl.

        Args:
            task_ctls: A dictionary of task controllers.
        """
        self.task_ctls = task_ctls
        self.log = logging.getLogger(self.__class__.__name__)

    def create_parser(self, parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
        """
        Create a command-line parser with arguments for managing the YAML configuration.

        Args:
            parser: The parser to add arguments to.

        Returns:
            The parser with added arguments.
        """
        parser.formatter_class = RichHelpFormatter
        parser.description = "Manage tasks with a YAML file."

        subparsers = parser.add_subparsers(dest="command")

        # Create subparser for running a specific component
        run_parser = subparsers.add_parser(
            "run",
            help="Run a specific task.",
            formatter_class=RichHelpFormatter,
        )
        run_parser.add_argument(
            "task_name",
            help="The name of the task to run.",
        )
        run_parser.add_argument(
            "--file",
            "-f",
            help="The YAML file to use. Default: genius.yml",
            default="genius.yml",
        )

        # Create subparser for running all components
        run_all_parser = subparsers.add_parser(
            "run-all",
            help="Run all tasks.",
            formatter_class=RichHelpFormatter,
        )
        run_all_parser.add_argument(
            "--file",
            "-f",
            help="The YAML file to use. Default: genius.yml",
            default="genius.yml",
        )
        run_all_parser.add_argument(
            "--parallel",
            "-p",
            help="Run tasks in parallel.",
            action="store_true",
        )

        return parser

    def run(self, args: argparse.Namespace) -> Any:
        """
        Run the YAML configuration.

        Args:
            args: The parsed command-line arguments.

        Returns:
            The result of the operation.
        """
        # Parse the YAML file
        yaml_file = args.file if hasattr(args, "file") else "genius.yml"
        self.log.info(emoji.emojize(f":page_facing_up: Loading YAML file {yaml_file}..."))
        try:
            with open(yaml_file, "r") as f:
                yaml_content = yaml.safe_load(f)
        except FileNotFoundError:
            self.log.error(emoji.emojize(f":warning: YAML file {yaml_file} not found."))
            return
        except yaml.YAMLError as e:
            self.log.error(emoji.emojize(f":warning: Error parsing YAML file {yaml_file}: {e}"))
            return

        # Validate the YAML file
        try:
            geniusfile = Geniusfile(**yaml_content)
        except Exception as e:
            self.log.error(emoji.emojize(f":warning: Invalid YAML file {yaml_file}: {e}"))
            return

        if not hasattr(args, "command") or not args.command:
            self.log.error(emoji.emojize(":warning: No command specified."))
            return

        if args.command == "run":
            # Run a specific task
            if not geniusfile.tasks or args.task_name not in geniusfile.tasks:
                self.log.error(emoji.emojize(f":warning: Task {args.task_name} not found in {yaml_file}."))
                return
            return self.run_task(args.task_name, geniusfile.tasks[args.task_name])
        elif args.command == "run-all":
            # Run all tasks
            if args.parallel:
                self.log.info(emoji.emojize(":rocket: Running all tasks in parallel..."))
                return self.run_all_parallel(geniusfile)
            else:
                self.log.info(emoji.emojize(":rocket: Running all tasks..."))
                return self.run_all(geniusfile)
        else:
            self.log.error(emoji.emojize(f":warning: Unknown command {args.command}."))
            return

    def run_task(self, task_name: str, task_config: Task) -> Any:
        """
        Run a task.

        Args:
            task_name: The name of the task.
            task_config: The task configuration.

        Returns:
            The result of the task.
        """
        self.log.info(emoji.emojize(f":rocket: Running task {task_name}..."))

        # Get the task controller
        if task_config.name.lower() not in self.task_ctls:
            # We need to create a discovered task
            module_name, class_name = task_config.name.rsplit(".", 1) if "." in task_config.name else ("", task_config.name)
            try:
                if module_name:
                    module = importlib.import_module(module_name)
                    task_class = getattr(module, class_name)
                else:
                    # Try to find the class in the imported modules
                    found = False
                    for module_name in list(sys.modules.keys()):
                        module = sys.modules[module_name]
                        if hasattr(module, class_name):
                            task_class = getattr(module, class_name)
                            found = True
                            break
                    if not found:
                        raise ImportError(f"Could not find class {class_name} in any imported module.")

                discovered_task = DiscoveredTask(
                    name=class_name.lower(),
                    klass=task_class,
                    init_args={},
                )
                self.task_ctls[task_config.name.lower()] = TaskCtl(discovered_task)
            except (ImportError, AttributeError) as e:
                self.log.error(emoji.emojize(f":warning: Error getting task class {task_config.name}: {e}"))
                return

        # Parse input, output, and state configurations
        input_type = task_config.input.type if task_config.input else None
        output_type = task_config.output.type if task_config.output else None
        state_type = task_config.state.type if task_config.state else "none"

        # Create an argparse.Namespace to pass to the task controller
        task_args = argparse.Namespace()
        task_args.method = task_config.method

        # Add flags for input, output, and state types
        if input_type == "batch":
            task_args.batch_input = True
            task_args.streaming_input = False
        elif input_type == "streaming":
            task_args.batch_input = False
            task_args.streaming_input = True
        else:
            task_args.batch_input = False
            task_args.streaming_input = False

        if output_type == "batch":
            task_args.batch_output = True
            task_args.streaming_output = False
        elif output_type == "streaming":
            task_args.batch_output = False
            task_args.streaming_output = True
        else:
            task_args.batch_output = False
            task_args.streaming_output = False

        if state_type == "none":
            task_args.in_memory_state = True
            task_args.redis_state = False
            task_args.postgres_state = False
            task_args.dynamodb_state = False
        elif state_type == "redis":
            task_args.in_memory_state = False
            task_args.redis_state = True
            task_args.postgres_state = False
            task_args.dynamodb_state = False
        elif state_type == "postgres":
            task_args.in_memory_state = False
            task_args.redis_state = False
            task_args.postgres_state = True
            task_args.dynamodb_state = False
        elif state_type == "dynamodb":
            task_args.in_memory_state = False
            task_args.redis_state = False
            task_args.postgres_state = False
            task_args.dynamodb_state = True

        # Add task ID
        task_args.id = task_config.id

        # Add input, output, and state args
        if task_config.input and task_config.input.args:
            for arg_name, arg_value in task_config.input.args.items():
                setattr(task_args, arg_name, arg_value)

        if task_config.output and task_config.output.args:
            for arg_name, arg_value in task_config.output.args.items():
                setattr(task_args, arg_name, arg_value)

        if task_config.state and task_config.state.args:
            for arg_name, arg_value in task_config.state.args.items():
                setattr(task_args, arg_name, arg_value)

        # Add method args
        if task_config.args:
            for arg_name, arg_value in task_config.args.items():
                setattr(task_args, arg_name, arg_value)

        # Run the task
        return self.task_ctls[task_config.name.lower()].run(task_args)

    def run_all(self, geniusfile: Geniusfile) -> None:
        """
        Run all tasks.

        Args:
            geniusfile: The parsed YAML file.
        """
        # Run tasks
        if geniusfile.tasks:
            for task_name, task_config in geniusfile.tasks.items():
                self.run_task(task_name, task_config)

    def run_all_parallel(self, geniusfile: Geniusfile) -> None:
        """
        Run all tasks in parallel.

        Args:
            geniusfile: The parsed YAML file.
        """
        # Create a process pool
        with ProcessPoolExecutor(mp_context=get_context("spawn")) as executor:
            futures = []

            # Add tasks to the pool
            if geniusfile.tasks:
                for task_name, task_config in geniusfile.tasks.items():
                    futures.append(executor.submit(self.run_task, task_name, task_config))

            # Wait for all tasks to complete
            wait(futures)
