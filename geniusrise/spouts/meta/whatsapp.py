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

import threading

from flask import Flask, request

from geniusrise.data_sources.stream import StreamingDataFetcher


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
