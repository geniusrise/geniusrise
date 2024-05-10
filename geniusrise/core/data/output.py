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

from abc import ABC, abstractmethod
from typing import Any


class Output(ABC):
    """
    Abstract base class for managing output data.
    """

    @abstractmethod
    def save(self, data: Any, **kwargs) -> None:
        """
        Save data to a file or ingest it into a Kafka topic.

        Args:
            data (Any): The data to save or ingest.
            filename (str): The filename to use when saving the data to a file.
        """

    @abstractmethod
    def flush(self):
        """
        Flush the output. This method should be implemented by subclasses.
        """
