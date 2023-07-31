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
import time
from typing import List

import boto3

from geniusrise.data_sources.streaming import StreamingDataFetcher


class ConfigEventFetcher(StreamingDataFetcher):
    def __init__(self, wait: int = 600, handler=None, state_manager=None):
        super().__init__(handler, state_manager)
        self.config = boto3.client("config")
        self.log = logging.getLogger(__name__)
        self.wait = wait

    def listen(self):
        """
        Start listening for Config events.
        """
        while True:
            try:
                events = self.get_events()
                for event in events:
                    self.save(event, f"{event['configRuleName']}.json")
            except Exception as e:
                self.log.error(f"Error fetching Config events: {e}")
            time.sleep(self.wait)  # wait for 60 seconds before fetching new events

    def get_events(self) -> List[dict]:
        """
        Get the Config events.

        :return: List of events.
        """
        events = []
        paginator = self.config.get_paginator("describe_config_rules")
        try:
            for page in paginator.paginate():
                events.extend(page["ConfigRules"])
        except Exception as e:
            self.log.error(f"Error fetching Config events: {e}")
        return events
