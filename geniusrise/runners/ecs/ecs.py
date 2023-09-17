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
from typing import List, Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError

log = logging.getLogger(__name__)


class ECSManager:
    """
    A class used to manage the lifecycle of an ECS container.

    ...

    Attributes
    ----------
    name : str
        the name of the ECS task or service
    command : List[str]
        the command that the container runs
    cluster : str
        the name of the ECS cluster
    subnet_ids : List[str]
        the subnet IDs for the task or service
    security_group_ids : List[str]
        the security group IDs for the task or service
    image : str
        the Docker image for the task
    replicas : int
        the number of task replicas
    port : int
        the port that the container listens on
    log_group : str
        the CloudWatch log group for the task logs
    cpu : int
        the CPU value for the task
    memory : int
        the memory value for the task

    Methods
    -------
    create_task_definition()
        Registers a new task definition from the attributes of this class
    run_task(task_definition_arn: str)
        Runs a new task using the specified task definition ARN
    describe_task(task_definition_arn: str)
        Describes a task using the specified task definition ARN
    stop_task(task_definition_arn: str)
        Stops a running task using the specified task definition ARN
    update_task(new_image: str, new_command: list)
        Updates a task with a new Docker image and command
    create_service(task_definition_arn: str)
        Creates a new service using the specified task definition ARN
    update_service(task_definition_arn: str)
        Updates a service with a new task definition ARN
    delete_service()
        Deletes the service
    """

    def __init__(
        self,
        name: str,
        account_id: str,
        cluster: str,
        command: List[str] = [],
        subnet_ids: List[str] = [],
        security_group_ids: List[str] = [],
        image: str = "geniusrise/geniusrise",
        replicas: int = 1,
        port: int = 80,
        log_group: str = "/ecs/geniusrise",
        cpu: int = 256,
        memory: int = 512,
    ):
        """
        Constructs all the necessary attributes for the ECSManager object.

        Parameters
        ----------
            name : str
                the name of the ECS task or service
            account_id : str
                the id of the AWS account
            command : List[str]
                the command that the container runs
            cluster : str
                the name of the ECS cluster
            subnet_ids : List[str]
                the subnet IDs for the task or service
            security_group_ids : List[str]
                the security group IDs for the task or service
            image : str, optional
                the Docker image for the task (default is "geniusrise/geniusrise")
            replicas : int, optional
                the number of task replicas (default is 1)
            port : int, optional
                the port that the container listens on (default is 80)
            log_group : str, optional
                the CloudWatch log group for the task logs (default is "/ecs/geniusrise")
            cpu : int, optional
                the CPU value for the task (default is 256)
            memory : int, optional
                the memory value for the task (default is 512)
        """
        self.name = name
        self.image = image
        self.cluster = cluster
        self.command = command
        self.replicas = replicas
        self.port = port
        self.client = boto3.client("ecs")
        self.log_group = log_group
        self.logs_client = boto3.client("logs")
        self.subnet_ids = subnet_ids
        self.security_group_ids = security_group_ids
        self.cpu = cpu
        self.account_id = account_id
        self.memory = memory

    def create_task_definition(self) -> Optional[str]:
        """
        Registers a new task definition from the attributes of this class.

        Returns
        -------
        str
            The ARN of the task definition, or None if an error occurred.
        """
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
                networkMode="awsvpc",
                containerDefinitions=container_definitions,
                requiresCompatibilities=[
                    "FARGATE",
                ],
                cpu=str(self.cpu),
                memory=str(self.memory),
                executionRoleArn=f"arn:aws:iam::{self.account_id}:role/ecsTaskExecutionRole",
            )
            log.info(f"Task definition {self.name} created.")
            return response["taskDefinition"]["taskDefinitionArn"]
        except (BotoCoreError, ClientError) as error:
            log.error(f"Error creating task definition {self.name}: {error}")
            return None

    def run_task(self, task_definition_arn: str) -> Optional[dict]:
        """
        Runs a new task using the specified task definition ARN.

        Parameters
        ----------
        task_definition_arn : str
            The ARN of the task definition to run.

        Returns
        -------
        dict
            The response from the ECS API, or None if an error occurred.
        """
        try:
            response = self.client.run_task(
                cluster=self.cluster,
                taskDefinition=task_definition_arn,
                count=self.replicas,
                launchType="FARGATE",
                networkConfiguration={
                    "awsvpcConfiguration": {
                        "subnets": self.subnet_ids,
                        "assignPublicIp": "ENABLED",
                        "securityGroups": self.security_group_ids,
                    }
                },
                platformVersion="LATEST",
            )
            log.info(f"Task {self.name} started.")
            return response
        except (BotoCoreError, ClientError) as error:
            log.error(f"Error starting task {self.name}: {error}")
            return None

    def describe_task(self, task_definition_arn: str) -> Optional[dict]:
        """
        Describes a task using the specified task definition ARN.

        Parameters
        ----------
        task_definition_arn : str
            The ARN of the task definition to describe.

        Returns
        -------
        dict
            The response from the ECS API, or None if an error occurred.
        """
        try:
            response = self.client.describe_tasks(cluster=self.cluster, tasks=[task_definition_arn])
            return response
        except (BotoCoreError, ClientError) as error:
            log.error(f"Error getting status of task {self.name}: {error}")
            return None

    def stop_task(self, task_definition_arn: str) -> Optional[dict]:
        """
        Stops a running task using the specified task definition ARN.

        Parameters
        ----------
        task_definition_arn : str
            The ARN of the task definition to stop.

        Returns
        -------
        dict
            The response from the ECS API, or None if an error occurred.
        """
        try:
            response = self.client.stop_task(cluster=self.cluster, task=task_definition_arn)
            log.info(f"Task {self.name} stopped.")
            return response
        except (BotoCoreError, ClientError) as error:
            log.error(f"Error stopping task {self.name}: {error}")
            return None

    def update_task(self, new_image: str, new_command: list) -> None:
        """
        Updates a task with a new Docker image and command.

        Parameters
        ----------
        new_image : str
            The new Docker image for the task.
        new_command : list
            The new command for the task.
        """
        self.image = new_image
        self.command = new_command
        task_definition_arn = self.create_task_definition()
        if task_definition_arn:
            self.stop_task(task_definition_arn)
            self.run_task(task_definition_arn)
        else:
            log.error(f"Error updating task {self.name} - could not create ECS task definition.")

    def create_service(self, task_definition_arn: str) -> Optional[dict]:
        """
        Creates a new service using the specified task definition ARN.

        Parameters
        ----------
        task_definition_arn : str
            The ARN of the task definition to use for the service.

        Returns
        -------
        dict
            The response from the ECS API, or None if an error occurred.
        """
        try:
            response = self.client.create_service(
                cluster=self.cluster,
                serviceName=self.name,
                taskDefinition=task_definition_arn,
                desiredCount=self.replicas,
                launchType="FARGATE",
                networkConfiguration={
                    "awsvpcConfiguration": {
                        "subnets": self.subnet_ids,
                        "assignPublicIp": "ENABLED",
                        "securityGroups": self.security_group_ids,
                    }
                },
            )
            log.info(f"Service {self.name} created.")
            return response
        except (BotoCoreError, ClientError) as error:
            log.error(f"Error creating service {self.name}: {error}")
            return None

    def update_service(self, task_definition_arn: str) -> Optional[dict]:
        """
        Updates a service with a new task definition ARN.

        Parameters
        ----------
        task_definition_arn : str
            The new ARN of the task definition to use for the service.

        Returns
        -------
        dict
            The response from the ECS API, or None if an error occurred.
        """
        try:
            response = self.client.update_service(
                cluster=self.cluster,
                service=self.name,
                taskDefinition=task_definition_arn,
                desiredCount=self.replicas,
            )
            log.info(f"Service {self.name} updated.")
            return response
        except (BotoCoreError, ClientError) as error:
            log.error(f"Error updating service {self.name}: {error}")
            return None

    def delete_service(self) -> Optional[dict]:
        """
        Deletes the service.

        Returns
        -------
        dict
            The response from the ECS API, or None if an error occurred.
        """
        try:
            response = self.client.delete_service(
                cluster=self.cluster,
                service=self.name,
            )
            log.info(f"Service {self.name} deleted.")
            return response
        except (BotoCoreError, ClientError) as error:
            log.error(f"Error deleting service {self.name}: {error}")
            return None
