import logging
import time
from typing import List

import boto3

from geniusrise_cli.data_sources.streaming import StreamingDataFetcher


class InspectorEventFetcher(StreamingDataFetcher):
    def __init__(self, wait: int = 600, handler=None, state_manager=None):
        super().__init__(handler, state_manager)
        self.inspector = boto3.client("inspector")
        self.log = logging.getLogger(__name__)
        self.wait = wait

    def listen(self):
        """
        Start listening for Inspector events.
        """
        while True:
            try:
                events = self.get_events()
                for event in events:
                    self.save(event, f"{event['arn']}.json")
            except Exception as e:
                self.log.error(f"Error fetching Inspector events: {e}")
            time.sleep(self.wait)  # wait for 60 seconds before fetching new events

    def get_events(self) -> List[dict]:
        """
        Get the Inspector events.

        :return: List of events.
        """
        events = []
        paginator = self.inspector.get_paginator("list_findings")
        try:
            for page in paginator.paginate():
                for finding_arn in page["findingArns"]:
                    finding = self.inspector.describe_findings(findingArns=[finding_arn])
                    events.extend(finding["findings"])
        except Exception as e:
            self.log.error(f"Error fetching Inspector events: {e}")
        return events
