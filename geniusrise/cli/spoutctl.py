# geniusrise
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

import argparse
import logging

import emoji  # type: ignore

from geniusrise.cli.discover import DiscoveredSpout
from geniusrise.core import ECSManager, K8sManager, Spout


class SpoutCtl:
    """
    Class for managing spouts end-to-end from the command line.
    """

    def __init__(self, discovered_spout: DiscoveredSpout):
        """
        Initialize SpoutCtl with a DiscoveredSpout object.

        Args:
            discovered_spout (DiscoveredSpout): DiscoveredSpout object used to create and manage spouts.
        """
        self.discovered_spout = discovered_spout
        self.spout = None
        self.log = logging.getLogger(self.__class__.__name__)

    def create_parser(self, parser):
        """
        Add arguments to the command-line parser for managing the spout.

        Args:
            parser (argparse.ArgumentParser): Command-line parser.
        """
        subparsers = parser.add_subparsers(dest="command")

        # Create subparser for 'create' command
        create_parser = subparsers.add_parser("run", help="Run a spout locally.")
        create_parser.add_argument(
            "output_type",
            choices=["batch", "streaming"],
            help="Choose the type of output configuration: batch or streaming.",
            default="batch",
        )
        create_parser.add_argument(
            "state_type",
            choices=["in_memory", "redis", "postgres", "dynamodb"],
            help="Select the type of state manager: in_memory, redis, postgres, or dynamodb.",
            default="in_memory",
        )
        create_parser.add_argument(
            "--output_folder",
            help="Specify the directory where output files should be stored temporarily.",
            default="/tmp",
            type=str,
        )
        create_parser.add_argument(
            "--kafka_servers",
            help="Kafka connection string for streaming spouts.",
            default="localhost:9092",
            type=str,
        )
        create_parser.add_argument(
            "--output_topic",
            help="Kafka output topic for streaming spouts.",
            default="test",
            type=str,
        )
        create_parser.add_argument(
            "--bucket", help="Provide the name of the S3 bucket for output storage.", default="my-bucket", type=str
        )
        create_parser.add_argument(
            "--s3_folder", help="Indicate the S3 folder for output storage.", default="my-s3-folder", type=str
        )
        create_parser.add_argument(
            "--redis_host", help="Enter the host address for the Redis server.", default="localhost", type=str
        )
        create_parser.add_argument(
            "--redis_port", help="Enter the port number for the Redis server.", default=6379, type=int
        )
        create_parser.add_argument("--redis_db", help="Specify the Redis database to be used.", default=0, type=int)
        create_parser.add_argument(
            "--postgres_host", help="Enter the host address for the PostgreSQL server.", default="localhost", type=str
        )
        create_parser.add_argument(
            "--postgres_port", help="Enter the port number for the PostgreSQL server.", default=5432, type=int
        )
        create_parser.add_argument(
            "--postgres_user", help="Provide the username for the PostgreSQL server.", default="postgres", type=str
        )
        create_parser.add_argument(
            "--postgres_password", help="Provide the password for the PostgreSQL server.", default="password", type=str
        )
        create_parser.add_argument(
            "--postgres_database", help="Specify the PostgreSQL database to be used.", default="mydatabase", type=str
        )
        create_parser.add_argument(
            "--postgres_table", help="Specify the PostgreSQL table to be used.", default="mytable", type=str
        )
        create_parser.add_argument(
            "--dynamodb_table_name", help="Provide the name of the DynamoDB table.", default="mytable", type=str
        )
        create_parser.add_argument(
            "--dynamodb_region_name", help="Specify the AWS region for DynamoDB.", default="us-west-2", type=str
        )
        create_parser.add_argument(
            "--other",
            nargs=argparse.REMAINDER,
            help="Additional keyword arguments to pass to the spout.",
        )

        # Create subparser for 'deploy' command
        deploy_parser = subparsers.add_parser("deploy", help="Deploy a spout remotely.")
        deploy_parser.add_argument(
            "manager_type",
            choices=["k8s", "ecs"],
            help="Choose the type of manager for remote execution: k8s or ecs.",
        )
        deploy_parser.add_argument(
            "method_name",
            type=str,
            help="The name of the method to execute remotely.",
        )
        deploy_parser.add_argument(
            "--name",
            type=str,
            help="The name of the ECS task or service (required for both k8s and ecs).",
        )
        deploy_parser.add_argument(
            "--account_id",
            type=str,
            help="The id of the AWS account (required for ecs).",
        )
        deploy_parser.add_argument(
            "--namespace",
            type=str,
            nargs="+",
            help="The command that the container runs (required for both k8s and ecs).",
        )
        deploy_parser.add_argument(
            "--cluster",
            help="The name of the ECS cluster (required for ecs).",
        )
        deploy_parser.add_argument(
            "--subnet_ids",
            type=str,
            nargs="+",
            help="The subnet IDs for the task or service (required for ecs).",
        )
        deploy_parser.add_argument(
            "--security_group_ids",
            type=str,
            nargs="+",
            help="The security group IDs for the task or service (required for ecs).",
        )
        deploy_parser.add_argument(
            "--image",
            type=str,
            help="The Docker image for the task (optional for both k8s and ecs, default is 'geniusrise/geniusrise').",
            default="geniusrise/geniusrise",
        )
        deploy_parser.add_argument(
            "--replicas",
            type=int,
            help="The number of task replicas (optional for both k8s and ecs, default is 1).",
            default=1,
        )
        deploy_parser.add_argument(
            "--port",
            type=int,
            help="The port that the container listens on (optional for both k8s and ecs, default is 80).",
            default=80,
        )
        deploy_parser.add_argument(
            "--log_group",
            type=str,
            help="The CloudWatch log group for the task logs (required for ecs, default is '/ecs/geniusrise').",
            default="/ecs/geniusrise",
        )
        deploy_parser.add_argument(
            "--cpu",
            type=int,
            help="The CPU value for the task (required for ecs, default is 256).",
            default=256,
        )
        deploy_parser.add_argument(
            "--memory",
            type=int,
            help="The memory value for the task (required for ecs, default is 512).",
            default=512,
        )
        deploy_parser.add_argument(
            "output_type",
            choices=["batch", "streaming"],
            help="Choose the type of output configuration: batch or streaming.",
            default="batch",
        )
        deploy_parser.add_argument(
            "state_type",
            choices=["in_memory", "redis", "postgres", "dynamodb"],
            help="Select the type of state manager: in_memory, redis, postgres, or dynamodb.",
            default="in_memory",
        )
        deploy_parser.add_argument(
            "--output_folder",
            help="Specify the directory where output files should be stored.",
            default="/tmp",
            type=str,
        )
        deploy_parser.add_argument(
            "--bucket", help="Provide the name of the S3 bucket for output storage.", default="my-bucket", type=str
        )
        deploy_parser.add_argument(
            "--s3_folder", help="Indicate the S3 folder for output storage.", default="my-s3-folder", type=str
        )
        deploy_parser.add_argument(
            "--redis_host", help="Enter the host address for the Redis server.", default="localhost", type=str
        )
        deploy_parser.add_argument(
            "--redis_port", help="Enter the port number for the Redis server.", default=6379, type=int
        )
        deploy_parser.add_argument("--redis_db", help="Specify the Redis database to be used.", default=0, type=int)
        deploy_parser.add_argument(
            "--postgres_host", help="Enter the host address for the PostgreSQL server.", default="localhost", type=str
        )
        deploy_parser.add_argument(
            "--postgres_port", help="Enter the port number for the PostgreSQL server.", default=5432, type=int
        )
        deploy_parser.add_argument(
            "--postgres_user", help="Provide the username for the PostgreSQL server.", default="postgres", type=str
        )
        deploy_parser.add_argument(
            "--postgres_password", help="Provide the password for the PostgreSQL server.", default="password", type=str
        )
        deploy_parser.add_argument(
            "--postgres_database", help="Specify the PostgreSQL database to be used.", default="mydatabase", type=str
        )
        deploy_parser.add_argument(
            "--postgres_table", help="Specify the PostgreSQL table to be used.", default="mytable", type=str
        )
        deploy_parser.add_argument(
            "--dynamodb_table_name", help="Provide the name of the DynamoDB table.", default="mytable", type=str
        )
        deploy_parser.add_argument(
            "--dynamodb_region_name", help="Specify the AWS region for DynamoDB.", default="us-west-2", type=str
        )
        deploy_parser.add_argument(
            "--other",
            nargs=argparse.REMAINDER,
            help="Additional keyword arguments to pass to the spout.",
        )

        # Kubernetes commands
        k8s_parser = subparsers.add_parser("k8s", help="Kubernetes management commands")
        k8s_parser.add_argument(
            "action",
            choices=["scale", "delete", "status", "statistics", "logs"],
            help="Action to perform",
        )
        k8s_parser.add_argument("--name", help="Name of the deployment")
        k8s_parser.add_argument("--namespace", default="geniusrise", help="Namespace of the deployment")
        k8s_parser.add_argument("--replicas", type=int, help="Number of replicas for update and scale actions")

        # ECS commands
        ecs_parser = subparsers.add_parser("ecs", help="ECS management commands")
        ecs_parser.add_argument("action", choices=["describe", "stop", "delete"], help="Action to perform")
        ecs_parser.add_argument("--name", help="Name of the task or service")
        ecs_parser.add_argument(
            "--task-definition-arn", help="ARN of the task definition for run, describe, stop, and update actions"
        )

        # Create subparser for 'help' command
        execute_parser = subparsers.add_parser("help", help="Print help for the spout.")
        execute_parser.add_argument("method", help="The method to execute.")

        return parser

    def run(self, args):
        """
        Run the command-line interface.

        Args:
            args (argparse.Namespace): Parsed command-line arguments.
        """
        self.log.info(emoji.emojize(f"Running command: {args.command} :rocket:"))
        try:
            if args.command == "run":
                kwargs = {
                    k: v
                    for k, v in vars(args).items()
                    if v is not None and k not in ["output_type", "state_type", "kwargs"]
                }
                other = args.other or {}
                self.spout = self.create_spout(args.output_type, args.state_type, **{**kwargs, **other})
                result = self.execute_spout(self.spout, args.method)
                print(result)

            elif args.command == "deploy":
                kwargs = {
                    k: v for k, v in vars(args).items() if v is not None and k not in ["manager_type", "method_name"]
                }
                other = args.other or {}
                result = self.execute_remote(args.manager_type, args.method_name, **{**kwargs, **other})
                print(result)

            elif args.command == "k8s":
                k8s_manager = K8sManager(name=args.name, namespace=args.namespace)  # Initialize K8sManager
                if args.action == "scale":
                    k8s_manager.scale_deployment(args.replicas)
                elif args.action == "delete":
                    k8s_manager.delete_deployment()
                elif args.action == "status":
                    k8s_manager.get_status()
                elif args.action == "statistics":
                    k8s_manager.get_statistics()
                elif args.action == "logs":
                    k8s_manager.get_logs()

            elif args.command == "ecs":
                ecs_manager = ECSManager(name=args.name, account_id="")  # Initialize ECSManager
                if args.action == "run":
                    ecs_manager.run_task(args.task_definition_arn)
                elif args.action == "describe":
                    ecs_manager.describe_task(args.task_definition_arn)
                elif args.action == "stop":
                    ecs_manager.stop_task(args.task_definition_arn)
                # elif args.action == "update": # TODO: did not init ECSManager full, this will call create_task_definition!
                #     ecs_manager.update_task(args.new_image, args.new_command)
                elif args.action == "delete":
                    ecs_manager.stop_task(args.task_definition_arn)

            elif args.command == "help":
                self.discovered_spout.klass.print_help(self.discovered_spout.klass)
        except Exception as e:
            self.log.error(f"An error occurred: {e}")

    def create_spout(self, output_type: str, state_type: str, **kwargs) -> Spout:
        """
        Create a spout of a specific type.

        Args:
            output_type (str): The type of output config ("batch" or "streaming").
            state_type (str): The type of state manager ("in_memory", "redis", "postgres", or "dynamodb").
            **kwargs: Additional keyword arguments for initializing the spout.

        Returns:
            Spout: The created spout.
        """
        return Spout.create(klass=self.discovered_spout.klass, output_type=output_type, state_type=state_type, **kwargs)  # type: ignore

    def execute_spout(self, spout: Spout, method_name: str, *args, **kwargs):
        """
        Execute a method of a spout.

        Args:
            spout (Spout): The spout to execute.
            method_name (str): The name of the method to execute.
            *args: Positional arguments to pass to the method.
            **kwargs: Keyword arguments to pass to the method.

        Returns:
            Any: The result of the method.
        """
        return spout.__call__(method_name, *args, **kwargs)

    def execute_remote(self, manager_type: str, method_name: str, **kwargs) -> None:
        """
        Execute a method remotely and manage the state.

        Args:
            manager_type (str): The type of manager to use for remote execution ("k8s" or "ecs").
            method_name (str): The name of the method to execute.
            **kwargs: Keyword arguments to pass to the method.

        Returns:
            Any: The result of the method.
        """
        if self.spout:
            self.manager = self.spout.execute_remote(manager_type=manager_type, method_name=method_name, **kwargs)
        else:
            self.log.error(f"Spout {self.discovered_spout.name} is not initialized.")
