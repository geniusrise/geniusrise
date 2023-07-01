import logging
import boto3
from botocore.exceptions import BotoCoreError, ClientError


log = logging.getLogger(__name__)


class ECSManager:
    def __init__(
        self,
        name: str,
        command: list,
        image: str = "geniusrise/geniusrise",
        replicas: int = 1,
        port: int = 80,
        log_group: str = "/ecs/geniusrise",
    ):
        self.name = name
        self.image = image
        self.command = command
        self.replicas = replicas
        self.port = port
        self.client = boto3.client("ecs")
        self.log_group = log_group
        self.logs_client = boto3.client("logs")

    def create_task_definition(self):
        container_definitions = [
            {
                "name": self.name,
                "image": self.image,
                "command": " ".join(self.command),
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
            log.info(f"Task definition {self.name} created.")
            return response["taskDefinition"]["taskDefinitionArn"]
        except (BotoCoreError, ClientError) as error:
            log.error(f"Error creating task definition {self.name}: {error}")
            return None

    def run_task(self, task_definition_arn: str):
        try:
            response = self.client.run_task(cluster=self.name, taskDefinition=task_definition_arn, count=self.replicas)
            log.info(f"Task {self.name} started.")
            return response
        except (BotoCoreError, ClientError) as error:
            log.error(f"Error starting task {self.name}: {error}")
            return None

    def describe_task(self, task_definition_arn: str):
        try:
            response = self.client.describe_tasks(cluster=self.name, tasks=[task_definition_arn])
            return response
        except (BotoCoreError, ClientError) as error:
            log.error(f"Error getting status of task {self.name}: {error}")
            return None

    def stop_task(self, task_definition_arn: str):
        try:
            response = self.client.stop_task(cluster=self.name, task=task_definition_arn)
            log.info(f"Task {self.name} stopped.")
            return response
        except (BotoCoreError, ClientError) as error:
            log.error(f"Error stopping task {self.name}: {error}")
            return None

    def update_task(self, new_image: str, new_command: list):
        self.image = new_image
        self.command = new_command
        task_definition_arn = self.create_task_definition()
        self.stop_task(task_definition_arn)
        self.run_task(task_definition_arn)