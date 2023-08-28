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

from abc import ABC, abstractmethod
from typing import Any, Optional


class Output(ABC):
    """
    Abstract base class for managing output data.
    """

    @abstractmethod
    def save(self, data: Any, filename: Optional[str] = None) -> None:
        """
        Save data to a file or ingest it into a Kafka topic.

        Args:
            data (Any): The data to save or ingest.
            filename (str): The filename to use when saving the data to a file.
        """
        pass

    @abstractmethod
    def flush(self):
        """
        Flush the output. This method should be implemented by subclasses.
        """
        pass
