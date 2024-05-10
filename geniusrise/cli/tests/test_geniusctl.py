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

# import pytest
# from geniusrise.cli.geniusctl import GeniusCtl
# from argparse import Namespace


# @pytest.fixture
# def genius_ctl():
#     return GeniusCtl()


# def test_initialization(genius_ctl):
#     assert genius_ctl is not None, "Initialization failed"
#     assert genius_ctl.discover is not None, "Discover object not initialized"
#     assert isinstance(genius_ctl.spouts, dict), "Spouts should be a dictionary"
#     assert isinstance(genius_ctl.bolts, dict), "Bolts should be a dictionary"


# def test_discovery(genius_ctl):
#     assert len(genius_ctl.spouts) > 0, "No spouts were discovered"
#     assert len(genius_ctl.bolts) > 0, "No bolts were discovered"


# def test_list_spouts_and_bolts(genius_ctl, capsys):
#     genius_ctl.list_spouts_and_bolts()
#     captured = capsys.readouterr()
#     for spout_name in genius_ctl.spouts.keys():
#         assert spout_name in captured.out, f"Spout {spout_name} was not listed"
#     for bolt_name in genius_ctl.bolts.keys():
#         assert bolt_name in captured.out, f"Bolt {bolt_name} was not listed"


# def test_run_spout_command(genius_ctl, capsys):
#     # Mocking a spout command
#     spout_name = list(genius_ctl.spouts.keys())[0]
#     args = Namespace(command=spout_name)
#     genius_ctl.run(args)
#     captured = capsys.readouterr()
#     assert f"Running command: {spout_name}" in captured.out


# def test_run_bolt_command(genius_ctl, capsys):
#     # Mocking a bolt command
#     bolt_name = list(genius_ctl.bolts.keys())[0]
#     args = Namespace(command=bolt_name)
#     genius_ctl.run(args)
#     captured = capsys.readouterr()
#     assert f"Running command: {bolt_name}" in captured.out


# def test_run_yaml_command(genius_ctl, capsys):
#     args = Namespace(command="yaml")
#     genius_ctl.run(args)
#     captured = capsys.readouterr()
#     assert "Running command: yaml" in captured.out


# def test_run_help_command(genius_ctl, capsys):
#     args = Namespace(command="help", spout_or_bolt=None)
#     genius_ctl.run(args)
#     captured = capsys.readouterr()
#     assert "Running command: help" in captured.out


# def test_run_list_command(genius_ctl, capsys):
#     args = Namespace(command="list")
#     genius_ctl.run(args)
#     captured = capsys.readouterr()
#     assert "Running command: list" in captured.out


# def test_create_parser(genius_ctl):
#     parser = genius_ctl.create_parser()
#     assert parser is not None, "Parser creation failed"
#     assert parser.description == "Manage the geniusrise application."


# def test_cli(genius_ctl, monkeypatch, capsys):
#     # Mocking the argparse's parse_args method
#     def mock_parse_args():
#         return Namespace(command="list")

#     monkeypatch.setattr("argparse.ArgumentParser.parse_args", mock_parse_args)
#     genius_ctl.cli()
#     captured = capsys.readouterr()
#     assert "Running command: list" in captured.out
