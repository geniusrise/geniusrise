import paho.mqtt.client as mqtt
import json
import logging
from typing import Optional, Callable
from geniusrise_cli.data_sources.base import StreamingDataFetcher


class MQTTDataFetcher(StreamingDataFetcher):
    def __init__(self, topic: str, port: int = 1883, handler: Optional[Callable] = None, state_manager=None):
        super().__init__(handler, state_manager)
        self.topic = topic
        self.log = logging.getLogger(__name__)
        self.port = port

    def __repr__(self) -> str:
        return f"MQTT data fetcher: {self.__class__.__name__}"

    def _on_connect(self, client, userdata, flags, rc):
        """
        Callback function that is called when the client connects to the broker.

        :param client: MQTT client instance.
        :param userdata: Private user data as set in Client() or userdata_set().
        :param flags: Response flags sent by the broker.
        :param rc: Connection result.
        """
        self.log.info(f"Connected with result code {rc}")
        client.subscribe(self.topic)

    def _on_message(self, client, userdata, msg):
        """
        Callback function that is called when a message is received.

        :param client: MQTT client instance.
        :param userdata: Private user data as set in Client() or userdata_set().
        :param msg: An instance of MQTTMessage.
        """
        self.log.info(f"Received message from MQTT: {msg.payload}")
        self.save(json.loads(msg.payload), f"{self.topic}.json")
        self.update_state("success")

    def listen(self):
        """
        Start listening for data from the MQTT broker.
        """
        try:
            self.log.info("Starting MQTT listener...")
            client = mqtt.Client()
            client.on_connect = self._on_connect
            client.on_message = self._on_message
            client.connect("localhost", self.port, 60)
            self.log.info("Waiting for messages. To exit press CTRL+C")
            client.loop_forever()
        except Exception as e:
            self.log.error(f"Error listening to MQTT: {e}")
            self.update_state("failure")
