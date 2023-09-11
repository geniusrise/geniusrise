from argparse import ArgumentParser, Namespace
import json
import ast
from kubernetes import client
from kubernetes.client import ApiClient
from typing import Optional, List

from .deployment import Deployment


class Service(Deployment):
    def __init__(self):
        """
        🚀 Initialize the Service class for managing Kubernetes Services.
        """
        super().__init__()
        self.apps_api_instance: ApiClient = None  # type: ignore

    def create_parser(self, parser: ArgumentParser) -> ArgumentParser:
        """
        🎛 Create a parser for CLI commands related to Service functionalities.

        Args:
            parser (ArgumentParser): The main parser.

        Returns:
            ArgumentParser: The parser with subparsers for each command.
        """
        subparsers = parser.add_subparsers(dest="service")

        # Parser for create
        create_parser = subparsers.add_parser("create", help="Create a new service.")
        create_parser.add_argument("name", help="Name of the service.", type=str)
        create_parser.add_argument("image", help="Docker image for the service.", type=str)
        create_parser.add_argument("command", help="Command to run in the container.", type=str)
        create_parser.add_argument("--replicas", help="Number of replicas.", default=1, type=int)
        create_parser.add_argument("--port", help="Service port.", default=80, type=int)
        create_parser.add_argument("--target_port", help="Container target port.", default=8080, type=int)
        create_parser.add_argument("--env_vars", help="Environment variables as a JSON string.", type=str, default="{}")

        # Parser for delete
        delete_parser = subparsers.add_parser("delete", help="Delete a service.")
        delete_parser.add_argument("name", help="Name of the service.", type=str)

        # Parser for describe
        describe_parser = subparsers.add_parser("describe", help="Describe a service.")
        describe_parser.add_argument("name", help="Name of the service.", type=str)

        # Parser for show
        show_parser = subparsers.add_parser("show", help="List all services.")

        return parser

    def run(self, args: Namespace) -> None:
        """
        🚀 Run the Service manager.

        Args:
            args (Namespace): The parsed command line arguments.
        """
        if args.service == "create":
            self.create(
                args.name,
                args.image,
                ast.literal_eval(args.command) if type(args.command) is str else args.command,
                replicas=args.replicas,
                port=args.port,
                target_port=args.target_port,
                env_vars=json.loads(args.env_vars),
            )
        elif args.service == "delete":
            self.delete(args.name)
        elif args.service == "show":
            self.show()
        elif args.service == "describe":
            self.describe(args.name)
        else:
            self.log.error("Unknown command: %s", args.service)

    def __create_service_spec(self, port: int, target_port: int) -> client.V1ServiceSpec:
        """
        📦 Create a Kubernetes Service specification.

        Args:
            port (int): Service port.
            target_port (int): Container target port.

        Returns:
            client.V1ServiceSpec: The Service specification.
        """
        return client.V1ServiceSpec(
            selector=self.labels, ports=[client.V1ServicePort(port=port, target_port=target_port)]
        )

    def create(  # type: ignore
        self,
        name: str,
        image: str,
        command: List[str],
        registry_creds: Optional[dict] = None,
        is_service: bool = False,
        replicas: int = 1,
        port: int = 80,
        target_port: int = 8080,
        env_vars: dict = {},
        cpu: Optional[str] = None,
        memory: Optional[str] = None,
        storage: Optional[str] = None,
        gpu: Optional[str] = None,
    ) -> None:
        """
        🛠 Create a Kubernetes resource Service.

        Args:
            name (str): Name of the resource.
            image (str): Docker image for the resource.
            command (str): Command to run in the container.
            registry_creds (dict): Credentials for Docker registry.
            is_service (bool): Whether the resource is a service.
            replicas (int): Number of replicas for Deployment.
            port (int): Service port.
            target_port (int): Container target port.
            env_vars (dict): Environment variables for the resource.
            cpu (str): CPU requirements.
            memory (str): Memory requirements.
            storage (str): Storage requirements.
            gpu (str): GPU requirements.
        """
        # Create the underlying deployment
        super().create(
            name=name,
            image=image,
            command=command,
            registry_creds=registry_creds,
            is_service=is_service,
            replicas=replicas,
            env_vars=env_vars,
            cpu=cpu,
            memory=memory,
            storage=storage,
            gpu=gpu,
        )

        # Create the service
        service_spec = self.__create_service_spec(port, target_port)
        service = client.V1Service(
            api_version="v1",
            kind="Service",
            metadata=client.V1ObjectMeta(name=f"{name}-service", labels=self.labels, annotations=self.annotations),
            spec=service_spec,
        )
        self.api_instance.create_namespaced_service(self.namespace, service)
        self.log.info(f"🌐 Created service {name}-service")

    def delete(self, name: str, is_service: bool = False) -> None:
        """
        🗑 Delete a Kubernetes resource (Pod/Deployment/Service).

        Args:
            name (str): Name of the resource to delete.
            is_service (bool): Whether the resource is a service.
        """
        self.apps_api_instance.delete_namespaced_deployment(name, self.namespace)
        self.api_instance.delete_namespaced_service(f"{name}-service", self.namespace)

    def status(self, name: str) -> dict:  # type: ignore
        """
        📊 Get the status of a Kubernetes service.

        Args:
            name (str): Name of the service.

        Returns:
            dict: Status of the service.
        """
        super().status(name=name)

        return super().status(name=name)

    def show(self) -> list:
        """
        🌐 Show all services in the namespace.

        Returns:
            list: List of services.
        """
        service_list = self.api_instance.list_namespaced_service(self.namespace)
        return [
            {"name": service.metadata.name, "cluster_ip": service.spec.cluster_ip} for service in service_list.items
        ]

    def describe(self, service_name: str) -> dict:
        """
        🌐 Describe a Kubernetes service.

        Args:
            service_name (str): Name of the service.

        Returns:
            dict: Description of the service.
        """
        service = self.api_instance.read_namespaced_service(service_name, self.namespace)
        return {
            "name": service.metadata.name,
            "cluster_ip": service.spec.cluster_ip,
            "ports": [port.port for port in service.spec.ports],
        }
