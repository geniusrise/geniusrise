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

import json
from argparse import ArgumentParser, Namespace
from typing import Optional, Dict, Any
import runpod as rp

from .base import RunPodResourceManager


class RunPodEndpoint(RunPodResourceManager):
    """
    RunPodEndpointManager manages RunPod endpoints and templates.

    This class extends RunPodResourceManager to include functionalities specific to managing
    RunPod endpoints and templates. It provides methods to create and manage these resources
    and is designed to be used as a command-line tool.
    """

    def create_parser(self, parser: ArgumentParser) -> ArgumentParser:
        """
        Extend the parser from RunPodResourceManager with additional subparsers for endpoint
        and template management.

        Args:
            parser (ArgumentParser): The main argparse parser from the superclass.

        Returns:
            ArgumentParser: The extended parser with additional subparsers for RunPod endpoint operations.
        """
        subparsers = parser.add_subparsers(dest="endpoint_command")

        # fmt: off
        # Parser for creating a template
        template_parser = subparsers.add_parser("create_template", help="Create a new template on RunPod.")
        template_parser.add_argument("--name", help="Name of the template.", type=str, required=True)
        template_parser.add_argument("--image_name", help="Docker image name for the template.", type=str, required=True)
        template_parser.add_argument("--docker_start_cmd", help="Docker start command.", type=str)
        template_parser.add_argument("--container_disk_in_gb", help="Size of the container disk in GB.", type=int, default=10)
        template_parser.add_argument("--volume_in_gb", help="Size of the volume in GB.", type=int)
        template_parser.add_argument("--volume_mount_path", help="Where to mount the volume.", type=str)
        template_parser.add_argument("--ports", help="The ports to open in the template.", type=str)
        template_parser.add_argument("--env", help="Environment variables as a JSON string.", type=json.loads)
        template_parser.add_argument("--is_serverless", help="Whether the template is serverless or not.", type=bool, default=False)
        template_parser = self._add_connection_args(template_parser)

        # Parser for creating an endpoint
        endpoint_parser = subparsers.add_parser("create_endpoint", help="Create a new endpoint on RunPod.")
        endpoint_parser.add_argument("--name", help="Name of the endpoint.", type=str, required=True)
        endpoint_parser.add_argument("--template_id", help="ID of the template to use for the endpoint.", type=str, required=True)
        endpoint_parser.add_argument("--gpu_ids", help="GPU IDs for the endpoint.", type=str, default="AMPERE_16")
        endpoint_parser.add_argument("--network_volume_id", help="Network volume ID for the endpoint.", type=str)
        endpoint_parser.add_argument("--locations", help="Locations for the endpoint.", type=str)
        endpoint_parser.add_argument("--idle_timeout", help="Idle timeout for the endpoint.", type=int, default=5)
        endpoint_parser.add_argument("--scaler_type", help="Scaler type for the endpoint.", type=str, default="QUEUE_DELAY")
        endpoint_parser.add_argument("--scaler_value", help="Scaler value for the endpoint.", type=int, default=4)
        endpoint_parser.add_argument("--workers_min", help="Minimum number of workers for the endpoint.", type=int, default=0)
        endpoint_parser.add_argument("--workers_max", help="Maximum number of workers for the endpoint.", type=int, default=3)
        endpoint_parser = self._add_connection_args(endpoint_parser)

        # fmt: on
        return parser

    def run(self, args: Namespace) -> None:
        """
        Extend the run method to handle additional commands for managing endpoints and templates.

        Args:
            args (Namespace): Parsed command-line arguments.
        """
        super().run(args)

        if args.endpoint_command == "create_template":
            self.create_template(
                name=args.name,
                image_name=args.image_name,
                docker_start_cmd=args.docker_start_cmd,
                container_disk_in_gb=args.container_disk_in_gb,
                volume_in_gb=args.volume_in_gb,
                volume_mount_path=args.volume_mount_path,
                ports=args.ports,
                env=args.env,
                is_serverless=args.is_serverless,
            )
        elif args.endpoint_command == "create_endpoint":
            self.create_endpoint(
                name=args.name,
                template_id=args.template_id,
                gpu_ids=args.gpu_ids,
                network_volume_id=args.network_volume_id,
                locations=args.locations,
                idle_timeout=args.idle_timeout,
                scaler_type=args.scaler_type,
                scaler_value=args.scaler_value,
                workers_min=args.workers_min,
                workers_max=args.workers_max,
            )

    def create_template(
        self,
        name: str,
        image_name: str,
        docker_start_cmd: Optional[str] = None,
        container_disk_in_gb: int = 10,
        volume_in_gb: Optional[int] = None,
        volume_mount_path: Optional[str] = None,
        ports: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        is_serverless: bool = False,
    ) -> Dict[str, Any]:
        """
        Create a new template on RunPod.

        Args:
            name (str): The name of the template.
            image_name (str): The name of the docker image to be used by the template.
            docker_start_cmd (Optional[str]): The command to start the docker container with.
            container_disk_in_gb (int): Size of the container disk in GB. Defaults to 10.
            volume_in_gb (Optional[int]): Size of the volume in GB.
            volume_mount_path (Optional[str]): Where to mount the volume.
            ports (Optional[str]): The ports to open in the pod, example format - "8888/http,666/tcp".
            env (Optional[Dict[str, str]]): The environment variables to inject into the pod.
            is_serverless (bool): Whether the template is serverless or not. Defaults to False.

        Returns:
            Dict[str, Any]: The response from the RunPod API after creating the template.

        Raises:
            Exception: If the template creation fails.
        """
        try:
            response = rp.create_template(
                name=name,
                image_name=image_name,
                docker_start_cmd=docker_start_cmd,
                container_disk_in_gb=container_disk_in_gb,
                volume_in_gb=volume_in_gb,
                volume_mount_path=volume_mount_path,
                ports=ports,
                env=env,
                is_serverless=is_serverless,
            )
            self.log.info(f"Template created. ID: {response['id']}")
            return response
        except Exception as e:
            self.log.exception(f"Error creating template: {e}")
            raise

    def create_endpoint(
        self,
        name: str,
        template_id: str,
        gpu_ids: str = "AMPERE_16",
        network_volume_id: Optional[str] = None,
        locations: Optional[str] = None,
        idle_timeout: int = 5,
        scaler_type: str = "QUEUE_DELAY",
        scaler_value: int = 4,
        workers_min: int = 0,
        workers_max: int = 3,
    ) -> Dict[str, Any]:
        """
        Create a new endpoint on RunPod.

        Args:
            name (str): The name of the endpoint.
            template_id (str): The ID of the template to use for the endpoint.
            gpu_ids (str): The IDs of the GPUs to use for the endpoint. Defaults to "AMPERE_16".
            network_volume_id (Optional[str]): The ID of the network volume to use for the endpoint.
            locations (Optional[str]): The locations to use for the endpoint.
            idle_timeout (int): The idle timeout for the endpoint. Defaults to 5.
            scaler_type (str): The scaler type for the endpoint. Defaults to "QUEUE_DELAY".
            scaler_value (int): The scaler value for the endpoint. Defaults to 4.
            workers_min (int): The minimum number of workers for the endpoint. Defaults to 0.
            workers_max (int): The maximum number of workers for the endpoint. Defaults to 3.

        Returns:
            Dict[str, Any]: The response from the RunPod API after creating the endpoint.

        Raises:
            Exception: If the endpoint creation fails.
        """
        try:
            response = rp.create_endpoint(
                name=name,
                template_id=template_id,
                gpu_ids=gpu_ids,
                network_volume_id=network_volume_id,
                locations=locations,
                idle_timeout=idle_timeout,
                scaler_type=scaler_type,
                scaler_value=scaler_value,
                workers_min=workers_min,
                workers_max=workers_max,
            )
            self.log.info(f"Endpoint created. ID: {response['id']}")
            return response
        except Exception as e:
            self.log.exception(f"Error creating endpoint: {e}")
            raise
