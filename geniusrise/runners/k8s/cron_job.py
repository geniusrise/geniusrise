from argparse import ArgumentParser, Namespace
import json
from kubernetes import client
from kubernetes.client import BatchV1beta1Api

from .job import Job


class CronJob(Job):
    def __init__(self):
        super().__init__()
        self.batch_beta_api_instance: BatchV1beta1Api = None  # type: ignore

    def create_parser(self, parser: ArgumentParser) -> ArgumentParser:
        subparsers = parser.add_subparsers(dest="command")

        # Parser for create_cronjob
        create_parser = subparsers.add_parser("create_cronjob", help="Create a new cronjob.")
        create_parser.add_argument("name", help="Name of the cronjob.", type=str)
        create_parser.add_argument("image", help="Docker image for the cronjob.", type=str)
        create_parser.add_argument("command", help="Command to run in the container.", type=str)
        create_parser.add_argument("schedule", help="Cron schedule.", type=str)
        create_parser.add_argument("--env_vars", help="Environment variables as a JSON string.", type=str, default="{}")

        # Parser for delete_cronjob
        delete_parser = subparsers.add_parser("delete_cronjob", help="Delete a cronjob.")
        delete_parser.add_argument("name", help="Name of the cronjob.", type=str)

        # Parser for get_cronjob_status
        status_parser = subparsers.add_parser("get_cronjob_status", help="Get the status of a cronjob.")
        status_parser.add_argument("name", help="Name of the cronjob.", type=str)

        return parser

    def run(self, args: Namespace) -> None:
        if args.command == "create_cronjob":
            self.create_cronjob(args.name, args.image, args.command, args.schedule, env_vars=json.loads(args.env_vars))
        elif args.command == "delete_cronjob":
            self.delete_cronjob(args.name)
        elif args.command == "get_cronjob_status":
            self.get_cronjob_status(args.name)
        else:
            self.log.error("Unknown command: %s", args.command)

    def __create_cronjob_spec(
        self, image: str, command: str, schedule: str, env_vars: dict = {}
    ) -> client.V1beta1CronJobSpec:
        """
        📦 Create a Kubernetes CronJob specification.

        Args:
            image (str): Docker image for the CronJob.
            command (str): Command to run in the container.
            schedule (str): Cron schedule.
            env_vars (dict): Environment variables for the CronJob.

        Returns:
            client.V1beta1CronJobSpec: The CronJob specification.
        """
        # TODO: Add resource requirements like CPU, memory, etc.
        return client.V1beta1CronJobSpec(
            schedule=schedule,
            job_template=client.V1beta1JobTemplateSpec(
                metadata=client.V1ObjectMeta(labels=self.labels, annotations=self.annotations),
                spec=self._create_job_spec(image, command, env_vars),
            ),
        )

    def create_cronjob(self, name: str, image: str, command: str, schedule: str, env_vars: dict = {}) -> None:
        """
        🛠 Create a Kubernetes CronJob.

        Args:
            name (str): Name of the CronJob.
            image (str): Docker image for the CronJob.
            command (str): Command to run in the container.
            schedule (str): Cron schedule.
            env_vars (dict): Environment variables for the CronJob.
        """
        cronjob_spec = self.__create_cronjob_spec(image, command, schedule, env_vars)
        cronjob = client.V1beta1CronJob(
            api_version="batch/v1beta1",
            kind="CronJob",
            metadata=client.V1ObjectMeta(name=name, labels=self.labels, annotations=self.annotations),
            spec=cronjob_spec,
        )
        self.batch_beta_api_instance.create_namespaced_cron_job(self.namespace, cronjob)
        self.log.info(f"🛠️ Created CronJob {name}")

    def delete_cronjob(self, name: str) -> None:
        """
        🗑 Delete a Kubernetes CronJob.

        Args:
            name (str): Name of the CronJob to delete.
        """
        self.batch_beta_api_instance.delete_namespaced_cron_job(name, self.namespace)
        self.log.info(f"🗑️ Deleted CronJob {name}")

    def get_cronjob_status(self, name: str) -> dict:
        """
        📊 Get the status of a Kubernetes CronJob.

        Args:
            name (str): Name of the CronJob.

        Returns:
            dict: Status of the CronJob.
        """
        cronjob = self.batch_beta_api_instance.read_namespaced_cron_job(name, self.namespace)
        return {"cronjob_status": cronjob.status}
