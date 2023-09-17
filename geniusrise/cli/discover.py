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

import fnmatch
import importlib
import inspect
import logging
import site
import os
import sys
from abc import ABCMeta
from typing import Any, Dict, List, Optional

import emoji  # type: ignore
import pydantic

from geniusrise.core import Bolt, Spout


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

    @staticmethod
    def get_geniusignore_patterns(directory: str) -> List[str]:
        """
        Read the .geniusignore file and return a list of patterns to ignore.

        Args:
            directory (str): Directory containing the .geniusignore file.

        Returns:
            List[str]: List of patterns to ignore.
        """
        geniusignore_path = os.path.join(directory, ".geniusignore")
        if not os.path.exists(geniusignore_path):
            return []

        with open(geniusignore_path, "r") as f:
            # Filter out empty lines and comments
            lines = [line.strip() for line in f.readlines() if line.strip() and not line.startswith("#")]
        return lines

    def scan_directory(self, directory: Optional[str] = None) -> Dict[str, Any]:
        """
        Scan for spouts/bolts in installed extensions and user's codebase.

        Args:
            directory (Optional[str]): Directory to scan for user-defined spouts/bolts.

        Returns:
            Dict[str, Any]: Discovered spouts/bolts.
        """
        directory = directory if directory else self.directory

        # Get patterns from .geniusignore
        geniusignore_patterns = self.get_geniusignore_patterns(directory)  # type: ignore

        # Discover user-defined spouts/bolts
        self.log.warning(emoji.emojize(f"🔍 Starting discovery in `{directory}`"))
        if directory:
            self.directory = directory
            for root, dirs, files in os.walk(self.directory):
                # Ignore directories starting with a .
                dirs[:] = [d for d in dirs if not d.startswith(".")]

                # Ignore directories matching .geniusignore patterns
                dirs[:] = [d for d in dirs if not any(fnmatch.fnmatch(d, pattern) for pattern in geniusignore_patterns)]

                if "__init__.py" in files:
                    try:
                        self.log.debug(f"Trying to import module in {root}")
                        module = self.import_module(root)
                        has_discovered = self.find_classes(module)
                        if not has_discovered:
                            del sys.modules[module.__name__]
                    except TypeError as e:
                        self.log.debug(f"Failed to import module at {root}: TypeError: {e}")
                    except Exception as e:
                        self.log.debug(f"Failed to import module at {root}: {e}")
                else:
                    self.log.debug(f"Ignoring directory {root}, no __init__.py found")

        return self.classes

    def discover_geniusrise_installed_modules(self) -> Dict[str, Any]:
        """
        Discover installed geniusrise modules from Python path directories.
        """
        self.log.warning(emoji.emojize("🔎 Discovering installed geniusrise modules..."))

        # Get the list of directories in the Python path
        python_path_dirs = site.getsitepackages() + [site.getusersitepackages()]
        self.classes = {}

        for directory in python_path_dirs:
            self.log.debug(f"Trying to import module in {directory}")
            try:
                # List all packages in the directory
                packages = os.listdir(directory)
            except FileNotFoundError:
                self.log.debug(f"Directory {directory} not found.")
                continue
            except PermissionError:
                self.log.debug(f"No permission to access directory {directory}.")
                continue

            # Filter packages that match the pattern geniusrise-*
            geniusrise_packages = fnmatch.filter(packages, "geniusrise_*")

            for package in geniusrise_packages:
                if "dist-info" in package:
                    continue
                package_path = os.path.join(directory, package)

                # Convert package_path to Python import path
                module_name = package_path.replace(directory + os.sep, "").replace(os.sep, ".")

                try:
                    module = importlib.import_module(module_name)
                    self.find_classes(module)
                except Exception as e:
                    self.log.debug(f"Failed to import module {module_name}: {e}")

        return self.classes

    def import_module(self, path: str):
        """
        Import a module given its path.

        Args:
            path (str): Path to the module.

        Returns:
            Any: Imported module.
        """
        directory = os.path.dirname(path)  # Get the directory containing the module
        if directory not in sys.path:
            sys.path.insert(0, directory)  # Add to sys.path

        relative_path = os.path.relpath(path, self.directory)
        module_path = relative_path.replace(os.sep, ".")
        if module_path.endswith("__init__"):
            module_path = module_path[:-9]  # remove trailing '__init__'

        module = importlib.import_module(module_path)
        return module

    def find_classes(self, module: Any) -> bool:
        """
        Discover spout/bolt classes in a module.

        Args:
            module (Any): Module to scan for spout/bolt classes.
        """
        has_discovered = False
        for name, obj in inspect.getmembers(module):
            discovered: DiscoveredSpout | DiscoveredBolt
            if inspect.isclass(obj) and issubclass(obj, Spout) and obj != Spout:
                discovered = DiscoveredSpout(name=name, klass=obj, init_args=self.get_init_args(obj))
                self.log.debug(emoji.emojize(f"🚀 Discovered Spout {discovered.name}"))
                self.classes[name] = discovered
                has_discovered = True
            elif inspect.isclass(obj) and issubclass(obj, Bolt) and obj != Bolt:
                discovered = DiscoveredBolt(name=name, klass=obj, init_args=self.get_init_args(obj))
                self.log.debug(emoji.emojize(f"⚡ Discovered Bolt {discovered.name}"))
                self.classes[name] = discovered
                has_discovered = True
        return has_discovered

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
