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
