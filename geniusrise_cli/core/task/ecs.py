import boto3
from botocore.exceptions import BotoCoreError, ClientError
import logging
from typing import Dict, Any
from .base import Task


log = logging.getLogger(__name__)


class ECSManager:
    def __init__(self, name: str, image: str, command: list, replicas: int = 1, port: int = 80):
        self.name = name
        self.image = image
        self.command = command
        self.replicas = replicas
        self.port = port
        self.client = boto3.client("ecs")

    def create_task_definition(self):
        container_definitions = [
            {
                "name": self.name,
                "image": self.image,
                "command": self.command,
                "portMappings": [{"containerPort": self.port, "protocol": "tcp"}],
            }
        ]

        try:
            response = self.client.register_task_definition(
                family=self.name,
                networkMode="bridge",
                containerDefinitions=container_definitions,
                requiresCompatibilities=[
                    "EC2",
                ],
                cpu="256",
                memory="512",
            )
            logging.info(f"Task definition {self.name} created.")
            return response["taskDefinition"]["taskDefinitionArn"]
        except (BotoCoreError, ClientError) as error:
            logging.error(f"Error creating task definition {self.name}: {error}")
            return None

    def run_task(self, task_definition_arn: str):
        try:
            response = self.client.run_task(cluster=self.name, taskDefinition=task_definition_arn, count=self.replicas)
            logging.info(f"Task {self.name} started.")
            return response
        except (BotoCoreError, ClientError) as error:
            logging.error(f"Error starting task {self.name}: {error}")
            return None

    def describe_task(self, task_definition_arn: str):
        try:
            response = self.client.describe_tasks(cluster=self.name, tasks=[task_definition_arn])
            return response
        except (BotoCoreError, ClientError) as error:
            logging.error(f"Error getting status of task {self.name}: {error}")
            return None

    def stop_task(self, task_definition_arn: str):
        try:
            response = self.client.stop_task(cluster=self.name, task=task_definition_arn)
            logging.info(f"Task {self.name} stopped.")
            return response
        except (BotoCoreError, ClientError) as error:
            logging.error(f"Error stopping task {self.name}: {error}")
            return None

    def update_task(self, new_image: str, new_command: list):
        self.image = new_image
        self.command = new_command
        task_definition_arn = self.create_task_definition()
        self.stop_task(task_definition_arn)
        self.run_task(task_definition_arn)


class ECSTask(Task, ECSManager):
    def __init__(
        self,
        name: str,
        image: str = "geniusrise/geniusrise",
        command: str = "--help",
        replicas: int = 1,
        port: int = 80,
        log_group: str = "/ecs/geniusrise",
    ):
        Task.__init__(self)
        ECSManager.__init__(self, name, image, command, replicas, port)  # type: ignore
        self.log_group = log_group
        self.logs_client = boto3.client("logs")

    def run(self):
        task_definition_arn = self.create_task_definition()
        self.run_task(task_definition_arn)

    def destroy(self):
        task_definition_arn = self.create_task_definition()
        self.stop_task(task_definition_arn)

    def get_status(self) -> Dict[str, Any]:
        """
        Get the status of the task

        Returns:
            Dict[str, Any]: The status of the task
        """
        try:
            task_definition_arn = self.create_task_definition()
            status = self.describe_task(task_definition_arn)
            return status
        except (BotoCoreError, ClientError) as error:
            logging.error(f"Error getting status of task {self.name}: {error}")
            return {}

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get the details of the task and the task definition

        Returns:
            Dict[str, Any]: The details of the task and the task definition
        """
        try:
            # Get the details of the task
            task_definition_arn = self.create_task_definition()
            task_stats = self.describe_task(task_definition_arn)

            # Get the details of the task definition
            response = self.client.list_task_definitions(
                familyPrefix=self.name, status="ACTIVE", sort="DESC", maxResults=1
            )
            task_definition_stats = response["taskDefinitionArns"]

            return {"task": task_stats, "task_definition": task_definition_stats}
        except (BotoCoreError, ClientError) as error:
            logging.error(f"Error getting statistics of task {self.name}: {error}")
            return {}

    def get_logs(self) -> Dict[str, str]:
        """
        Get the logs of the task

        Returns:
            Dict[str, str]: The logs of the task
        """
        try:
            response = self.logs_client.filter_log_events(logGroupName=self.log_group, filterPattern=self.name)
            logs = {event["timestamp"]: event["message"] for event in response["events"]}
            return logs
        except (BotoCoreError, ClientError) as error:
            logging.error(f"Error getting logs of task {self.name}: {error}")
            return {}
