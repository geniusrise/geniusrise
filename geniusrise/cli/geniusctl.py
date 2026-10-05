# 🧠 Geniusrise
# Copyright (C) 2023-2025  geniusrise.ai
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
import logging
import os
import sys
import warnings
from typing import Dict, Optional

from prettytable import PrettyTable
from rich import print as richprint
from rich.style import Style
from rich.text import Text
from rich_argparse import RichHelpFormatter
from termcolor import colored  # type: ignore

from geniusrise.cli.discover import Discover, DiscoveredTask
from geniusrise.cli.dockerctl import DockerCtl
from geniusrise.cli.taskctl import TaskCtl
from geniusrise.cli.yamlctl import YamlCtl
from geniusrise.core import AVAILABLE_RUNNERS
from geniusrise.core.state.base import PrometheusMetricsServer
from geniusrise.logging import setup_logger


class GeniusCtl:
    """
    Main class for managing the geniusrise CLI application.
    """

    def __init__(self):
        """
        Initialize GeniusCtl.

        Args:
            directory (str): The directory to scan for tasks.
        """
        self.log = logging.getLogger(self.__class__.__name__)
        self.task_ctls: Dict[str, TaskCtl] = {}

        text = """
         %&&&&&&&&&&
     %%%@%@%%@@%%%%@@@@&&&&/
  /%@@@%%%%@%%%#%@%%%%%&@//%%        ██████  ███████ ███    ██ ██ ██    ██ ███████ ██████  ██ ███████ ███████
  ###@###@###@@@/@%%%%%%/%@%@&&     ██       ██      ████   ██ ██ ██    ██ ██      ██   ██ ██ ██      ██
 ##@##@##@#@##/@%%@@%@@%%%%&@#@&    ██   ███ █████   ██ ██  ██ ██ ██    ██ ███████ ██████  ██ ███████ █████
#@#@@@@@@@(#######@#/%@%%%%%%@%%    ██    ██ ██      ██  ██ ██ ██ ██    ██      ██ ██   ██ ██      ██ ██
 ((((@(@@######/########@@@@#%%%     ██████  ███████ ██   ████ ██  ██████  ███████ ██   ██ ██ ███████ ███████
  /#@#@##@###@#@#@##@##@###
    (((((@&#(@((@(((((##
        ((@/#/
         ///
        """

        # Print the text in red with a box around it and a dark background
        richprint(Text(text, style=Style(color="red")))

        metrics_server = PrometheusMetricsServer(port=os.environ.get("PROMETHEUS_PORT", 8282))
        metrics_server.start()

        # Print the link without a panel
        link_text = Text("🧠 https://geniusrise.ai", style=Style(color="deep_pink4"))
        link_text.stylize("link", 0, len(link_text))
        richprint(link_text)
        richprint("")

    def create_parser(self):
        """
        Create a command-line parser with arguments for managing the application.

        Returns:
            argparse.ArgumentParser: Command-line parser.
        """
        parser = argparse.ArgumentParser(description="Geniusrise", formatter_class=RichHelpFormatter)
        parser.allow_abbrev = False
        subparsers = parser.add_subparsers(dest="top_level_command")

        # Run module discovery
        self.discover()

        # Create subparser for each discovered task
        for task_name, discovered_task in self.tasks.items():
            task_parser = subparsers.add_parser(
                task_name,
                help=f"Manage task {task_name}.",
                formatter_class=RichHelpFormatter,
            )
            task_ctl = TaskCtl(discovered_task)
            self.task_ctls[task_name] = task_ctl
            task_ctl.create_parser(task_parser)

        # Create subparser for YAML operations
        yaml_parser = subparsers.add_parser(
            "rise",
            help="Manage tasks with a YAML file.",
            formatter_class=RichHelpFormatter,
        )
        # Initialize YamlCtl with task controllers
        self.yaml_ctl = YamlCtl(self.task_ctls)
        self.yaml_ctl.create_parser(yaml_parser)

        docker_parser = subparsers.add_parser(
            "docker",
            help="Package this application into a Docker image.",
            formatter_class=RichHelpFormatter,
        )
        self.docker_ctl = DockerCtl()
        self.docker_ctl.create_parser(docker_parser)

        # Add all available runners from the plugin system
        self.runners = {}
        for runner_name, runner_class in AVAILABLE_RUNNERS.items():
            runner_parser = subparsers.add_parser(
                runner_name,
                help=f"Manage tasks with {runner_name}",
                formatter_class=RichHelpFormatter,
            )
            runner = runner_class()
            runner.create_parser(runner_parser)
            self.runners[runner_name] = runner

        # Try to load legacy runners with warnings
        # K8s runners - these could be moved to plugins
        try:
            from geniusrise.runners.k8s import CronJob, Deployment, Job, K8sResourceManager, Service

            warnings.warn(
                "The embedded Kubernetes runners are deprecated and will be moved to a separate package. "
                "Please install geniusrise-runner-kubernetes in the future.",
                DeprecationWarning,
            )

            # All of these will be handled with the plugin system
        except ImportError:
            pass

        # Try to load legacy OpenStack runners
        try:
            from geniusrise.runners.openstack import OpenStackAutoscaleRunner, OpenStackInstanceRunner

            warnings.warn(
                "The embedded OpenStack runners are deprecated and will be moved to a separate package. "
                "Please install geniusrise-runner-openstack in the future.",
                DeprecationWarning,
            )

            # All of these will be handled with the plugin system
        except ImportError:
            pass

        # Try to load legacy AceCloud runners
        try:
            from geniusrise.runners.acecloud import AceCloudAutoscaleRunner, AceCloudInstanceRunner

            warnings.warn(
                "The embedded AceCloud runners are deprecated and will be moved to a separate package. "
                "Please install geniusrise-runner-acecloud in the future.",
                DeprecationWarning,
            )

            # All of these will be handled with the plugin system
        except ImportError:
            pass

        # Try to load legacy E2E runners
        try:
            from geniusrise.runners.e2e_networks import E2EAutoscaleRunner, E2EInstanceRunner

            warnings.warn(
                "The embedded E2E Networks runners are deprecated and will be moved to a separate package. "
                "Please install geniusrise-runner-e2e in the future.",
                DeprecationWarning,
            )

            # All of these will be handled with the plugin system
        except ImportError:
            pass

        # Add a 'help' command to print help for all components
        help_parser = subparsers.add_parser(
            "plugins",
            help="Print help for all discovered components.",
            formatter_class=RichHelpFormatter,
        )
        help_parser.add_argument("component", nargs="?", help="The component to print help for.")

        # Add a 'list' command to list all discovered components
        list_parser = subparsers.add_parser(
            "list",
            help="List all discovered components.",
            formatter_class=RichHelpFormatter,
        )
        list_parser.add_argument("--verbose", action="store_true", help="Print verbose output.")

        # Add a 'runners' command to list all available runners
        runners_parser = subparsers.add_parser(
            "runners",
            help="List all available runners.",
            formatter_class=RichHelpFormatter,
        )

        return parser

    def discover(self):
        self.discover_obj = Discover()
        discovered_components = self.discover_obj.scan_directory(os.getenv("GENIUS_DIR", "."))
        discovered_installed_components = self.discover_obj.discover_geniusrise_installed_modules()

        components = {**discovered_components, **discovered_installed_components}

        # Get the discovered tasks
        self.tasks = {
            name: component for name, component in components.items() if isinstance(component, DiscoveredTask)
        }

    def run(self, args):
        """
        Run the command-line interface.

        Args:
            args (argparse.Namespace): Parsed command-line arguments.

        Returns:
            int: Exit code (0 for success, 1 for error)
        """
        if not hasattr(args, "top_level_command") or not args.top_level_command:
            self.log.error("No command specified.")
            return 1

        self.log.debug(f"Running command: {args.top_level_command} with args {args}")

        # Task command
        if args.top_level_command in self.tasks:
            self.task_ctls[args.top_level_command].run(args)
        # YAML command
        elif args.top_level_command == "rise":
            self.yaml_ctl.run(args)
        # Docker command
        elif args.top_level_command == "docker":
            self.docker_ctl.run(args)
        # Plugin runners
        elif args.top_level_command in self.runners:
            self.runners[args.top_level_command].run(args)
        # Legacy commands - these will be handled by the plugin system
        elif args.top_level_command in ["pod", "deployment", "service", "job", "cron_job",
                                      "openstack", "openstack-autoscale",
                                      "acecloud", "acecloud-autoscale",
                                      "e2e", "e2e-autoscale"]:
            self.log.error(f"The '{args.top_level_command}' command is now handled by the plugin system. "
                           f"Please install the appropriate plugin package.")
            return 1
        # Plugins command
        elif args.top_level_command == "plugins":
            if hasattr(args, "component") and args.component:
                if args.component in self.tasks:
                    self.task_ctls[args.component].run(args)
                elif args.component in self.runners:
                    self.runners[args.component].run(args)
                else:
                    self.log.error(f"Unknown component: {args.component}")
                    return 1
            else:
                # Show all components
                for task_ctl in self.task_ctls.values():
                    task_ctl.run(args)
                for runner in self.runners.values():
                    if hasattr(runner, "help"):
                        runner.help()
        # List command
        elif args.top_level_command == "list":
            if len(self.tasks.keys()) == 0:
                self.log.warn("No components discovered.")
            self.list_components(args.verbose if hasattr(args, "verbose") else False)
        # Runners command
        elif args.top_level_command == "runners":
            self.list_runners()
        else:
            self.log.error(f"Unknown command: {args.top_level_command}")
            return 1

        return 0

    def list_components(self, verbose: bool = False):
        """
        List all discovered components in a table.
        """
        table = (
            PrettyTable(
                [
                    colored("Name", "green"),
                    colored("Type", "green"),
                    colored("Methods", "green"),
                ],
                align="l",
            )
            if verbose
            else PrettyTable(
                [
                    colored("Name", "green"),
                    colored("Type", "green"),
                ],
                align="l",
            )
        )

        # List tasks
        for task_name in self.tasks.keys():
            t = self.tasks[task_name].klass
            table.add_row(
                (
                    [
                        colored(task_name, "yellow"),
                        colored("Task", "blue"),
                        "\n".join([colored(x, "blue") for x in dir(t) if not x.startswith("_")]),
                    ]
                    if verbose
                    else [
                        colored(task_name, "yellow"),
                        colored("Task", "blue"),
                    ]
                ),
                divider=verbose,
            )

        sys.stdout.write(table.__repr__())

    def list_runners(self):
        """
        List all available runners.
        """
        table = PrettyTable(
            [
                colored("Runner Name", "green"),
                colored("Description", "green"),
            ],
            align="l",
        )

        for runner_name, runner_class in AVAILABLE_RUNNERS.items():
            table.add_row(
                [
                    colored(runner_name, "yellow"),
                    colored(getattr(runner_class, "__doc__", "No description").split("\n")[0].strip(), "cyan"),
                ],
            )
        sys.stdout.write(table.__repr__())

    def cli(self):
        """
        Main function to be called when geniusrise is run from the command line.

        Returns:
            int: Exit code (0 for success, 1 for error)
        """
        parser = self.create_parser()
        args = parser.parse_args()
        return self.run(args)


def main():
    """
    Main entry point for the geniusrise CLI.

    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    setup_logger()
    genius_ctl = GeniusCtl()
    return genius_ctl.cli()


if __name__ == "__main__":
    sys.exit(main())


def create_parser():
    """
    Create a command-line parser for the geniusrise CLI.

    Returns:
        argparse.ArgumentParser: The command-line parser.
    """
    genius_ctl = GeniusCtl()
    return genius_ctl.create_parser()
