import logging
from typing import Any, Dict

from kubernetes import client, config
from kubernetes.client.rest import ApiException

from geniusrise_cli.core.data import InputConfig, OutputConfig

from .base import Task

log = logging.getLogger(__name__)


class K8sManager:
    def __init__(
        self,
        name: str,
        namespace: str = "default",
        image: str = "geniusrise/geniusrise",
        command: str = "--help",
        replicas: int = 1,
        port: int = 80,
    ):
        self.name = name
        self.namespace = namespace
        self.image = image
        self.command = command
        self.replicas = replicas
        self.port = port

        # Load kube config from default location
        config.load_kube_config()

        # Create a client instance for Core V1 and Apps V1 of Kubernetes API
        self.core_api = client.CoreV1Api()
        self.apps_api = client.AppsV1Api()

    def create_deployment(self):
        # Define the container
        container = client.V1Container(name=self.name, image=self.image, command=self.command)

        # Define the template
        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels={"app": self.name}), spec=client.V1PodSpec(containers=[container])
        )

        # Define the spec
        spec = client.V1DeploymentSpec(
            replicas=self.replicas, selector=client.V1LabelSelector(match_labels={"app": self.name}), template=template
        )

        # Define the deployment
        deployment = client.V1Deployment(metadata=client.V1ObjectMeta(name=self.name), spec=spec)

        # Create the deployment
        try:
            self.apps_api.create_namespaced_deployment(namespace=self.namespace, body=deployment)
            log.info(f"Deployment {self.name} created.")
        except ApiException as e:
            log.error(f"Exception when creating deployment {self.name}: {e}")

    def update_deployment(self, new_spec):
        # Get the existing deployment
        try:
            deployment = self.apps_api.read_namespaced_deployment(name=self.name, namespace=self.namespace)

            # Update the deployment spec
            deployment.spec = new_spec

            # Update the deployment
            self.apps_api.replace_namespaced_deployment(name=self.name, namespace=self.namespace, body=deployment)
            log.info(f"Deployment {self.name} updated.")
        except ApiException as e:
            log.error(f"Exception when updating deployment {self.name}: {e}")

    def scale_deployment(self, replicas):
        # Get the existing deployment
        try:
            deployment = self.apps_api.read_namespaced_deployment(name=self.name, namespace=self.namespace)

            # Update the number of replicas
            deployment.spec.replicas = replicas

            # Update the deployment
            self.apps_api.replace_namespaced_deployment(name=self.name, namespace=self.namespace, body=deployment)
            log.info(f"Deployment {self.name} scaled to {replicas} replicas.")
        except ApiException as e:
            log.error(f"Exception when scaling deployment {self.name}: {e}")

    def delete_deployment(self):
        # Delete the deployment
        try:
            self.apps_api.delete_namespaced_deployment(name=self.name, namespace=self.namespace)
            log.info(f"Deployment {self.name} deleted.")
        except ApiException as e:
            log.error(f"Exception when deleting deployment {self.name}: {e}")

    def create_service(self):
        # Define the service spec
        spec = client.V1ServiceSpec(
            selector={"app": self.name}, ports=[client.V1ServicePort(port=self.port, target_port=self.port)]
        )

        # Define the service
        service = client.V1Service(metadata=client.V1ObjectMeta(name=self.name), spec=spec)

        # Create the service
        try:
            self.core_api.create_namespaced_service(namespace=self.namespace, body=service)
            log.info(f"Service {self.name} created.")
        except ApiException as e:
            log.error(f"Exception when creating service {self.name}: {e}")

    def delete_service(self):
        # Delete the service
        try:
            self.core_api.delete_namespaced_service(name=self.name, namespace=self.namespace)
            log.info(f"Service {self.name} deleted.")
        except ApiException as e:
            log.error(f"Exception when deleting service {self.name}: {e}")


class K8sTask(Task, K8sManager):
    def __init__(
        self,
        name: str,
        input_config: InputConfig,
        output_config: OutputConfig,
        namespace: str = "default",
        image: str = "geniusrise/geniusrise",
        command: str = "--help",
        replicas: int = 1,
        port: int = 80,
    ):
        Task.__init__(self, input_config=input_config, output_config=output_config)
        K8sManager.__init__(self, name, namespace, image, command, replicas, port)

    def run(self):
        self.create_deployment()
        self.create_service()

    def destroy(self):
        self.delete_deployment()
        self.delete_service()

    def get_status(self) -> Dict[str, Any]:
        """
        Get the status of the deployment

        Returns:
            Dict[str, Any]: The status of the deployment
        """
        try:
            # Get the status of the deployment
            deployment = self.apps_api.read_namespaced_deployment(name=self.name, namespace=self.namespace)
            return deployment.status
        except ApiException as e:
            log.error(f"Exception when getting status of deployment {self.name}: {e}")
            return {}

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get the details of the deployment and the pods in the deployment

        Returns:
            Dict[str, Any]: The details of the deployment and the pods
        """
        try:
            # Get the details of the deployment
            deployment = self.apps_api.read_namespaced_deployment(name=self.name, namespace=self.namespace)
            deployment_stats = deployment.status

            # Get the details of the pods in the deployment
            pod_list = self.core_api.list_namespaced_pod(self.namespace, label_selector=f"app={self.name}")
            pod_stats = [pod.status for pod in pod_list.items]

            return {"deployment": deployment_stats, "pods": pod_stats}
        except ApiException as e:
            log.error(f"Exception when getting statistics of deployment {self.name}: {e}")
            return {}

    def get_logs(self) -> Dict[str, str]:
        """
        Get the logs of the pods in the deployment

        Returns:
            Dict[str, str]: The logs of the pods
        """
        try:
            # Get the logs of the pods in the deployment
            pod_list = self.core_api.list_namespaced_pod(self.namespace, label_selector=f"app={self.name}")
            logs = {}
            for pod in pod_list.items:
                logs[pod.metadata.name] = self.core_api.read_namespaced_pod_log(pod.metadata.name, self.namespace)
            return logs
        except ApiException as e:
            log.error(f"Exception when getting logs of deployment {self.name}: {e}")
            return {}
