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
from docker.types import (
    EndpointSpec,
    ServiceMode,
    UpdateConfig,
    RollbackConfig,
    Healthcheck,
    DNSConfig,
    Privileges,
)
from typing import Union, List, Dict, Any
from docker.errors import APIError
from rich.table import Table

from geniusrise.runners.docker.base import DockerResourceManager


class DockerSwarmManager(DockerResourceManager):
    r"""
    DockerSwarmManager is a utility for managing Docker Swarm services, including creating, inspecting, updating, and removing services. It extends DockerResourceManager to provide swarm-specific functionalities and commands via a command-line interface (CLI).

    The manager interacts with the Docker Swarm API, offering a convenient way to manage Swarm services, nodes, and other swarm-related tasks from the command line.

    CLI Usage:
        genius docker swarm [sub-command] [options]

    Sub-commands:
        - list_nodes: List all nodes in the Docker Swarm.
                    `genius docker swarm list_nodes`
        - inspect_node: Inspect a specific Swarm node by its ID.
                      `genius docker swarm inspect_node <node_id>`
        - create_service: Create a new service in the Docker Swarm with comprehensive specifications.
                        `genius docker swarm create_service [options]`
        - list_services: List all services in the Docker Swarm.
                       `genius docker swarm list_services`
        - inspect_service: Inspect a specific service by its ID.
                         `genius docker swarm inspect_service <service_id>`
        - update_service: Update an existing service with new parameters.
                        `genius docker swarm update_service <service_id> [options]`
        - remove_service: Remove a service from the Docker Swarm.
                        `genius docker swarm remove_service <service_id>`
        - service_logs: Retrieve logs of a Docker Swarm service.
                      `genius docker swarm service_logs <service_id> [--tail] [--follow]`
        - scale_service: Scale a service to a specified number of replicas.
                       `genius docker swarm scale_service <service_id> <replicas>`

    Each sub-command supports various options to specify the details of the swarm node or service operation. These options include node and service IDs, image and command specifications for services, environment variables, resource limits, and much more.

    Attributes:
        swarm_client: The Docker Swarm client connection to interact with the Docker Swarm API.
        log: Logger for the class to log information, warnings, and errors.
        console: Rich console object to print formatted and styled outputs.

    Methods:
        - connect_to_swarm: Method to establish a connection to the Docker Swarm.
        - list_nodes: Method to list all nodes in the Docker Swarm.
        - inspect_node: Method to inspect details of a specific Swarm node.
        - create_service: Method to create a new service with given specifications.
        - list_services: Method to list all services in the Docker Swarm.
        - inspect_service: Method to inspect a specific service.
        - update_service: Method to update an existing service with new parameters.
        - remove_service: Method to remove a service from the Docker Swarm.
        - get_service_logs: Method to retrieve logs of a Docker Swarm service.
        - scale_service: Method to scale a service to a specified number of replicas.

    Note:
        - Ensure that the Docker Swarm is initialized and running.
        - Make sure to have the necessary permissions to interact with the Docker Swarm and manage services and nodes.
    """

    def __init__(self):
        """
        Initialize the Docker Swarm Manager.
        """
        super().__init__()
        self.swarm_client = None

    def _add_service_spec_arguments(self, parser: ArgumentParser) -> ArgumentParser:
        """
        Add arguments to a parser for service specifications.

        Args:
            parser (ArgumentParser): The parser to add arguments to.
        """
        # fmt: off
        parser.add_argument("--image", required=True, help="Docker image to use for the service.")
        parser.add_argument("--command", nargs="+", help="Command to run in the service.")
        parser.add_argument("--args", nargs="+", help="Arguments to the command.")
        parser.add_argument("--constraints", nargs="+", help="Service placement constraints.")
        parser.add_argument("--preferences", nargs="+", help="Service placement preferences.")
        parser.add_argument("--maxreplicas", type=int, help="Maximum number of replicas per node.")
        parser.add_argument("--platforms", nargs="+", help="Platform constraints (arch, os).")
        parser.add_argument("--container_labels", type=json.loads, help="Labels for the container in JSON format.")
        parser.add_argument("--endpoint_spec", type=json.loads, help="Properties for service access (JSON format).")
        parser.add_argument("--env", nargs="+", help="Environment variables in the form KEY=val.")
        parser.add_argument("--hostname", help="Hostname to set on the container.")
        parser.add_argument("--init", action='store_true', help="Run an init inside the container that forwards signals and reaps processes.")
        parser.add_argument("--isolation", choices=['default', 'process', 'hyperv'], help="Isolation technology for the service's containers.")
        parser.add_argument("--labels", type=json.loads, help="Labels to apply to the service in JSON format.")
        parser.add_argument("--log_driver", help="Log driver to use for containers.")
        parser.add_argument("--log_driver_options", type=json.loads, help="Log driver options in JSON format.")
        parser.add_argument("--mode", choices=['replicated', 'global'], help="Scheduling mode for the service.")
        parser.add_argument("--mounts", nargs="+", help="Mounts for the containers in the form source:target:options.")
        parser.add_argument("--name", help="Name to give to the service.")
        parser.add_argument("--networks", nargs="+", help="List of network names or IDs to attach the service to.")
        parser.add_argument("--resources", type=json.loads, help="Resource limits and reservations in JSON format.")
        parser.add_argument("--restart_policy", type=json.loads, help="Restart policy for containers in JSON format.")
        parser.add_argument("--secrets", nargs="+", help="List of secrets accessible to containers for this service.")
        parser.add_argument("--stop_grace_period", type=int, help="Time to wait for containers to terminate before killing them.")
        parser.add_argument("--update_config", type=json.loads, help="Update strategy of the service in JSON format.")
        parser.add_argument("--rollback_config", type=json.loads, help="Rollback strategy of the service in JSON format.")
        parser.add_argument("--user", help="User to run commands as.")
        parser.add_argument("--workdir", help="Working directory for commands to run.")
        parser.add_argument("--tty", action='store_true', help="Allocate a pseudo-TTY.")
        parser.add_argument("--groups", nargs="+", help="A list of additional groups for the container process.")
        parser.add_argument("--open_stdin", action='store_true', help="Open stdin.")
        parser.add_argument("--read_only", action='store_true', help="Mount the container's root filesystem as read-only.")
        parser.add_argument("--stop_signal", help="Signal to stop the service's containers.")
        parser.add_argument("--healthcheck", type=json.loads, help="Healthcheck configuration for this service in JSON format.")
        parser.add_argument("--hosts", type=json.loads, help="Host to IP mappings to add to the container's hosts file in JSON format.")
        parser.add_argument("--dns_config", type=json.loads, help="DNS related configurations in JSON format.")
        parser.add_argument("--configs", nargs="+", help="List of config references exposed to the service.")
        parser.add_argument("--privileges", type=json.loads, help="Security options for the service's containers in JSON format.")
        parser.add_argument("--cap_add", nargs="+", help="List of kernel capabilities to add.")
        parser.add_argument("--cap_drop", nargs="+", help="List of kernel capabilities to drop.")
        parser.add_argument("--sysctls", type=json.loads, help="Sysctl values to add to the container in JSON format.")

        # fmt: on
        return parser

    def create_parser(self, parser: ArgumentParser) -> ArgumentParser:
        """
        Extend the parser for CLI commands to include Docker Swarm operations.

        Args:
            parser (ArgumentParser): The existing parser.

        Returns:
            ArgumentParser: The extended parser with Docker Swarm operations.
        """
        parser = super().create_parser(parser)

        # fmt: off
        # Adding Docker Swarm specific parsers
        swarm_subparsers = parser.add_subparsers(dest="swarm_command", required=False)

        # Parser for listing Swarm nodes
        list_nodes_parser = swarm_subparsers.add_parser("list_nodes", help="List all Swarm nodes.")
        list_nodes_parser = self._add_connection_args(list_nodes_parser)

        # Parser for inspecting a Swarm node
        inspect_node_parser = swarm_subparsers.add_parser("inspect_node", help="Inspect a specific Swarm node.")
        inspect_node_parser.add_argument("node_id", help="ID of the node to inspect.")
        inspect_node_parser = self._add_connection_args(inspect_node_parser)

        # Parser for creating a service
        create_service_parser = swarm_subparsers.add_parser("create_service", help="Create a new service.")
        create_service_parser.add_argument("image", help="Name of the docker image.")
        create_service_parser.add_argument("command", help="Command to execute in docker container.")
        create_service_parser = self._add_service_spec_arguments(create_service_parser)
        create_service_parser = self._add_connection_args(create_service_parser)

        # Parser for listing services
        list_services_parser = swarm_subparsers.add_parser("list_services", help="List all services.")
        list_services_parser = self._add_connection_args(list_services_parser)

        # Parser for inspecting a service
        inspect_service_parser = swarm_subparsers.add_parser("inspect_service", help="Inspect a specific service.")
        inspect_service_parser.add_argument("service_id", help="ID of the service to inspect.")
        inspect_service_parser = self._add_connection_args(inspect_service_parser)

        # Parser for updating a service
        update_service_parser = swarm_subparsers.add_parser("update_service", help="Update a service.")
        update_service_parser.add_argument("service_id", help="ID of the service to inspect.")
        update_service_parser.add_argument("image", help="Name of the docker image.")
        update_service_parser.add_argument("command", help="Command to execute in docker container.")
        update_service_parser = self._add_service_spec_arguments(update_service_parser)
        update_service_parser.add_argument("--force_update", type=bool, default=False, help="Forcefully update the service.")
        update_service_parser = self._add_connection_args(update_service_parser)

        # Parser for removing a service
        remove_service_parser = swarm_subparsers.add_parser("remove_service", help="Remove a service.")
        remove_service_parser.add_argument("service_id", help="ID of the service to remove.")
        remove_service_parser = self._add_connection_args(remove_service_parser)

        # Parser for retrieving service logs
        logs_parser = swarm_subparsers.add_parser("service_logs", help="Retrieve logs of a service.")
        logs_parser.add_argument("service_id", help="ID of the service to retrieve logs from.")
        logs_parser.add_argument("--tail", type=int, default=100, help="Number of lines to tail from the logs.")
        logs_parser.add_argument("--follow", action='store_true', help="Follow log output.")

        # Parser for scaling a service
        scale_parser = swarm_subparsers.add_parser("scale_service", help="Scale a service to a specified number of replicas.")
        scale_parser.add_argument("service_id", help="ID of the service to scale.")
        scale_parser.add_argument("replicas", type=int, help="Number of replicas to scale the service to.")

        # fmt: on
        return parser

    def run(self, args: Namespace) -> None:
        """
        Run the Docker Swarm Manager based on the parsed CLI arguments.

        Args:
            args (Namespace): The parsed CLI arguments.
        """
        super().run(args)  # Handle Docker commands

        # Handling Swarm-specific commands
        if hasattr(args, "swarm_command"):
            self.connect_to_swarm(args.base_url)

            if args.swarm_command == "list_nodes":
                nodes = self.list_nodes()
                self.log.debug(json.dumps([node.attrs for node in nodes], indent=4))

            elif args.swarm_command == "inspect_node":
                node = self.inspect_node(args.node_id)
                self.log.debug(json.dumps(node, indent=4))

            elif args.swarm_command == "create_service":
                service_id = self.create_service(image=args.image, command=args.command, args=args)
                self.log.debug(f"Service created with ID: {service_id}")

            elif args.swarm_command == "list_services":
                services = self.list_services()
                self.log.debug(json.dumps([service.attrs for service in services], indent=4))

            elif args.swarm_command == "inspect_service":
                service = self.inspect_service(args.service_id)
                self.log.debug(json.dumps(service, indent=4))

            elif args.swarm_command == "update_service":
                self.update_service(
                    service_id=args.service_id,
                    image=args.image,
                    command=args.command,
                    args=args,
                )
                self.log.debug(f"Service {args.service_id} updated.")

            elif args.swarm_command == "remove_service":
                self.remove_service(args.service_id)
                self.log.debug(f"Service {args.service_id} removed.")

            elif args.swarm_command == "service_logs":
                self.get_service_logs(args.service_id, tail=args.tail, follow=args.follow)

            elif args.swarm_command == "scale_service":
                self.scale_service(service_id=args.service_id, replicas=args.replicas)

        else:
            self.log.error(f"Unknown command: {args.swarm_command}")

    def connect_to_swarm(self, base_url: str = "unix://var/run/docker.sock") -> None:
        """
        Connect to the Docker Swarm.

        Args:
            base_url (str): URL to the Docker daemon.
        """
        super().connect(base_url=base_url)
        try:
            self.swarm_client = self.client.swarm
            self.log.info("Connected to Docker Swarm.")
        except APIError as e:
            self.log.error(f"Failed to connect to Docker Swarm: {e}")
            raise

    def list_nodes(self) -> List[Any]:
        """
        List all nodes in the Docker Swarm.

        Returns:
            List[Any]: List of Swarm nodes.
        """
        try:
            nodes = self.swarm_client.nodes.list()

            # Create a formatted table for nodes
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("ID", style="dim")
            table.add_column("Hostname")
            table.add_column("Status")
            table.add_column("Availability")
            table.add_column("Manager Status", justify="right")

            for node in nodes:
                node_attrs = node.attrs
                table.add_row(
                    node_attrs["ID"][:12],
                    node_attrs["Description"]["Hostname"],
                    node_attrs["Status"]["State"],
                    node_attrs["Spec"]["Availability"],
                    node_attrs["ManagerStatus"]["Reachability"] if "ManagerStatus" in node_attrs else "N/A",
                )

            self.console.print(table)

            return nodes
        except APIError as e:
            self.log.error(f"Error listing Swarm nodes: {e}")
            raise

    def inspect_node(self, node_id: str) -> Dict[str, Any]:
        """
        Inspect a specific Swarm node.

        Args:
            node_id (str): ID of the node to inspect.

        Returns:
            Dict[str, Any]: Node details.
        """
        try:
            node = self.swarm_client.nodes.get(node_id)
            self.console.print(node.attrs, style="bold green")
            return node.attrs
        except APIError as e:
            self.log.error(f"Error inspecting Swarm node {node_id}: {e}")
            raise

    def create_service(self, image: str, command: Union[str, List[str]], args: Namespace) -> str:
        """
        Create a new service in the Docker Swarm with comprehensive specifications.

        Args:
            image (str): Docker image to use for the service.
            command (Union[str, List[str]]): Command to run in the service.
            args (Namespace): Arguments from the CLI for service creation.

        Returns:
            str: ID of the created service.
        """
        service_specs = {
            "image": image,
            "command": command,
            "args": args.args,
            "constraints": args.constraints,
            "preferences": args.preferences,
            "maxreplicas": args.maxreplicas,
            "platforms": args.platforms,
            "container_labels": args.container_labels,
            "endpoint_spec": EndpointSpec(**args.endpoint_spec) if args.endpoint_spec else None,
            "env": args.env,
            "hostname": args.hostname,
            "init": args.init,
            "isolation": args.isolation,
            "labels": args.labels,
            "log_driver": args.log_driver,
            "log_driver_options": args.log_driver_options,
            "mode": ServiceMode(args.mode) if args.mode else None,
            "mounts": args.mounts,
            "name": args.name,
            "networks": args.networks,
            "resources": args.resources,
            "restart_policy": args.restart_policy,
            "secrets": args.secrets,
            "stop_grace_period": args.stop_grace_period,
            "update_config": UpdateConfig(**args.update_config) if args.update_config else None,
            "rollback_config": RollbackConfig(**args.rollback_config) if args.rollback_config else None,
            "user": args.user,
            "workdir": args.workdir,
            "tty": args.tty,
            "groups": args.groups,
            "open_stdin": args.open_stdin,
            "read_only": args.read_only,
            "stop_signal": args.stop_signal,
            "healthcheck": Healthcheck(**args.healthcheck) if args.healthcheck else None,
            "hosts": args.hosts,
            "dns_config": DNSConfig(**args.dns_config) if args.dns_config else None,
            "configs": args.configs,
            "privileges": Privileges(**args.privileges) if args.privileges else None,
            "cap_add": args.cap_add,
            "cap_drop": args.cap_drop,
            "sysctls": args.sysctls,
        }

        try:
            service = self.swarm_client.services.create(**service_specs)
            self.log.info(f"Service created with ID: {service.id}")
            return service.id
        except APIError as e:
            self.log.error(f"Error creating service: {e}")
            raise

    def list_services(self) -> List[Any]:
        """
        List all services in the Docker Swarm.

        Returns:
            List[Any]: List of services.
        """
        try:
            services = self.swarm_client.services.list()
            # TODO: Format and display services in a table or similar format
            return services
        except APIError as e:
            self.log.error(f"Error listing services: {e}")
            raise

    def inspect_service(self, service_id: str) -> Dict[str, Any]:
        """
        Inspect a specific service in the Docker Swarm.

        Args:
            service_id (str): ID of the service to inspect.

        Returns:
            Dict[str, Any]: Service details.
        """
        try:
            service = self.swarm_client.services.get(service_id)
            self.console.print(service.attrs, style="bold green")
            return service.attrs
        except APIError as e:
            self.log.error(f"Error inspecting service {service_id}: {e}")
            raise

    def update_service(
        self,
        service_id: str,
        image: str,
        command: Union[str, List[str]],
        args: Namespace,
    ) -> None:
        """
        Update an existing service in the Docker Swarm.

        Args:
            service_id (str): ID of the service to update.
            args (Namespace): Arguments from the CLI for service update.
        """
        update_specs = {
            "image": image,
            "command": command,
            "args": args.args,
            "constraints": args.constraints,
            "preferences": args.preferences,
            "maxreplicas": args.maxreplicas,
            "platforms": args.platforms,
            "container_labels": args.container_labels,
            "endpoint_spec": EndpointSpec(**args.endpoint_spec) if args.endpoint_spec else None,
            "env": args.env,
            "hostname": args.hostname,
            "init": args.init,
            "isolation": args.isolation,
            "labels": args.labels,
            "log_driver": args.log_driver,
            "log_driver_options": args.log_driver_options,
            "mode": ServiceMode(args.mode) if args.mode else None,
            "mounts": args.mounts,
            "name": args.name,
            "networks": args.networks,
            "resources": args.resources,
            "restart_policy": args.restart_policy,
            "secrets": args.secrets,
            "stop_grace_period": args.stop_grace_period,
            "update_config": UpdateConfig(**args.update_config) if args.update_config else None,
            "rollback_config": RollbackConfig(**args.rollback_config) if args.rollback_config else None,
            "user": args.user,
            "workdir": args.workdir,
            "tty": args.tty,
            "groups": args.groups,
            "open_stdin": args.open_stdin,
            "read_only": args.read_only,
            "stop_signal": args.stop_signal,
            "healthcheck": Healthcheck(**args.healthcheck) if args.healthcheck else None,
            "hosts": args.hosts,
            "dns_config": DNSConfig(**args.dns_config) if args.dns_config else None,
            "configs": args.configs,
            "privileges": Privileges(**args.privileges) if args.privileges else None,
            "cap_add": args.cap_add,
            "cap_drop": args.cap_drop,
            "sysctls": args.sysctls,
            "force_update": args.force_update,
        }

        try:
            service = self.swarm_client.services.get(service_id)
            service.update(**update_specs)
            self.log.info(f"Service {service_id} updated.")
        except APIError as e:
            self.log.error(f"Error updating service {service_id}: {e}")
            raise

    def remove_service(self, service_id: str) -> None:
        """
        Remove a service from the Docker Swarm.

        Args:
            service_id (str): ID of the service to remove.
        """
        try:
            service = self.swarm_client.services.get(service_id)
            service.remove()
            self.log.info(f"Service {service_id} removed.")
        except APIError as e:
            self.log.error(f"Error removing service {service_id}: {e}")
            raise

    def get_service_logs(self, service_id: str, tail: int = 100, follow: bool = False) -> None:
        """
        Retrieve logs of a Docker Swarm service.

        Args:
            service_id (str): ID of the service.
            tail (int): Number of lines to tail from the end of the logs. Defaults to 100.
            follow (bool): Follow log output. Defaults to False.
        """
        try:
            service = self.swarm_client.services.get(service_id)
            logs = service.logs(tail=tail, follow=follow, stdout=True, stderr=True)
            for line in logs:
                print(line.decode("utf-8").rstrip())
        except APIError as e:
            self.log.error(f"Error retrieving logs for service {service_id}: {e}")
            raise

    def scale_service(self, service_id: str, replicas: int) -> None:
        """
        Scale a Docker Swarm service to a specified number of replicas.

        Args:
            service_id (str): ID of the service to scale.
            replicas (int): Desired number of replicas.
        """
        try:
            service = self.swarm_client.services.get(service_id)
            service_spec = service.attrs["Spec"]
            service_spec["Mode"] = {"Replicated": {"Replicas": replicas}}
            service.update(**service_spec)
            self.log.info(f"Scaled service {service_id} to {replicas} replicas.")
        except APIError as e:
            self.log.error(f"Error scaling service {service_id}: {e}")
            raise
