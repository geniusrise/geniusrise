# geniusrise
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

import requests

from geniusrise.data_sources.streaming_data_fetcher import StreamingDataFetcher


class FIUNotificationFetcher(StreamingDataFetcher):
    """
    A streaming data fetcher for the /FI/Notification endpoint.
    """

    def __init__(self, domain_name: str, handler=None, state_manager=None):
        super().__init__(handler, state_manager)
        self.endpoint = f"https://{domain_name}/FI/Notification"  # replace with your actual endpoint

    def listen(self):
        """
        Start listening for data from the /FI/Notification endpoint.
        """
        while True:
            try:
                response = requests.get(self.endpoint)
                response.raise_for_status()
                data = response.json()
                self.save(data, "fi_notification.json")
                self.update_state("success")
            except Exception as e:
                self.log.error(f"Error fetching data: {e}")
                self.update_state("failure")

    def __repr__(self) -> str:
        """
        Return a string representation of the streaming data fetcher.

        :return: A string representation of the streaming data fetcher.
        """
        return f"FI Notification fetcher: {self.__class__.__name__}"
