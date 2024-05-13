# 🧠 Geniusrise
# Copyright (C) 2023  geniusrise.ai
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import json
import logging
import tempfile
import uuid
from typing import Optional

import emoji  # type: ignore
from rich_argparse import RichHelpFormatter

from geniusrise.cli.discover import DiscoveredSpout
from geniusrise.core import Spout
from geniusrise.runners.k8s import CronJob, Deployment, Job, Service
from geniusrise.utils.parse_function_args import parse_args_kwargs
from geniusrise.runners.openstack import OpenStackInstanceRunner, OpenStackAutoscaleRunner
from geniusrise.runners.acecloud import AceCloudAutoscaleRunner, AceCloudInstanceRunner


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
        create_parser.add_argument("output_type", choices=["batch", "streaming"], help="Choose the type of output data: batch or streaming.", default="batch")
        create_parser.add_argument("state_type", choices=["none", "redis", "postgres", "dynamodb"], help="Select the type of state manager: none, redis, postgres, or dynamodb.", default="none")
        create_parser.add_argument("--buffer_size", help="Specify the size of the buffer.", default=100, type=int)
        create_parser.add_argument("--id", help="A unique identifier for the task", default=str(uuid.uuid4()), type=str)
        # output
        create_parser.add_argument("--output_folder", help="Specify the directory where output files should be stored temporarily.", default=tempfile.mkdtemp(), type=str)
        create_parser.add_argument("--output_kafka_topic", help="Kafka output topic for streaming spouts.", default="test", type=str)
        create_parser.add_argument("--output_kafka_cluster_connection_string", help="Kafka connection string for streaming spouts.", default="localhost:9094", type=str)
        create_parser.add_argument("--output_s3_bucket", help="Provide the name of the S3 bucket for output storage.", default=None, type=str)
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
        # function
        create_parser.add_argument("method_name", help="The name of the method to execute on the spout.", type=str)
        create_parser.add_argument("--args", nargs=argparse.REMAINDER, help="Additional keyword arguments to pass to the spout.")

        deploy_parser = subparsers.add_parser("deploy", help="Run a spout remotely.", formatter_class=RichHelpFormatter)
        deploy_parser.add_argument("output_type", choices=["batch", "streaming"], help="Choose the type of output data: batch or streaming.", default="batch")
        deploy_parser.add_argument("state_type", choices=["none", "redis", "postgres", "dynamodb"], help="Select the type of state manager: none, redis, postgres, or dynamodb.", default="none")
        deploy_parser.add_argument("deployment_type", choices=["k8s", "openstack", "acecloud"], help="Choose the type of deployment.", default="k8s")
        deploy_parser.add_argument("--id", help="A unique identifier for the task", default=None, type=str)
        # output
        deploy_parser.add_argument("--buffer_size", help="Specify the size of the buffer.", default=100, type=int)
        deploy_parser.add_argument("--output_folder", help="Specify the directory where output files should be stored temporarily.", default="/tmp", type=str)
        deploy_parser.add_argument("--output_kafka_topic", help="Kafka output topic for streaming spouts.", default="test", type=str)
        deploy_parser.add_argument("--output_kafka_cluster_connection_string", help="Kafka connection string for streaming spouts.", default="localhost:9094", type=str)
        deploy_parser.add_argument("--output_s3_bucket", help="Provide the name of the S3 bucket for output storage.", default=None, type=str)
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
        # deployment
        # kubernetes
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
        # openstack
        deploy_parser.add_argument("--openstack_kind", choices=["instance", "autoscale"], help="Choose the type of openstack resource.", default="job")
        deploy_parser.add_argument("--openstack_name", help="Name of the OpenStack instance.", type=str)
        deploy_parser.add_argument("--openstack_image", help="Image ID or name for the OpenStack instance.", type=str)
        deploy_parser.add_argument("--openstack_flavor", help="Flavor ID or name for the OpenStack instance.", type=str)
        deploy_parser.add_argument("--openstack_key_name", help="Key pair name for the OpenStack instance.", type=str)
        deploy_parser.add_argument("--openstack_network", help="Network ID or name for the OpenStack instance.", type=str)
        deploy_parser.add_argument("--openstack_block_storage_size", help="Size of the block storage in GB for the OpenStack instance.", type=int)
        deploy_parser.add_argument("--openstack_open_ports", help="Comma-separated list of ports to open for the OpenStack instance.", type=str)
        deploy_parser.add_argument("--openstack_allocate_ip", help="Whether to allocate a floating IP for the OpenStack instance.", action="store_true")
        deploy_parser.add_argument("--openstack_auth_url", help="Authentication URL for OpenStack.", type=str, required=True)
        deploy_parser.add_argument("--openstack_username", help="OpenStack username.", type=str, required=True)
        deploy_parser.add_argument("--openstack_password", help="OpenStack password.", type=str, required=True)
        deploy_parser.add_argument("--openstack_project_name", help="OpenStack project name.", type=str, required=True)
        deploy_parser.add_argument("--openstack_min_instances", help="Minimum number of instances for OpenStack autoscaling.", type=int, default=1)
        deploy_parser.add_argument("--openstack_max_instances", help="Maximum number of instances for OpenStack autoscaling.", type=int, default=5)
        deploy_parser.add_argument("--openstack_desired_instances", help="Desired number of instances for OpenStack autoscaling.", type=int, default=2)
        deploy_parser.add_argument("--openstack_protocol", help="Load balancer protocol (HTTP or HTTPS) for OpenStack autoscaling.", type=str, default="HTTP")
        deploy_parser.add_argument("--openstack_scale_up_threshold", help="Threshold for triggering scale-up action in OpenStack autoscaling.", type=int, default=80)
        deploy_parser.add_argument("--openstack_scale_up_adjustment", help="Number of instances to add during scale-up in OpenStack autoscaling.", type=int, default=1)
        deploy_parser.add_argument("--openstack_scale_down_threshold", help="Threshold for triggering scale-down action in OpenStack autoscaling.", type=int, default=20)
        deploy_parser.add_argument("--openstack_scale_down_adjustment", help="Number of instances to remove during scale-down in OpenStack autoscaling.", type=int, default=-1)
        deploy_parser.add_argument("--openstack_alarm_period", help="Period for alarms (in seconds) in OpenStack autoscaling.", type=int, default=60)
        deploy_parser.add_argument("--openstack_alarm_evaluation_periods", help="Number of periods to evaluate alarms in OpenStack autoscaling.", type=int, default=1)
        # acecloud
        deploy_parser.add_argument("--acecloud_kind", choices=["instance", "autoscale"], help="Choose the type of acecloud resource.", default="job")
        deploy_parser.add_argument("--acecloud_name", help="Name of the AceCloud instance.", type=str)
        deploy_parser.add_argument("--acecloud_image", help="Image ID or name for the AceCloud instance.", type=str)
        deploy_parser.add_argument("--acecloud_flavor", help="Flavor ID or name for the AceCloud instance.", type=str)
        deploy_parser.add_argument("--acecloud_key_name", help="Key pair name for the AceCloud instance.", type=str)
        deploy_parser.add_argument("--acecloud_network", help="Network ID or name for the AceCloud instance.", type=str)
        deploy_parser.add_argument("--acecloud_block_storage_size", help="Size of the block storage in GB for the AceCloud instance.", type=int)
        deploy_parser.add_argument("--acecloud_open_ports", help="Comma-separated list of ports to open for the AceCloud instance.", type=str)
        deploy_parser.add_argument("--acecloud_allocate_ip", help="Whether to allocate a floating IP for the AceCloud instance.", action="store_true")
        deploy_parser.add_argument("--acecloud_auth_url", help="Authentication URL for AceCloud.", type=str, required=True)
        deploy_parser.add_argument("--acecloud_username", help="AceCloud username.", type=str, required=True)
        deploy_parser.add_argument("--acecloud_password", help="AceCloud password.", type=str, required=True)
        deploy_parser.add_argument("--acecloud_project_name", help="AceCloud project name.", type=str, required=True)
        deploy_parser.add_argument("--acecloud_min_instances", help="Minimum number of instances for AceCloud autoscaling.", type=int, default=1)
        deploy_parser.add_argument("--acecloud_max_instances", help="Maximum number of instances for AceCloud autoscaling.", type=int, default=5)
        deploy_parser.add_argument("--acecloud_desired_instances", help="Desired number of instances for AceCloud autoscaling.", type=int, default=2)
        deploy_parser.add_argument("--acecloud_protocol", help="Load balancer protocol (HTTP or HTTPS) for AceCloud autoscaling.", type=str, default="HTTP")
        deploy_parser.add_argument("--acecloud_scale_up_threshold", help="Threshold for triggering scale-up action in AceCloud autoscaling.", type=int, default=80)
        deploy_parser.add_argument("--acecloud_scale_up_adjustment", help="Number of instances to add during scale-up in AceCloud autoscaling.", type=int, default=1)
        deploy_parser.add_argument("--acecloud_scale_down_threshold", help="Threshold for triggering scale-down action in AceCloud autoscaling.", type=int, default=20)
        deploy_parser.add_argument("--acecloud_scale_down_adjustment", help="Number of instances to remove during scale-down in AceCloud autoscaling.", type=int, default=-1)
        deploy_parser.add_argument("--acecloud_alarm_period", help="Period for alarms (in seconds) in AceCloud autoscaling.", type=int, default=60)
        deploy_parser.add_argument("--acecloud_alarm_evaluation_periods", help="Number of periods to evaluate alarms in AceCloud autoscaling.", type=int, default=1)

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
                    and "openstack_" not in k
                    and "acecloud_" not in k
                    and k
                    not in [
                        "output_type",
                        "state_type",
                        "args",
                        "method_name",
                        "deployment_type",
                    ]
                }
                other = args.args or []
                other_args, other_kwargs = parse_args_kwargs(other)
                self.spout = self.create_spout(args.output_type, args.state_type, **kwargs)

                # Pass the method_name from args to execute_spout
                result = self.execute_spout(self.spout, args.method_name, *other_args, **other_kwargs)
                self.log.info(emoji.emojize(f"Successfully executed the spout method: {args.method_name} :thumbs_up:"))
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

    def create_spout(self, output_type: str, state_type: str, id: Optional[str], **kwargs) -> Spout:
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
                    Deployment
                    Kubernetes
                    - k8s_kind (str): Kind of kubernetes resource to be deployed as, choices are "deployment", "service", "job", "cron_job"
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
                    Openstack instance
                    - openstack_kind (str): Type of openstack resource: instance or autoscale.
                    - openstack_name (str): Name of the OpenStack instance.
                    - openstack_image (str): Image ID or name for the OpenStack instance.
                    - openstack_flavor (str): Flavor ID or name for the OpenStack instance.
                    - openstack_key_name (str): Key pair name for the OpenStack instance.
                    - openstack_network (str): Network ID or name for the OpenStack instance.
                    - openstack_block_storage_size (int): Size of the block storage in GB for the OpenStack instance.
                    - openstack_open_ports (str): Comma-separated list of ports to open for the OpenStack instance.
                    - openstack_allocate_ip (bool): Whether to allocate a floating IP for the OpenStack instance.
                    - openstack_auth_url (str): Authentication URL for OpenStack.
                    - openstack_username (str): OpenStack username.
                    - openstack_password (str): OpenStack password.
                    - openstack_project_name (str): OpenStack project name.
                    Openstack autoscale (heat + orchestration)
                    - openstack_kind (str): Type of openstack resource: instance or autoscale.
                    - openstack_name (str): Name of the OpenStack autoscaled deployment.
                    - openstack_image (str): Image ID or name for the OpenStack instances.
                    - openstack_flavor (str): Flavor ID or name for the OpenStack instances.
                    - openstack_key_name (str): Key pair name for the OpenStack instances.
                    - openstack_network (str): Network ID or name for the OpenStack instances.
                    - openstack_min_instances (int): Minimum number of instances for OpenStack autoscaling.
                    - openstack_max_instances (int): Maximum number of instances for OpenStack autoscaling.
                    - openstack_desired_instances (int): Desired number of instances for OpenStack autoscaling.
                    - openstack_protocol (str): Load balancer protocol (HTTP or HTTPS) for OpenStack autoscaling.
                    - openstack_scale_up_threshold (int): Threshold for triggering scale-up action in OpenStack autoscaling.
                    - openstack_scale_up_adjustment (int): Number of instances to add during scale-up in OpenStack autoscaling.
                    - openstack_scale_down_threshold (int): Threshold for triggering scale-down action in OpenStack autoscaling.
                    - openstack_scale_down_adjustment (int): Number of instances to remove during scale-down in OpenStack autoscaling.
                    - openstack_alarm_period (int): Period for alarms (in seconds) in OpenStack autoscaling.
                    - openstack_alarm_evaluation_periods (int): Number of periods to evaluate alarms in OpenStack autoscaling.
                    - openstack_auth_url (str): Authentication URL for OpenStack.
                    - openstack_username (str): OpenStack username.
                    - openstack_password (str): OpenStack password.
                    - openstack_project_name (str): OpenStack project name.
                    AceCloud instance
                    - acecloud_kind (str): Type of acecloud resource: instance or autoscale.
                    - acecloud_name (str): Name of the AceCloud instance.
                    - acecloud_image (str): Image ID or name for the AceCloud instance.
                    - acecloud_flavor (str): Flavor ID or name for the AceCloud instance.
                    - acecloud_key_name (str): Key pair name for the AceCloud instance.
                    - acecloud_network (str): Network ID or name for the AceCloud instance.
                    - acecloud_block_storage_size (int): Size of the block storage in GB for the AceCloud instance.
                    - acecloud_open_ports (str): Comma-separated list of ports to open for the AceCloud instance.
                    - acecloud_allocate_ip (bool): Whether to allocate a floating IP for the AceCloud instance.
                    - acecloud_auth_url (str): Authentication URL for AceCloud.
                    - acecloud_username (str): AceCloud username.
                    - acecloud_password (str): AceCloud password.
                    - acecloud_project_name (str): AceCloud project name.
                    AceCloud autoscale (heat + orchestration)
                    - acecloud_kind (str): Type of acecloud resource: instance or autoscale.
                    - acecloud_name (str): Name of the AceCloud autoscaled deployment.
                    - acecloud_image (str): Image ID or name for the AceCloud instances.
                    - acecloud_flavor (str): Flavor ID or name for the AceCloud instances.
                    - acecloud_key_name (str): Key pair name for the AceCloud instances.
                    - acecloud_network (str): Network ID or name for the AceCloud instances.
                    - acecloud_min_instances (int): Minimum number of instances for AceCloud autoscaling.
                    - acecloud_max_instances (int): Maximum number of instances for AceCloud autoscaling.
                    - acecloud_desired_instances (int): Desired number of instances for AceCloud autoscaling.
                    - acecloud_protocol (str): Load balancer protocol (HTTP or HTTPS) for AceCloud autoscaling.
                    - acecloud_scale_up_threshold (int): Threshold for triggering scale-up action in AceCloud autoscaling.
                    - acecloud_scale_up_adjustment (int): Number of instances to add during scale-up in AceCloud autoscaling.
                    - acecloud_scale_down_threshold (int): Threshold for triggering scale-down action in AceCloud autoscaling.
                    - acecloud_scale_down_adjustment (int): Number of instances to remove during scale-down in AceCloud autoscaling.
                    - acecloud_alarm_period (int): Period for alarms (in seconds) in AceCloud autoscaling.
                    - acecloud_alarm_evaluation_periods (int): Number of periods to evaluate alarms in AceCloud autoscaling.
                    - acecloud_auth_url (str): Authentication URL for AceCloud.
                    - acecloud_username (str): AceCloud username.
                    - acecloud_password (str): AceCloud password.
                    - acecloud_project_name (str): AceCloud project name.
                ```
        """
        # Construct the command to run geniusrise on remote machine / container

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
        else:
            raise ValueError(f"Invalid output type: {args.output_type}")

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
        else:
            raise ValueError(f"Invalid state type: {args.state_type}")

        other = args.args or []

        command = (
            [
                "genius",
                self.discovered_spout.name,
                "rise",
                args.output_type,
                args.state_type,
            ]
            + ["--id", args.id if args.id else str(uuid.uuid4())]
            + [y for x in [[f"--{k}", str(v)] for k, v in ({**output, **state}).items()] for y in x]
            + [args.method_name]
            + other
        )

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
            resource.create(command=command, **k8s_kwargs)
            return resource

        elif args.deployment_type == "openstack" and args.openstack_kind == "instance":
            openstack_instance_kwargs = {
                "name": args.openstack_name,
                "image": args.openstack_image,
                "flavor": args.openstack_flavor,
                "key_name": args.openstack_key_name,
                "network": args.openstack_network,
                "block_storage_size": args.openstack_block_storage_size,
                "open_ports": args.openstack_open_ports,
                "allocate_ip": args.openstack_allocate_ip,
                "user_data": command,
            }

            openstack_instance_runner = OpenStackInstanceRunner()
            openstack_instance_runner.connect(
                auth_url=args.openstack_auth_url,
                username=args.openstack_username,
                password=args.openstack_password,
                project_name=args.openstack_project_name,
            )

            instance = openstack_instance_runner.create(**openstack_instance_kwargs)
            return instance

        elif args.deployment_type == "openstack" and args.openstack_kind == "autoscale":
            openstack_autoscale_kwargs = {
                "name": args.openstack_name,
                "image": args.openstack_image,
                "flavor": args.openstack_flavor,
                "key_name": args.openstack_key_name,
                "network": args.openstack_network,
                "min_instances": args.openstack_min_instances,
                "max_instances": args.openstack_max_instances,
                "desired_instances": args.openstack_desired_instances,
                "protocol": args.openstack_protocol,
                "scale_up_threshold": args.openstack_scale_up_threshold,
                "scale_up_adjustment": args.openstack_scale_up_adjustment,
                "scale_down_threshold": args.openstack_scale_down_threshold,
                "scale_down_adjustment": args.openstack_scale_down_adjustment,
                "alarm_period": args.openstack_alarm_period,
                "alarm_evaluation_periods": args.openstack_alarm_evaluation_periods,
                "user_data": command,
            }

            openstack_autoscale_runner = OpenStackAutoscaleRunner()
            openstack_autoscale_runner.connect(
                auth_url=args.openstack_auth_url,
                username=args.openstack_username,
                password=args.openstack_password,
                project_name=args.openstack_project_name,
            )

            openstack_autoscale_runner.create(**openstack_autoscale_kwargs)
            return openstack_autoscale_runner

        elif args.deployment_type == "acecloud" and args.acecloud_kind == "instance":
            acecloud_instance_kwargs = {
                "name": args.acecloud_name,
                "image": args.acecloud_image,
                "flavor": args.acecloud_flavor,
                "key_name": args.acecloud_key_name,
                "network": args.acecloud_network,
                "block_storage_size": args.acecloud_block_storage_size,
                "open_ports": args.acecloud_open_ports,
                "allocate_ip": args.acecloud_allocate_ip,
                "user_data": command,
            }

            acecloud_instance_runner = AceCloudInstanceRunner()
            acecloud_instance_runner.connect(
                auth_url=args.acecloud_auth_url,
                username=args.acecloud_username,
                password=args.acecloud_password,
                project_name=args.acecloud_project_name,
            )

            instance = acecloud_instance_runner.create(**acecloud_instance_kwargs)
            return instance

        elif args.deployment_type == "acecloud" and args.acecloud_kind == "autoscale":
            acecloud_autoscale_kwargs = {
                "name": args.acecloud_name,
                "image": args.acecloud_image,
                "flavor": args.acecloud_flavor,
                "key_name": args.acecloud_key_name,
                "network": args.acecloud_network,
                "min_instances": args.acecloud_min_instances,
                "max_instances": args.acecloud_max_instances,
                "desired_instances": args.acecloud_desired_instances,
                "protocol": args.acecloud_protocol,
                "scale_up_threshold": args.acecloud_scale_up_threshold,
                "scale_up_adjustment": args.acecloud_scale_up_adjustment,
                "scale_down_threshold": args.acecloud_scale_down_threshold,
                "scale_down_adjustment": args.acecloud_scale_down_adjustment,
                "alarm_period": args.acecloud_alarm_period,
                "alarm_evaluation_periods": args.acecloud_alarm_evaluation_periods,
                "user_data": command,
            }

            acecloud_autoscale_runner = AceCloudAutoscaleRunner()
            acecloud_autoscale_runner.connect(
                auth_url=args.acecloud_auth_url,
                username=args.acecloud_username,
                password=args.acecloud_password,
                project_name=args.acecloud_project_name,
            )

            acecloud_autoscale_runner.create(**acecloud_autoscale_kwargs)
            return acecloud_autoscale_runner
