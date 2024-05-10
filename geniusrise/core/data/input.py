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

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Union

from retrying import retry


class Input(ABC):
    """
    Abstract class for managing input data.

    Attributes:
        log (logging.Logger): Logger instance.
    """

    def __init__(self) -> None:
        self.log = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def get(self) -> Any:
        """
        Abstract method to get data from the input source.

        Returns:
            Any: The data from the input source.
        """

    @abstractmethod
    def collect_metrics(self) -> Dict[str, float]:
        """
        Collect metrics like latency.

        Returns:
            Dict[str, float]: A dictionary containing metrics.
        """

    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def retryable_get(self) -> Any:
        """
        Retryable get method.

        Returns:
            Any: The data from the input source.
        """
        return self.get()

    @abstractmethod
    def compose(self, *inputs: "Input") -> Union[bool, str]:
        """
        Compose multiple inputs.

        Args:
            inputs (Input): Variable number of Input instances.

        Returns:
            Union[bool, str]: True if successful, error message otherwise.
        """

    def __add__(self, *inputs: "Input") -> Union[bool, str]:
        """
        Compose multiple inputs.

        Args:
            inputs (Input): Variable number of Input instances.

        Returns:
            Union[bool, str]: True if successful, error message otherwise.
        """
        return self.compose(*inputs)
