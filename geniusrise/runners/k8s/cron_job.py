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
from kubernetes.client import BatchV1Api
from typing import List, Optional

from .job import Job


class CronJob(Job):
    def __init__(self):
        super().__init__()
        self.batch_api_instance: BatchV1Api = None  # type: ignore

    def create_parser(self, parser: ArgumentParser) -> ArgumentParser:
        subparsers = parser.add_subparsers(dest="command")

        # Parser for create_cronjob
        create_parser = subparsers.add_parser("create_cronjob", help="Create a new cronjob.")
        create_parser.add_argument("name", help="Name of the cronjob.", type=str)
        create_parser.add_argument(
            "image", help="Docker image for the cronjob.", type=str, default="geniusrise/geniusrise"
        )
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

        return parser

    def run(self, args: Namespace) -> None:
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
            self.log.error("Unknown command: %s", args.command)

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
    ) -> None:
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

    def delete(self, name: str) -> None:
        """
        🗑 Delete a Kubernetes CronJob.

        Args:
            name (str): Name of the CronJob to delete.
        """
        self.batch_api_instance.delete_namespaced_cron_job(name, self.namespace)
        self.log.info(f"🗑️ Deleted CronJob {name}")

    def status(self, name: str) -> dict:  # type: ignore
        """
        📊 Get the status of a Kubernetes CronJob.

        Args:
            name (str): Name of the CronJob.

        Returns:
            dict: Status of the CronJob.
        """
        cronjob = self.batch_api_instance.read_namespaced_cron_job(name, self.namespace)
        return {"cronjob_status": cronjob.status}
