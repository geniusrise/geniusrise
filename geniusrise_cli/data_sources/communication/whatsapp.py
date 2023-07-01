import threading

from flask import Flask, request

from geniusrise_cli.data_sources.stream import StreamingDataFetcher


class WhatsAppDataFetcher(StreamingDataFetcher):
    def __init__(self, handler=None, state_manager=None, port: int = 3000):
        super().__init__(handler, state_manager)
        self.app = Flask(__name__)
        self.port = port

        @self.app.route("/whatsapp", methods=["POST"])
        def handle_webhook():
            data = request.get_json()
            self.save(data, "whatsapp.json")
            self.update_state("success")
            return "", 200

    def listen(self):
        """
        Start listening for data from the WhatsApp webhook.
        """
        threading.Thread(target=self.app.run, kwargs={"host": "0.0.0.0", "port": self.port}).start()
