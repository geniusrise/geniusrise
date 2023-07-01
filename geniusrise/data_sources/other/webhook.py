import threading

from flask import Flask, request

from geniusrise.data_sources.streaming import StreamingDataFetcher


class WebhookDataFetcher(StreamingDataFetcher):
    def __init__(self, endpoint: str, handler=None, state_manager=None, port: int = 3000):
        super().__init__(handler, state_manager)
        self.app = Flask(__name__)
        self.endpoint = endpoint
        self.port = port

        @self.app.route(self.endpoint, methods=["GET", "POST", "PUT", "DELETE"])
        def handle_webhook():
            data = request.get_json()
            self.save(data, "webhook.json")
            self.update_state("success")
            return "", 200

    def listen(self):
        """
        Start listening for data from the webhook.
        """
        threading.Thread(target=self.app.run, kwargs={"host": "0.0.0.0", "port": self.port}).start()
