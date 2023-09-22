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

import argparse
import json
import logging
import tempfile
from typing import Any

import emoji  # type: ignore
from rich_argparse import RichHelpFormatter

from geniusrise.cli.discover import DiscoveredSpout
from geniusrise.core import Spout
from geniusrise.runners.k8s import Deployment, Service, Job, CronJob


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
        # fmt: off

        # Create subparser for 'create' command
        create_parser = subparsers.add_parser("rise", help="Run a spout locally.", formatter_class=RichHelpFormatter)
        create_parser.add_argument("output_type", choices=["batch", "streaming", "stream_to_batch"], help="Choose the type of output data: batch or streaming.", default="batch")
        create_parser.add_argument("state_type", choices=["none", "redis", "postgres", "dynamodb", "prometheus"], help="Select the type of state manager: none, redis, postgres, or dynamodb.", default="none")
        create_parser.add_argument("--buffer_size", help="Specify the size of the buffer.", default=100, type=int)
        # output
        create_parser.add_argument("--output_folder", help="Specify the directory where output files should be stored temporarily.", default=tempfile.mkdtemp(), type=str)
        create_parser.add_argument("--output_kafka_topic", help="Kafka output topic for streaming spouts.", default="test", type=str)
        create_parser.add_argument("--output_kafka_cluster_connection_string", help="Kafka connection string for streaming spouts.", default="localhost:9094", type=str)
        create_parser.add_argument("--output_s3_bucket", help="Provide the name of the S3 bucket for output storage.", default="geniusrise-test", type=str)
        create_parser.add_argument("--output_s3_folder", help="Indicate the S3 folder for output storage.", default="geniusrise", type=str)
        # state
        create_parser.add_argument("--redis_host", help="Enter the host address for the Redis server.", default="localhost", type=str)
        create_parser.add_argument("--redis_port", help="Enter the port number for the Redis server.", default=6379, type=int)
        create_parser.add_argument("--redis_db", help="Specify the Redis database to be used.", default=0, type=int)
        create_parser.add_argument("--postgres_host", help="Enter the host address for the PostgreSQL server.", default="localhost", type=str)
        create_parser.add_argument("--postgres_port", help="Enter the port number for the PostgreSQL server.", default=5432, type=int)
        create_parser.add_argument("--postgres_user", help="Provide the username for the PostgreSQL server.", default="postgres", type=str)
        create_parser.add_argument("--postgres_password", help="Provide the password for the PostgreSQL server.", default="password", type=str)
        create_parser.add_argument("--postgres_database", help="Specify the PostgreSQL database to be used.", default="mydatabase", type=str)
        create_parser.add_argument("--postgres_table", help="Specify the PostgreSQL table to be used.", default="mytable", type=str)
        create_parser.add_argument("--dynamodb_table_name", help="Provide the name of the DynamoDB table.", default="mytable", type=str)
        create_parser.add_argument("--dynamodb_region_name", help="Specify the AWS region for DynamoDB.", default="us-west-2", type=str)
        create_parser.add_argument("--prometheus_gateway", help="Specify the prometheus gateway URL.", default="localhost:9091", type=str)
        # function
        create_parser.add_argument("method_name", help="The name of the method to execute on the spout.", type=str)
        create_parser.add_argument("--args", nargs=argparse.REMAINDER, help="Additional keyword arguments to pass to the spout.")

        deploy_parser = subparsers.add_parser("deploy", help="Run a spout remotely.", formatter_class=RichHelpFormatter)
        deploy_parser.add_argument("output_type", choices=["batch", "streaming", "stream_to_batch"], help="Choose the type of output data: batch or streaming.", default="batch")
        deploy_parser.add_argument("state_type", choices=["none", "redis", "postgres", "dynamodb", "prometheus"], help="Select the type of state manager: none, redis, postgres, or dynamodb.", default="none")
        deploy_parser.add_argument("deployment_type", choices=["k8s"], help="Choose the type of deployment.", default="k8s")
        # output
        deploy_parser.add_argument("--buffer_size", help="Specify the size of the buffer.", default=100, type=int)
        deploy_parser.add_argument("--output_folder", help="Specify the directory where output files should be stored temporarily.", default="/tmp", type=str)
        deploy_parser.add_argument("--output_kafka_topic", help="Kafka output topic for streaming spouts.", default="test", type=str)
        deploy_parser.add_argument("--output_kafka_cluster_connection_string", help="Kafka connection string for streaming spouts.", default="localhost:9094", type=str)
        deploy_parser.add_argument("--output_s3_bucket", help="Provide the name of the S3 bucket for output storage.", default="geniusrise-test", type=str)
        deploy_parser.add_argument("--output_s3_folder", help="Indicate the S3 folder for output storage.", default="geniusrise", type=str)
        # state
        deploy_parser.add_argument("--redis_host", help="Enter the host address for the Redis server.", default="localhost", type=str)
        deploy_parser.add_argument("--redis_port", help="Enter the port number for the Redis server.", default=6379, type=int)
        deploy_parser.add_argument("--redis_db", help="Specify the Redis database to be used.", default=0, type=int)
        deploy_parser.add_argument("--postgres_host", help="Enter the host address for the PostgreSQL server.", default="localhost", type=str)
        deploy_parser.add_argument("--postgres_port", help="Enter the port number for the PostgreSQL server.", default=5432, type=int)
        deploy_parser.add_argument("--postgres_user", help="Provide the username for the PostgreSQL server.", default="postgres", type=str)
        deploy_parser.add_argument("--postgres_password", help="Provide the password for the PostgreSQL server.", default="password", type=str)
        deploy_parser.add_argument("--postgres_database", help="Specify the PostgreSQL database to be used.", default="mydatabase", type=str)
        deploy_parser.add_argument("--postgres_table", help="Specify the PostgreSQL table to be used.", default="mytable", type=str)
        deploy_parser.add_argument("--dynamodb_table_name", help="Provide the name of the DynamoDB table.", default="mytable", type=str)
        deploy_parser.add_argument("--dynamodb_region_name", help="Specify the AWS region for DynamoDB.", default="us-west-2", type=str)
        deploy_parser.add_argument("--prometheus_gateway", help="Specify the prometheus gateway URL.", default="localhost:9091", type=str)
        # deployment
        deploy_parser.add_argument("--k8s_kind", choices=["deployment", "service", "job", "cron_job"], help="Choose the type of kubernetes resource.", default="job")
        deploy_parser.add_argument("--k8s_name", help="Name of the Kubernetes resource.", type=str)
        deploy_parser.add_argument("--k8s_image", help="Docker image for the Kubernetes resource.", type=str)
        deploy_parser.add_argument("--k8s_replicas", help="Number of replicas.", default=1, type=int)
        deploy_parser.add_argument("--k8s_env_vars", help="Environment variables as a JSON string.", type=json.loads, default="{}")
        deploy_parser.add_argument("--k8s_cpu", help="CPU requirements.", type=str)
        deploy_parser.add_argument("--k8s_memory", help="Memory requirements.", type=str)
        deploy_parser.add_argument("--k8s_storage", help="Storage requirements.", type=str)
        deploy_parser.add_argument("--k8s_gpu", help="GPU requirements.", type=str)
        deploy_parser.add_argument("--k8s_kube_config_path", help="Name of the Kubernetes cluster local config.", type=str, default="~/.kube/config")
        deploy_parser.add_argument("--k8s_api_key", help="GPU requirements.", type=str)
        deploy_parser.add_argument("--k8s_api_host", help="GPU requirements.", type=str)
        deploy_parser.add_argument("--k8s_verify_ssl", help="GPU requirements.", type=str)
        deploy_parser.add_argument("--k8s_ssl_ca_cert", help="GPU requirements.", type=str)
        deploy_parser.add_argument("--k8s_cluster_name", help="Name of the Kubernetes cluster.", type=str)
        deploy_parser.add_argument("--k8s_context_name", help="Name of the kubeconfig context.", type=str)
        deploy_parser.add_argument("--k8s_namespace", help="Kubernetes namespace.", default="default", type=str)
        deploy_parser.add_argument("--k8s_labels", help="Labels for Kubernetes resources, as a JSON string.", type=json.loads, default='{"created_by": "geniusrise"}')
        deploy_parser.add_argument("--k8s_annotations", help="Annotations for Kubernetes resources, as a JSON string.", type=json.loads, default='{"created_by": "geniusrise"}')
        deploy_parser.add_argument("--k8s_port", help="Port to run the spout on as a service.", type=int)
        deploy_parser.add_argument("--k8s_target_port", help="Port to expose the spout on as a service.", type=int)
        deploy_parser.add_argument("--k8s_schedule", help="Schedule to run the spout on as a cron job.", type=str)
        # function
        deploy_parser.add_argument("method_name", help="The name of the method to execute on the spout.", type=str)
        deploy_parser.add_argument("--args", nargs=argparse.REMAINDER, help="Additional keyword arguments to pass to the spout.")

        # Create subparser for 'help' command
        execute_parser = subparsers.add_parser("help", help="Print help for the spout.", formatter_class=RichHelpFormatter)
        execute_parser.add_argument("method", help="The method to execute.")

        # fmt: on
        return parser

    def run(self, args):
        """
        Run the command-line interface.

        Args:
            args (argparse.Namespace): Parsed command-line arguments.
        """
        self.log.info(emoji.emojize(f"Running command: {args.command} :rocket:"))
        try:
            if args.command == "rise":
                kwargs = {
                    k: v
                    for k, v in vars(args).items()
                    if v is not None
                    and "k8s_" not in k
                    and k not in ["output_type", "state_type", "args", "method_name", "deployment_type"]
                }
                other = args.args or []
                other_args, other_kwargs = self.parse_args_kwargs(other)
                self.spout = self.create_spout(args.output_type, args.state_type, **kwargs)

                # Pass the method_name from args to execute_spout
                result = self.execute_spout(self.spout, args.method_name, *other_args, **other_kwargs)
                return result

            elif args.command == "deploy":
                self.deploy_spout(args)

            elif args.command == "help":
                self.discovered_spout.klass.print_help(self.discovered_spout.klass)
        except ValueError as ve:
            self.log.exception(f"Value error: {ve}")
            raise
        except AttributeError as ae:
            self.log.exception(f"Attribute error: {ae}")
            raise
        except Exception as e:
            self.log.exception(f"An unexpected error occurred: {e}")
            raise

    @staticmethod
    def parse_args_kwargs(args_list):
        args = []
        kwargs = {}

        def convert(value):
            try:
                return int(value.replace('"', ""))
            except ValueError:
                try:
                    return float(value.replace('"', ""))
                except ValueError:
                    try:
                        return json.loads(value)
                    except ValueError:
                        return value

        for item in args_list:
            if item[0] == "{":
                i = json.loads(item)
                kwargs = {**kwargs, **i}
            elif "=" in item:
                key, value = item.split("=", 1)
                kwargs[key] = convert(value)
            else:
                args.append(convert(item))

        return args, kwargs

    def create_spout(self, output_type: str, state_type: str, **kwargs) -> Spout:
        r"""
        Create a spout of a specific type.

        Args:
            output_type (str): The type of output ("batch" or "streaming").
            state_type (str): The type of state manager ("none", "redis", "postgres", or "dynamodb").
            **kwargs: Additional keyword arguments for initializing the spout.
                ```
                Keyword Arguments:
                    Batch output:
                    - output_folder (str): The directory where output files should be stored temporarily.
                    - output_s3_bucket (str): The name of the S3 bucket for output storage.
                    - output_s3_folder (str): The S3 folder for output storage.
                    Streaming output:
                    - output_kafka_topic (str): Kafka output topic for streaming spouts.
                    - output_kafka_cluster_connection_string (str): Kafka connection string for streaming spouts.
                    Stream to Batch output:
                    - output_folder (str): The directory where output files should be stored temporarily.
                    - output_s3_bucket (str): The name of the S3 bucket for output storage.
                    - output_s3_folder (str): The S3 folder for output storage.
                    - buffer_size (int): Number of messages to buffer.
                    Redis state manager config:
                    - redis_host (str): The host address for the Redis server.
                    - redis_port (int): The port number for the Redis server.
                    - redis_db (int): The Redis database to be used.
                    Postgres state manager config:
                    - postgres_host (str): The host address for the PostgreSQL server.
                    - postgres_port (int): The port number for the PostgreSQL server.
                    - postgres_user (str): The username for the PostgreSQL server.
                    - postgres_password (str): The password for the PostgreSQL server.
                    - postgres_database (str): The PostgreSQL database to be used.
                    - postgres_table (str): The PostgreSQL table to be used.
                    DynamoDB state manager config:
                    - dynamodb_table_name (str): The name of the DynamoDB table.
                    - dynamodb_region_name (str): The AWS region for DynamoDB.
                    Prometheus state manager config:
                    - prometheus_gateway (str): The push gateway for Prometheus metrics.
                ```

        Returns:
            Spout: The created spout.
        """
        return Spout.create(
            klass=self.discovered_spout.klass,
            output_type=output_type,
            state_type=state_type,
            **kwargs,
        )

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

    def deploy_spout(self, args):
        r"""
        Deploy a spout of a specific type.

        Args:
            **kwargs: Additional keyword arguments for initializing the spout.
                ```
                Keyword Arguments:
                    Batch output:
                    - output_folder (str): The directory where output files should be stored temporarily.
                    - output_s3_bucket (str): The name of the S3 bucket for output storage.
                    - output_s3_folder (str): The S3 folder for output storage.
                    Streaming output:
                    - output_kafka_topic (str): Kafka output topic for streaming spouts.
                    - output_kafka_cluster_connection_string (str): Kafka connection string for streaming spouts.
                    Stream to Batch output:
                    - output_folder (str): The directory where output files should be stored temporarily.
                    - output_s3_bucket (str): The name of the S3 bucket for output storage.
                    - output_s3_folder (str): The S3 folder for output storage.
                    - buffer_size (int): Number of messages to buffer.
                    Redis state manager config:
                    - redis_host (str): The host address for the Redis server.
                    - redis_port (int): The port number for the Redis server.
                    - redis_db (int): The Redis database to be used.
                    Postgres state manager config:
                    - postgres_host (str): The host address for the PostgreSQL server.
                    - postgres_port (int): The port number for the PostgreSQL server.
                    - postgres_user (str): The username for the PostgreSQL server.
                    - postgres_password (str): The password for the PostgreSQL server.
                    - postgres_database (str): The PostgreSQL database to be used.
                    - postgres_table (str): The PostgreSQL table to be used.
                    DynamoDB state manager config:
                    - dynamodb_table_name (str): The name of the DynamoDB table.
                    - dynamodb_region_name (str): The AWS region for DynamoDB.
                    Prometheus state manager config:
                    - prometheus_gateway (str): The push gateway for Prometheus metrics.
                    Deployment
                    - k8s_kind (str): Kind opf kubernetes resource to be deployed as, choices are "deployment", "service", "job", "cron_job"
                    - k8s_name (str): Name of the Kubernetes resource.
                    - k8s_image (str): Docker image for the Kubernetes resource.
                    - k8s_replicas (int): Number of replicas.
                    - k8s_env_vars (json): Environment variables as a JSON string.
                    - k8s_cpu (str): CPU requirements.
                    - k8s_memory (str): Memory requirements.
                    - k8s_storage (str): Storage requirements.
                    - k8s_gpu (str): GPU requirements.
                    - k8s_kube_config_path (str): Name of the Kubernetes cluster local config.
                    - k8s_api_key (str): GPU requirements.
                    - k8s_api_host (str): GPU requirements.
                    - k8s_verify_ssl (str): GPU requirements.
                    - k8s_ssl_ca_cert (str): GPU requirements.
                    - k8s_cluster_name (str): Name of the Kubernetes cluster.
                    - k8s_context_name (str): Name of the kubeconfig context.
                    - k8s_namespace (str): Kubernetes namespace.", default="default
                    - k8s_labels (json): Labels for Kubernetes resources, as a JSON string.
                    - k8s_annotations (json): Annotations for Kubernetes resources, as a JSON string.
                    - k8s_port (int): Port to run the spout on as a service.
                    - k8s_target_port (int): Port to expose the spout on as a service.
                    - k8s_schedule (str): Schedule to run the spout on as a cron job.
                ```
        """
        if args.deployment_type == "k8s":
            kind = args.k8s_kind if args.k8s_kind else "job"

            resource: Deployment | Service | Job | CronJob  # type: ignore
            if kind == "deployment":
                resource = Deployment()
            elif kind == "service":
                resource = Service()
            elif kind == "job":
                resource = Job()
            elif kind == "cron_job":
                resource = CronJob()
            else:
                raise ValueError(f"Invalid kind: {kind}")

            self.log.debug(f"Deploying {kind} {args.k8s_name} with args {args}")
            resource.connect(
                kube_config_path=args.k8s_kube_config_path if args.k8s_kube_config_path else None,
                cluster_name=args.k8s_cluster_name if args.k8s_cluster_name else None,
                context_name=args.k8s_context_name if args.k8s_context_name else None,
                namespace=args.k8s_namespace if args.k8s_namespace else None,
                labels=args.k8s_labels if args.k8s_labels else {"created_by": "geniusrise"},
                annotations=args.k8s_annotations if args.k8s_annotations else None,
                api_key=args.k8s_api_key if args.k8s_api_key else None,
                api_host=args.k8s_api_host if args.k8s_api_host else None,
                verify_ssl=args.k8s_verify_ssl if args.k8s_verify_ssl else None,
                ssl_ca_cert=args.k8s_ssl_ca_cert if args.k8s_ssl_ca_cert else None,
            )
            k8s_kwargs = {k.replace("k8s_", ""): v for k, v in vars(args).items() if v is not None and "k8s_" in k}

            output: dict[str, Any] = {}
            if args.output_type == "batch":
                output = {
                    "output_s3_bucket": args.output_s3_bucket,
                    "output_s3_folder": args.output_s3_folder,
                }
            elif args.output_type == "streaming":
                output = {
                    "output_kafka_topic": args.output_kafka_topic,
                    "output_kafka_cluster_connection_string": args.output_kafka_cluster_connection_string,
                }
            elif args.output_type == "stream_to_batch":
                output = {
                    "output_s3_bucket": args.output_s3_bucket,
                    "output_s3_folder": args.output_s3_folder,
                    "buffer_size": args.buffer_size,
                }
            else:
                raise ValueError(f"Invalid output type: {args.output_type}")

            # Create the state manager
            state: dict[str, Any] = {}
            if args.state_type == "none":
                state = {}
            elif args.state_type == "redis":
                state = {
                    "redis_host": args.redis_host,
                    "redis_port": args.redis_port,
                    "redis_db": args.redis_db,
                }
            elif args.state_type == "postgres":
                state = {
                    "postgres_host": args.postgres_host,
                    "postgres_port": args.postgres_port,
                    "postgres_user": args.postgres_user,
                    "postgres_password": args.postgres_password,
                    "postgres_database": args.postgres_database,
                    "postgres_table": args.postgres_table,
                }
            elif args.state_type == "dynamodb":
                state = {
                    "dyanmodb_table_name": args.dynamodb_table_name,
                    "dyanmodb_region_name": args.dynamodb_region_name,
                }
            elif args.state_type == "prometheus":
                state = {
                    "gateway": args.prometheus_gateway,
                }
            else:
                raise ValueError(f"Invalid state type: {args.state_type}")

            command = [
                "genius",
                self.discovered_spout.name,
                "rise",
                args.output_type,
                args.state_type,
                args.method_name,
            ] + [y for x in [[f"--{k}", str(v)] for k, v in ({**output, **state}).items()] for y in x]

            resource.create(command=command, **k8s_kwargs)
