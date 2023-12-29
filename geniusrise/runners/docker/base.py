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
import logging
from argparse import ArgumentParser, Namespace
from typing import Any, Dict, List, Optional
from rich.console import Console
from rich.table import Table

import docker  # type: ignore


class DockerResourceManager:
    r"""
    DockerResourceManager is a utility for managing Docker resources, including containers and images. It provides a command-line interface (CLI) for various Docker operations, such as listing, inspecting, creating, starting, and stopping containers, as well as managing images.

    This class uses the Docker SDK for Python to interact with the Docker daemon, offering a convenient way to manage Docker containers and images from the command line.

    CLI Usage:
        genius docker [sub-command] [options]

    Sub-commands:
        - list_containers: List all containers, with an option to include stopped containers.
                         `genius docker list_containers [--all]`
        - inspect_container: Inspect a specific container by its ID.
                           `genius docker inspect_container <container_id>`
        - create_container: Create a new container with specified image, command, and other parameters.
                          `genius docker create_container <image> [options]`
        - start_container: Start a container by its ID.
                         `genius docker start_container <container_id>`
        - stop_container: Stop a container by its ID.
                        `genius docker stop_container <container_id>`
        - list_images: List all Docker images available on the local system.
                     `genius docker list_images`
        - inspect_image: Inspect a specific image by its ID.
                       `genius docker inspect_image <image_id>`
        - pull_image: Pull an image from a Docker registry.
                    `genius docker pull_image <image>`
        - push_image: Push an image to a Docker registry.
                    `genius docker push_image <image>`

    Each sub-command supports various options to specify the details of the container or image operation, such as environment variables, port mappings, volume mappings, and more.

    Attributes:
        client: The Docker client connection to interact with the Docker daemon.
        log: Logger for the class to log information, warnings, and errors.
        console: Rich console object to print formatted and styled outputs.

    Methods:
        - connect: Method to establish a connection to the Docker daemon.
        - list_containers: Method to list all containers, with an option to include stopped ones.
        - inspect_container: Method to inspect details of a specific container.
        - create_container: Method to create a new container with given parameters.
        - start_container: Method to start a specific container.
        - stop_container: Method to stop a specific container.
        - list_images: Method to list all Docker images.
        - inspect_image: Method to inspect a specific image.
        - pull_image: Method to pull an image from a Docker registry.
        - push_image: Method to push an image to a Docker registry.

    Note:
        - Ensure that the Docker daemon is running and accessible at the specified URL.
        - Make sure to have the necessary permissions to interact with the Docker daemon and manage containers and images.
    """

    def __init__(self):
        """
        Initialize the Docker Resource Manager.
        """
        self.client = None
        self.log = logging.getLogger(self.__class__.__name__)
        self.console = Console()

    def _add_connection_args(self, parser: ArgumentParser) -> ArgumentParser:
        parser.add_argument(
            "--base_url",
            help="URL of the docker daemon.",
            type=str,
            default="unix://var/run/docker.sock",
        )
        return parser

    def create_parser(self, parser: ArgumentParser) -> ArgumentParser:
        """
        Create a parser for CLI commands.

        Returns:
            ArgumentParser: The parser for Docker operations.
        """
        # fmt: off
        subparsers = parser.add_subparsers(dest="docker_command", required=True)

        # Parser for listing containers
        list_containers_parser = subparsers.add_parser("list_containers", help="List all containers.")
        list_containers_parser.add_argument("--all", action="store_true", help="Include stopped containers.")
        list_containers_parser = self._add_connection_args(list_containers_parser)

        # Parser for inspecting a container
        inspect_container_parser = subparsers.add_parser("inspect_container", help="Inspect a specific container.")
        inspect_container_parser.add_argument("container_id", help="ID of the container to inspect.")
        inspect_container_parser = self._add_connection_args(inspect_container_parser)

        # Parser for creating a container
        create_parser = subparsers.add_parser("create_container", help="Create a new container.")
        create_parser.add_argument("image", help="Docker image to use.")
        create_parser.add_argument("--command", help="Command to run in the container.", nargs="+")
        create_parser.add_argument("--name", help="Name of the container.")
        create_parser.add_argument("--env", help="Environment variables (key=value)", nargs="+")
        create_parser.add_argument("--port", help="Port mappings (host:container)", nargs="+")
        create_parser.add_argument("--volume", help="Volume mappings (host:container)", nargs="+")
        create_parser = self._add_connection_args(create_parser)

        # Parser for starting a container
        start_parser = subparsers.add_parser("start_container", help="Start a container.")
        start_parser.add_argument("container_id", help="ID of the container to start.")
        start_parser = self._add_connection_args(start_parser)

        # Parser for stopping a container
        stop_parser = subparsers.add_parser("stop_container", help="Stop a container.")
        stop_parser.add_argument("container_id", help="ID of the container to stop.")
        stop_parser = self._add_connection_args(stop_parser)

        # Parser for listing images
        list_images_parser = subparsers.add_parser("list_images", help="List all Docker images.")
        list_images_parser = self._add_connection_args(list_images_parser)

        # Parser for inspecting an image
        inspect_image_parser = subparsers.add_parser("inspect_image", help="Inspect a specific image.")
        inspect_image_parser.add_argument("image_id", help="ID of the image to inspect.")
        inspect_image_parser = self._add_connection_args(inspect_image_parser)

        # Parser for pulling an image
        pull_parser = subparsers.add_parser("pull_image", help="Pull an image.")
        pull_parser.add_argument("image", help="Name of the image to pull.")
        pull_parser = self._add_connection_args(pull_parser)

        # Parser for pushing an image
        push_parser = subparsers.add_parser("push_image", help="Push an image.")
        push_parser.add_argument("image", help="Name of the image to push.")
        push_parser = self._add_connection_args(push_parser)

        # fmt: on
        return parser

    def run(self, args: Namespace) -> None:
        """
        Run the Docker Resource Manager based on the parsed CLI arguments.

        Args:
            args (Namespace): The parsed CLI arguments.
        """
        self.connect()

        if args.docker_command == "list_containers":
            containers = self.list_containers(all_containers=args.all)
            print(json.dumps(containers, indent=4))

        elif args.docker_command == "inspect_container":
            container = self.inspect_container(args.container_id)
            print(json.dumps(container, indent=4))

        elif args.docker_command == "create_container":
            env_vars = dict(arg.split("=", 1) for arg in args.env) if args.env else None
            ports = dict(arg.split(":", 1) for arg in args.port) if args.port else None
            volumes = dict(arg.split(":", 1) for arg in args.volume) if args.volume else None

            container_id = self.create_container(
                image=args.image,
                command=args.command,
                name=args.name,
                env_vars=env_vars,
                ports=ports,
                volumes=volumes
                # Add additional kwargs if needed
            )
            self.log.info(f"Created container with ID: {container_id}")

        elif args.docker_command == "start_container":
            self.start_container(args.container_id)

        elif args.docker_command == "stop_container":
            self.stop_container(args.container_id)

        elif args.docker_command == "list_images":
            images = self.list_images()
            print(json.dumps(images, indent=4))

        elif args.docker_command == "inspect_image":
            image = self.inspect_image(args.image_id)
            print(json.dumps(image, indent=4))

        elif args.docker_command == "pull_image":
            self.pull_image(args.image)

        elif args.docker_command == "push_image":
            self.push_image(args.image)

        else:
            self.log.error(f"Unknown command: {args.docker_command}")

    def connect(self, base_url: str = "unix://var/run/docker.sock") -> None:
        """
        Connect to the Docker daemon.

        Args:
            base_url (str): URL to the Docker daemon.
        """
        try:
            self.client = docker.DockerClient(base_url=base_url)
            self.log.info("Connected to Docker daemon.")
        except Exception as e:
            self.log.error(f"Failed to connect to Docker daemon: {e}")
            raise

    def list_containers(self, all_containers: bool = False) -> List[Any]:
        """
        List all containers.

        Args:
            all_containers (bool): Flag to list all containers, including stopped ones.

        Returns:
            List[Any]: List of containers.
        """
        try:
            containers = self.client.containers.list(all=all_containers)

            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("ID", style="dim")
            table.add_column("Image")
            table.add_column("Status")

            for container in containers:
                table.add_row(
                    container.short_id,
                    ", ".join(container.image.tags),
                    container.status,
                )

            self.console.print(table)

            return containers
        except Exception as e:
            self.log.error(f"Error listing containers: {e}")
            raise

    def inspect_container(self, container_id: str) -> Dict[str, Any]:
        """
        Inspect a specific container.

        Args:
            container_id (str): ID of the container to inspect.

        Returns:
            Dict[str, Any]: Container details.
        """
        try:
            container = self.client.containers.get(container_id)
            self.console.print(container.attrs, style="bold green")
            return container.attrs
        except Exception as e:
            self.log.error(f"Error inspecting container {container_id}: {e}")
            raise

    def create_container(
        self,
        image: str,
        command: Optional[str] = None,
        name: Optional[str] = None,
        env_vars: Optional[Dict[str, str]] = None,
        ports: Optional[Dict[str, str]] = None,
        volumes: Optional[Dict[str, Dict[str, str]]] = None,
        **kwargs,
    ) -> str:
        """
        Create a new container.

        Args:
            image (str): Name of the image to create the container from.
            command (Optional[str]): Command to run in the container.
            name (Optional[str]): Name of the container.
            env_vars (Optional[Dict[str, str]]): Environment variables.
            ports (Optional[Dict[str, str]]): Port mappings.
            volumes (Optional[Dict[str, Dict[str, str]]]): Volume mappings.

        Returns:
            str: ID of the created container.
        """
        try:
            self.log.info(f"🌒 Creating container with image: {image}")
            container = self.client.containers.create(
                image,
                command=command,
                name=name,
                environment=env_vars,
                ports=ports,
                volumes=volumes,
                **kwargs,
            )
            self.log.info(f"🌕 Container created with ID: {container.id}")
            return container.id
        except Exception as e:
            self.log.error(f"Error creating container: {e}")
            raise

    def start_container(self, container_id: str) -> None:
        """
        Start a container.

        Args:
            container_id (str): ID of the container to start.
        """
        try:
            self.log.info(f"🌒 Starting container with ID: {container_id}")
            container = self.client.containers.get(container_id)
            container.start()
            self.log.info(f"🌕 Started container {container_id}")
        except Exception as e:
            self.log.error(f"Error starting container {container_id}: {e}")
            raise

    def stop_container(self, container_id: str) -> None:
        """
        Stop a container.

        Args:
            container_id (str): ID of the container to stop.
        """
        try:
            self.log.info(f"🌒 Stopping container with ID: {container_id}")
            container = self.client.containers.get(container_id)
            container.stop()
            self.log.info(f"🌑 Stopped container {container_id}")
        except Exception as e:
            self.log.error(f"Error stopping container {container_id}: {e}")
            raise

    def list_images(self) -> List[Any]:
        """
        List all Docker images.

        Returns:
            List[Any]: List of images.
        """
        try:
            images = self.client.images.list()

            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("ID", style="dim")
            table.add_column("Tags")

            for image in images:
                table.add_row(image.short_id, ", ".join(image.tags))
            self.console.print(table)

            return images
        except Exception as e:
            self.log.error(f"Error listing images: {e}")
            raise

    def inspect_image(self, image_id: str) -> Dict[str, Any]:
        """
        Inspect a specific image.

        Args:
            image_id (str): ID of the image to inspect.

        Returns:
            Dict[str, Any]: Image details.
        """
        try:
            image = self.client.images.get(image_id)

            self.console.print(image.attrs, style="bold green")

            return image.attrs
        except Exception as e:
            self.log.error(f"Error inspecting image {image_id}: {e}")
            raise

    def pull_image(self, image: str) -> None:
        """
        Pull an image from a Docker registry.

        Args:
            image (str): Name of the image to pull.
        """
        try:
            self.client.images.pull(image)
            self.log.info(f"✅ Pulled image {image}")
        except Exception as e:
            self.log.error(f"Error pulling image {image}: {e}")
            raise

    def push_image(self, image: str) -> None:
        """
        Push an image to a Docker registry.

        Args:
            image (str): Name of the image to push.
        """
        try:
            self.client.images.push(image)
            self.log.info(f"✅ Pushed image {image}")
        except Exception as e:
            self.log.error(f"Error pushing image {image}: {e}")
            raise
