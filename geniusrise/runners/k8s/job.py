# 🧠 Geniusrise
# Copyright (C) 2023  geniusrise.ai
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import ast
import json
from argparse import ArgumentParser, Namespace
from typing import List, Optional

from kubernetes import client  # type: ignore
from kubernetes.client import BatchV1Api, V1JobSpec, V1Job  # type: ignore

from .deployment import Deployment


class Job(Deployment):
    r"""
    🚀 The Job class is responsible for managing Kubernetes Jobs. It extends the Deployment class
    and provides additional functionalities specific to Kubernetes Jobs.

    CLI Usage:
        genius job [sub-command] [options]
        Examples:
            ```bash
            genius job create --name example-job --image example-image --command "echo hello" --cpu "100m" --memory "256Mi" --namespace geniusrise \
                --context_name arn:aws:eks:us-east-1:genius-dev:cluster/geniusrise-dev
            ```

            ```bash
            genius job delete --name example-job --namespace geniusrise \
                --context_name arn:aws:eks:us-east-1:genius-dev:cluster/geniusrise-dev
            ```

            ```bash
            genius job status --name example-job --namespace geniusrise \
                --context_name arn:aws:eks:us-east-1:genius-dev:cluster/geniusrise-dev
            ```

    YAML Configuration:
    ```yaml
        version: "1.0"
        jobs:
          - name: "example-job"
            image: "example-image"
            command: "example-command"
            env_vars:
              KEY: "value"
            cpu: "100m"
            memory: "256Mi"
            storage: "1Gi"
            gpu: "1"
    ```

    Extended CLI Examples:

    ```bash
        genius job create \
          --k8s_kind job \
          --k8s_namespace geniusrise \
          --k8s_context_name arn:aws:eks:us-east-1:genius-dev:cluster/geniusrise-dev \
          --k8s_name example-job \
          --k8s_image "genius-dev.dkr.ecr.ap-south-1.amazonaws.com/geniusrise" \
          --k8s_env_vars '{"AWS_DEFAULT_REGION": "ap-south-1", "AWS_SECRET_ACCESS_KEY": "", "AWS_ACCESS_KEY_ID": ""}' \
          --k8s_cpu "100m" \
          --k8s_memory "256Mi"
    ```

    ```bash
        genius job delete \
          example-job \
          --namespace geniusrise \
          --context_name arn:aws:eks:us-east-1:genius-dev:cluster/geniusrise-dev
    ```

    ```yaml
        genius job status \
          example-job \
          --namespace geniusrise \
          --context_name arn:aws:eks:us-east-1:genius-dev:cluster/geniusrise-dev
    ```
    """

    def __init__(self):
        """
        🚀 Initialize the Job class for managing Kubernetes Jobs.
        """
        super().__init__()
        self.batch_api_instance: BatchV1Api = None  # type: ignore

    def create_parser(self, parser: ArgumentParser) -> ArgumentParser:
        """
        🎛 Create a parser for CLI commands related to Job functionalities.

        Args:
            parser (ArgumentParser): The main parser.

        Returns:
            ArgumentParser: The parser with subparsers for each command.
        """
        subparsers = parser.add_subparsers(dest="job")

        # Parser for create
        # fmt: off
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

        # fmt: on
        return parser

    def run(self, args: Namespace) -> None:
        """
        🚀 Run the Job manager.

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
            self.log.exception("Unknown command: %s", args.job)

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
    ) -> V1Job:
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
        return job

    def delete(self, name: str) -> None:
        """
        🗑 Delete a Kubernetes Job.

        Args:
            name (str): Name of the Job to delete.
        """
        self.batch_api_instance.delete_namespaced_job(name, self.namespace)
        self.log.info(f"🗑️ Deleted Job {name}")

    def status(self, name: str) -> V1Job:  # type: ignore
        """
        📊 Get the status of a Kubernetes Job.

        Args:
            name (str): Name of the Job.

        Returns:
            dict: Status of the Job.
        """
        job = self.batch_api_instance.read_namespaced_job(name, self.namespace)
        self.log.info(f"📊 Job {name} status: {job.status}")
        self.log.info(f"📊 Job {name} status details: {job.status.details}")
        self.log.info(f"📊 Job {name} status message: {job.status.message}")
        self.log.info(f"📊 Job {name} status reason: {job.status.reason}")
        self.log.info(f"📊 Job {name} status status: {job.status.status}")
        self.log.info(f"📊 Job {name} status type: {job.status.type}")
        self.log.info(f"📊 Job {name} status uid: {job.status.uid}")
        self.log.info(f"📊 Job {name} status updated_at: {job.status.updated_at}")
        self.log.info(f"📊 Job {name} status conditions: {job.status.conditions}")
        self.log.info(f"📊 Job {name} status active: {job.status.active}")
        self.log.info(f"📊 Job {name} status completion_time: {job.status.completion_time}")

        return job
