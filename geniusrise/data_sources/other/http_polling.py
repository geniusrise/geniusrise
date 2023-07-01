import logging
import time

import requests

from geniusrise.data_sources.streaming import StreamingDataFetcher


class RESTAPIPollingDataFetcher(StreamingDataFetcher):
    def __init__(self, url: str, method: str, handler=None, state_manager=None, interval: int = 60, body=None):
        super().__init__(handler, state_manager)
        self.url = url
        self.method = method
        self.interval = interval
        self.body = body

    def listen(self):
        """
        Start polling the REST API for data.
        """
        while True:
            try:
                response = getattr(requests, self.method.lower())(self.url, json=self.body)
                response.raise_for_status()
                data = response.json()
                self.save(data, "rest_api.json")
                self.update_state("success")
            except Exception as e:
                logging.error(f"Error fetching data from REST API: {e}")
                self.update_state("failure")
            time.sleep(self.interval)
