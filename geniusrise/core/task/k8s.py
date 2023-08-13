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
from typing import Any, Dict

from kubernetes import client, config
from kubernetes.client.rest import ApiException

log = logging.getLogger(__name__)


class K8sManager:
    """
    A class used to manage Kubernetes deployments and services.

    Attributes
    ----------
    name : str
        The name of the deployment and service.
    namespace : str
        The namespace to create the deployment and service in.
    image : str
        The Docker image to use for the deployment.
    command : list
        The command to run in the Docker container.
    replicas : int
        The number of replicas to create for the deployment.
    port : int
        The port to expose on the service.

    Methods
    -------
    create_deployment()
        Creates a new deployment.
    update_deployment(replicas)
        Updates the number of replicas in the deployment.
    scale_deployment(replicas)
        Scales the deployment to a new number of replicas.
    delete_deployment()
        Deletes the deployment.
    create_service()
        Creates a new service.
    delete_service()
        Deletes the service.
    run()
        Creates the deployment and service.
    destroy()
        Deletes the deployment and service.
    get_status()
        Returns the status of the deployment.
    get_statistics()
        Returns the details of the deployment and the pods in the deployment.
    get_logs()
        Returns the logs of the pods in the deployment.
    """

    def __init__(
        self,
        name: str,
        command: list = [],
        namespace: str = "default",
        image: str = "geniusrise/geniusrise",
        replicas: int = 1,
        port: int = 80,
    ):
        """
        Constructs all the necessary attributes for the K8sManager object.

        Parameters
        ----------
        name : str
            The name of the deployment and service.
        command : list
            The command to run in the Docker container.
        namespace : str, optional
            The namespace to create the deployment and service in (default is "default").
        image : str, optional
            The Docker image to use for the deployment (default is "geniusrise/geniusrise").
        replicas : int, optional
            The number of replicas to create for the deployment (default is 1).
        port : int, optional
            The port to expose on the service (default is 80).
        """
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
        """
        Creates a new deployment.

        The deployment is created in the namespace specified in the constructor. The deployment uses the Docker image
        and command specified in the constructor, and creates the number of replicas specified in the constructor.

        If an error occurs while creating the deployment, an error message is logged and the method returns None.
        """
        # Define the container
        container = client.V1Container(name=self.name, image=self.image, command=self.command)

        # Define the template
        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels={"app": self.name, "service": "geniusrise"}),
            spec=client.V1PodSpec(containers=[container]),
        )

        # Define the spec
        spec = client.V1DeploymentSpec(
            replicas=self.replicas,
            selector=client.V1LabelSelector(match_labels={"app": self.name, "service": "geniusrise"}),
            template=template,
        )

        # Define the deployment
        deployment = client.V1Deployment(metadata=client.V1ObjectMeta(name=self.name), spec=spec)

        # Create the deployment
        try:
            self.apps_api.create_namespaced_deployment(namespace=self.namespace, body=deployment)
            log.info(f"Deployment {self.name} created.")
        except ApiException as e:
            log.error(f"Exception when creating deployment {self.name}: {e}")

    def update_deployment(self, replicas):
        """
        Updates the number of replicas in the deployment.

        Parameters
        ----------
        replicas : int
            The new number of replicas for the deployment.

        If an error occurs while updating the deployment, an error message is logged and the method returns None.
        """
        # Get the existing deployment
        try:
            deployment = self.apps_api.read_namespaced_deployment(name=self.name, namespace=self.namespace)

            # Update the number of replicas
            deployment.spec.replicas = replicas

            # Update the deployment
            self.apps_api.replace_namespaced_deployment(name=self.name, namespace=self.namespace, body=deployment)
            log.info(f"Deployment {self.name} updated.")
        except ApiException as e:
            log.error(f"Exception when updating deployment {self.name}: {e}")

    def scale_deployment(self, replicas):
        """
        Scales the deployment to a new number of replicas.

        Parameters
        ----------
        replicas : int
            The new number of replicas for the deployment.

        If an error occurs while scaling the deployment, an error message is logged and the method returns None.
        """
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
        """
        Deletes the deployment.

        If an error occurs while deleting the deployment, an error message is logged and the method returns None.
        """
        # Define the service spec
        spec = client.V1ServiceSpec(
            selector={"app": self.name},
            ports=[client.V1ServicePort(port=self.port, target_port=self.port)],
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
        """
        Creates a new service.

        The service is created in the namespace specified in the constructor. The service exposes the port specified
        in the constructor.

        If an error occurs while creating the service, an error message is logged and the method returns None.
        """
        # Delete the service
        try:
            self.core_api.delete_namespaced_service(name=self.name, namespace=self.namespace)
            log.info(f"Service {self.name} deleted.")
        except ApiException as e:
            log.error(f"Exception when deleting service {self.name}: {e}")

    def run(self):
        """
        Creates the deployment and service.

        If an error occurs while creating the deployment or service,
        an error message is logged and the method returns None.
        """
        self.create_deployment()
        self.create_service()

    def destroy(self):
        """
        Deletes the deployment and service.

        If an error occurs while deleting the deployment or service,
        an error message is logged and the method returns None.
        """
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
            return deployment.status.__dict__
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
            logs = {}
            _continue = None
            while True:
                pod_list = self.core_api.list_namespaced_pod(
                    self.namespace,
                    label_selector=f"app={self.name}",
                    _continue=_continue,
                )
                for pod in pod_list.items:
                    logs[pod.metadata.name] = self.core_api.read_namespaced_pod_log(pod.metadata.name, self.namespace)
                _continue = pod_list.metadata._continue
                if not _continue:
                    break
            return logs
        except ApiException as e:
            log.error(f"Exception when getting logs of deployment {self.name}: {e}")
            return {}
