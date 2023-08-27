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


class Input(ABC):
    """
    Abstract class for managing input configurations.
    """

    def __init__(self):
        self.log = logging.getLogger(self.__class__.__name__)
        self.start_time = None
        self.end_time = None

    @abstractmethod
    def get(self):
        """
        Abstract method to get data from the input source.

        Returns:
            The data from the input source.
        """
        pass

    def collect_metrics(self):
        latency = self.end_time - self.start_time
        return {"latency": latency}

    def validate_data(self, data):
        # TODO: This could be the start of integration to a data catalog like openmetadata
        return True

    def __compose(self):
        # TODO: can we make inputs to compose?
        # how would that work? we cannot exactly zip msgs in kafka cause order not guaranteed
        # we can do the "bunch everything and throw" like a batch fashion, but would that be useful?
        return True
