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
import base64
import time
import logging
from argparse import ArgumentParser, Namespace
from kubernetes import client, config
from kubernetes.client import Configuration, ApiClient, V1ResourceRequirements, BatchV1Api
from typing import Optional, List


class K8sResourceManager:
    def __init__(self):
        """
        🚀 Initialize the Kubernetes Resource Manager.

        Attributes:
            api_instance: Core API instance for Kubernetes
            apps_api_instance: Apps API instance for Kubernetes
            cluster_name: Name of the Kubernetes cluster
            context_name: Name of the kubeconfig context
            namespace: Kubernetes namespace
            labels: Labels for Kubernetes resources
            annotations: Annotations for Kubernetes resources
        """
        self.log = logging.getLogger(self.__class__.__name__)

        self.api_instance: ApiClient = None  # type: ignore
        self.cluster_name: str = None  # type: ignore
        self.context_name: str = None  # type: ignore
        self.namespace: str = None  # type: ignore
        self.labels: dict = {}  # type: ignore
        self.annotations: dict = {}  # type: ignore

    def _add_connection_args(self, parser: ArgumentParser) -> ArgumentParser:
        """
        🛠 Add common cluster connection arguments to a parser.

        Args:
            parser (ArgumentParser): The parser to which arguments will be added.

        Returns:
            ArgumentParser: The parser with added arguments.
        """
        parser.add_argument(
            "--kube_config_path", help="Path to the kubeconfig file.", type=str, default="~/.kube/config"
        )
        parser.add_argument("--cluster_name", help="Name of the Kubernetes cluster.", type=str)
        parser.add_argument("--context_name", help="Name of the kubeconfig context.", type=str)
        parser.add_argument("--namespace", help="Kubernetes namespace.", default="default", type=str)
        parser.add_argument(
            "--labels",
            help="Labels for Kubernetes resources, as a JSON string.",
            type=str,
            default='{"created_by": "geniusrise"}',
        )
        parser.add_argument("--annotations", help="Annotations for Kubernetes resources, as a JSON string.", type=str)
        parser.add_argument("--api_key", help="API key for Kubernetes cluster.", type=str)
        parser.add_argument("--api_host", help="API host for Kubernetes cluster.", type=str)
        parser.add_argument("--verify_ssl", help="Whether to verify SSL certificates.", default=True, type=bool)
        parser.add_argument("--ssl_ca_cert", help="Path to the SSL CA certificate.", type=str)
        return parser

    def create_parser(self, parser: ArgumentParser) -> ArgumentParser:
        subparsers = parser.add_subparsers(dest="command")

        pod_status_parser = subparsers.add_parser("status", help="Get the status of the Kubernetes pod.")
        pod_status_parser.add_argument("name", help="Name of the Kubernetes pod.", type=str)
        pod_status_parser = self._add_connection_args(pod_status_parser)

        # Parser for list
        list_pods_parser = subparsers.add_parser("show", help="List all pods.")
        list_pods_parser = self._add_connection_args(list_pods_parser)

        # Parser for describe
        describe_pod_parser = subparsers.add_parser("describe", help="Describe a pod.")
        describe_pod_parser.add_argument("name", help="Name of the pod.", type=str)
        describe_pod_parser = self._add_connection_args(describe_pod_parser)

        # Parser for pod logs
        logs_parser = subparsers.add_parser("logs", help="Get the logs of a pod.")
        logs_parser.add_argument("name", help="Name of the pod.", type=str)
        logs_parser.add_argument("--follow", help="Whether to follow the logs.", default=False, type=bool)
        logs_parser.add_argument("--tail", help="Number of lines to show from the end of the logs.", type=int)
        logs_parser = self._add_connection_args(logs_parser)

        return parser

    def run(self, args: Namespace) -> None:
        """
        🚀 Run the Kubernetes resource manager.

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

        if args.command == "status":
            self.status(args.name)
        elif args.command == "show":
            self.show()
        elif args.command == "describe":
            self.describe(args.name)
        elif args.command == "logs":
            self.logs(args.name, args.follow, args.tail)
        else:
            self.log.error("Unknown command: %s", args.command)

    def connect(
        self,
        kube_config_path: str,
        cluster_name: str,
        context_name: str,
        namespace: str = "default",
        labels: dict = {},
        annotations: dict = {},
        api_key: Optional[str] = None,
        api_host: Optional[str] = None,
        verify_ssl: bool = True,
        ssl_ca_cert: Optional[str] = None,
    ) -> None:
        """
        🌐 Connect to a Kubernetes cluster.

        Args:
            kube_config_path (str): Path to the kubeconfig file.
            cluster_name (str): Name of the Kubernetes cluster.
            context_name (str): Name of the kubeconfig context.
            namespace (str): Kubernetes namespace.
            labels (dict): Labels for Kubernetes resources.
            annotations (dict): Annotations for Kubernetes resources.
            api_key (str): API key for Kubernetes cluster.
            api_host (str): API host for Kubernetes cluster.
            verify_ssl (bool): Whether to verify SSL certificates.
            ssl_ca_cert (str): Path to the SSL CA certificate.

        Raises:
            ValueError: If neither kube_config_path and context_name nor api_key and api_host are provided.
        """
        if kube_config_path and context_name:
            config.load_kube_config(config_file=kube_config_path, context=context_name)
            self.api_instance = client.CoreV1Api(ApiClient())
            self.apps_api_instance = client.AppsV1Api(ApiClient())
            self.batch_api_instance = BatchV1Api(ApiClient())
            self.batch_beta_api_instance = BatchV1Api(ApiClient())
        elif api_key and api_host:
            configuration = Configuration()
            configuration.host = api_host
            configuration.verify_ssl = verify_ssl
            if ssl_ca_cert:
                configuration.ssl_ca_cert = ssl_ca_cert
            configuration.api_key = {"authorization": api_key}
            client.Configuration.set_default(configuration)
            self.api_instance = client.CoreV1Api(ApiClient(configuration))
            self.apps_api_instance = client.AppsV1Api(ApiClient(configuration))
            self.batch_api_instance = BatchV1Api(ApiClient(configuration))
            self.batch_beta_api_instance = BatchV1Api(ApiClient(configuration))
        else:
            raise ValueError("Either kube_config_path and context_name or api_key and api_host must be provided.")

        self.cluster_name = cluster_name
        self.context_name = context_name
        self.namespace = namespace
        self.labels = labels
        self.annotations = annotations
        self.log.info(f"🌐 Connected to cluster: {self.cluster_name}, in namespace: {self.namespace}")

    def __create_image_pull_secret(self, name: str, registry: str, username: str, password: str) -> None:
        """
        🔑 Create an image pull secret for a Docker registry.

        Args:
            name (str): Name of the secret.
            registry (str): Docker registry URL.
            username (str): Username for the registry.
            password (str): Password for the registry.
        """
        docker_config = {"auths": {registry: {"username": username, "password": password}}}
        docker_config_bytes = base64.b64encode(json.dumps(docker_config).encode()).decode()
        secret = client.V1Secret(
            api_version="v1",
            kind="Secret",
            metadata=client.V1ObjectMeta(name=name),
            type="kubernetes.io/dockerconfigjson",
            data={"config.json": docker_config_bytes},
        )
        self.api_instance.create_namespaced_secret(self.namespace, secret)
        self.log.info(f"🔑 Created image pull secret {name}")

    def _create_pod_spec(
        self,
        image: str,
        command: List[str],
        image_pull_secret_name: str,
        env_vars: dict = {},
        cpu: Optional[str] = None,
        memory: Optional[str] = None,
        storage: Optional[str] = None,
        gpu: Optional[str] = None,
    ) -> client.V1PodSpec:
        """
        📦 Create a Kubernetes Pod specification.

        Args:
            image (str): Docker image for the Pod.
            command (str): Command to run in the container.
            image_pull_secret_name (str): Name of the image pull secret.
            env_vars (dict): Environment variables for the Pod.
            cpu (str): CPU requirements.
            memory (str): Memory requirements.
            storage (str): Storage requirements.
            gpu (str): GPU requirements.

        Returns:
            client.V1PodSpec: The Pod specification.
        """
        resources = {}
        if cpu:
            resources["cpu"] = cpu
        if memory:
            resources["memory"] = memory
        if storage:
            resources["storage"] = storage
        if gpu:
            resources["nvidia.com/gpu"] = gpu

        return client.V1PodSpec(
            containers=[
                client.V1Container(
                    name="resource-container",
                    image=image,
                    command=command,
                    env=[client.V1EnvVar(name=k, value=v) for k, v in env_vars.items()],
                    resources=V1ResourceRequirements(limits=resources) if resources else None,
                )
            ],
            image_pull_secrets=[client.V1LocalObjectReference(name=image_pull_secret_name)]
            if image_pull_secret_name
            else None,
        )

    def __wait_for_pod_completion(self, pod_name: str, timeout: int = 600, poll_interval: int = 5) -> bool:
        """
        ⏳ Wait for a Pod to complete its execution.

        Args:
            pod_name (str): Name of the Pod.
            timeout (int): Maximum time to wait in seconds.
            poll_interval (int): Time between status checks in seconds.

        Returns:
            bool: True if the Pod succeeded, False otherwise.

        Raises:
            TimeoutError: If waiting for the Pod times out.
        """
        end_time = time.time() + timeout
        while time.time() < end_time:
            pod_status = self.status(pod_name)
            if pod_status == "Succeeded":
                return True
            elif pod_status in ["Failed", "Unknown"]:
                return False
            time.sleep(poll_interval)
        raise TimeoutError(f"Timed out waiting for pod {pod_name} to complete.")

    def status(self, pod_name: str) -> str:
        """
        📜 Get the status of a Pod.

        Args:
            pod_name (str): Name of the Pod.

        Returns:
            str: The status of the Pod.
        """
        pod = self.api_instance.read_namespaced_pod(pod_name, self.namespace)
        return pod.status.phase

    def show(self) -> list:
        """
        📋 Show all pods in the namespace.

        Returns:
            list: List of pods.
        """
        pod_list = self.api_instance.list_namespaced_pod(self.namespace)
        return [{"name": pod.metadata.name, "status": pod.status.phase} for pod in pod_list.items]

    def describe(self, pod_name: str) -> dict:
        """
        📝 Describe a Kubernetes pod.

        Args:
            pod_name (str): Name of the pod.

        Returns:
            dict: Description of the pod.
        """
        pod = self.api_instance.read_namespaced_pod(pod_name, self.namespace)
        return {
            "name": pod.metadata.name,
            "status": pod.status.phase,
            "containers": [container.name for container in pod.spec.containers],
        }

    def logs(self, name: str, tail: int = 10, follow: bool = True) -> str:
        """
        📜 Get logs of a Kubernetes pod.

        Args:
            name (str): Name of the pod.
            tail (int): Number of lines to tail.

        Returns:
            str: Logs of the pod.
        """
        return self.api_instance.read_namespaced_pod_log(name, self.namespace, tail_lines=tail, follow=follow)
