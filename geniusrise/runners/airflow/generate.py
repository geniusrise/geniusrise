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

import json
from argparse import ArgumentParser, Namespace
from jinja2 import Template
from airflow.models import DagBag
import requests
import os
import logging


class AirflowRunner:
    r"""
    AirflowRunner is a utility for managing and orchestrating Airflow DAGs. It is designed
    to provide a command-line interface (CLI) for creating, describing, showing, deleting,
    and getting the status of Airflow DAGs.

    This class uses the Airflow models to interact with DAGs and DockerOperator to
    run tasks in Docker containers. It is aimed to simplify the deployment and management
    of Airflow tasks, providing a straightforward way to deploy DAGs with Docker tasks
    from the command line.

    CLI Usage:
        genius airflow [sub-command] [options]

    Sub-commands:
        - create: Create a new DAG with the given parameters and Docker task.
                `genius airflow create [options]`
        - describe: Describe a specific DAG by its ID.
                  `genius airflow describe --dag_id example_dag`
        - show: Show all available DAGs in the Airflow environment.
              `genius airflow show`
        - delete: Delete a specific DAG by its ID.
                `genius airflow delete --dag_id example_dag`
        - status: Get the status of a specific DAG by its ID.
                `genius airflow status --dag_id example_dag --airflow_api_base_url http://localhost:8080/api/v1`

    Each sub-command supports various options to specify the details of the DAG or the
    Docker task, such as the schedule interval, start date, owner, image, command, and
    more.

    Example:
        Creating a new DAG:
        ```bash
        genius airflow create --dag_directory ~/airflow/dags \
                              --dag_id my_dag \
                              --image python:3.10-slim \
                              --command "echo Hello World"
        ```

    Attributes:
        dag_directory (str): Directory where DAGs are stored. This path should be known to Airflow.

    Methods:
        - create: Method to create a new DAG based on the provided parameters and template.
        - describe: Method to describe a specific DAG by its ID, showing details like tasks and schedule.
        - show: Method to list all available DAGs.
        - delete: Method to remove a specific DAG by its ID from the directory.
        - status: Method to fetch and display the status of a specific DAG using Airflow's REST API.

    Note:
        - Ensure that the Airflow environment is properly configured and the specified DAG directory is correct.
        - Make sure that the Airflow REST API base URL is accessible if using the status command.
    """

    def __init__(self):
        """
        Initialize the AirflowRunner class for managing Airflow DAGs.
        """
        self.log = logging.getLogger(self.__class__.__name__)

        self.dag_directory = "."

    def create_parser(self, parser: ArgumentParser) -> ArgumentParser:
        subparsers = parser.add_subparsers(dest="airflow_command", help="Airflow commands")

        # Parser for create command
        # fmt: off
        create_parser = subparsers.add_parser("create", help="Create a new DAG.")
        create_parser.add_argument("dag_directory", help="The directory where DAGs are stored", type=str)
        create_parser.add_argument("--dag_id", help="The ID of the DAG", type=str)
        create_parser.add_argument("--owner", help="Owner of the DAG", type=str, default="airflow")
        create_parser.add_argument("--retries", help="Number of retries", type=int, default=1)
        create_parser.add_argument("--retry_delay_minutes", help="Retry delay in minutes", type=int, default=5)
        create_parser.add_argument("--description", help="Description of the DAG", type=str, default="DAG created with AirflowRunner")
        create_parser.add_argument("--schedule_interval", help="Schedule interval for DAG", type=str, default="None")
        create_parser.add_argument("--start_date", help="Start date for DAG (e.g., days_ago(2))", type=str, default="days_ago(1)")
        create_parser.add_argument("--catchup", help="Catchup for DAG", type=bool, default=False)
        create_parser.add_argument("--task_id", help="Task ID for DockerOperator", type=str, default="docker_task")
        create_parser.add_argument("--image", help="Docker image to use", type=str, default="python:3.10-slim")
        create_parser.add_argument("--api_version", help="API version of Docker", type=str, default="auto")
        create_parser.add_argument("--command", help="Command to run in the Docker container", type=str, default="echo Hello World")
        create_parser.add_argument("--container_name", help="Container name", type=str, default="")
        create_parser.add_argument("--cpus", help="Number of CPUs", type=float, default=0.1)
        create_parser.add_argument("--docker_url", help="Docker URL", type=str, default="unix://var/run/docker.sock")
        create_parser.add_argument("--environment", help="Environment variables (json)", type=json.loads, default={})
        create_parser.add_argument("--private_environment", help="Private environment variables (json)", type=json.loads, default={})
        create_parser.add_argument("--network_mode", help="Network mode for Docker", type=str, default="bridge")
        create_parser.add_argument("--tls_hostname", help="TLS hostname for Docker", type=str, default="")
        create_parser.add_argument("--tls_ca_cert", help="TLS CA certificate", type=str, default="")
        create_parser.add_argument("--tls_client_cert", help="TLS client certificate", type=str, default="")
        create_parser.add_argument("--tls_client_key", help="TLS client key", type=str, default="")
        create_parser.add_argument("--tls_ssl_version", help="TLS SSL version", type=str, default="")
        create_parser.add_argument("--tls_assert_hostname", help="TLS assert hostname", type=str, default="")
        create_parser.add_argument("--tls_verify", help="TLS verify", type=bool, default=True)
        create_parser.add_argument("--mem_limit", help="Memory limit (e.g., 512m)", type=str, default="")
        create_parser.add_argument("--user", help="User to run inside the container", type=str, default="")
        create_parser.add_argument("--ports", help="Ports to bind (json list of ints)", type=json.loads, default=[])
        create_parser.add_argument("--volumes", help="Volumes to bind (json list of strings)", type=json.loads, default=[])
        create_parser.add_argument("--working_dir", help="Working directory inside the container", type=str, default="")
        create_parser.add_argument("--xcom_push", help="Push to XCom", type=bool, default=False)
        create_parser.add_argument("--xcom_all", help="Push all the stdout or just the last line", type=bool, default=False)
        create_parser.add_argument("--auto_remove", help="Auto remove the container when finished", type=bool, default=True)
        create_parser.add_argument("--shm_size", help="Size of /dev/shm", type=str, default="")
        create_parser.add_argument("--tty", help="Allocate pseudo-TTY to the container", type=bool, default=False)
        create_parser.add_argument("--privileged", help="Give extended privileges to this container", type=bool, default=False)
        create_parser.add_argument("--cap_add", help="Add Linux capabilities (json list of strings)", type=json.loads, default=[])
        create_parser.add_argument("--extra_hosts", help="Add hostname mappings (json dictionary)", type=json.loads, default={})
        create_parser.add_argument("--tmp_dir", help="Temporary directory that is mounted into the container", type=str, default="")
        create_parser.add_argument("--host_tmp_dir", help="Host temporary directory to mount", type=str, default="")
        create_parser.add_argument("--dns", help="Custom DNS servers (json list of strings)", type=json.loads, default=[])
        create_parser.add_argument("--dns_search", help="Custom DNS search domains (json list of strings)", type=json.loads, default=[])
        create_parser.add_argument("--mount_tmp_dir", help="Whether to mount a tmp dir", type=bool, default=True)
        create_parser.add_argument("--mount_volume", help="Whether to mount a volume", type=bool, default=False)

        # Parser for describe command
        describe_parser = subparsers.add_parser("describe", help="Describe a DAG.")
        describe_parser.add_argument("dag_id", help="The ID of the DAG to describe", type=str)

        # Parser for show command
        subparsers.add_parser("show", help="Show all DAGs.")

        # Parser for delete command
        delete_parser = subparsers.add_parser("delete", help="Delete a DAG.")
        delete_parser.add_argument("dag_id", help="The ID of the DAG to delete", type=str)

        # Parser for status command
        status_parser = subparsers.add_parser("status", help="Get the status of a DAG.")
        status_parser.add_argument("dag_id", help="The ID of the DAG to get the status of", type=str)
        status_parser.add_argument("--airflow_api_base_url", help="Base URL for Airflow's REST API", type=str, default="http://localhost:8080/api/v1")

        # fmt: on
        return parser

    def run(self, args: Namespace) -> None:
        """
        Execute the command based on the parsed arguments.
        """

        self.dag_directory = args.dag_directory

        if args.airflow_command == "create":
            self.create(args)
        elif args.airflow_command == "describe":
            self.describe(args.dag_id)
        elif args.airflow_command == "show":
            self.show()
        elif args.airflow_command == "delete":
            self.delete(args.dag_id)
        elif args.airflow_command == "status":
            self.status(args.dag_id, args.airflow_api_base_url)
        else:
            self.log.error(f"Unknown command: {args.airflow_command}")

    def create(self, args: Namespace) -> None:
        """
        Create a new DAG with a Docker task using the provided arguments.

        Args:
            args (Namespace): Namespace containing all the arguments needed for creating the DAG.
        """
        # Load the DAG template
        dir_path = os.path.dirname(os.path.realpath(__file__))
        dag_template_path = os.path.join(dir_path, "template.jinja")

        with open(dag_template_path, "r") as file:
            template_str = file.read()

        template = Template(template_str)

        # Prepare the arguments for the template
        rendered_content = template.render(
            dag_id=args.dag_id,
            owner=args.owner,
            retries=args.retries,
            retry_delay_minutes=args.retry_delay_minutes,
            description=args.description,
            schedule_interval=args.schedule_interval,
            start_date=args.start_date,
            catchup=args.catchup,
            task_id=args.task_id,
            image=args.image,
            api_version=args.api_version,
            command=args.command,
            container_name=args.container_name,
            cpus=args.cpus,
            docker_url=args.docker_url,
            environment=args.environment,
            private_environment=args.private_environment,
            network_mode=args.network_mode,
            tls_hostname=args.tls_hostname,
            tls_ca_cert=args.tls_ca_cert,
            tls_client_cert=args.tls_client_cert,
            tls_client_key=args.tls_client_key,
            tls_ssl_version=args.tls_ssl_version,
            tls_assert_hostname=args.tls_assert_hostname,
            tls_verify=args.tls_verify,
            mem_limit=args.mem_limit,
            user=args.user,
            ports=args.ports,
            volumes=args.volumes,
            working_dir=args.working_dir,
            xcom_push=args.xcom_push,
            xcom_all=args.xcom_all,
            auto_remove=args.auto_remove,
            shm_size=args.shm_size,
            tty=args.tty,
            privileged=args.privileged,
            cap_add=args.cap_add,
            extra_hosts=args.extra_hosts,
            tmp_dir=args.tmp_dir,
            host_tmp_dir=args.host_tmp_dir,
            dns=args.dns,
            dns_search=args.dns_search,
            mount_tmp_dir=args.mount_tmp_dir,
            mount_volume=args.mount_volume,
        )

        # Write the rendered DAG to the DAG directory
        dag_file_path = os.path.join(self.dag_directory, f"{args.dag_id}.py")
        with open(dag_file_path, "w") as dag_file:
            dag_file.write(rendered_content)

        self.log.info(f"🛠️ DAG {args.dag_id} created successfully. File: {dag_file_path}")

    def describe(self, dag_id: str) -> None:
        """
        Describe the details of a specific DAG.

        Args:
            dag_id (str): The ID of the DAG to describe.

        Returns:
            The DAG object if found, None otherwise.
        """
        dagbag = DagBag(dag_folder=self.dag_directory, include_examples=False)
        dag = dagbag.get_dag(dag_id)
        if dag:
            self.log.info(f"Details for DAG '{dag_id}':")
            self.log.info(f"  DAG ID: {dag.dag_id}")
            self.log.info(f"  Description: {dag.description}")
            self.log.info(f"  Schedule Interval: {dag.schedule_interval}")
            self.log.info(f"  Default Args: {dag.default_args}")
            self.log.info(f"  Filepath: {dag.filepath}")
            self.log.info(f"  Owner: {dag.owner}")
            self.log.info(f"  Start Date: {dag.start_date}")
            self.log.info(f"  Catchup: {dag.catchup}")
            self.log.info(f"  Latest Execution Date: {dag.latest_execution_date}")
            self.log.info(f"  Is Paused: {dag.is_paused}")
            self.log.info(f"  Tasks: {[task.task_id for task in dag.tasks]}")

            # Task details
            for task in dag.tasks:
                self.log.info(f"    Task ID: {task.task_id}")
                self.log.info(f"    Task Type: {task.__class__.__name__}")
                self.log.info(f"    Owner: {task.owner}")
                self.log.info(f"    Upstream: {[t.task_id for t in task.upstream_list]}")
                self.log.info(f"    Downstream: {[t.task_id for t in task.downstream_list]}")
        else:
            self.log.warning(f"No DAG found with ID '{dag_id}'.")
            return None

        return dag

    def show(self) -> None:
        """
        Show all available DAGs by listing their IDs.
        """
        dagbag = DagBag(dag_folder=self.dag_directory, include_examples=False)
        if dagbag.dags:
            self.log.info("Available DAGs:")
            for dag_id, dag in dagbag.dags.items():
                self.log.info(f"  DAG ID: {dag_id} - Description: {dag.description}")
        else:
            self.log.info("No DAGs available.")

    def delete(self, dag_id: str) -> None:
        """
        Delete a specific DAG by removing its file from the DAG directory.

        Args:
            dag_id (str): The ID of the DAG to delete.
        """
        dagbag = DagBag(dag_folder=self.dag_directory, include_examples=False)
        dag = dagbag.get_dag(dag_id)
        if dag:
            # Construct the path to the DAG file and remove it
            dag_file_path = os.path.join(self.dag_directory, f"{dag_id}.py")
            if os.path.exists(dag_file_path):
                os.remove(dag_file_path)
                self.log.info(f"Deleted DAG '{dag_id}' successfully.")
            else:
                self.log.warning(f"DAG file '{dag_file_path}' does not exist.")
        else:
            self.log.warning(f"No DAG found with ID '{dag_id}'.")

    def status(self, dag_id: str, airflow_api_base_url: str) -> None:
        """
        Get the status of a specific DAG using Airflow's REST API.

        Args:
            dag_id (str): The ID of the DAG to get the status of.
            airflow_api_base_url (str):  URL of airflow for calling its APIs.
        """

        # Endpoint for fetching DAG details
        dag_detail_url = f"{airflow_api_base_url}/dags/{dag_id}"
        dag_runs_url = f"{dag_detail_url}/dagRuns"

        # Make the request to the Airflow REST API
        dag_response = requests.get(dag_detail_url)
        runs_response = requests.get(dag_runs_url)

        # Check if the requests were successful
        if dag_response.status_code == 200 and runs_response.status_code == 200:
            dag_data = dag_response.json()
            runs_data = runs_response.json()

            # Log the DAG status details
            self.log.info(f"Status for DAG '{dag_id}':")
            self.log.info(f"  Is Paused: {dag_data.get('is_paused')}")
            self.log.info(f"  Schedule Interval: {dag_data.get('schedule_interval')}")

            # Assuming 'runs_data' contains a list of runs, display the latest run
            if runs_data.get("dag_runs"):
                latest_run = runs_data["dag_runs"][0]  # Assuming the first is the latest
                self.log.info("  Latest Run:")
                self.log.info(f"    Execution Date: {latest_run.get('execution_date')}")
                self.log.info(f"    State: {latest_run.get('state')}")
                self.log.info(f"    Run ID: {latest_run.get('run_id')}")
            else:
                self.log.info("  No runs found for this DAG.")
        else:
            self.log.warning(f"Failed to fetch status for DAG '{dag_id}'.")
