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
from typing import Optional, List

from .base import K8sResourceManager


class Deployment(K8sResourceManager):
    def __init__(self):
        """
        🚀 Initialize the Deployment class for managing Kubernetes Deployments.
        """
        super().__init__()

    def create_parser(self, parser: ArgumentParser) -> ArgumentParser:
        """
        🎛 Create a parser for CLI commands related to Deployment functionalities.

        Args:
            parser (ArgumentParser): The main parser.

        Returns:
            ArgumentParser: The parser with subparsers for each command.
        """
        subparsers = parser.add_subparsers(dest="deployment")

        # Parser for create
        create_parser = subparsers.add_parser("create", help="Create a new deployment.")
        create_parser.add_argument("name", help="Name of the deployment.", type=str)
        create_parser.add_argument(
            "image", help="Docker image for the deployment.", type=str, default="geniusrise/geniusrise"
        )
        create_parser.add_argument("command", help="Command to run in the container.", type=str)
        create_parser.add_argument("--replicas", help="Number of replicas.", default=1, type=int)
        create_parser.add_argument("--env_vars", help="Environment variables as a JSON string.", type=str, default="{}")
        create_parser.add_argument("--cpu", help="CPU requirements.", type=str)
        create_parser.add_argument("--memory", help="Memory requirements.", type=str)
        create_parser.add_argument("--storage", help="Storage requirements.", type=str)
        create_parser.add_argument("--gpu", help="GPU requirements.", type=str)
        create_parser = self._add_connection_args(create_parser)

        # Parser for scale
        scale_parser = subparsers.add_parser("scale", help="Scale a deployment.")
        scale_parser.add_argument("name", help="Name of the deployment.", type=str)
        scale_parser.add_argument("replicas", help="Number of replicas.", type=int)
        scale_parser = self._add_connection_args(scale_parser)

        # Parser for describe
        describe_parser = subparsers.add_parser("describe", help="Describe a deployment.")
        describe_parser.add_argument("name", help="Name of the deployment.", type=str)
        describe_parser = self._add_connection_args(describe_parser)

        # Parser for show
        show_parser = subparsers.add_parser("show", help="List all deployments.")
        show_parser = self._add_connection_args(show_parser)

        # Parser for delete
        delete_parser = subparsers.add_parser("delete", help="Delete a deployment.")
        delete_parser.add_argument("name", help="Name of the deployment.", type=str)
        delete_parser = self._add_connection_args(delete_parser)

        # Parser for status
        status_parser = subparsers.add_parser("status", help="Get the status of a deployment.")
        status_parser.add_argument("name", help="Name of the deployment.", type=str)
        status_parser = self._add_connection_args(status_parser)

        return parser

    def run(self, args: Namespace) -> None:
        """
        🚀 Run the Deployment manager.

        Args:
            args (Namespace): The parsed command line arguments.
        """

        self.connect(
            kube_config_path=args.kube_config_path if args.kube_config_path else None,
            cluster_name=args.cluster_name if args.cluster_name else None,
            context_name=args.context_name if args.context_name else None,
            namespace=args.namespace if args.namespace else None,
            labels=args.labels if args.labels else {"created_by": "geniusrise"},
            annotations=args.annotations if args.annotations else None,
            api_key=args.api_key if args.api_key else None,
            api_host=args.api_host if args.api_host else None,
            verify_ssl=args.verify_ssl if args.verify_ssl else None,
            ssl_ca_cert=args.ssl_ca_cert if args.ssl_ca_cert else None,
        )

        if args.deployment == "create":
            self.create(
                args.name,
                args.image,
                ast.literal_eval(args.command) if type(args.command) is str else args.command,
                replicas=args.replicas,
                env_vars=json.loads(args.env_vars),
                cpu=args.cpu,
                memory=args.memory,
                storage=args.storage,
                gpu=args.gpu,
            )
        elif args.deployment == "scale":
            self.scale(args.name, args.replicas)
        elif args.deployment == "show":
            self.show()
        elif args.deployment == "describe":
            self.describe(args.name)
        elif args.deployment == "delete":
            self.delete(args.name)
        elif args.deployment == "status":
            self.status(args.name)
        else:
            self.log.error("Unknown command: %s", args.deployment)

    def __create_deployment_spec(
        self,
        image: str,
        command: List[str],
        replicas: int,
        image_pull_secret_name: str,
        env_vars: dict,
        cpu: Optional[str] = None,
        memory: Optional[str] = None,
        storage: Optional[str] = None,
        gpu: Optional[str] = None,
    ) -> client.V1DeploymentSpec:
        """
        📦 Create a Kubernetes Deployment specification.

        Args:
            image (str): Docker image for the Deployment.
            command (str): Command to run in the container.
            replicas (int): Number of replicas.
            image_pull_secret_name (str): Name of the image pull secret.
            env_vars (dict): Environment variables for the Deployment.
            cpu (str): CPU requirements.
            memory (str): Memory requirements.
            storage (str): Storage requirements.
            gpu (str): GPU requirements.

        Returns:
            client.V1DeploymentSpec: The Deployment specification.
        """
        return client.V1DeploymentSpec(
            replicas=replicas,
            selector=client.V1LabelSelector(match_labels=self.labels),
            template=client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(labels=self.labels, annotations=self.annotations),
                spec=self._create_pod_spec(image, command, image_pull_secret_name, env_vars, cpu, memory, storage, gpu),
            ),
        )

    def create(
        self,
        name: str,
        image: str,
        command: List[str],
        registry_creds: Optional[dict] = None,
        replicas: int = 1,
        env_vars: dict = {},
        cpu: Optional[str] = None,
        memory: Optional[str] = None,
        storage: Optional[str] = None,
        gpu: Optional[str] = None,
        **kwargs,
    ) -> None:
        """
        🛠 Create a Kubernetes resource Deployment.

        Args:
            name (str): Name of the resource.
            image (str): Docker image for the resource.
            command (str): Command to run in the container.
            registry_creds (dict): Credentials for Docker registry.
            replicas (int): Number of replicas for Deployment.
            env_vars (dict): Environment variables for the resource.
            cpu (str): CPU requirements.
            memory (str): Memory requirements.
            storage (str): Storage requirements.
            gpu (str): GPU requirements.
        """
        if registry_creds:
            secret_name = f"{name}-image-pull-secret"
            self.__create_image_pull_secret(secret_name, **registry_creds)
            self.log.info(f"🔑 Created image pull secret {secret_name}")
        else:
            secret_name = None

        deployment_spec = self.__create_deployment_spec(
            image,
            command,
            replicas,
            secret_name,  # type: ignore
            env_vars,
            cpu,
            memory,
            storage,
            gpu,
        )
        deployment = client.V1Deployment(
            api_version="apps/v1",
            kind="Deployment",
            metadata=client.V1ObjectMeta(name=name, labels=self.labels, annotations=self.annotations),
            spec=deployment_spec,
        )
        self.apps_api_instance.create_namespaced_deployment(self.namespace, deployment)
        self.log.info(f"🛠️ Created deployment {name}")

    def scale(self, name: str, replicas: int) -> None:
        """
        📈 Scale a Kubernetes deployment.

        Args:
            name (str): Name of the deployment.
            replicas (int): Number of replicas.
        """
        deployment = self.apps_api_instance.read_namespaced_deployment(name, self.namespace)
        deployment.spec.replicas = replicas
        self.apps_api_instance.patch_namespaced_deployment(name, self.namespace, deployment)
        self.log.info(f"📈 Scaled deployment {name} to {replicas} replicas")

    def show(self) -> list:
        """
        🗂 List all deployments in the namespace.

        Returns:
            list: List of deployments.
        """
        deployment_list = self.apps_api_instance.list_namespaced_deployment(self.namespace)
        return [
            {"name": deployment.metadata.name, "replicas": deployment.spec.replicas}
            for deployment in deployment_list.items
        ]

    def describe(self, deployment_name: str) -> dict:
        """
        🗂 Describe a Kubernetes deployment.

        Args:
            deployment_name (str): Name of the deployment.

        Returns:
            dict: Description of the deployment.
        """
        deployment = self.apps_api_instance.read_namespaced_deployment(deployment_name, self.namespace)
        return {
            "name": deployment.metadata.name,
            "replicas": deployment.spec.replicas,
            "labels": deployment.metadata.labels,
            "annotations": deployment.metadata.annotations,
        }

    def delete(self, name: str) -> None:
        """
        🗑 Delete a Kubernetes resource (Pod/Deployment/Service).

        Args:
            name (str): Name of the resource to delete.
        """
        self.apps_api_instance.delete_namespaced_deployment(name, self.namespace)

    def status(self, name: str) -> dict:  # type: ignore
        """
        📊 Get the status of a Kubernetes deployment.

        Args:
            name (str): Name of the deployment.

        Returns:
            dict: Status of the deployment.
        """
        deployment = self.apps_api_instance.read_namespaced_deployment(name, self.namespace)
        return {"deployment_status": deployment.status}
