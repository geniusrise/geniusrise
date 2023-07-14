from abc import ABCMeta
import os
import importlib
import inspect

import typing
from typing import Any

from geniusrise.core import Spout


class DirectoryScanner:
    def __init__(self, directory):
        self.directory = directory
        self.spout_classes = {}

    def scan_directory(self):
        for root, dirs, files in os.walk(self.directory):
            if "__init__.py" in files:
                module = self.import_module(root)
                self.find_spout_classes(module)
        return self.spout_classes

    def import_module(self, path):
        path = path.replace("/", ".")
        module = importlib.import_module(path)
        return module

    def find_spout_classes(self, module):
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and issubclass(obj, Spout) and obj != Spout:
                self.spout_classes[name] = {
                    "spout_name": name,
                    "spout_class": obj,
                    "spout_init_args": self.get_init_args(obj),
                }

    def get_init_args(self, cls):
        init_signature = inspect.signature(cls.__init__)

        hints = typing.get_type_hints(cls.__init__)

        init_params = init_signature.parameters
        init_args = {}
        for name, kind in init_params.items():
            # print(name, "=====", param, type(param))
            if name == "self":
                continue
            if name == "kwargs" or name == "args":
                init_args["kwargs"] = Any
                continue
            print(kind, type(kind), type(kind.annotation), isinstance(kind.annotation, ABCMeta), "---------------")
            if isinstance(kind.annotation, ABCMeta):
                init_args[name] = self.get_init_args(kind.annotation)
            elif kind.annotation == inspect.Parameter.empty:
                init_args[name] = "No type hint provided 😢"
            else:
                init_args[name] = kind.annotation
        print(init_args)
        return init_args
