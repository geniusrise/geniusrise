import json
import logging
from typing import Any

from kafka import KafkaProducer
from .output import OutputConfig


log = logging.getLogger(__name__)


class StreamingOutputConfig(OutputConfig):
    """
    Class for managing streaming output configurations.

    Attributes:
        output_topic (str): Kafka topic to ingest data.
        producer (KafkaProducer): Kafka producer for ingesting data.
    """

    def __init__(self, output_topic: str, kafka_servers: str):
        """
        Initialize a new streaming output configuration.

        Args:
            output_topic (str): Kafka topic to ingest data.
            kafka_servers (str): Kafka bootstrap servers.
        """
        self.output_topic = output_topic
        try:
            self.producer = KafkaProducer(bootstrap_servers=kafka_servers)
        except Exception as e:
            log.error(f"Failed to create Kafka producer: {e}")
            self.producer = None

    def save(self, data: Any, filename: str):
        """
        Ingest data into the Kafka topic.

        Args:
            data (Any): The data to ingest.
            filename (str): This argument is ignored for streaming outputs.
        """
        if self.producer:
            try:
                self.producer.send(self.output_topic, json.dumps(data))
                log.debug(f"Inserted the data into {self.output_topic} topic.")
            except Exception as e:
                log.error(f"Failed to send data to Kafka topic: {e}")
        else:
            log.error("No Kafka producer available.")

    def flush(self):
        """
        Flush the output by flushing the Kafka producer.
        """
        if self.producer:
            self.producer.flush()
        else:
            log.error("No Kafka producer available.")
