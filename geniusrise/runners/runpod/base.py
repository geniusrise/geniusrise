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
from typing import Optional, Dict, Any
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
        subparsers = parser.add_subparsers(dest="runpod_command")

        # fmt: off
        # Parser for run
        run_parser = subparsers.add_parser("create_pod", help="Run a task on a RunPod endpoint.")
        run_parser.add_argument("--pod_name", help="Name of the pod to create.", type=str, required=True)
        run_parser.add_argument("--image_name", help="Docker image name for the pod.", type=str, required=True)
        run_parser.add_argument("--gpu_type_id", help="GPU type ID for the pod.", type=str, required=True)
        run_parser.add_argument("--cloud_type", help="Type of cloud for the pod. Defaults to 'ALL'.", type=str, default="ALL")
        run_parser.add_argument("--support_public_ip", help="Whether to support public IP. Defaults to True.", type=bool, default=True)
        run_parser.add_argument("--start_ssh", help="Whether to start SSH. Defaults to True.", type=bool, default=True)
        run_parser.add_argument("--data_center_id", help="The ID of the data center.", type=str)
        run_parser.add_argument("--country_code", help="The code for the country to start the pod in.", type=str)
        run_parser.add_argument("--gpu_count", help="How many GPUs should be attached to the pod. Defaults to 1.", type=int, default=1)
        run_parser.add_argument("--volume_in_gb", help="How big should the pod volume be. Defaults to 0.", type=int, default=0)
        run_parser.add_argument("--container_disk_in_gb", help="Size of the container disk in GB.", type=int)
        run_parser.add_argument("--min_vcpu_count", help="Minimum vCPU count. Defaults to 1.", type=int, default=1)
        run_parser.add_argument("--min_memory_in_gb", help="Minimum memory in GB. Defaults to 1.", type=int, default=1)
        run_parser.add_argument("--docker_args", help="Docker arguments.", type=str, default="")
        run_parser.add_argument("--ports", help="The ports to open in the pod.", type=str)
        run_parser.add_argument("--volume_mount_path", help="Where to mount the volume. Defaults to '/runpod-volume'.", type=str, default="/runpod-volume")
        run_parser.add_argument("--env", help="Environment variables to inject into the pod as a JSON string.", type=json.loads)
        run_parser.add_argument("--template_id", help="The ID of the template to use for the pod.", type=str)
        run_parser.add_argument("--network_volume_id", help="The ID of the network volume to use for the pod.", type=str)
        run_parser = self._add_connection_args(run_parser)

        # Parser for get pods
        get_pods_parser = subparsers.add_parser("get_pods", help="Get all pods.")
        get_pods_parser = self._add_connection_args(get_pods_parser)

        # Parser for stopping a pod
        stop_parser = subparsers.add_parser("stop_pod", help="Stop a RunPod pod.")
        stop_parser.add_argument("pod_id", help="ID of the RunPod pod.", type=str)
        stop_parser = self._add_connection_args(stop_parser)

        # Parser for terminating a pod
        terminate_parser = subparsers.add_parser("terminate_pod", help="Terminate a RunPod pod.")
        terminate_parser.add_argument("pod_id", help="ID of the RunPod pod.", type=str)
        terminate_parser = self._add_connection_args(terminate_parser)

        # fmt: on
        return parser

    def run(self, args: Namespace) -> None:
        """
        Execute the appropriate action based on the parsed command-line arguments.

        This method acts as a dispatcher, calling the relevant internal method (like
        'create_pod', etc.) based on the user's input command. It also ensures that the RunPod
        API key is set correctly before any action is performed.

        Args:
            args (Namespace): Parsed command-line arguments.
        """
        self.api_key = args.api_key  # Set the API key from arguments
        rp.api_key = self.api_key  # Update the RunPod API key globally

        if args.runpod_command == "create_pod":
            self.create_pod(
                pod_name=args.pod_name,
                image_name=args.image_name,
                gpu_type_id=args.gpu_type_id,
                cloud_type=args.cloud_type,
                support_public_ip=args.support_public_ip,
                start_ssh=args.start_ssh,
                data_center_id=args.data_center_id,
                country_code=args.country_code,
                gpu_count=args.gpu_count,
                volume_in_gb=args.volume_in_gb,
                container_disk_in_gb=args.container_disk_in_gb,
                min_vcpu_count=args.min_vcpu_count,
                min_memory_in_gb=args.min_memory_in_gb,
                docker_args=args.docker_args,
                ports=args.ports,
                volume_mount_path=args.volume_mount_path,
                env=args.env,
                template_id=args.template_id,
                network_volume_id=args.network_volume_id,
            )
        elif args.runpod_command == "get_pods":
            self.get_pods()
        elif args.runpod_command == "stop_pod":
            self.stop_pod(args.pod_id)
        elif args.runpod_command == "terminate_pod":
            self.terminate_pod(args.pod_id)
        else:
            self.log.exception("Unknown command: %s", args.command)
            raise

    def __create_pod(
        self,
        name: str,
        image_name: str,
        gpu_type_id: str,
        cloud_type: str = "ALL",
        support_public_ip: bool = True,
        start_ssh: bool = True,
        data_center_id: Optional[str] = None,
        country_code: Optional[str] = None,
        gpu_count: int = 1,
        volume_in_gb: int = 0,
        container_disk_in_gb: Optional[int] = None,
        min_vcpu_count: int = 1,
        min_memory_in_gb: int = 1,
        docker_args: str = "",
        ports: Optional[str] = None,
        volume_mount_path: str = "/runpod-volume",
        env: Optional[Dict[str, str]] = None,
        template_id: Optional[str] = None,
        network_volume_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new pod on RunPod.

        Args:
            name (str): The name of the pod.
            image_name (str): The name of the docker image to be used by the pod.
            gpu_type_id (str): The GPU type wanted by the pod (retrievable by get_gpus).
            cloud_type (str): If secure cloud, community cloud, or all is wanted. Defaults to "ALL".
            support_public_ip (bool): Whether to support public IP. Defaults to True.
            start_ssh (bool): Whether to start SSH. Defaults to True.
            data_center_id (Optional[str]): The ID of the data center.
            country_code (Optional[str]): The code for the country to start the pod in.
            gpu_count (int): How many GPUs should be attached to the pod. Defaults to 1.
            volume_in_gb (int): How big should the pod volume be. Defaults to 0.
            container_disk_in_gb (Optional[int]): Size of the container disk in GB.
            min_vcpu_count (int): Minimum vCPU count. Defaults to 1.
            min_memory_in_gb (int): Minimum memory in GB. Defaults to 1.
            docker_args (str): Docker arguments. Defaults to an empty string.
            ports (Optional[str]): The ports to open in the pod.
            volume_mount_path (str): Where to mount the volume. Defaults to "/runpod-volume".
            env (Optional[Dict[str, str]]): Environment variables to inject into the pod.
            template_id (Optional[str]): The ID of the template to use for the pod.
            network_volume_id (Optional[str]): The ID of the network volume to use for the pod.

        Returns:
            Dict[str, Any]: The response from the RunPod API after creating the pod.

        Raises:
            Exception: If the pod creation fails.
        """
        try:
            response = rp.create_pod(
                name=name,
                image_name=image_name,
                gpu_type_id=gpu_type_id,
                cloud_type=cloud_type,
                support_public_ip=support_public_ip,
                start_ssh=start_ssh,
                data_center_id=data_center_id,
                country_code=country_code,
                gpu_count=gpu_count,
                volume_in_gb=volume_in_gb,
                container_disk_in_gb=container_disk_in_gb,
                min_vcpu_count=min_vcpu_count,
                min_memory_in_gb=min_memory_in_gb,
                docker_args=docker_args,
                ports=ports,
                volume_mount_path=volume_mount_path,
                env=env,
                template_id=template_id,
                network_volume_id=network_volume_id,
            )
            self.log.info(f"Pod created. ID: {response['id']}")
            return response
        except Exception as e:
            self.log.exception(f"Error creating pod: {e}")
            raise

    def create_pod(
        self,
        pod_name: str,
        image_name: str,
        gpu_type_id: str,
        cloud_type: str = "ALL",
        support_public_ip: bool = True,
        start_ssh: bool = True,
        data_center_id: Optional[str] = None,
        country_code: Optional[str] = None,
        gpu_count: int = 1,
        volume_in_gb: int = 0,
        container_disk_in_gb: Optional[int] = None,
        min_vcpu_count: int = 1,
        min_memory_in_gb: int = 1,
        docker_args: str = "",
        ports: Optional[str] = None,
        volume_mount_path: str = "/runpod-volume",
        env: Optional[Dict[str, str]] = None,
        template_id: Optional[str] = None,
        network_volume_id: Optional[str] = None,
    ) -> None:
        """
        Submit a task with specified parameters to be run on a RunPod endpoint.
        Optionally, create a new pod before running the task.

        Args:
            pod_name (str): Name of the pod to create.
            image_name (str): Docker image name for the pod.
            gpu_type_id (str): GPU type ID for the pod.
            cloud_type (str): Type of cloud for the pod. Defaults to "ALL".
            support_public_ip (bool): Whether to support public IP. Defaults to True.
            start_ssh (bool): Whether to start SSH. Defaults to True.
            data_center_id (Optional[str]): The ID of the data center.
            country_code (Optional[str]): The code for the country to start the pod in.
            gpu_count (int): How many GPUs should be attached to the pod. Defaults to 1.
            volume_in_gb (int): How big should the pod volume be. Defaults to 0.
            container_disk_in_gb (Optional[int]): Size of the container disk in GB.
            min_vcpu_count (int): Minimum vCPU count. Defaults to 1.
            min_memory_in_gb (int): Minimum memory in GB. Defaults to 1.
            docker_args (str): Docker arguments. Defaults to an empty string.
            ports (Optional[str]): The ports to open in the pod.
            volume_mount_path (str): Where to mount the volume. Defaults to "/runpod-volume".
            env (Optional[Dict[str, str]]): Environment variables to inject into the pod.
            template_id (Optional[str]): The ID of the template to use for the pod.
            network_volume_id (Optional[str]): The ID of the network volume to use for the pod.
        """
        try:
            pod_response = self.__create_pod(
                name=pod_name,
                image_name=image_name,
                gpu_type_id=gpu_type_id,
                cloud_type=cloud_type,
                support_public_ip=support_public_ip,
                start_ssh=start_ssh,
                data_center_id=data_center_id,
                country_code=country_code,
                gpu_count=gpu_count,
                volume_in_gb=volume_in_gb,
                container_disk_in_gb=container_disk_in_gb,
                min_vcpu_count=min_vcpu_count,
                min_memory_in_gb=min_memory_in_gb,
                docker_args=docker_args,
                ports=ports,
                volume_mount_path=volume_mount_path,
                env=env,
                template_id=template_id,
                network_volume_id=network_volume_id,
            )
            self.log.info(f"New pod created with ID: {pod_response['id']}")
        except Exception as e:
            self.log.exception(f"Failed to create pod: {e}")
            return

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
