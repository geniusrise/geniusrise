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
import typing
from typing import Dict, List

import emoji  # type: ignore
import yaml  # type: ignore

from geniusrise.cli.boltctl import BoltCtl
from geniusrise.cli.schema import Bolt, Geniusfile, Spout
from geniusrise.cli.spoutctl import SpoutCtl


class YamlCtl:
    """
    Command-line interface for managing spouts and bolts based on a YAML configuration.

    The YamlCtl class provides methods to run specific or all spouts and bolts defined in a YAML file.
    The YAML file's structure is defined by the Geniusfile schema.

    Example YAML structure:
    ```
    version: "1"
    spouts:
      spout_name1:
        name: "spout1"
        method: "method_name"
        ...
    bolts:
      bolt_name1:
        name: "bolt1"
        method: "method_name"
        ...
    ```

    Attributes:
        geniusfile (Geniusfile): Parsed YAML configuration.
        spout_ctls (Dict[str, SpoutCtl]): Dictionary of SpoutCtl instances.
        bolt_ctls (Dict[str, BoltCtl]): Dictionary of BoltCtl instances.
    """

    def __init__(self, spout_ctls: Dict[str, SpoutCtl], bolt_ctls: Dict[str, BoltCtl]):
        """
        Initialize YamlCtl with the path to the YAML file and control instances for spouts and bolts.

        Args:
            spout_ctls (Dict[str, SpoutCtl]): Dictionary of SpoutCtl instances.
            bolt_ctls (Dict[str, BoltCtl]): Dictionary of BoltCtl instances.
        """
        self.spout_ctls = spout_ctls
        self.bolt_ctls = bolt_ctls
        self.log = logging.getLogger(self.__class__.__name__)

    def create_parser(self, parser):
        """
        Create and return the command-line parser for managing spouts and bolts.
        """
        parser.add_argument("--spout", type=str, help="Name of the specific spout to run.")
        parser.add_argument("--bolt", type=str, help="Name of the specific bolt to run.")
        parser.add_argument(
            "--file",
            default=".",
            type=str,
            help="Path of the genius.yml file, default to .",
        )
        return parser

    def run(self, args):
        """
        Run the command-line interface for managing spouts and bolts based on provided arguments.
        Please note that there is no ordering of the spouts and bolts in the YAML configuration.
        Each spout and bolt is an independent entity even when connected together.

        Args:
            args (argparse.Namespace): Parsed command-line arguments.
        """
        with open(args.file, "r") as file:
            self.geniusfile = Geniusfile.model_validate(yaml.safe_load(file), strict=True)
        if args.spout == "all":
            self.run_spouts()
        elif args.bolt == "all":
            self.run_bolts()
        elif args.spout:
            self.run_spout(args.spout)
        elif args.bolt:
            self.run_bolt(args.bolt)
        else:
            self.run_spouts()
            self.run_bolts()

    def run_spouts(self):
        """Run all spouts defined in the YAML configuration."""
        self.log.info(emoji.emojize(":rocket: Running all spouts..."))
        for spout_name, _ in self.geniusfile.spouts.items():
            self.run_spout(spout_name)

    def run_bolts(self):
        """Run all bolts defined in the YAML configuration."""
        self.log.info(emoji.emojize(":rocket: Running all bolts..."))
        for bolt_name, _ in self.geniusfile.bolts.items():
            self.run_bolt(bolt_name)

    def run_spout(self, spout_name: str):
        """
        Run a specific spout based on its name.

        Args:
            spout_name (str): Name of the spout to run.
        """
        spout = self.geniusfile.spouts.get(spout_name)
        if not spout:
            self.log.error(emoji.emojize(f":x: Spout {spout_name} not found."))
            return

        spout_ctl = self.spout_ctls.get(spout_name)
        if not spout_ctl:
            self.log.error(emoji.emojize(f":x: SpoutCtl for {spout_name} not found."))
            return

        self.log.info(emoji.emojize(f":rocket: Running spout {spout_name}..."))
        flat_args = [
            "rise",
            spout.output.type,
            spout.state.type,
            spout.method,
        ] + self._convert_spout(spout)

        parser = argparse.ArgumentParser()
        self.spout_ctls[spout_name].create_parser(parser)
        try:
            namespace_args = parser.parse_args(flat_args)
            spout_ctl.run(namespace_args)
        except Exception as e:
            self.log.exception(f"Could not execute: {e}")
            parser.print_help()

    def run_bolt(self, bolt_name: str):
        """
        Run a specific bolt based on its name.

        Args:
            bolt_name (str): Name of the bolt to run.
        """
        bolt = self.geniusfile.bolts.get(bolt_name)
        if not bolt:
            self.log.error(emoji.emojize(f":x: Bolt {bolt_name} not found."))
            return

        # Resolve reference if input type is "spout" or "bolt"
        if bolt.input.type in ["spout", "bolt"]:
            if not bolt.input.args or not bolt.input.args.name:
                raise ValueError(emoji.emojize(f"Need referenced spouts or bolt to be mentioned here {bolt.input}"))
            ref_name = bolt.input.args.name
            resolved_output = self.resolve_reference(bolt.input.type, ref_name)
            if not resolved_output:
                self.log.error(emoji.emojize(f":x: Failed to resolve reference for bolt {bolt_name}."))
                return
            bolt.input.type = resolved_output.type  # Set the resolved output type as the bolt's input type
            bolt.input.args = resolved_output.args  # Set the resolved output args as the bolt's input args

        bolt_ctl = self.bolt_ctls.get(bolt_name)
        if not bolt_ctl:
            self.log.error(emoji.emojize(f":x: BoltCtl for {bolt_name} not found."))
            return

        self.log.info(emoji.emojize(f":rocket: Running bolt {bolt_name}..."))
        flat_args = [
            "rise",
            bolt.input.type,
            bolt.output.type,
            bolt.state.type,
            bolt.method,
        ] + self._convert_bolt(bolt)

        # TODO: choosing this weird approach helps us build validations at argparser
        # and print argparser's help in case of problems in yaml?
        parser = argparse.ArgumentParser()
        self.bolt_ctls[bolt_name].create_parser(parser)
        namespace_args = parser.parse_args(flat_args)
        bolt_ctl.run(namespace_args)

    def resolve_reference(self, input_type: str, ref_name: str):
        """
        Resolve the reference of a bolt's input based on the input type (spout or bolt).

        Args:
            input_type (str): Type of the input ("spout" or "bolt").
            ref_name (str): Name of the spout or bolt to refer to.

        Returns:
            Output: The output data of the referred spout or bolt.
        """
        if input_type == "spout":
            referred_spout = self.geniusfile.spouts.get(ref_name)
            if not referred_spout:
                self.log.error(emoji.emojize(f":x: Referred spout {ref_name} not found."))
                return None
            return referred_spout.output
        elif input_type == "bolt":
            referred_bolt = self.geniusfile.bolts.get(ref_name)
            if not referred_bolt:
                self.log.error(emoji.emojize(f":x: Referred bolt {ref_name} not found."))
                return None
            return referred_bolt.output
        else:
            self.log.error(emoji.emojize(f":x: Invalid reference type {input_type}."))
            return None

    @typing.no_type_check
    def _convert_spout(self, spout: Spout) -> List[str]:
        spout_args = []

        # Convert output
        if spout.output.type == "batch":
            spout_args.append(f"--output_folder={spout.output.args.folder}")
            spout_args.append(f"--output_s3_bucket={spout.output.args.bucket}")
            spout_args.append(f"--output_s3_folder={spout.output.args.folder}")
        elif spout.output.type == "streaming":
            spout_args.append(f"--output_kafka_topic={spout.output.args.output_topic}")
            spout_args.append(f"--output_kafka_cluster_connection_string={spout.output.args.kafka_servers}")
        elif spout.output.type == "stream_to_batch":
            spout_args.append(f"--output_folder={spout.output.args.folder}")
            spout_args.append(f"--output_s3_bucket={spout.output.args.bucket}")
            spout_args.append(f"--output_s3_folder={spout.output.args.folder}")
            spout_args.append(f"--buffer_size={spout.output.args.buffer_size}")

        # Convert state
        if spout.state.type == "redis":
            spout_args.append(f"--redis_host={spout.state.args.redis_host}")
            spout_args.append(f"--redis_port={spout.state.args.redis_port}")
            spout_args.append(f"--redis_db={spout.state.args.redis_db}")
        elif spout.state.type == "postgres":
            spout_args.append(f"--postgres_host={spout.state.args.postgres_host}")
            spout_args.append(f"--postgres_port={spout.state.args.postgres_port}")
            spout_args.append(f"--postgres_user={spout.state.args.postgres_user}")
            spout_args.append(f"--postgres_password={spout.state.args.postgres_password}")
            spout_args.append(f"--postgres_database={spout.state.args.postgres_database}")
            spout_args.append(f"--postgres_table={spout.state.args.postgres_table}")
        elif spout.state.type == "dynamodb":
            spout_args.append(f"--dynamodb_table_name={spout.state.args.dynamodb_table_name}")
            spout_args.append(f"--dynamodb_region_name={spout.state.args.dynamodb_region_name}")
        elif spout.state.type == "prometheus":
            spout_args.append(f"--prometheus_gateway={spout.state.args.prometheus_gateway}")

        return spout_args

    @typing.no_type_check
    def _convert_bolt(self, bolt: Bolt) -> List[str]:
        bolt_args = []

        # Convert input
        if bolt.input.type == "batch":
            bolt_args.append(f"--input_folder={bolt.input.args.folder}")
            bolt_args.append(f"--input_s3_bucket={bolt.input.args.bucket}")
            bolt_args.append(f"--input_s3_folder={bolt.input.args.folder}")
        elif bolt.input.type == "streaming":
            bolt_args.append(f"--input_kafka_topic={bolt.input.args.input_topic}")
            bolt_args.append(f"--input_kafka_consumer_group_id={bolt.input.args.group_id}")
            bolt_args.append(f"--input_kafka_cluster_connection_string={bolt.input.args.kafka_servers}")
            bolt_args.append(f"--input_kafka_consumer_group_id={bolt.input.args.group_id}")
        elif bolt.input.type == "batch_to_stream":
            bolt_args.append(f"--input_folder={bolt.input.args.folder}")
            bolt_args.append(f"--input_s3_bucket={bolt.input.args.bucket}")
            bolt_args.append(f"--input_s3_folder={bolt.input.args.folder}")
        elif bolt.input.type == "stream_to_batch":
            bolt_args.append(f"--input_kafka_topic={bolt.input.args.input_topic}")
            bolt_args.append(f"--input_kafka_consumer_group_id={bolt.input.args.group_id}")
            bolt_args.append(f"--input_kafka_cluster_connection_string={bolt.input.args.kafka_servers}")
            bolt_args.append(f"--input_kafka_consumer_group_id={bolt.input.args.group_id}")
            bolt_args.append(f"--buffer_size={bolt.output.args.buffer_size}")

        # Convert output
        if bolt.output.type == "batch":
            bolt_args.append(f"--output_folder={bolt.output.args.folder}")
            bolt_args.append(f"--output_s3_bucket={bolt.output.args.bucket}")
            bolt_args.append(f"--output_s3_folder={bolt.output.args.folder}")
        elif bolt.output.type == "streaming":
            bolt_args.append(f"--output_kafka_topic={bolt.output.args.output_topic}")
            bolt_args.append(f"--output_kafka_cluster_connection_string={bolt.output.args.kafka_servers}")
        elif bolt.output.type == "stream_to_batch":
            bolt_args.append(f"--output_folder={bolt.output.args.folder}")
            bolt_args.append(f"--output_s3_bucket={bolt.output.args.bucket}")
            bolt_args.append(f"--output_s3_folder={bolt.output.args.folder}")
            bolt_args.append(f"--buffer_size={bolt.output.args.buffer_size}")

        # Convert state
        if bolt.state.type == "redis":
            bolt_args.append(f"--redis_host={bolt.state.args.redis_host}")
            bolt_args.append(f"--redis_port={bolt.state.args.redis_port}")
            bolt_args.append(f"--redis_db={bolt.state.args.redis_db}")
        elif bolt.state.type == "postgres":
            bolt_args.append(f"--postgres_host={bolt.state.args.postgres_host}")
            bolt_args.append(f"--postgres_port={bolt.state.args.postgres_port}")
            bolt_args.append(f"--postgres_user={bolt.state.args.postgres_user}")
            bolt_args.append(f"--postgres_password={bolt.state.args.postgres_password}")
            bolt_args.append(f"--postgres_database={bolt.state.args.postgres_database}")
            bolt_args.append(f"--postgres_table={bolt.state.args.postgres_table}")
        elif bolt.state.type == "dynamodb":
            bolt_args.append(f"--dynamodb_table_name={bolt.state.args.dynamodb_table_name}")
            bolt_args.append(f"--dynamodb_region_name={bolt.state.args.dynamodb_region_name}")
        elif bolt.state.type == "prometheus":
            bolt_args.append(f"--prometheus_gateway={bolt.state.args.prometheus_gateway}")

        return bolt_args
