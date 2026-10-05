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

import fnmatch
import importlib
import inspect
import logging
import os
import site
import sys
from typing import Any, Dict, List, Optional, Type

import emoji  # type: ignore
import pydantic

from geniusrise.core import Task


class DiscoveredTask(pydantic.BaseModel):
    """
    Represents a discovered Task class.
    """

    name: str
    klass: type
    init_args: dict


class Discover:
    """
    Class for discovering Task classes in the codebase.
    """

    def __init__(self, directory: Optional[str] = None) -> None:
        """
        Initialize the Discover class.

        Args:
            directory: The directory to scan for components.
        """
        self.classes: Dict[str, Any] = {}
        self.log = logging.getLogger(self.__class__.__name__)
        self.directory = directory

    def is_task_subclass(self, cls: type) -> bool:
        """
        Check if a class is a subclass of Task.

        Args:
            cls: The class to check.

        Returns:
            True if the class is a subclass of Task, False otherwise.
        """
        try:
            return issubclass(cls, Task) and cls is not Task
        except TypeError:
            return False

    def scan_directory(self, directory: str) -> Dict[str, Any]:
        """
        Recursively scan a directory for Task classes.

        Args:
            directory: The directory to scan.

        Returns:
            A dictionary mapping component names to their discovered classes.
        """
        if not os.path.isdir(directory):
            self.log.warning(emoji.emojize(f":warning: {directory} is not a directory"))
            return {}

        self.log.info(emoji.emojize(f":magnifying_glass_tilted_right: Scanning directory {directory}..."))

        for root, _, files in os.walk(directory):
            python_files = [file for file in files if file.endswith(".py")]
            for file in python_files:
                file_path = os.path.join(root, file)
                module_name = os.path.splitext(file)[0]
                package_path = os.path.relpath(root, directory).replace(os.path.sep, ".")
                if package_path == ".":
                    package_path = ""
                else:
                    package_path = package_path + "."
                full_module_name = package_path + module_name

                try:
                    spec = importlib.util.spec_from_file_location(full_module_name, file_path)  # type: ignore
                    if spec is not None and spec.loader is not None:
                        module = importlib.util.module_from_spec(spec)  # type: ignore
                        sys.modules[full_module_name] = module
                        spec.loader.exec_module(module)
                        self.scan_module(module, full_module_name)
                    else:
                        self.log.debug(f"Failed to load module at {root}: spec or loader is None")
                except (ImportError, TypeError) as e:
                    self.log.debug(f"Failed to import module at {root}: {e}")

        return self.classes

    def scan_module(self, module: Any, module_name: str) -> None:
        """
        Scan a module for Task classes.

        Args:
            module: The module to scan.
            module_name: The name of the module.
        """
        for name, member in inspect.getmembers(module):
            if inspect.isclass(member):
                # Skip classes that are imported
                if member.__module__ != module_name:
                    continue

                # Check if it's a subclass of Task
                if self.is_task_subclass(member):
                    class_name = member.__name__.lower()
                    self.log.debug(emoji.emojize(f":check_mark: Found Task class {class_name} in {module_name}"))

                    # Extract initialization arguments
                    init_args = self.extract_init_args(member)

                    self.classes[class_name] = DiscoveredTask(
                        name=class_name,
                        klass=member,
                        init_args=init_args,
                    )

    def extract_init_args(self, cls: type) -> Dict[str, Any]:
        """
        Extract initialization arguments from a class.

        Args:
            cls: The class to extract arguments from.

        Returns:
            A dictionary of initialization arguments.
        """
        init_args = {}
        if hasattr(cls, "__init__"):
            init_signature = inspect.signature(cls.__init__)  # type: ignore
            for param_name, param in init_signature.parameters.items():
                if param_name not in ["self", "args", "kwargs"]:
                    init_args[param_name] = {
                        "default": param.default if param.default is not inspect.Parameter.empty else None,
                        "annotation": param.annotation if param.annotation is not inspect.Parameter.empty else None,
                    }
        return init_args

    def discover_geniusrise_installed_modules(self) -> Dict[str, Any]:
        """
        Discover Task classes in installed geniusrise modules.

        Returns:
            A dictionary mapping component names to their discovered classes.
        """
        self.log.info(emoji.emojize(":magnifying_glass_tilted_right: Scanning installed geniusrise modules..."))

        # Get all installed packages
        installed_packages = []
        for path in site.getsitepackages():
            try:
                for pkg in os.listdir(path):
                    if pkg.startswith("geniusrise") and not pkg.endswith((".dist-info", ".egg-info")):
                        installed_packages.append(pkg)
            except (FileNotFoundError, NotADirectoryError):
                pass

        for module_name in installed_packages:
            try:
                # Try to import the module
                self.log.debug(f"Trying to import module {module_name}")
                module = importlib.import_module(module_name)
                self.scan_package(module)
            except ImportError as e:
                self.log.debug(f"Failed to import module {module_name}: {e}")

        return self.classes

    def scan_package(self, package: Any) -> None:
        """
        Recursively scan a package for Task classes.

        Args:
            package: The package to scan.
        """
        # Direct scan of the package
        self.scan_module(package, package.__name__)

        # Recursively scan submodules
        if hasattr(package, "__path__"):
            package_path = package.__path__ if hasattr(package, "__path__") else []
            for directory in package_path:
                self.log.debug(f"Trying to import module in {directory}")
                try:
                    for item in os.listdir(directory):
                        root = os.path.join(directory, item)
                        if os.path.isdir(root) and os.path.exists(os.path.join(root, "__init__.py")):
                            # This is a package
                            self.log.debug(f"Trying to import module in {root}")
                            module_name = f"{package.__name__}.{item}"
                            try:
                                submodule = importlib.import_module(module_name)
                                self.scan_package(submodule)
                            except ImportError as e:
                                self.log.debug(f"Failed to import module at {root}: {e}")
                        elif item.endswith(".py") and item != "__init__.py":
                            # This is a module
                            module_name = f"{package.__name__}.{item[:-3]}"
                            try:
                                submodule = importlib.import_module(module_name)
                                self.scan_module(submodule, module_name)
                            except ImportError as e:
                                self.log.debug(f"Failed to import module at {root}: {e}")
                            except TypeError as e:
                                self.log.debug(f"Failed to import module at {root}: TypeError: {e}")
                except (FileNotFoundError, NotADirectoryError):
                    pass
