import argparse
import logging
import os
from typing import Dict

from prettytable import PrettyTable
from termcolor import colored  # type: ignore
from rich import print
from rich.panel import Panel
from rich.style import Style

from geniusrise.cli.boltctl import BoltCtl
from geniusrise.cli.discover import Discover, DiscoveredBolt, DiscoveredSpout
from geniusrise.cli.spoutctl import SpoutCtl
from geniusrise.cli.yamlctl import YamlCtl


class GeniusCtl:
    """
    Main class for managing the geniusrise CLI application.
    """

    def __init__(self):
        """
        Initialize GeniusCtl.

        Args:
            directory (str): The directory to scan for spouts and bolts.
        """
        self.log = logging.getLogger(self.__class__.__name__)

        self.spout_ctls: Dict[str, SpoutCtl] = {}
        self.bolt_ctls: Dict[str, BoltCtl] = {}

        text = """
        ██████  ███████ ███    ██ ██ ██    ██ ███████ ██████  ██ ███████ ███████
        ██       ██      ████   ██ ██ ██    ██ ██      ██   ██ ██ ██      ██
        ██   ███ █████   ██ ██  ██ ██ ██    ██ ███████ ██████  ██ ███████ █████ 
        ██    ██ ██      ██  ██ ██ ██ ██    ██      ██ ██   ██ ██      ██ ██
         ██████  ███████ ██   ████ ██  ██████  ███████ ██   ██ ██ ███████ ███████
        """

        # Print the text in red with a box around it
        print(Panel(text, style=Style(color="red")))

    def create_parser(self):
        """
        Create a command-line parser with arguments for managing the application.

        Returns:
            argparse.ArgumentParser: Command-line parser.
        """
        parser = argparse.ArgumentParser(description="Manage the geniusrise application.")
        subparsers = parser.add_subparsers(dest="command")

        # Create subparser for each discovered spout
        for spout_name, discovered_spout in self.spouts.items():
            spout_parser = subparsers.add_parser(spout_name, help=f"Manage {spout_name}.")
            spout_ctl = SpoutCtl(discovered_spout)
            self.spout_ctls[spout_name] = spout_ctl
            spout_ctl.create_parser(spout_parser)

        # Create subparser for each discovered bolt
        for bolt_name, discovered_bolt in self.bolts.items():
            bolt_parser = subparsers.add_parser(bolt_name, help=f"Manage {bolt_name}.")
            bolt_ctl = BoltCtl(discovered_bolt)
            self.bolt_ctls[bolt_name] = bolt_ctl
            bolt_ctl.create_parser(bolt_parser)

        # Create subparser for YAML operations
        yaml_parser = subparsers.add_parser("yaml", help="Control spouts and bolts with a YAML file.")
        # Initialize YamlCtl with both spout_ctls and bolt_ctls
        self.yaml_ctl = YamlCtl(self.spout_ctls, self.bolt_ctls)
        self.yaml_ctl.create_parser(yaml_parser)

        # Add a 'help' command to print help for all spouts and bolts
        help_parser = subparsers.add_parser("plugins", help="Print help for all spouts and bolts.")
        help_parser.add_argument("spout_or_bolt", nargs="?", help="The spout or bolt to print help for.")

        # Add a 'list' command to list all discovered spouts and bolts
        list_parser = subparsers.add_parser("list", help="List all discovered spouts and bolts.")

        return parser

    def run(self, args):
        """
        Run the command-line interface.

        Args:
            args (argparse.Namespace): Parsed command-line arguments.
        """
        self.log.info(f"Running command: {args.command}")

        self.discover = Discover()
        discovered_components = self.discover.scan_directory(os.getenv("GENIUS_DIR", "."))

        # Segregate the discovered components based on their type
        self.spouts = {
            name: component
            for name, component in discovered_components.items()
            if isinstance(component, DiscoveredSpout)
        }
        self.bolts = {
            name: component
            for name, component in discovered_components.items()
            if isinstance(component, DiscoveredBolt)
        }

        if args.command in self.spouts:
            self.spout_ctls[args.command].run(args)
        elif args.command in self.bolts:
            self.bolt_ctls[args.command].run(args)
        elif args.command == "yaml":
            self.yaml_ctl.run(args)
        elif args.command == "plugins":
            if args.spout_or_bolt in self.spouts:
                self.spout_ctls[args.spout_or_bolt].run(args)
            elif args.spout_or_bolt in self.bolts:
                self.bolt_ctls[args.spout_or_bolt].run(args)
            else:
                for spout_ctl in self.spout_ctls.values():
                    spout_ctl.run(args)
                for bolt_ctl in self.bolt_ctls.values():
                    bolt_ctl.run(args)
        elif args.command == "list":
            if len(self.spout.keys()) == 0:
                print("No spouts or bolts discovered.")
            self.list_spouts_and_bolts()

    def list_spouts_and_bolts(self):
        """
        List all discovered spouts and bolts in a table.
        """
        table = PrettyTable(
            [
                colored("Name", "green"),
                colored("Type", "green"),
                colored("Methods", "green"),
            ],
            align="l",
        )
        for spout_name in self.spouts.keys():
            s = self.spouts[spout_name].klass
            table.add_row(
                [
                    colored(spout_name, "yellow"),
                    colored("Spout", "cyan"),
                    "\n".join([x for x in dir(s) if "fetch_" in x]),
                ],
                divider=True,
            )
        for bolt_name in self.bolts.keys():
            b = self.bolts[bolt_name].klass
            table.add_row(
                [
                    colored(bolt_name, "yellow"),
                    colored("Bolt", "magenta"),
                    "\n".join([x for x in dir(b) if not x.startswith("_")]),
                ],
                divider=True,
            )
        print(table)

    def cli(self):
        """
        Main function to be called when geniusrise is run from the command line.
        """
        parser = self.create_parser()
        args = parser.parse_args()
        return self.run(args)


def main():
    genius_ctl = GeniusCtl()
    genius_ctl.cli()


if __name__ == "__main__":
    genius_ctl = GeniusCtl()
    genius_ctl.cli()
