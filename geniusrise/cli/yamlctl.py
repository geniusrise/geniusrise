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
from typing import Dict, List, Optional

import yaml  # type: ignore
from pydantic import ValidationError

from geniusrise.cli.schema import SpoutConfig
from geniusrise.cli.spoutctl import SpoutCtl
from geniusrise.core import ECSManager, K8sManager


class YamlCtl:
    def __init__(self, yaml_file: str, spout_ctls: Dict[str, SpoutCtl]):
        """
        Initialize a new YamlCtl instance.

        Args:
            yaml_file (str): The path to the YAML configuration file.
            spout_ctls (Dict[str, SpoutCtl]): A dictionary mapping spout names to their corresponding SpoutCtl instances.
        """
        self.yaml_file = yaml_file
        self.config: SpoutConfig
        self.spout_ctls = spout_ctls

    def load_config(self) -> bool:
        """
        Load the configuration from the YAML file.

        Returns:
            bool: True if the configuration was loaded successfully, False otherwise.
        """
        with open(self.yaml_file, "r") as file:
            config_data = yaml.safe_load(file)
        try:
            self.config = SpoutConfig(**config_data)
        except ValidationError as e:
            print(f"Invalid configuration: {e}")
            return False
        return True

    def run_spouts(self, spout_names: Optional[List[str]] = None):
        """
        Run specified spouts or all spouts if no spout names are provided.

        Args:
            spout_names (Optional[List[str]]): The names of the spouts to run. If not provided, all spouts are run.

        Returns:
            Dict[str, Any]: A dictionary mapping spout names to the results of the method.
        """
        if spout_names is None:
            spout_names = list(self.spout_ctls.keys())
        results = {}
        for spout_name in spout_names:
            if spout_name in self.spout_ctls:
                spout_ctl = self.spout_ctls[spout_name]
                yaml_config = self.config.spouts[spout_name]
                spout = spout_ctl.create_spout(
                    output_type=yaml_config.output.type,
                    state_type=yaml_config.state_type,
                    **{
                        **yaml_config.state.args.dict(),  # type: ignore
                        **yaml_config.output.args.dict(),  # type: ignore
                        **yaml_config.other.dict(),  # type: ignore
                    },
                )
                results[spout_name] = spout_ctl.execute_spout(spout=spout, method_name=yaml_config.method)
            else:
                print(f"Spout {spout_name} not found in configuration")
        return results

    def deploy_spouts(self, spout_names: Optional[List[str]] = None):
        """
        Deploy specified spouts or all spouts if no spout names are provided.

        Args:
            spout_names (Optional[List[str]]): The names of the spouts to deploy. If not provided, all spouts are deployed.

        Returns:
            Dict[str, Any]: A dictionary mapping spout names to the results of the method.
        """
        if spout_names is None:
            spout_names = list(self.spout_ctls.keys())
        results = {}
        for spout_name in spout_names:
            if spout_name in self.spout_ctls:
                spout_ctl = self.spout_ctls[spout_name]
                yaml_config = self.config.spouts[spout_name]
                results[spout_name] = spout_ctl.execute_remote(
                    manager_type=yaml_config.deploy.type,
                    method_name=yaml_config.method,
                    **{
                        **yaml_config.state.args.dict(),  # type: ignore
                        **yaml_config.output.args.dict(),  # type: ignore
                        **yaml_config.other.dict(),  # type: ignore
                    },
                )
            else:
                print(f"Spout {spout_name} not found in configuration")
        return results

    def create_parser(self, parser: argparse.ArgumentParser):
        """
        Create a subparser for the YAML control commands.

        Args:
            parser (argparse.ArgumentParser): The parent argument parser.
        """
        subparsers = parser.add_subparsers(dest="command")

        run_parser = subparsers.add_parser("run", help="Run a spout locally.")
        run_parser.add_argument(
            "spout_names",
            nargs="*",
            default=None,
            help="The names of the spouts to run. If not provided, all spouts are run.",
        )

        deploy_parser = subparsers.add_parser("deploy", help="Deploy a spout remotely.")
        deploy_parser.add_argument(
            "spout_names",
            nargs="*",
            default=None,
            help="The names of the spouts to deploy. If not provided, all spouts are deployed.",
        )

        # Kubernetes commands
        k8s_parser = subparsers.add_parser("k8s", help="Kubernetes management commands")
        k8s_parser.add_argument(
            "action",
            choices=["scale", "delete", "status", "statistics", "logs"],
            help="Action to perform",
        )
        k8s_parser.add_argument("--name", help="Name of the deployment")
        k8s_parser.add_argument(
            "--names",
            nargs="*",
            default=None,
            help="Names of the spout k8s deployments. If not provided, all spouts are considered in the yaml.",
        )
        k8s_parser.add_argument("--replicas", type=int, help="Number of replicas for update and scale actions")

        # ECS commands
        ecs_parser = subparsers.add_parser("ecs", help="ECS management commands")
        ecs_parser.add_argument("action", choices=["describe", "stop", "delete"], help="Action to perform")
        ecs_parser.add_argument(
            "--names",
            nargs="*",
            default=None,
            help="Name of the spout ECS tasks. If not provided, all spouts are considered in the yaml.",
        )
        # TODO: The ECS interface needs to improve
        ecs_parser.add_argument(
            "--task-definition-arns",
            nargs="*",
            default=None,
            help="Task definition ARNs of spout ECS tasks.",
        )
        # ecs_parser.add_argument("--name", help="Name of the task or service")
        # ecs_parser.add_argument(
        #     "--task-definition-arn", help="ARN of the task definition for run, describe, stop, and update actions"
        # )

        # Create subparser for 'help' command
        execute_parser = subparsers.add_parser("help", help="Print help for the spout.")
        execute_parser.add_argument("method", help="The method to execute.")

    def run(self, args):
        """
        Run the appropriate command based on the provided arguments.

        Args:
            args: The command line arguments.
        """
        if not self.load_config():
            return

        if args.command == "run":
            results = self.run_spouts(args.spout_names)
            print(results)
        elif args.command == "deploy":
            results = self.deploy_spouts(args.spout_names)
            print(results)
        elif args.command == "k8s":
            if args.names is None:
                spout_names = list(self.spout_ctls.keys())
            else:
                spout_names = args.names
            for spout in spout_names:
                k8s_manager = K8sManager(
                    name=spout, namespace=self.config.spouts[spout].delpoy.args.namespace
                )  # Initialize K8sManager
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
            if args.names is None:
                spout_names = list(self.spout_ctls.keys())
            else:
                spout_names = args.names
            for spout in spout_names:
                ecs_manager = ECSManager(name=spout, account_id="")  # Initialize ECSManager
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
