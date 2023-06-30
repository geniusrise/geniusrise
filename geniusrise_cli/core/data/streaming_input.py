import logging

from kafka import KafkaConsumer
from .input import InputConfig

log = logging.getLogger(__name__)


class StreamingInputConfig(InputConfig):
    """
    Class for managing streaming input configurations.

    Attributes:
        input_topic (str): Kafka topic to consume data.
        consumer (KafkaConsumer): Kafka consumer for consuming data.
    """

    def __init__(self, input_topic: str, kafka_cluster_connection_string: str):
        """
        Initialize a new streaming input configuration.

        Args:
            input_topic (str): Kafka topic to consume data.
            kafka_cluster_connection_string (str): Kafka cluster connection string.
        """
        self.input_topic = input_topic
        try:
            self.consumer = KafkaConsumer(self.input_topic, bootstrap_servers=kafka_cluster_connection_string)
        except Exception as e:
            log.error(f"Failed to create Kafka consumer: {e}")
            self.consumer = None

    def get(self):
        """
        Get data from the input topic.

        Returns:
            KafkaConsumer: The Kafka consumer.
        """
        if self.input_topic and self.consumer:
            try:
                return self.consumer
            except Exception as e:
                log.error(f"Failed to consume from Kafka topic {self.input_topic}: {e}")
                return None
        else:
            log.error("No input source specified.")
            return None
