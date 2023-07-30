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
import logging

from prettytable import PrettyTable
from termcolor import colored  # type: ignore

from geniusrise.cli.discover import Discover
from geniusrise.cli.spoutctl import SpoutCtl
from geniusrise.cli.yamlctl import YamlCtl

# from geniusrise.cli.boltctl import BoltCtl  # Uncomment when BoltCtl is ready


class GeniusCtl:
    """
    Main class for managing the geniusrise CLI application.
    """

    def __init__(self, directory: str):
        """
        Initialize GeniusCtl.

        Args:
            directory (str): The directory to scan for spouts.
        """
        self.log = logging.getLogger(self.__class__.__name__)
        self.discover = Discover(directory)
        self.spouts = self.discover.scan_directory()

    def create_parser(self):
        """
        Create a command-line parser with arguments for managing the application.

        Returns:
            argparse.ArgumentParser: Command-line parser.
        """
        parser = argparse.ArgumentParser(description="Manage the geniusrise application.")
        subparsers = parser.add_subparsers(dest="command")

        # Create subparser for each discovered spout
        spout_ctls = []
        for spout_name, discovered_spout in self.spouts.items():
            spout_parser = subparsers.add_parser(spout_name, help=f"Manage {spout_name}.")
            spout_ctl = SpoutCtl(discovered_spout)  # Initialize SpoutCtl with the discovered spout
            spout_ctls.append(spout_ctl)  # Add the SpoutCtl to the list of spout
            spout_ctl.create_parser(spout_parser)  # Pass the spout_parser to the SpoutCtl's create_parser method
        self.spout_ctls = spout_ctls

        # Create subparser for YAML opserations
        yaml_parser = subparsers.add_parser("yaml", help="Control spouts with a YAML file.")
        yaml_parser.add_argument("--file", default="genius.yml", help="The YAML file to use.")
        yaml_ctl = YamlCtl("", self.spout_ctls)
        yaml_ctl.create_parser(yaml_parser)

        # Add a 'help' command to print help for all spouts
        help_parser = subparsers.add_parser("help", help="Print help for all spouts.")
        help_parser.add_argument("spout", nargs="?", help="The spout to print help for.")

        # Add a 'list' command to list all discovered spouts
        list_parser = subparsers.add_parser("list", help="List all discovered spouts.")

        return parser

    def run(self, args):
        """
        Run the command-line interface.

        Args:
            args (argparse.Namespace): Parsed command-line arguments.
        """
        self.log.info(f"Running command: {args.command}")

        if args.command in self.spouts:
            spout_ctl = SpoutCtl(self.spouts[args.command])  # Initialize SpoutCtl with the chosen spout
            spout_ctl.run(args)
        elif args.command == "yaml":
            yaml_ctl = YamlCtl(args.file, self.spout_ctls)
            yaml_ctl.run(args)
        elif args.command == "help":
            if args.spout:
                spout_ctl = SpoutCtl(self.spouts[args.spout])  # Initialize SpoutCtl with the chosen spout
                spout_ctl.run(args)
            else:
                for _, discovered_spout in self.spouts.items():
                    spout_ctl = SpoutCtl(discovered_spout)  # Initialize SpoutCtl with each spout
                    spout_ctl.run(args)
        elif args.command == "list":
            self.list_spouts()

    def list_spouts(self):
        """
        List all discovered spouts in a table.
        """
        table = PrettyTable([colored("Spout", "green"), colored("Methods", "green")], align="l")
        for spout_name in self.spouts.keys():
            s = self.spouts[spout_name].klass
            table.add_row(
                [colored(spout_name, "yellow"), "\n".join([x for x in dir(s) if "fetch_" in x])], divider=True
            )
        print(table)

    def cli(self):
        """
        Main function to be called when geniusrise is run from the command line.
        """
        parser = self.create_parser()
        args = parser.parse_args()
        return self.run(args)


if __name__ == "__main__":
    directory = "geniusrise/spouts"
    genius_ctl = GeniusCtl(directory)
    genius_ctl.cli()
