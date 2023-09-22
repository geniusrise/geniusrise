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
import logging
import os
import sys
from typing import Dict

from prettytable import PrettyTable
from rich import print
from rich.style import Style
from rich.text import Text
from rich_argparse import RichHelpFormatter
from termcolor import colored  # type: ignore

from geniusrise.cli.boltctl import BoltCtl
from geniusrise.cli.discover import Discover, DiscoveredBolt, DiscoveredSpout
from geniusrise.cli.spoutctl import SpoutCtl
from geniusrise.cli.yamlctl import YamlCtl
from geniusrise.cli.dockerctl import DockerCtl
from geniusrise.logging import setup_logger
from geniusrise.runners.k8s import Deployment, Service, Job, CronJob, K8sResourceManager


class GeniusCtl:
    """
    Main class for managing the geniusrise CLI application.
    """

    def __init__(self):
        """
        Initialize GeniusCtl.v

        Args:
            directory (str): The directory to scan for spouts and bolts.
        """
        self.log = logging.getLogger(self.__class__.__name__)

        self.spout_ctls: Dict[str, SpoutCtl] = {}
        self.bolt_ctls: Dict[str, BoltCtl] = {}

        text = """
         %&&&&&&&&&&
     %%%@%@%%@@%%%%@@@@&&&&/
  /%@@@%%%%@%%%#%@%%%%%&@//%%        ██████  ███████ ███    ██ ██ ██    ██ ███████ ██████  ██ ███████ ███████
  ###@###@###@@@/@%%%%%%/%@%@&&     ██       ██      ████   ██ ██ ██    ██ ██      ██   ██ ██ ██      ██
 ##@##@##@#@##/@%%@@%@@%%%%&@#@&    ██   ███ █████   ██ ██  ██ ██ ██    ██ ███████ ██████  ██ ███████ █████ 
#@#@@@@@@@(#######@#/%@%%%%%%@%%    ██    ██ ██      ██  ██ ██ ██ ██    ██      ██ ██   ██ ██      ██ ██
 ((((@(@@######/########@@@@#%%%     ██████  ███████ ██   ████ ██  ██████  ███████ ██   ██ ██ ███████ ███████
  /#@#@##@###@#@#@##@##@###
    (((((@&#(@((@(((((##
        ((@/#/
         ///
        """

        # Print the text in red with a box around it and a dark background
        print(Text(text, style=Style(color="red")))

        # Print the link without a panel
        link_text = Text("🧠 https://geniusrise.ai", style=Style(color="deep_pink4"))
        link_text.stylize("link", 0, len(link_text))
        print(link_text)
        print("")

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

        # Create subparser for each discovered spout
        for spout_name, discovered_spout in self.spouts.items():
            spout_parser = subparsers.add_parser(
                spout_name,
                help=f"Manage spout {spout_name}.",
                formatter_class=RichHelpFormatter,
            )
            spout_ctl = SpoutCtl(discovered_spout)
            self.spout_ctls[spout_name] = spout_ctl
            spout_ctl.create_parser(spout_parser)

        # Create subparser for each discovered bolt
        for bolt_name, discovered_bolt in self.bolts.items():
            bolt_parser = subparsers.add_parser(
                bolt_name,
                help=f"Manage bolt {bolt_name}.",
                formatter_class=RichHelpFormatter,
            )
            bolt_ctl = BoltCtl(discovered_bolt)
            self.bolt_ctls[bolt_name] = bolt_ctl
            bolt_ctl.create_parser(bolt_parser)

        # Create subparser for YAML operations
        yaml_parser = subparsers.add_parser(
            "rise",
            help="Manage spouts and bolts with a YAML file.",
            formatter_class=RichHelpFormatter,
        )
        # Initialize YamlCtl with both spout_ctls and bolt_ctls
        self.yaml_ctl = YamlCtl(self.spout_ctls, self.bolt_ctls)
        self.yaml_ctl.create_parser(yaml_parser)

        docker_parser = subparsers.add_parser("docker", help="Package this application into a Docker image.")
        self.docker_ctl = DockerCtl()
        self.docker_ctl.create_parser(docker_parser)

        # Connect to kubernetes runner
        pod_parser = subparsers.add_parser("pod", help="Manage spouts and bolts as kubernetes pod")
        self.k8s_pod = K8sResourceManager()
        self.k8s_pod.create_parser(pod_parser)

        deployment_parser = subparsers.add_parser("deployment", help="Manage spouts and bolts as kubernetes deployment")
        self.k8s_deployment = Deployment()
        self.k8s_deployment.create_parser(deployment_parser)

        service_parser = subparsers.add_parser("service", help="Manage spouts and bolts as kubernetes service")
        self.k8s_service = Service()
        self.k8s_service.create_parser(service_parser)

        job_parser = subparsers.add_parser("job", help="Manage spouts and bolts as kubernetes job")
        self.k8s_job = Job()
        self.k8s_job.create_parser(job_parser)

        cron_job_parser = subparsers.add_parser("cron_job", help="Manage spouts and bolts as kubernetes cron_job")
        self.k8s_cron_job = CronJob()
        self.k8s_cron_job.create_parser(cron_job_parser)

        # Add a 'help' command to print help for all spouts and bolts
        help_parser = subparsers.add_parser(
            "plugins",
            help="Print help for all spouts and bolts.",
            formatter_class=RichHelpFormatter,
        )
        help_parser.add_argument("spout_or_bolt", nargs="?", help="The spout or bolt to print help for.")

        # Add a 'list' command to list all discovered spouts and bolts
        list_parser = subparsers.add_parser(
            "list",
            help="List all discovered spouts and bolts.",
            formatter_class=RichHelpFormatter,
        )
        list_parser.add_argument("--verbose", action="store_true", help="Print verbose output.")

        return parser

    def discover(self):
        self.discover = Discover()
        discovered_components = self.discover.scan_directory(os.getenv("GENIUS_DIR", "."))
        discovered_installed_components = self.discover.discover_geniusrise_installed_modules()

        components = {**discovered_components, **discovered_installed_components}

        # Segregate the discovered components based on their type
        self.spouts = {
            name: component for name, component in components.items() if isinstance(component, DiscoveredSpout)
        }
        self.bolts = {
            name: component for name, component in components.items() if isinstance(component, DiscoveredBolt)
        }

    def run(self, args):
        """
        Run the command-line interface.

        Args:
            args (argparse.Namespace): Parsed command-line arguments.
        """
        self.log.debug(f"Running command: {args.top_level_command} with args {args}")

        if args.top_level_command in self.spouts:
            self.spout_ctls[args.top_level_command].run(args)
        elif args.top_level_command in self.bolts:
            self.bolt_ctls[args.top_level_command].run(args)
        elif args.top_level_command == "rise":
            self.yaml_ctl.run(args)
        elif args.top_level_command == "docker":
            self.docker_ctl.run(args)
        elif args.top_level_command == "pod":
            self.k8s_pod.run(args)
        elif args.top_level_command == "deployment":
            self.k8s_deployment.run(args)
        elif args.top_level_command == "service":
            self.k8s_service.run(args)
        elif args.top_level_command == "job":
            self.k8s_job.run(args)
        elif args.top_level_command == "cron_job":
            self.k8s_cron_job.run(args)
        elif args.top_level_command == "plugins":
            if args.spout_or_bolt in self.spouts:
                self.spout_ctls[args.spout_or_bolt].run(args)
            elif args.spout_or_bolt in self.bolts:
                self.bolt_ctls[args.spout_or_bolt].run(args)
            else:
                for spout_ctl in self.spout_ctls.values():
                    spout_ctl.run(args)
                for bolt_ctl in self.bolt_ctls.values():
                    bolt_ctl.run(args)
        elif args.top_level_command == "list":
            if len(self.spouts.keys()) == 0 and len(self.bolts.keys()) == 0:
                self.log.warn("No spouts or bolts discovered.")
            self.list_spouts_and_bolts(args.verbose)

    def list_spouts_and_bolts(self, verbose: bool = False):
        """
        List all discovered spouts and bolts in a table.
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

        for spout_name in self.spouts.keys():
            s = self.spouts[spout_name].klass
            table.add_row(
                [
                    colored(spout_name, "yellow"),
                    colored("Spout", "cyan"),
                    "\n".join([colored(x, "cyan") for x in dir(s) if not x.startswith("_")]),
                ]
                if verbose
                else [
                    colored(spout_name, "yellow"),
                    colored("Spout", "cyan"),
                ],
                divider=verbose,
            )
        for bolt_name in self.bolts.keys():
            b = self.bolts[bolt_name].klass
            table.add_row(
                [
                    colored(bolt_name, "yellow"),
                    colored("Bolt", "magenta"),
                    "\n".join([colored(x, "magenta") for x in dir(b) if not x.startswith("_")]),
                ]
                if verbose
                else [
                    colored(bolt_name, "yellow"),
                    colored("Bolt", "magenta"),
                ],
                divider=verbose,
            )
        sys.stdout.write(table.__repr__())

    def cli(self):
        """
        Main function to be called when geniusrise is run from the command line.
        """
        parser = self.create_parser()
        args = parser.parse_args()
        return self.run(args)


def main():
    setup_logger()
    genius_ctl = GeniusCtl()
    genius_ctl.cli()


if __name__ == "__main__":
    genius_ctl = GeniusCtl()
    genius_ctl.cli()


def create_parser():
    genius_ctl = GeniusCtl()
    return genius_ctl.create_parser()
