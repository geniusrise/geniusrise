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


class CloudWatchAlarmFetcher(StreamingDataFetcher):
    def __init__(self, wait: int = 600, handler=None, state_manager=None):
        super().__init__(handler, state_manager)
        self.cloudwatch = boto3.client("cloudwatch")
        self.log = logging.getLogger(__name__)
        self.wait = wait

    def listen(self):
        """
        Start listening for CloudWatch Alarms.
        """
        while True:
            try:
                alarms = self.get_alarms()
                for alarm in alarms:
                    self.save(alarm, f"{alarm['AlarmName']}.json")
            except Exception as e:
                self.log.error(f"Error fetching CloudWatch Alarms: {e}")
            time.sleep(self.wait)  # wait for 60 seconds before fetching new alarms

    def get_alarms(self) -> List[dict]:
        """
        Get the CloudWatch Alarms.

        :return: List of alarms.
        """
        alarms = []
        paginator = self.cloudwatch.get_paginator("describe_alarms")
        try:
            for page in paginator.paginate():
                alarms.extend(page["MetricAlarms"])
        except Exception as e:
            self.log.error(f"Error fetching CloudWatch Alarms: {e}")
        return alarms
