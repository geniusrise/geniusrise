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
