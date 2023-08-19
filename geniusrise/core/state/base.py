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
from typing import Dict, Optional


class State(ABC):
    """
    Abstract base class for a state manager.

    A state manager is responsible for getting and setting state.
    """

    @abstractmethod
    def get_state(self, key: str) -> Optional[Dict]:
        """
        Get the state associated with a key.

        Args:
            key (str): The key to get the state for.

        Returns:
            Dict: The state associated with the key.
        """
        pass

    @abstractmethod
    def set_state(self, key: str, value: Dict):
        """
        Set the state associated with a key.

        Args:
            key (str): The key to set the state for.
            value (Dict): The state to set.
        """
        pass
