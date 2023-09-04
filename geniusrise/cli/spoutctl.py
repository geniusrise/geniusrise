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

import emoji  # type: ignore
from rich_argparse import RichHelpFormatter

from geniusrise.cli.discover import DiscoveredSpout
from geniusrise.core import Spout


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
        create_parser = subparsers.add_parser("rise", help="Run a spout locally.", formatter_class=RichHelpFormatter)
        create_parser.add_argument(
            "output_type",
            choices=["batch", "streaming", "stream_to_batch"],
            help="Choose the type of output data: batch or streaming.",
            default="batch",
        )
        create_parser.add_argument(
            "state_type",
            choices=["in_memory", "redis", "postgres", "dynamodb", "prometheus"],
            help="Select the type of state manager: in_memory, redis, postgres, or dynamodb.",
            default="in_memory",
        )
        create_parser.add_argument(
            "--buffer_size",
            help="Specify the size of the buffer.",
            default=100,
            type=int,
        )
        create_parser.add_argument(
            "--output_folder",
            help="Specify the directory where output files should be stored temporarily.",
            default="/tmp",
            type=str,
        )
        create_parser.add_argument(
            "--output_kafka_topic",
            help="Kafka output topic for streaming spouts.",
            default="test",
            type=str,
        )
        create_parser.add_argument(
            "--output_kafka_cluster_connection_string",
            help="Kafka connection string for streaming spouts.",
            default="localhost:9094",
            type=str,
        )
        create_parser.add_argument(
            "--output_s3_bucket",
            help="Provide the name of the S3 bucket for output storage.",
            default="my-bucket",
            type=str,
        )
        create_parser.add_argument(
            "--output_s3_folder",
            help="Indicate the S3 folder for output storage.",
            default="my-s3-folder",
            type=str,
        )
        create_parser.add_argument(
            "--redis_host",
            help="Enter the host address for the Redis server.",
            default="localhost",
            type=str,
        )
        create_parser.add_argument(
            "--redis_port",
            help="Enter the port number for the Redis server.",
            default=6379,
            type=int,
        )
        create_parser.add_argument(
            "--redis_db",
            help="Specify the Redis database to be used.",
            default=0,
            type=int,
        )
        create_parser.add_argument(
            "--postgres_host",
            help="Enter the host address for the PostgreSQL server.",
            default="localhost",
            type=str,
        )
        create_parser.add_argument(
            "--postgres_port",
            help="Enter the port number for the PostgreSQL server.",
            default=5432,
            type=int,
        )
        create_parser.add_argument(
            "--postgres_user",
            help="Provide the username for the PostgreSQL server.",
            default="postgres",
            type=str,
        )
        create_parser.add_argument(
            "--postgres_password",
            help="Provide the password for the PostgreSQL server.",
            default="password",
            type=str,
        )
        create_parser.add_argument(
            "--postgres_database",
            help="Specify the PostgreSQL database to be used.",
            default="mydatabase",
            type=str,
        )
        create_parser.add_argument(
            "--postgres_table",
            help="Specify the PostgreSQL table to be used.",
            default="mytable",
            type=str,
        )
        create_parser.add_argument(
            "--dynamodb_table_name",
            help="Provide the name of the DynamoDB table.",
            default="mytable",
            type=str,
        )
        create_parser.add_argument(
            "--dynamodb_region_name",
            help="Specify the AWS region for DynamoDB.",
            default="us-west-2",
            type=str,
        )
        create_parser.add_argument(
            "--prometheus_gateway",
            help="Specify the prometheus gateway URL.",
            default="localhost:9091",
            type=str,
        )
        create_parser.add_argument(
            "method_name",
            help="The name of the method to execute on the spout.",
            type=str,
        )
        create_parser.add_argument(
            "--args",
            nargs=argparse.REMAINDER,
            help="Additional keyword arguments to pass to the spout.",
        )

        # Create subparser for 'help' command
        execute_parser = subparsers.add_parser(
            "help", help="Print help for the spout.", formatter_class=RichHelpFormatter
        )
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
            if args.command == "rise":
                kwargs = {
                    k: v
                    for k, v in vars(args).items()
                    if v is not None and k not in ["output_type", "state_type", "args", "method_name"]
                }
                other = args.args or []
                other_args, other_kwargs = self.parse_args_kwargs(other)
                self.spout = self.create_spout(args.output_type, args.state_type, **kwargs)

                # Pass the method_name from args to execute_spout
                result = self.execute_spout(self.spout, args.method_name, *other_args, **other_kwargs)
                return result

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

    def create_spout(self, output_type: str, state_type: str, **kwargs) -> Spout:
        r"""
        Create a spout of a specific type.

        Args:
            output_type (str): The type of output ("batch" or "streaming").
            state_type (str): The type of state manager ("in_memory", "redis", "postgres", or "dynamodb").
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
