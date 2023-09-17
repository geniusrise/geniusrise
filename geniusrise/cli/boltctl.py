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

import emoji  # type: ignore
from rich_argparse import RichHelpFormatter

from geniusrise.cli.discover import DiscoveredBolt
from geniusrise.core import Bolt
from geniusrise.runners.k8s import Deployment, Service, Job, CronJob


class BoltCtl:
    """
    Class for managing bolts end-to-end from the command line.
    """

    def __init__(self, discovered_bolt: DiscoveredBolt):
        """
        Initialize BoltCtl with a DiscoveredBolt object.

        Args:
            discovered_bolt (DiscoveredBolt): DiscoveredBolt object used to create and manage bolts.
        """
        self.discovered_bolt = discovered_bolt
        self.bolt = None
        self.log = logging.getLogger(self.__class__.__name__)

    def create_parser(self, parser):
        """
        Add arguments to the command-line parser for managing the bolt.

        Args:
            parser (argparse.ArgumentParser): Command-line parser.
        """
        subparsers = parser.add_subparsers(dest="command")

        # fmt: off
        # Create subparser for 'run' command
        run_parser = subparsers.add_parser("rise", help="Run a bolt locally.", formatter_class=RichHelpFormatter)
        run_parser.add_argument("input_type", choices=["batch", "streaming", "batch_to_stream", "stream_to_batch"], help="Choose the type of input data: batch or streaming.", default="batch")
        run_parser.add_argument("output_type", choices=["batch", "streaming", "stream_to_batch"], help="Choose the type of output data: batch or streaming.", default="batch")
        run_parser.add_argument("state_type", choices=["none", "redis", "postgres", "dynamodb", "prometheus"], help="Select the type of state manager: none, redis, postgres, or dynamodb.", default="none")
        # input
        run_parser.add_argument("--buffer_size", help="Specify the size of the buffer.", default=100, type=int)
        run_parser.add_argument("--input_folder", help="Specify the directory where output files should be stored temporarily.", default=tempfile.mkdtemp(), type=str)
        run_parser.add_argument("--input_kafka_topic", help="Kafka output topic for streaming spouts.", default="test", type=str)
        run_parser.add_argument("--input_kafka_cluster_connection_string", help="Kafka connection string for streaming spouts.", default="localhost:9094", type=str)
        run_parser.add_argument("--input_kafka_consumer_group_id", help="Kafka consumer group id to use.", default="geniusrise", type=str)
        run_parser.add_argument("--input_s3_bucket", help="Provide the name of the S3 bucket for output storage.", default="geniusrise-test", type=str)
        run_parser.add_argument("--input_s3_folder", help="Indicate the S3 folder for output storage.", default="geniusrise", type=str)
        # output
        run_parser.add_argument("--output_folder", help="Specify the directory where output files should be stored temporarily.", default=tempfile.mkdtemp(), type=str)
        run_parser.add_argument("--output_kafka_topic", help="Kafka output topic for streaming spouts.", default="test", type=str)
        run_parser.add_argument("--output_kafka_cluster_connection_string", help="Kafka connection string for streaming spouts.", default="localhost:9094", type=str)
        run_parser.add_argument("--output_s3_bucket", help="Provide the name of the S3 bucket for output storage.", default="geniusrise-test", type=str)
        run_parser.add_argument("--output_s3_folder", help="Indicate the S3 folder for output storage.", default="geniusrise", type=str)
        # state
        run_parser.add_argument("--redis_host", help="Enter the host address for the Redis server.", default="localhost", type=str)
        run_parser.add_argument("--redis_port", help="Enter the port number for the Redis server.", default=6379, type=int)
        run_parser.add_argument("--redis_db", help="Specify the Redis database to be used.", default=0, type=int)
        run_parser.add_argument("--postgres_host", help="Enter the host address for the PostgreSQL server.", default="localhost", type=str)
        run_parser.add_argument("--postgres_port", help="Enter the port number for the PostgreSQL server.", default=5432, type=int)
        run_parser.add_argument("--postgres_user", help="Provide the username for the PostgreSQL server.", default="postgres", type=str)
        run_parser.add_argument("--postgres_password", help="Provide the password for the PostgreSQL server.", default="password", type=str)
        run_parser.add_argument("--postgres_database", help="Specify the PostgreSQL database to be used.", default="mydatabase", type=str)
        run_parser.add_argument("--postgres_table", help="Specify the PostgreSQL table to be used.", default="mytable", type=str)
        run_parser.add_argument("--dynamodb_table_name", help="Provide the name of the DynamoDB table.", default="mytable", type=str)
        run_parser.add_argument("--dynamodb_region_name", help="Specify the AWS region for DynamoDB.", default="us-west-2", type=str)
        run_parser.add_argument("--prometheus_gateway", help="Specify the prometheus gateway URL.", default="localhost:9091", type=str)
        # function
        run_parser.add_argument("method_name", help="The name of the method to execute on the bolt.", type=str)
        run_parser.add_argument("--args", nargs=argparse.REMAINDER, help="Additional keyword arguments to pass to the bolt.")

        deploy_parser = subparsers.add_parser("deploy", help="Run a spout remotely.", formatter_class=RichHelpFormatter)
        deploy_parser.add_argument("output_type", choices=["batch", "streaming", "stream_to_batch"], help="Choose the type of output data: batch or streaming.", default="batch")
        deploy_parser.add_argument("state_type", choices=["none", "redis", "postgres", "dynamodb", "prometheus"], help="Select the type of state manager: none, redis, postgres, or dynamodb.", default="none")
        deploy_parser.add_argument("deployment_type", choices=["k8s"], help="Choose the type of deployment.", default="k8s")
        # input
        deploy_parser.add_argument("--buffer_size", help="Specify the size of the buffer.", default=100, type=int)
        deploy_parser.add_argument("--input_folder", help="Specify the directory where output files should be stored temporarily.", default="/tmp", type=str)
        deploy_parser.add_argument("--input_kafka_topic", help="Kafka output topic for streaming spouts.", default="test", type=str)
        deploy_parser.add_argument("--input_kafka_cluster_connection_string", help="Kafka connection string for streaming spouts.", default="localhost:9094", type=str)
        deploy_parser.add_argument("--input_kafka_consumer_group_id", help="Kafka consumer group id to use.", default="geniusrise", type=str)
        deploy_parser.add_argument("--input_s3_bucket", help="Provide the name of the S3 bucket for output storage.", default="geniusrise-test", type=str)
        deploy_parser.add_argument("--input_s3_folder", help="Indicate the S3 folder for output storage.", default="geniusrise", type=str)
        # output
        # deploy_parser.add_argument("--buffer_size", help="Specify the size of the buffer.", default=100, type=int)
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
        deploy_parser.add_argument("--k8s_env_vars", help="Environment variables as a JSON string.", type=str, default="{}")
        deploy_parser.add_argument("--k8s_cpu", help="CPU requirements.", type=str)
        deploy_parser.add_argument("--k8s_memory", help="Memory requirements.", type=str)
        deploy_parser.add_argument("--k8s_storage", help="Storage requirements.", type=str)
        deploy_parser.add_argument("--k8s_gpu", help="GPU requirements.", type=str)
        deploy_parser.add_argument("--k8s_cluster_name", help="Name of the Kubernetes cluster.", type=str)
        deploy_parser.add_argument("--k8s_context_name", help="Name of the kubeconfig context.", type=str)
        deploy_parser.add_argument("--k8s_namespace", help="Kubernetes namespace.", default="default", type=str)
        deploy_parser.add_argument("--k8s_labels", help="Labels for Kubernetes resources, as a JSON string.", type=str, default='{"created_by": "geniusrise"}')
        deploy_parser.add_argument("--k8s_annotations", help="Annotations for Kubernetes resources, as a JSON string.", type=str)
        deploy_parser.add_argument("--port", help="Port to run the spout on as a service.", type=int)
        deploy_parser.add_argument("--target_port", help="Port to expose the spout on as a service.", type=int)
        deploy_parser.add_argument("--schedule", help="Schedule to run the spout on as a cron job.", type=str)
        # function
        deploy_parser.add_argument("method_name", help="The name of the method to execute on the spout.", type=str)
        deploy_parser.add_argument("--args", nargs=argparse.REMAINDER, help="Additional keyword arguments to pass to the spout.")

        # Create subparser for 'help' command
        help_parser = subparsers.add_parser("help", help="Print help for the bolt.", formatter_class=RichHelpFormatter)
        help_parser.add_argument("method", help="The method to execute.")

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
                    and k not in ["input_type", "output_type", "state_type", "args", "method_name", "deployment_type"]
                }
                other = args.args or []
                other_args, other_kwargs = self.parse_args_kwargs(other)
                self.bolt = self.create_bolt(args.input_type, args.output_type, args.state_type, **kwargs)

                # Pass the method_name from args to execute_bolt
                result = self.execute_bolt(self.bolt, args.method_name, *other_args, **other_kwargs)
                self.log.info(emoji.emojize(f"Successfully executed the bolt method: {args.method_name} :thumbs_up:"))
                return result

            elif args.command == "deploy":
                self.deploy_bolt(args)

            elif args.command == "help":
                self.discovered_bolt.klass.print_help(self.discovered_bolt.klass)
        except ValueError as ve:
            self.log.exception(f"Value error: {ve}")
            raise
        except AttributeError as ae:
            self.log.exception(f"Attribute error: {ae}")
            raise
        except KeyError as ke:
            self.log.exception(f"Missing key: {ke}")
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
                return int(value)
            except ValueError:
                try:
                    return float(value)
                except ValueError:
                    try:
                        return json.loads(value)
                    except ValueError:
                        return value

        for item in args_list:
            if "=" in item:
                key, value = item.split("=", 1)
                kwargs[key] = convert(value)
            else:
                args.append(convert(item))

        return args, kwargs

    def create_bolt(self, input_type: str, output_type: str, state_type: str, **kwargs) -> Bolt:
        r"""
        Create a bolt of a specific type.

        Args:
            input_type (str): The type of input ("batch" or "streaming").
            output_type (str): The type of output ("batch" or "streaming").
            state_type (str): The type of state manager ("none", "redis", "postgres", or "dynamodb").
            **kwargs: Additional keyword arguments for initializing the bolt.
                ```
                Keyword Arguments:
                    Batch input:
                    - input_folder (str): The input folder argument.
                    - input_s3_bucket (str): The input bucket argument.
                    - input_s3_folder (str): The input S3 folder argument.
                    Batch outupt config:
                    - output_folder (str): The output folder argument.
                    - output_s3_bucket (str): The output bucket argument.
                    - output_s3_folder (str): The output S3 folder argument.
                    Streaming input:
                    - input_kafka_cluster_connection_string (str): The input Kafka servers argument.
                    - input_kafka_topic (str): The input kafka topic argument.
                    - input_kafka_consumer_group_id (str): The Kafka consumer group id.
                    Streaming output:
                    - output_kafka_cluster_connection_string (str): The output Kafka servers argument.
                    - output_kafka_topic (str): The output kafka topic argument.
                    Stream-to-Batch input:
                    - buffer_size (int): Number of messages to buffer.
                    - input_kafka_cluster_connection_string (str): The input Kafka servers argument.
                    - input_kafka_topic (str): The input kafka topic argument.
                    - input_kafka_consumer_group_id (str): The Kafka consumer group id.
                    Batch-to-Streaming input:
                    - buffer_size (int): Number of messages to buffer.
                    - input_folder (str): The input folder argument.
                    - input_s3_bucket (str): The input bucket argument.
                    - input_s3_folder (str): The input S3 folder argument.
                    Stream-to-Batch output:
                    - buffer_size (int): Number of messages to buffer.
                    - output_folder (str): The output folder argument.
                    - output_s3_bucket (str): The output bucket argument.
                    - output_s3_folder (str): The output S3 folder argument.
                    Redis state manager config:
                    - redis_host (str): The Redis host argument.
                    - redis_port (str): The Redis port argument.
                    - redis_db (str): The Redis database argument.
                    Postgres state manager config:
                    - postgres_host (str): The PostgreSQL host argument.
                    - postgres_port (str): The PostgreSQL port argument.
                    - postgres_user (str): The PostgreSQL user argument.
                    - postgres_password (str): The PostgreSQL password argument.
                    - postgres_database (str): The PostgreSQL database argument.
                    - postgres_table (str): The PostgreSQL table argument.
                    DynamoDB state manager config:
                    - dynamodb_table_name (str): The DynamoDB table name argument.
                    - dynamodb_region_name (str): The DynamoDB region name argument.
                    Prometheus state manager config:
                    - prometheus_gateway (str): The push gateway for Prometheus metrics.
                ```

        Returns:
            Bolt: The created bolt.
        """
        return Bolt.create(
            klass=self.discovered_bolt.klass,
            input_type=input_type,
            output_type=output_type,
            state_type=state_type,
            **kwargs,
        )

    def execute_bolt(self, bolt: Bolt, method_name: str, *args, **kwargs):
        """
        Execute a method of a bolt.

        Args:
            bolt (Bolt): The bolt to execute.
            method_name (str): The name of the method to execute.
            *args: Positional arguments to pass to the method.
            **kwargs: Keyword arguments to pass to the method.

        Returns:
            Any: The result of the method.
        """
        return bolt.__call__(method_name, *args, **kwargs)

    def deploy_bolt(self, args):
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
            k8s_kwargs = {k: v for k, v in vars(args).items() if v is not None and "k8s_" in k}

            # create the command to run remotely
            spout_kwargs = {
                k: v
                for k, v in vars(args).items()
                if v is not None
                and "k8s_" not in k
                and k not in ["input_type", "output_type", "state_type", "args", "method_name", "deployment_type"]
            }
            command = [
                "genius",
                self.__class__.__name__,
                "rise",
                "input_type",
                args.input_type,
                "output_type",
                args.output_type,
                "state_type",
                args.state_type,
                "method_name",
                args.method_name,
            ] + [y for x in [[f"--{k}", v] for k, v in spout_kwargs.items()] for y in x]

            print(command)
            print(k8s_kwargs)

            # resource.create(command=command, **k8s_kwargs)
