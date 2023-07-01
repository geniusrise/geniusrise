import logging
import time
from typing import List

import boto3

from geniusrise_cli.data_sources.streaming import StreamingDataFetcher


class CloudTrailEventFetcher(StreamingDataFetcher):
    def __init__(self, wait: int = 600, handler=None, state_manager=None):
        super().__init__(handler, state_manager)
        self.cloudtrail = boto3.client("cloudtrail")
        self.log = logging.getLogger(__name__)
        self.wait = wait

    def listen(self):
        """
        Start listening for CloudTrail events.
        """
        while True:
            try:
                events = self.get_events()
                for event in events:
                    self.save(event, f"{event['EventId']}.json")
            except Exception as e:
                self.log.error(f"Error fetching CloudTrail events: {e}")
            time.sleep(self.wait)  # wait for 60 seconds before fetching new events

    def get_events(self) -> List[dict]:
        """
        Get the CloudTrail events.

        :return: List of events.
        """
        events = []
        paginator = self.cloudtrail.get_paginator("lookup_events")
        try:
            for page in paginator.paginate():
                events.extend(page["Events"])
        except Exception as e:
            self.log.error(f"Error fetching CloudTrail events: {e}")
        return events
