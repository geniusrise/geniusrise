import argparse
from typing import Optional, Any

from geniusrise.core import Spout, K8sManager, ECSManager
from geniusrise.cli.discover import DiscoveredSpout


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

    def create_parser(self):
        """
        Create a command-line parser with arguments for managing the spout.

        Returns:
            argparse.ArgumentParser: Command-line parser.
        """
        parser = argparse.ArgumentParser(description="Manage a spout.")
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
            help="Specify the directory where output files should be stored.",
            default="/tmp",
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
            "--command",
            type=str,
            nargs="+",
            help="The command that the container runs (required for both k8s and ecs).",
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
        if args.command == "run":
            kwargs = {
                k: v
                for k, v in vars(args).items()
                if v is not None and k not in ["command", "output_type", "state_type"]
            }
            self.spout = self.create_spout(args.output_type, args.state_type, **kwargs)
            result = self.execute_spout(self.spout, args.method)
            print(result)
        elif args.command == "deploy":
            kwargs = {
                k: v
                for k, v in vars(args).items()
                if v is not None and k not in ["command", "manager_type", "method_name"]
            }
            result = self.execute_remote(args.manager_type, args.method_name, **kwargs)
            print(result)
        elif args.command == "help":
            self.discovered_spout.klass.print_help()

    def create_spout(self, output_type: str, state_type: str, **kwargs):
        """
        Create a spout of a specific type.

        Args:
            output_type (str): The type of output config ("batch" or "streaming").
            state_type (str): The type of state manager ("in_memory", "redis", "postgres", or "dynamodb").
            **kwargs: Additional keyword arguments for initializing the spout.

        Returns:
            Spout: The created spout.
        """
        return self.discovered_spout.klass.create(output_type, state_type, **kwargs)  # type: ignore

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

    def execute_remote(self, manager_type: str, method_name: str, **kwargs) -> Optional[Any]:
        """
        Execute a method remotely and manage the state.

        Args:
            manager_type (str): The type of manager to use for remote execution ("k8s" or "ecs").
            method_name (str): The name of the method to execute.
            **kwargs: Keyword arguments to pass to the method.

        Returns:
            Any: The result of the method.
        """
        manager: K8sManager | ECSManager
        if manager_type == "k8s":
            manager = K8sManager(
                name=kwargs["name"],
                namespace=kwargs["namespace"],
                image=kwargs["image"],
                command=kwargs["command"],
                replicas=kwargs["replicas"],
                port=kwargs["port"],
            )
        elif manager_type == "ecs":
            manager = ECSManager(
                name=kwargs["name"],
                account_id=kwargs["account_id"],
                command=kwargs["command"],
                cluster=kwargs["cluster"],
                subnet_ids=kwargs["subnet_ids"],
                security_group_ids=kwargs["security_group_ids"],
                image=kwargs["image"],
                replicas=kwargs["replicas"],
                port=kwargs["port"],
                log_group=kwargs["log_group"],
                cpu=kwargs["cpu"],
                memory=kwargs["memory"],
            )
        else:
            raise ValueError(f"Unknown manager type: {manager_type}")

        return getattr(manager, method_name)()

    def cli(self):
        """
        Main function to be called when geniusrise is run from the command line.
        """
        parser = self.create_parser()
        return parser
