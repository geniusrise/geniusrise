import argparse
import logging
from prettytable import PrettyTable

from geniusrise.cli.discover import Discover
from geniusrise.cli.spoutctl import SpoutCtl

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
        for spout_name, discovered_spout in self.spouts.items():
            spout_parser = subparsers.add_parser(spout_name, help=f"Manage {spout_name}.")
            spout_ctl = SpoutCtl(discovered_spout)  # Initialize SpoutCtl with the discovered spout
            spout_ctl.create_parser(spout_parser)  # Pass the spout_parser to the SpoutCtl's create_parser method

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
        elif args.command == "help":
            if args.spout:
                spout_ctl = SpoutCtl(self.spouts[args.spout])  # Initialize SpoutCtl with the chosen spout
                spout_ctl.cli(["--help"])
            else:
                for _, discovered_spout in self.spouts.items():
                    spout_ctl = SpoutCtl(discovered_spout)  # Initialize SpoutCtl with each spout
                    spout_ctl.cli(["--help"])
        elif args.command == "list":
            self.list_spouts()

    def list_spouts(self):
        """
        List all discovered spouts in a table.
        """
        table = PrettyTable(["Spout"])
        for spout_name in self.spouts.keys():
            table.add_row([spout_name])
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
