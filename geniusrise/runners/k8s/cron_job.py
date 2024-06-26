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
from kubernetes.client import BatchV1Api, V1CronJob  # type: ignore

from .job import Job


class CronJob(Job):
    r"""
    🚀 The CronJob class is responsible for managing Kubernetes CronJobs. It extends the Job class
    and provides additional functionalities specific to Kubernetes CronJobs.

    CLI Usage:
        genius cronjob [sub-command] [options]
        Examples:
            ```bash
            genius cronjob create_cronjob --name example-cronjob --image example-image --command "echo hello" --schedule "*/5 * * * *" --namespace geniusrise \
                --context_name arn:aws:eks:us-east-1:genius-dev:cluster/geniusrise-dev
            ```

            ```bash
            genius cronjob delete_cronjob --name example-cronjob --namespace geniusrise \
                --context_name arn:aws:eks:us-east-1:genius-dev:cluster/geniusrise-dev
            ```

            ```bash
            genius cronjob get_cronjob_status --name example-cronjob --namespace geniusrise \
                --context_name arn:aws:eks:us-east-1:genius-dev:cluster/geniusrise-dev
            ```

    YAML Configuration:
    ```yaml
        version: "1.0"
        cronjobs:
          - name: "example-cronjob"
            image: "example-image"
            command: "example-command"
            schedule: "*/5 * * * *"
            env_vars:
              KEY: "value"
            cpu: "100m"
            memory: "256Mi"
            storage: "1Gi"
            gpu: "1"
    ```

    Extended CLI Examples:
        ```bash
        genius cronjob create_cronjob \
          --k8s_kind cronjob \
          --k8s_namespace geniusrise \
          --k8s_context_name arn:aws:eks:us-east-1:genius-dev:cluster/geniusrise-dev \
          --k8s_name example-cronjob \
          --k8s_image "genius-dev.dkr.ecr.ap-south-1.amazonaws.com/geniusrise" \
          --k8s_schedule "*/5 * * * *" \
          --k8s_env_vars '{"AWS_DEFAULT_REGION": "ap-south-1", "AWS_SECRET_ACCESS_KEY": "", "AWS_ACCESS_KEY_ID": ""}' \
          --k8s_cpu "100m" \
          --k8s_memory "256Mi"
        ```

        ```bash
        genius cronjob delete_cronjob \
          example-cronjob \
          --namespace geniusrise \
          --context_name arn:aws:eks:us-east-1:genius-dev:cluster/geniusrise-dev
        ```

        ```bash
        genius cronjob get_cronjob_status \
          example-cronjob \
          --namespace geniusrise \
          --context_name arn:aws:eks:us-east-1:genius-dev:cluster/geniusrise-dev
        ```
    """

    def __init__(self):
        """
        🚀 Initialize the CronJob class for managing Kubernetes Cron Jobs.
        """
        super().__init__()
        self.batch_api_instance: BatchV1Api = None  # type: ignore

    def create_parser(self, parser: ArgumentParser) -> ArgumentParser:
        """
        🎛 Create a parser for CLI commands related to Cron Job functionalities.

        Args:
            parser (ArgumentParser): The main parser.

        Returns:
            ArgumentParser: The parser with subparsers for each command.
        """
        subparsers = parser.add_subparsers(dest="command")

        # Parser for create_cronjob
        # fmt: off
        create_parser = subparsers.add_parser("create_cronjob", help="Create a new cronjob.")
        create_parser.add_argument("name", help="Name of the cronjob.", type=str)
        create_parser.add_argument("image", help="Docker image for the cronjob.", type=str, default="geniusrise/geniusrise")
        create_parser.add_argument("command", help="Command to run in the container.", type=str)
        create_parser.add_argument("schedule", help="Cron schedule.", type=str)
        create_parser.add_argument("--env_vars", help="Environment variables as a JSON string.", type=str, default="{}")
        create_parser.add_argument("--cpu", help="CPU requirements.", type=str)
        create_parser.add_argument("--memory", help="Memory requirements.", type=str)
        create_parser.add_argument("--storage", help="Storage requirements.", type=str)
        create_parser.add_argument("--gpu", help="GPU requirements.", type=str)
        create_parser = self._add_connection_args(create_parser)

        # Parser for delete_cronjob
        delete_parser = subparsers.add_parser("delete_cronjob", help="Delete a cronjob.")
        delete_parser.add_argument("name", help="Name of the cronjob.", type=str)
        delete_parser = self._add_connection_args(delete_parser)

        # Parser for get_cronjob_status
        status_parser = subparsers.add_parser("get_cronjob_status", help="Get the status of a cronjob.")
        status_parser.add_argument("name", help="Name of the cronjob.", type=str)
        status_parser = self._add_connection_args(status_parser)

        # fmt: on
        return parser

    def run(self, args: Namespace) -> None:
        """
        🚀 Run the Cron Job manager.

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

        if args.command == "create_cronjob":
            self.create(
                args.name,
                args.image,
                ast.literal_eval(args.command) if type(args.command) is str else args.command,
                args.schedule,
                env_vars=json.loads(args.env_vars),
                cpu=args.cpu,
                memory=args.memory,
                storage=args.storage,
                gpu=args.gpu,
            )
        elif args.command == "delete_cronjob":
            self.delete(args.name)
        elif args.command == "get_cronjob_status":
            self.status(args.name)
        else:
            self.log.exception("Unknown command: %s", args.command)

    def __create_cronjob_spec(
        self,
        image: str,
        command: List[str],
        schedule: str,
        env_vars: dict = {},
        cpu: Optional[str] = None,
        memory: Optional[str] = None,
        storage: Optional[str] = None,
        gpu: Optional[str] = None,
        image_pull_secret_name: Optional[str] = None,
    ) -> client.V1CronJobSpec:
        """
        📦 Create a Kubernetes CronJob specification.

        Args:
            image (str): Docker image for the CronJob.
            command (str): Command to run in the container.
            env_vars (dict): Environment variables for the CronJob.
            cpu (Optional[str]): CPU requirements.
            memory (Optional[str]): Memory requirements.
            storage (Optional[str]): Storage requirements.
            gpu (Optional[str]): GPU requirements.
            image_pull_secret_name (Optional[str]): Name of the image pull secret.

        Returns:
            client.V1CronJobSpec: The CronJob specification.
        """
        return client.V1CronJobSpec(
            schedule=schedule,
            job_template=client.V1JobTemplateSpec(
                metadata=client.V1ObjectMeta(labels=self.labels, annotations=self.annotations),
                spec=self._create_job_spec(
                    image=image,
                    command=command,
                    env_vars=env_vars,
                    cpu=cpu,
                    memory=memory,
                    storage=storage,
                    gpu=gpu,
                    image_pull_secret_name=image_pull_secret_name,
                ),
            ),
        )

    def create(  # type: ignore
        self,
        name: str,
        image: str,
        schedule: str,
        command: List[str],
        env_vars: dict = {},
        cpu: Optional[str] = None,
        memory: Optional[str] = None,
        storage: Optional[str] = None,
        gpu: Optional[str] = None,
        image_pull_secret_name: Optional[str] = None,
        **kwargs,
    ) -> V1CronJob:
        """
        🛠 Create a Kubernetes CronJob.

        Args:
            name (str): Name of the CronJob.
            image (str): Docker image for the CronJob.
            command (str): Command to run in the container.
            schedule (str): Cron schedule.
            env_vars (dict): Environment variables for the CronJob.
        """
        cronjob_spec = self.__create_cronjob_spec(
            image=image,
            command=command,
            schedule=schedule,
            env_vars=env_vars,
            cpu=cpu,
            memory=memory,
            storage=storage,
            gpu=gpu,
            image_pull_secret_name=image_pull_secret_name,
        )
        cronjob = client.V1CronJob(
            api_version="batch/v1",
            kind="CronJob",
            metadata=client.V1ObjectMeta(name=name, labels=self.labels, annotations=self.annotations),
            spec=cronjob_spec,
        )
        self.batch_api_instance.create_namespaced_cron_job(self.namespace, cronjob)
        self.log.info(f"🛠️ Created CronJob {name}")
        return cronjob

    def delete(self, name: str) -> None:
        """
        🗑 Delete a Kubernetes CronJob.

        Args:
            name (str): Name of the CronJob to delete.
        """
        self.batch_api_instance.delete_namespaced_cron_job(name, self.namespace)
        self.log.info(f"🗑️ Deleted CronJob {name}")

    def status(self, name: str) -> V1CronJob:  # type: ignore
        """
        📊 Get the status of a Kubernetes CronJob.

        Args:
            name (str): Name of the CronJob.

        Returns:
            dict: Status of the CronJob.
        """
        cronjob = self.batch_api_instance.read_namespaced_cron_job(name, self.namespace)

        self.log.info(f"📊 Status of CronJob {name}: {cronjob.status}")

        return cronjob
