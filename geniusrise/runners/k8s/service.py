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

from argparse import ArgumentParser, Namespace
import json
import ast
from kubernetes import client
from kubernetes.client import ApiClient
from typing import Optional, List

from .deployment import Deployment


class Service(Deployment):
    r"""
    🚀 Initialize the Service class for managing Kubernetes Services.

    CLI Usage:
        genius service [sub-command] [options]
        Examples:

        ```bash
        genius service create --name example-service --image example-image --command "echo hello" --port 8080 --target_port 8080
        ```

        ```bash
        genius service delete --name example-service
        ```

        ```bash
        genius service describe --name example-service
        ```

        ```bash
        genius service show
        ```

    YAML Configuration:

    ```yaml
    version: "1.0"
    services:
        - name: "example-service"
        image: "example-image"
        command: "example-command"
        replicas: 3
        port: 8080
        target_port: 8080
        env_vars:
            KEY: "value"
        cpu: "100m"
        memory: "256Mi"
        storage: "1Gi"
        gpu: "1"
    ```

    Extended CLI Examples:

        ```bash
            genius service deploy \
            --k8s_kind service \
            --k8s_namespace geniusrise \
            --k8s_context_name arn:aws:eks:us-east-1:genius-dev:cluster/geniusrise-dev \
            --k8s_name webhook \
            --k8s_image "genius-dev.dkr.ecr.ap-south-1.amazonaws.com/geniusrise" \
            --k8s_env_vars '{"AWS_DEFAULT_REGION": "ap-south-1", "AWS_SECRET_ACCESS_KEY": "", "AWS_ACCESS_KEY_ID": ""}' \
            --k8s_port 8080 \
            --k8s_target_port 8080
        ```

        ```bash
            genius service delete \
            webhook \
            --namespace geniusrise \
            --context_name arn:aws:eks:us-east-1:genius-dev:cluster/geniusrise-dev
        ```
    """

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
        create_parser.add_argument(
            "image", help="Docker image for the service.", type=str, default="geniusrise/geniusrise"
        )
        create_parser.add_argument("command", help="Command to run in the container.", type=str)
        create_parser.add_argument("--replicas", help="Number of replicas.", default=1, type=int)
        create_parser.add_argument("--port", help="Service port.", default=80, type=int)
        create_parser.add_argument("--target_port", help="Container target port.", default=8080, type=int)
        create_parser.add_argument("--env_vars", help="Environment variables as a JSON string.", type=str, default="{}")
        create_parser.add_argument("--cpu", help="CPU requirements.", type=str)
        create_parser.add_argument("--memory", help="Memory requirements.", type=str)
        create_parser.add_argument("--storage", help="Storage requirements.", type=str)
        create_parser.add_argument("--gpu", help="GPU requirements.", type=str)
        create_parser = self._add_connection_args(create_parser)

        # Parser for delete
        delete_parser = subparsers.add_parser("delete", help="Delete a service.")
        delete_parser.add_argument("name", help="Name of the service.", type=str)
        delete_parser = self._add_connection_args(delete_parser)

        # Parser for describe
        describe_parser = subparsers.add_parser("describe", help="Describe a service.")
        describe_parser.add_argument("name", help="Name of the service.", type=str)
        describe_parser = self._add_connection_args(describe_parser)

        # Parser for show
        show_parser = subparsers.add_parser("show", help="List all services.")
        show_parser = self._add_connection_args(show_parser)

        return parser

    def run(self, args: Namespace) -> None:
        """
        🚀 Run the Service manager.

        Args:
            args (Namespace): The parsed command line arguments.
        """
        self.connect(
            kube_config_path=args.kube_config_path if args.kube_config_path else None,
            cluster_name=args.cluster_name if args.cluster_name else None,
            context_name=args.context_name if args.context_name else None,
            namespace=args.namespace if args.namespace else None,
            labels=json.loads(args.labels) if args.labels else {"created_by": "geniusrise"},
            annotations=args.annotations if args.annotations else None,
            api_key=args.api_key if args.api_key else None,
            api_host=args.api_host if args.api_host else None,
            verify_ssl=args.verify_ssl if args.verify_ssl else None,
            ssl_ca_cert=args.ssl_ca_cert if args.ssl_ca_cert else None,
        )

        if args.service == "create":
            self.create(
                args.name,
                args.image,
                ast.literal_eval(args.command) if type(args.command) is str else args.command,
                replicas=args.replicas,
                port=args.port,
                target_port=args.target_port,
                env_vars=json.loads(args.env_vars),
                cpu=args.cpu,
                memory=args.memory,
                storage=args.storage,
                gpu=args.gpu,
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
        replicas: int = 1,
        port: int = 80,
        target_port: int = 8080,
        env_vars: dict = {},
        cpu: Optional[str] = None,
        memory: Optional[str] = None,
        storage: Optional[str] = None,
        gpu: Optional[str] = None,
        **kwargs,
    ) -> None:
        """
        🛠 Create a Kubernetes resource Service.

        Args:
            name (str): Name of the resource.
            image (str): Docker image for the resource.
            command (str): Command to run in the container.
            registry_creds (dict): Credentials for Docker registry.
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
            metadata=client.V1ObjectMeta(name=f"{name}", labels=self.labels, annotations=self.annotations),
            spec=service_spec,
        )
        self.api_instance.create_namespaced_service(self.namespace, service)
        self.log.info(f"🌐 Created service {name}")

    def delete(self, name: str) -> None:
        """
        🗑 Delete a Kubernetes resource (Pod/Deployment/Service).

        Args:
            name (str): Name of the resource to delete.
        """
        self.apps_api_instance.delete_namespaced_deployment(name, self.namespace)
        self.api_instance.delete_namespaced_service(f"{name}", self.namespace)
        self.log.info(f"🗑️ Deleted service {name}")

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
        self.log.info(f"🧿 Services: {[service.metadata.name for service in service_list.items]}")
        self.log.info(f"🧿 Cluster IPs: {[service.spec.cluster_ip for service in service_list.items]}")

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

        self.log.info(f"🧿 Service: {service.metadata.name}")
        self.log.info(f"🧿 Cluster IP: {service.spec.cluster_ip}")
        self.log.info(f"🧿 Ports: {service.spec.ports}")
        self.log.info(f"🧿 Labels: {service.metadata.labels}")
        self.log.info(f"🧿 Annotations: {service.metadata.annotations}")
        self.log.info(f"🧿 Target port: {service.spec.ports[0].target_port}")
        self.log.info(f"🧿 Port: {service.spec.ports[0].port}")

        return {
            "name": service.metadata.name,
            "cluster_ip": service.spec.cluster_ip,
            "ports": [port.port for port in service.spec.ports],
        }
