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

import json
import logging
from typing import Callable, Optional

import pika

from geniusrise.data_sources.base import StreamingDataFetcher


class RabbitMQDataFetcher(StreamingDataFetcher):
    def __init__(self, queue_name: str, handler: Optional[Callable] = None, state_manager=None):
        super().__init__(handler, state_manager)
        self.queue_name = queue_name
        self.log = logging.getLogger(__name__)

    def __repr__(self) -> str:
        return f"RabbitMQ data fetcher: {self.__class__.__name__}"

    def _callback(self, ch, method, properties, body):
        """
        Callback function that is called when a message is received.

        :param ch: Channel.
        :param method: Method.
        :param properties: Properties.
        :param body: Message body.
        """
        self.log.info(f"Received message from RabbitMQ: {body}")
        self.save(json.loads(body), f"{self.queue_name}.json")
        self.update_state("success")

    def listen(self):
        """
        Start listening for data from the RabbitMQ server.
        """
        try:
            self.log.info("Starting RabbitMQ listener...")
            connection = pika.BlockingConnection(pika.ConnectionParameters(host="localhost"))
            channel = connection.channel()
            channel.queue_declare(queue=self.queue_name)
            channel.basic_consume(queue=self.queue_name, on_message_callback=self._callback, auto_ack=True)
            self.log.info("Waiting for messages. To exit press CTRL+C")
            channel.start_consuming()
        except Exception as e:
            self.log.error(f"Error listening to RabbitMQ: {e}")
            self.update_state("failure")
