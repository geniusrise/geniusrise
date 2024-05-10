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

import inspect
import logging
import uuid
from abc import ABC
from typing import Any, List, Optional, Tuple

from prettytable import PrettyTable
from termcolor import colored  # type: ignore

from geniusrise.core.data import Input, Output


class Task(ABC):
    """
    🛠️ **Task**: Class for managing tasks.

    This class provides a foundation for creating and managing tasks. Each task has a unique identifier and can be associated with specific input and output data.

    ## Attributes:
    - `id` (uuid.UUID): Unique identifier for the task.
    - `input` (Input): Configuration for input data.
    - `output` (Output): Configuration for output data.

    ## Usage:
    ```python
    task = Task()
    task.execute("fetch_data")
    ```

    !!! note
        Extend this class to implement specific task functionalities.
    """

    input: Input
    output: Output

    def __init__(self, id: Optional[str] = None) -> None:
        """
        Initialize a new task.

        Args:
            input (Input): Configuration for input data.
            output (Output): Configuration for output data.
        """
        self.id = str(self.__class__.__name__) + "--" + (id if id else str(uuid.uuid4()))
        self.log = logging.getLogger(self.__class__.__name__)
        self.log.info(f"🚀 Initialized Task with ID: {self.id}")

    def __repr__(self) -> str:
        """
        Return a string representation of the task.

        Returns:
            str: A string representation of the task.
        """
        return f"Task(id={self.id}, input={self.input}, output={self.output})"

    def execute(self, method_name: str, *args, **kwargs) -> Any:
        """
        🚀 Execute a given fetch_* method if it exists.

        Args:
            method_name (str): The name of the fetch_* method to execute.
            *args: Positional arguments to pass to the method.
            **kwargs: Keyword arguments to pass to the method.

        Returns:
            Any: The result of the fetch_* method, or None if the method does not exist.

        Raises:
            AttributeError: If the specified method doesn't exist.
        """
        method = getattr(self, method_name, None)
        if callable(method):
            return method(*args, **kwargs)
        else:
            self.log.exception(f"🚫 Method '{method_name}' not found!")
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{method_name}'")

    @staticmethod
    def get_methods(cls) -> List[Tuple[str, List[str], Optional[str]]]:
        """
        📜 Get all the fetch_* methods and their parameters along with their default values and docstrings.

        Returns:
            List[Tuple[str, List[str], str]]: A list of tuples, where each tuple contains the name of a fetch_* method,
            a list of its parameters along with their default values, and its docstring.
        """
        fetch_methods = []
        for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
            if name.startswith("fetch_"):
                params = inspect.signature(method).parameters
                params_str = [
                    f"{name}={param.default if param.default is not param.empty else ''}"
                    for name, param in params.items()
                ]
                docstring = inspect.getdoc(method)
                fetch_methods.append((name, params_str, docstring))
        return fetch_methods

    @staticmethod
    def print_help(cls) -> None:
        """
        🖨️ Pretty print the fetch_* methods and their parameters along with their default values and docstrings.
        Also prints the class's docstring and __init__ parameters.
        """
        # Print class docstring
        print(cls.__name__, colored(inspect.getdoc(cls) if inspect.getdoc(cls) else "", "green"))  # type: ignore

        # Print fetch_* methods
        fetch_methods = cls.get_methods(cls)
        if fetch_methods:
            table = PrettyTable(align="l")
            table.field_names = [
                colored("Method", "cyan"),
                colored("Parameters", "cyan"),
                colored("Description", "cyan"),
            ]
            for name, params, docstring in fetch_methods:
                parameters = [_p.replace("=", "") for _p in params if "self" not in _p]
                table.add_row(
                    [colored(name, "yellow"), "\n".join(parameters), docstring],
                    divider=True,
                )
            print(table)
        else:
            print(colored("No fetch_* methods found.", "red"))
