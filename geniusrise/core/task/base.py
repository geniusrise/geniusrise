import inspect
import uuid
from abc import ABC
from typing import Any, List, Optional, Tuple

from prettytable import PrettyTable
from termcolor import colored  # type: ignore

from geniusrise.core.data import InputConfig, OutputConfig


class Task(ABC):
    input_config: InputConfig
    output_config: OutputConfig

    """
    Class for managing tasks.

    Attributes:
        id (uuid.UUID): Unique identifier for the task.
        input_config (InputConfig): Configuration for input data.
        output_config (OutputConfig): Configuration for output data.
    """

    def __init__(self):
        """
        Initialize a new task.

        Args:
            input_config (InputConfig): Configuration for input data.
            output_config (OutputConfig): Configuration for output data.
        """
        self.id = str(uuid.uuid4())

    def __repr__(self):
        """
        Return a string representation of the task.

        Returns:
            str: A string representation of the task.
        """
        return f"Task(id={self.id}, input_config={self.input_config}, output_config={self.output_config})"

    def execute(self, method_name: str, *args, **kwargs) -> Any:
        """
        Execute a given fetch_* method if it exists.

        Args:
            method_name (str): The name of the fetch_* method to execute.
            *args: Positional arguments to pass to the method.
            **kwargs: Keyword arguments to pass to the method.

        Returns:
            Any: The result of the fetch_* method, or None if the method does not exist.
        """
        method = getattr(self, method_name, None)
        if callable(method):
            return method(*args, **kwargs)
        else:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{method_name}'")

    def get_methods(self) -> List[Tuple[str, List[str], Optional[str]]]:
        """
        Get all the fetch_* methods and their parameters along with their default values and docstrings.

        Returns:
            List[Tuple[str, List[str], str]]: A list of tuples, where each tuple contains the name of a fetch_* method,
            a list of its parameters along with their default values, and its docstring.
        """
        fetch_methods = []
        for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if name.startswith("fetch_"):
                params = inspect.signature(method).parameters
                params_str = [
                    f"{name}={param.default if param.default is not param.empty else ''}"
                    for name, param in params.items()
                ]
                docstring = inspect.getdoc(method)
                fetch_methods.append((name, params_str, docstring))
        return fetch_methods

    def print_help(self):
        """
        Pretty print the fetch_* methods and their parameters along with their default values and docstrings.
        Also prints the class's docstring and __init__ parameters.
        """
        # Print class docstring
        print(self.__class__.__name__, colored(inspect.getdoc(self) if inspect.getdoc(self) else "", "green"))

        # Print fetch_* methods
        fetch_methods = self.get_methods()
        if fetch_methods:
            table = PrettyTable(align="l")
            table.field_names = [
                colored("Method", "cyan"),
                colored("Parameters", "cyan"),
                colored("Description", "cyan"),
            ]
            for name, params, docstring in fetch_methods:
                table.add_row([colored(name, "yellow"), "\n".join(params), docstring])
            print(table)
        else:
            print(colored("No fetch_* methods found.", "red"))
