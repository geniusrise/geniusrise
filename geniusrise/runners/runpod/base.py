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
from typing import Optional
from argparse import ArgumentParser, Namespace
import runpod


class RunPodResourceManager:
    def __init__(self):
        self.log = logging.getLogger(self.__class__.__name__)
        self.api_key: Optional[str] = None
        runpod.api_key = self.api_key

    def _add_connection_args(self, parser: ArgumentParser) -> ArgumentParser:
        parser.add_argument("--api_key", help="API key for RunPod.", type=str, required=True)
        return parser

    def create_parser(self, parser: ArgumentParser) -> ArgumentParser:
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
        self.api_key = args.api_key  # Set the API key from arguments
        runpod.api_key = self.api_key  # Update the RunPod API key globally

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

    def status(self, endpoint_id: str, task_id: str) -> None:
        endpoint = runpod.Endpoint(endpoint_id)
        run_request = endpoint.get_run(task_id)
        self.log.info(f"Status of task {task_id}: {run_request.status()}")

    def run_task(self, endpoint_id: str, input_data: str) -> None:
        endpoint = runpod.Endpoint(endpoint_id)
        run_request = endpoint.run(input_data)
        self.log.info(f"Task submitted. ID: {run_request.id}")

    def get_pods(self) -> None:
        pods = runpod.get_pods()
        for pod in pods:
            self.log.info(f"Pod ID: {pod.id}, Status: {pod.status}")

    def stop_pod(self, pod_id: str) -> None:
        pod = runpod.Pod(pod_id)
        pod.stop()
        self.log.info(f"Stopped pod {pod_id}")

    def terminate_pod(self, pod_id: str) -> None:
        pod = runpod.Pod(pod_id)
        pod.terminate()
        self.log.info(f"Terminated pod {pod_id}")
