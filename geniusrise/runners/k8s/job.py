from argparse import ArgumentParser, Namespace
import json
import ast
from kubernetes import client
from kubernetes.client import BatchV1Api, V1JobSpec
from typing import Optional, List

from .deployment import Deployment


class Job(Deployment):
    def __init__(self):
        super().__init__()
        self.batch_api_instance: BatchV1Api = None  # type: ignore

    def create_parser(self, parser: ArgumentParser) -> ArgumentParser:
        subparsers = parser.add_subparsers(dest="job")

        # Parser for create
        create_parser = subparsers.add_parser("create", help="Create a new job.")
        create_parser.add_argument("name", help="Name of the job.", type=str)
        create_parser.add_argument("image", help="Docker image for the job.", type=str)
        create_parser.add_argument("command", help="Command to run in the container.", type=str)
        create_parser.add_argument("--env_vars", help="Environment variables as a JSON string.", type=str, default="{}")

        # Parser for delete
        delete_parser = subparsers.add_parser("delete", help="Delete a job.")
        delete_parser.add_argument("name", help="Name of the job.", type=str)

        # Parser for status
        status_parser = subparsers.add_parser("status", help="Get the status of a job.")
        status_parser.add_argument("name", help="Name of the job.", type=str)

        return parser

    def run(self, args: Namespace) -> None:
        if args.job == "create":
            self.create(
                args.name,
                args.image,
                ast.literal_eval(args.command) if type(args.command) is str else args.command,
                env_vars=json.loads(args.env_vars),
            )
        elif args.job == "delete":
            self.delete(args.name)
        elif args.job == "status":
            self.status(args.name)
        else:
            self.log.error("Unknown command: %s", args.job)

    def _create_job_spec(
        self,
        image: str,
        command: List[str],
        env_vars: dict = {},
        cpu: Optional[str] = None,
        memory: Optional[str] = None,
        storage: Optional[str] = None,
        gpu: Optional[str] = None,
        image_pull_secret_name: Optional[str] = None,
    ) -> V1JobSpec:
        """
        📦 Create a Kubernetes Job specification.

        This method creates a Kubernetes Job specification with detailed resource requirements.

        Args:
            image (str): Docker image for the Job.
            command (str): Command to run in the container.
            env_vars (dict): Environment variables for the Job.
            cpu (Optional[str]): CPU requirements.
            memory (Optional[str]): Memory requirements.
            storage (Optional[str]): Storage requirements.
            gpu (Optional[str]): GPU requirements.
            image_pull_secret_name (Optional[str]): Name of the image pull secret.

        Returns:
            V1JobSpec: The Job specification.
        """
        # Create resource requirements dictionary
        resources = {}
        if cpu:
            resources["cpu"] = cpu
        if memory:
            resources["memory"] = memory
        if storage:
            resources["storage"] = storage
        if gpu:
            resources["nvidia.com/gpu"] = gpu

        # Create Pod spec for the Job
        pod_spec = self._create_pod_spec(
            image=image,
            command=command,
            image_pull_secret_name=image_pull_secret_name,  # type: ignore
            env_vars=env_vars,
            cpu=cpu,
            memory=memory,
            storage=storage,
            gpu=gpu,
        )
        pod_spec.restart_policy = "OnFailure"

        # Create and return the Job spec
        return V1JobSpec(
            template=client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(labels=self.labels, annotations=self.annotations),
                spec=pod_spec,
            )
        )

    def create(self, name: str, image: str, command: List[str], env_vars: dict = {}) -> None:  # type: ignore
        """
        🛠 Create a Kubernetes Job.

        Args:
            name (str): Name of the Job.
            image (str): Docker image for the Job.
            command (str): Command to run in the container.
            env_vars (dict): Environment variables for the Job.
        """
        job_spec = self._create_job_spec(image, command, env_vars)
        job = client.V1Job(
            api_version="batch/v1",
            kind="Job",
            metadata=client.V1ObjectMeta(name=name, labels=self.labels, annotations=self.annotations),
            spec=job_spec,
        )
        self.batch_api_instance.create_namespaced_job(self.namespace, job)
        self.log.info(f"🛠️ Created Job {name}")

    def delete(self, name: str) -> None:
        """
        🗑 Delete a Kubernetes Job.

        Args:
            name (str): Name of the Job to delete.
        """
        self.batch_api_instance.delete_namespaced_job(name, self.namespace)
        self.log.info(f"🗑️ Deleted Job {name}")

    def status(self, name: str) -> dict:  # type: ignore
        """
        📊 Get the status of a Kubernetes Job.

        Args:
            name (str): Name of the Job.

        Returns:
            dict: Status of the Job.
        """
        job = self.batch_api_instance.read_namespaced_job(name, self.namespace)
        return {"job_status": job.status}
