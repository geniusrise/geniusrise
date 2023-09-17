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
        create_parser.add_argument("image", help="Docker image for the job.", type=str, default="geniusrise/geniusrise")
        create_parser.add_argument("command", help="Command to run in the container.", type=str)
        create_parser.add_argument("--env_vars", help="Environment variables as a JSON string.", type=str, default="{}")
        create_parser.add_argument("--cpu", help="CPU requirements.", type=str)
        create_parser.add_argument("--memory", help="Memory requirements.", type=str)
        create_parser.add_argument("--storage", help="Storage requirements.", type=str)
        create_parser.add_argument("--gpu", help="GPU requirements.", type=str)
        create_parser = self._add_connection_args(create_parser)

        # Parser for delete
        delete_parser = subparsers.add_parser("delete", help="Delete a job.")
        delete_parser.add_argument("name", help="Name of the job.", type=str)
        delete_parser = self._add_connection_args(delete_parser)

        # Parser for status
        status_parser = subparsers.add_parser("status", help="Get the status of a job.")
        status_parser.add_argument("name", help="Name of the job.", type=str)
        status_parser = self._add_connection_args(status_parser)

        return parser

    def run(self, args: Namespace) -> None:
        if args.job == "create":
            self.create(
                args.name,
                args.image,
                ast.literal_eval(args.command) if type(args.command) is str else args.command,
                env_vars=json.loads(args.env_vars),
                cpu=args.cpu,
                memory=args.memory,
                storage=args.storage,
                gpu=args.gpu,
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

    def create(  # type: ignore
        self,
        name: str,
        image: str,
        command: List[str],
        env_vars: dict = {},
        cpu: Optional[str] = None,
        memory: Optional[str] = None,
        storage: Optional[str] = None,
        gpu: Optional[str] = None,
        image_pull_secret_name: Optional[str] = None,
        **kwargs,
    ) -> None:
        """
        🛠 Create a Kubernetes Job.

        Args:
            name (str): Name of the Job.
            image (str): Docker image for the Job.
            command (str): Command to run in the container.
            env_vars (dict): Environment variables for the Job.
        """
        job_spec = self._create_job_spec(
            image=image,
            command=command,
            env_vars=env_vars,
            cpu=cpu,
            memory=memory,
            storage=storage,
            gpu=gpu,
        )
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
