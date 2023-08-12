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

from abc import ABCMeta
import os
import pkg_resources  # type: ignore
import logging
import inspect
from typing import Dict, Any, Optional
from geniusrise.core import Spout, Bolt
import pydantic
import emoji  # type: ignore
import importlib


class DiscoveredSpout(pydantic.BaseModel):
    name: str
    klass: type
    init_args: dict


class DiscoveredBolt(pydantic.BaseModel):
    name: str
    klass: type
    init_args: dict


class Discover:
    def __init__(self, directory: Optional[str] = None):
        """Initialize the Discover class."""
        self.classes: Dict[str, Any] = {}
        self.log = logging.getLogger(self.__class__.__name__)
        self.directory = directory

    def scan_directory(self, directory: Optional[str] = None) -> Dict[str, Any]:
        """
        Scan for spouts/bolts in installed extensions and user's codebase.

        Args:
            directory (Optional[str]): Directory to scan for user-defined spouts/bolts.

        Returns:
            Dict[str, Any]: Discovered spouts/bolts.
        """
        directory = directory if directory else self.directory
        self.log.info(emoji.emojize("🔍 Starting discovery..."))

        # Discover installed extensions
        self.discover_installed_extensions()

        # Discover user-defined spouts/bolts
        if directory:
            self.directory = directory
            for root, _, files in os.walk(self.directory):
                if "__init__.py" in files:
                    module = self.import_module(root)
                    self.find_classes(module)
        return self.classes

    def discover_installed_extensions(self):
        """Discover installed geniusrise extensions."""
        self.log.info(emoji.emojize("🔎 Discovering installed extensions..."))
        for entry_point in pkg_resources.iter_entry_points(group="geniusrise.extensions"):
            try:
                module = entry_point.load()
                self.find_classes(module)
            except Exception as e:
                self.log.error(emoji.emojize(f"❌ Error discovering classes in {entry_point.name}: {e}"))

    def import_module(self, path: str):
        """
        Import a module given its path.

        Args:
            path (str): Path to the module.

        Returns:
            Any: Imported module.
        """
        project_root = os.path.abspath(os.path.join(self.directory, "../../../../"))  # type: ignore
        relative_path = os.path.relpath(path, project_root)
        module_path = relative_path.replace(os.sep, ".")
        if module_path.endswith("__init__"):
            module_path = module_path[:-9]  # remove trailing '__init__'

        self.log.info(emoji.emojize(f"📦 Importing module {module_path}..."))
        module = importlib.import_module(module_path)
        return module

    def find_classes(self, module: Any):
        """
        Discover spout/bolt classes in a module.

        Args:
            module (Any): Module to scan for spout/bolt classes.
        """
        for name, obj in inspect.getmembers(module):
            discovered: DiscoveredSpout | DiscoveredBolt
            if inspect.isclass(obj) and issubclass(obj, Spout) and obj != Spout:
                discovered = DiscoveredSpout(name=name, klass=obj, init_args=self.get_init_args(obj))
                self.log.info(emoji.emojize(f"🚀 Discovered Spout {discovered.name}"))
                self.classes[name] = discovered
            elif inspect.isclass(obj) and issubclass(obj, Bolt) and obj != Bolt:
                discovered = DiscoveredBolt(name=name, klass=obj, init_args=self.get_init_args(obj))
                self.log.info(emoji.emojize(f"⚡ Discovered Bolt {discovered.name}"))
                self.classes[name] = discovered

    def get_init_args(self, cls: type) -> Dict[str, Any]:
        """
        Extract initialization arguments of a class.

        Args:
            cls (type): Class to extract initialization arguments from.

        Returns:
            Dict[str, Any]: Initialization arguments.
        """
        init_signature = inspect.signature(cls.__init__)  # type: ignore
        init_params = init_signature.parameters
        init_args = {}
        for name, kind in init_params.items():
            if name == "self":
                continue
            if name == "kwargs" or name == "args":
                init_args["kwargs"] = Any
                continue
            if isinstance(kind.annotation, ABCMeta):
                init_args[name] = self.get_init_args(kind.annotation)
            elif kind.annotation == inspect.Parameter.empty:
                init_args[name] = "No type hint provided 😢"
            else:
                init_args[name] = kind.annotation
        return init_args
