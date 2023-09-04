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
from argparse import ArgumentParser
from kubernetes import client, config
from kubernetes.client import Configuration, ApiClient, V1ResourceRequirements
from rich_argparse import RichHelpFormatter
from typing import Optional


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
        self.apps_api_instance: ApiClient = None  # type: ignore
        self.cluster_name: str = None  # type: ignore
        self.context_name: str = None  # type: ignore
        self.namespace: str = None  # type: ignore
        self.labels: dict = {}  # type: ignore
        self.annotations: dict = {}  # type: ignore

    def __add_common_parser_args(self, parser: ArgumentParser) -> ArgumentParser:
        """
        🛠 Add common arguments to a parser.

        Args:
            parser (ArgumentParser): The parser to which arguments will be added.

        Returns:
            ArgumentParser: The parser with added arguments.
        """
        parser.add_argument("--kube_config_path", help="Path to the kubeconfig file.", type=str)
        parser.add_argument("--cluster_name", help="Name of the Kubernetes cluster.", type=str)
        parser.add_argument("--context_name", help="Name of the kubeconfig context.", type=str)
        parser.add_argument("--namespace", help="Kubernetes namespace.", default="default", type=str)
        parser.add_argument("--labels", help="Labels for Kubernetes resources, as a JSON string.", type=str)
        parser.add_argument("--annotations", help="Annotations for Kubernetes resources, as a JSON string.", type=str)
        parser.add_argument("--api_key", help="API key for Kubernetes cluster.", type=str)
        parser.add_argument("--api_host", help="API host for Kubernetes cluster.", type=str)
        parser.add_argument("--verify_ssl", help="Whether to verify SSL certificates.", default=True, type=bool)
        parser.add_argument("--ssl_ca_cert", help="Path to the SSL CA certificate.", type=str)
        parser.add_argument("--cpu", help="CPU requirements.", type=str)
        parser.add_argument("--memory", help="Memory requirements.", type=str)
        parser.add_argument("--storage", help="Storage requirements.", type=str)
        parser.add_argument("--gpu", help="GPU requirements.", type=str)
        parser.add_argument("--env_vars", help="Environment variables as a JSON string.", type=json.loads, default={})
        return parser

    def create_parser(self, parser: ArgumentParser) -> ArgumentParser:
        """
        🎛 Create a parser for CLI commands.

        Args:
            parser (ArgumentParser): The main parser.

        Returns:
            ArgumentParser: The parser with subparsers for each command.
        """
        subparsers = parser.add_subparsers(dest="command")

        # Parser for create_resource
        create_resource_parser = subparsers.add_parser(
            "deploy", help="Create a Kubernetes resource / deploy to kubernetes.", formatter_class=RichHelpFormatter
        )
        create_resource_parser = self.__add_common_parser_args(create_resource_parser)
        create_resource_parser.add_argument("name", help="Name of the resource.", type=str)
        create_resource_parser.add_argument("image", help="Docker image for the resource.", type=str)
        create_resource_parser.add_argument("command", help="Command to run in the container.", type=str)
        create_resource_parser.add_argument(
            "--registry_creds", help="Credentials for Docker registry.", type=json.loads
        )
        create_resource_parser.add_argument("--is_service", help="Is this a service?", default=False, type=bool)
        create_resource_parser.add_argument("--replicas", help="Number of replicas.", default=1, type=int)
        create_resource_parser.add_argument("--port", help="Service port.", default=80, type=int)
        create_resource_parser.add_argument("--target_port", help="Container target port.", default=8080, type=int)
        create_resource_parser.add_argument("--env_vars", help="Environment variables.", default={}, type=json.loads)

        # Parser for delete_resource
        delete_resource_parser = subparsers.add_parser(
            "delete", help="Delete a Kubernetes resource.", formatter_class=RichHelpFormatter
        )
        delete_resource_parser = self.__add_common_parser_args(delete_resource_parser)
        delete_resource_parser.add_argument("name", help="Name of the resource.", type=str)
        delete_resource_parser.add_argument("--is_service", help="Is this a service?", default=False, type=bool)

        # Parser for get_status
        get_status_parser = subparsers.add_parser(
            "status", help="Get the status of a Kubernetes resource.", formatter_class=RichHelpFormatter
        )
        get_status_parser = self.__add_common_parser_args(get_status_parser)
        get_status_parser.add_argument("name", help="Name of the resource.", type=str)

        # Parser for get_logs
        get_logs_parser = subparsers.add_parser(
            "logs", help="Get logs of a Kubernetes resource.", formatter_class=RichHelpFormatter
        )
        get_logs_parser = self.__add_common_parser_args(get_logs_parser)
        get_logs_parser.add_argument("name", help="Name of the resource.", type=str)
        get_logs_parser.add_argument("--tail_lines", help="Number of lines to tail.", default=10, type=int)

        # Parser for scale
        scale_parser = subparsers.add_parser("scale", help="Scale a Kubernetes deployment.")
        scale_parser = self.__add_common_parser_args(scale_parser)
        scale_parser.add_argument("name", help="Name of the deployment.", type=str)
        scale_parser.add_argument("replicas", help="Number of replicas.", type=int)

        # Parser for list_pods
        list_pods_parser = subparsers.add_parser("pods", help="List all pods.")
        list_pods_parser = self.__add_common_parser_args(list_pods_parser)

        # Parser for list_services
        list_services_parser = subparsers.add_parser("services", help="List all services.")
        list_services_parser = self.__add_common_parser_args(list_services_parser)

        # Parser for list_deployments
        list_deployments_parser = subparsers.add_parser("deployments", help="List all deployments.")
        list_deployments_parser = self.__add_common_parser_args(list_deployments_parser)

        # Parser for describe_pod
        describe_pod_parser = subparsers.add_parser("pod", help="Describe a pod.")
        describe_pod_parser = self.__add_common_parser_args(describe_pod_parser)
        describe_pod_parser.add_argument("name", help="Name of the pod.", type=str)

        # Parser for describe_service
        describe_service_parser = subparsers.add_parser("service", help="Describe a service.")
        describe_service_parser = self.__add_common_parser_args(describe_service_parser)
        describe_service_parser.add_argument("name", help="Name of the service.", type=str)

        # Parser for describe_deployment
        describe_deployment_parser = subparsers.add_parser("deployment", help="Describe a deployment.")
        describe_deployment_parser = self.__add_common_parser_args(describe_deployment_parser)
        describe_deployment_parser.add_argument("name", help="Name of the deployment.", type=str)

        return parser

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
        else:
            raise ValueError("Either kube_config_path and context_name or api_key and api_host must be provided.")

        self.cluster_name = cluster_name
        self.context_name = context_name
        self.namespace = namespace
        self.labels = labels
        self.annotations = annotations
        self.log.info(f"🌐 Connected to cluster: {self.cluster_name}, in namespace: {self.namespace}")

    def _create_image_pull_secret(self, name: str, registry: str, username: str, password: str) -> None:
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
        command: str,
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

    def _create_deployment_spec(
        self,
        image: str,
        command: str,
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

    def _create_service_spec(self, port: int, target_port: int) -> client.V1ServiceSpec:
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

    def wait_for_pod_completion(self, pod_name: str, timeout: int = 600, poll_interval: int = 5) -> bool:
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
            pod_status = self._get_pod_status(pod_name)
            if pod_status == "Succeeded":
                return True
            elif pod_status in ["Failed", "Unknown"]:
                return False
            time.sleep(poll_interval)
        raise TimeoutError(f"Timed out waiting for pod {pod_name} to complete.")

    def _get_pod_status(self, pod_name: str) -> str:
        """
        📜 Get the status of a Pod.

        Args:
            pod_name (str): Name of the Pod.

        Returns:
            str: The status of the Pod.
        """
        pod = self.api_instance.read_namespaced_pod(pod_name, self.namespace)
        return pod.status.phase

    def create_resource(
        self,
        name: str,
        image: str,
        command: str,
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
        🛠 Create a Kubernetes resource (Pod/Deployment/Service).

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
        if registry_creds:
            secret_name = f"{name}-image-pull-secret"
            self._create_image_pull_secret(secret_name, **registry_creds)
            self.log.info(f"🔑 Created image pull secret {secret_name}")
        else:
            secret_name = None

        deployment_spec = self._create_deployment_spec(
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
        self.log.info(f"🛠️ Created resource {name}")

        if is_service:
            service_spec = self._create_service_spec(port, target_port)
            service = client.V1Service(
                api_version="v1",
                kind="Service",
                metadata=client.V1ObjectMeta(name=f"{name}-service", labels=self.labels, annotations=self.annotations),
                spec=service_spec,
            )
            self.api_instance.create_namespaced_service(self.namespace, service)
            self.log.info(f"🌐 Created service {name}-service")

    def delete_resource(self, name: str, is_service: bool = False) -> None:
        """
        🗑 Delete a Kubernetes resource (Pod/Deployment/Service).

        Args:
            name (str): Name of the resource to delete.
            is_service (bool): Whether the resource is a service.
        """
        self.apps_api_instance.delete_namespaced_deployment(name, self.namespace)
        if is_service:
            self.api_instance.delete_namespaced_service(f"{name}-service", self.namespace)

    def get_status(self, name: str) -> dict:
        """
        📊 Get the status of a Kubernetes deployment.

        Args:
            name (str): Name of the deployment.

        Returns:
            dict: Status of the deployment.
        """
        deployment = self.apps_api_instance.read_namespaced_deployment(name, self.namespace)
        return {"deployment_status": deployment.status}

    def get_logs(self, name: str, tail_lines: int = 10) -> str:
        """
        📜 Get logs of a Kubernetes pod.

        Args:
            name (str): Name of the pod.
            tail_lines (int): Number of lines to tail.

        Returns:
            str: Logs of the pod.
        """
        pod_list = self.api_instance.list_namespaced_pod(self.namespace, label_selector=f"app={name}")
        pod_name = pod_list.items[0].metadata.name
        return self.api_instance.read_namespaced_pod_log(pod_name, self.namespace, tail_lines=tail_lines)

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

    def list_pods(self) -> list:
        """
        📋 List all pods in the namespace.

        Returns:
            list: List of pods.
        """
        pod_list = self.api_instance.list_namespaced_pod(self.namespace)
        return [{"name": pod.metadata.name, "status": pod.status.phase} for pod in pod_list.items]

    def list_services(self) -> list:
        """
        🌐 List all services in the namespace.

        Returns:
            list: List of services.
        """
        service_list = self.api_instance.list_namespaced_service(self.namespace)
        return [
            {"name": service.metadata.name, "cluster_ip": service.spec.cluster_ip} for service in service_list.items
        ]

    def list_deployments(self) -> list:
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

    def describe_pod(self, pod_name: str) -> dict:
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

    def describe_service(self, service_name: str) -> dict:
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

    def describe_deployment(self, deployment_name: str) -> dict:
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
