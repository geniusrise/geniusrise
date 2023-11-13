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
import json
from argparse import ArgumentParser, Namespace
from typing import Optional
import runpod as rp
import os


class RunPodResourceManager:
    """
    RunPodResourceManager manages RunPod tasks and pod operations.

    This class interfaces with the RunPod API to perform operations such as running tasks,
    checking their status, managing pods, and more. It is designed to be used as a command-line tool.

    Attributes:
        api_key (Optional[str]): API key for RunPod authentication.
    """

    def __init__(self):
        """
        Initialize the RunPod resource manager.

        This constructor method sets up the logging configuration and loads the API key from
        an environment variable. The API key is essential for authenticating requests to the
        RunPod service.

        The API key should be set as an environment variable named 'RUNPOD_API_KEY'.
        If the environment variable is not set, logging will record a warning.
        """
        self.log = logging.getLogger(self.__class__.__name__)
        self.api_key: Optional[str] = os.getenv("RUNPOD_API_KEY")
        rp.api_key = self.api_key

    def _add_connection_args(self, parser: ArgumentParser) -> ArgumentParser:
        """
        Add common connection arguments to an argparse parser.

        This method enhances a given ArgumentParser object by adding the '--api_key' argument
        to it, which is required for connecting to RunPod services.

        Args:
            parser (ArgumentParser): An existing ArgumentParser object to be extended.

        Returns:
            ArgumentParser: The modified parser with additional connection arguments.
        """
        parser.add_argument("--api_key", help="API key for rp.", type=str, required=True)
        return parser

    def create_parser(self, parser: ArgumentParser) -> ArgumentParser:
        """
        Create and configure a parser for RunPod resource manager CLI commands.

        This method sets up subparsers for various command-line actions such as 'status',
        'run', 'get_pods', 'stop', and 'terminate'. Each subparser is configured with necessary
        arguments for its corresponding action.

        Args:
            parser (ArgumentParser): The main argparse parser to which subparsers are added.

        Returns:
            ArgumentParser: The main parser configured with all subparsers for RunPod operations.
        """
        subparsers = parser.add_subparsers(dest="command")

        # Parser for status
        status_parser = subparsers.add_parser("status", help="Get the status of a RunPod task.")
        status_parser.add_argument("endpoint_id", help="ID of the RunPod endpoint.", type=str)
        status_parser.add_argument("task_id", help="ID of the task.", type=str)
        status_parser = self._add_connection_args(status_parser)

        # Parser for run
        run_parser = subparsers.add_parser("run", help="Run a task on a RunPod endpoint.")
        run_parser.add_argument("endpoint_id", help="ID of the RunPod endpoint.", type=str)
        run_parser.add_argument("input_data", help="Input data for the task as a JSON string.", type=str)
        run_parser = self._add_connection_args(run_parser)

        # Parser for get pods
        get_pods_parser = subparsers.add_parser("get_pods", help="Get all pods.")
        get_pods_parser = self._add_connection_args(get_pods_parser)

        # Parser for stopping a pod
        stop_parser = subparsers.add_parser("stop", help="Stop a RunPod pod.")
        stop_parser.add_argument("pod_id", help="ID of the RunPod pod.", type=str)
        stop_parser = self._add_connection_args(stop_parser)

        # Parser for terminating a pod
        terminate_parser = subparsers.add_parser("terminate", help="Terminate a RunPod pod.")
        terminate_parser.add_argument("pod_id", help="ID of the RunPod pod.", type=str)
        terminate_parser = self._add_connection_args(terminate_parser)

        return parser

    def run(self, args: Namespace) -> None:
        """
        Execute the appropriate action based on the parsed command-line arguments.

        This method acts as a dispatcher, calling the relevant internal method (like 'status',
        'run_task', etc.) based on the user's input command. It also ensures that the RunPod
        API key is set correctly before any action is performed.

        Args:
            args (Namespace): Parsed command-line arguments.
        """
        self.api_key = args.api_key  # Set the API key from arguments
        rp.api_key = self.api_key  # Update the RunPod API key globally

        if args.command == "status":
            self.status(args.endpoint_id, args.task_id)
        elif args.command == "run":
            self.run_task(args.endpoint_id, args.input_data)
        elif args.command == "get_pods":
            self.get_pods()
        elif args.command == "stop":
            self.stop_pod(args.pod_id)
        elif args.command == "terminate":
            self.terminate_pod(args.pod_id)
        else:
            self.log.exception("Unknown command: %s", args.command)
            raise

    def status(self, endpoint_id: str, task_id: str) -> None:
        """
        Retrieve and log the status of a specific task in RunPod.

        This method queries the status of a task identified by its 'task_id' on a specific
        'endpoint_id'. The status is logged for review.

        Args:
            endpoint_id (str): The identifier for the RunPod endpoint.
            task_id (str): The identifier of the task whose status is to be retrieved.

        The method logs the status of the specified task along with its ID.
        """
        endpoint = rp.Endpoint(endpoint_id)
        run_request = endpoint.get_run(task_id)
        self.log.info(f"Status of task {task_id}: {run_request.status()}")

    def run_task(self, endpoint_id: str, input_data: str) -> None:
        """
        Submit a task to be run on a RunPod endpoint.

        This method takes JSON-formatted input data and an endpoint ID, and submits a task
        to the RunPod service. It handles JSON parsing and logs the ID of the submitted task.

        Args:
            endpoint_id (str): The identifier for the RunPod endpoint where the task will be run.
            input_data (str): A JSON string containing the data for the task.

        Throws an error if the input data is not valid JSON or if the task submission fails.
        """
        try:
            input_data_json = json.loads(input_data)
        except json.JSONDecodeError:
            self.log.error("Invalid JSON input data.")
            return

        try:
            endpoint = rp.Endpoint(endpoint_id)
            run_request = endpoint.run(input_data_json)
            self.log.info(f"Task submitted. ID: {run_request.id}")
        except Exception as e:
            self.log.exception(f"Error running task: {e}")
            raise

    def get_pods(self) -> None:
        """
        Retrieve and log the list of all active pods from RunPod.

        This method queries RunPod for all active pods and logs their IDs and statuses.

        Each pod's ID and status are logged for review.
        """
        pods = rp.get_pods()
        for pod in pods:
            self.log.info(f"Pod ID: {pod.id}, Status: {pod.status}")

    def stop_pod(self, pod_id: str) -> None:
        """
        Stop a specific pod on RunPod.

        This method sends a request to stop a pod identified by 'pod_id'. The action is logged
        for confirmation.

        Args:
            pod_id (str): The identifier of the RunPod pod to be stopped.
        """
        pod = rp.Pod(pod_id)
        pod.stop()
        self.log.info(f"Stopped pod {pod_id}")

    def terminate_pod(self, pod_id: str) -> None:
        """
        Terminate a specific pod on RunPod.

        This method sends a request to terminate a pod identified by 'pod_id'. The termination
        action is logged for confirmation.

        Args:
            pod_id (str): The identifier of the RunPod pod to be terminated.
        """
        pod = rp.Pod(pod_id)
        pod.terminate()
        self.log.info(f"Terminated pod {pod_id}")
