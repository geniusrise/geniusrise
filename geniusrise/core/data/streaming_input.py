import logging

from kafka import KafkaConsumer
from typing import Callable

from .input import InputConfig

log = logging.getLogger(__name__)


class StreamingInputConfig(InputConfig):
    """
    Class for managing streaming input configurations.

    Attributes:
        input_topic (str): Kafka topic to consume data.
        consumer (KafkaConsumer): Kafka consumer for consuming data.
    """

    def __init__(self, input_topic: str, kafka_cluster_connection_string: str, group_id: str = "geniusrise"):
        """
        Initialize a new streaming input configuration.

        Args:
            input_topic (str): Kafka topic to consume data.
            kafka_cluster_connection_string (str): Kafka cluster connection string.
            group_id (str, optional): Kafka consumer group id. Defaults to "geniusrise".
        """
        self.input_topic = input_topic
        try:
            self.consumer = KafkaConsumer(
                self.input_topic, bootstrap_servers=kafka_cluster_connection_string, group_id=group_id
            )
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

    def iterator(self):
        """
        Iterator method for yielding data from the Kafka consumer.

        Yields:
            Kafka message: The next message from the Kafka consumer.
        """
        if self.consumer:
            try:
                for message in self.consumer:
                    yield message
            except Exception as e:
                log.error(f"Failed to iterate over Kafka consumer: {e}")
        else:
            log.error("No Kafka consumer available.")

    def __iter__(self):
        """
        Make the class iterable.
        """
        return self

    def __next__(self):
        """
        Get the next message from the Kafka consumer.
        """
        if self.consumer:
            try:
                return next(self.consumer)
            except StopIteration:
                raise
            except Exception as e:
                log.error(f"Failed to get next message from Kafka consumer: {e}")
                return None
        else:
            log.error("No Kafka consumer available.")
            return None

    def close(self):
        """
        Close the Kafka consumer.
        """
        if self.consumer:
            try:
                self.consumer.close()
            except Exception as e:
                log.error(f"Failed to close Kafka consumer: {e}")

    def seek(self, partition: int, offset: int):
        """
        Change the position from which the Kafka consumer reads.
        """
        if self.consumer:
            try:
                self.consumer.seek(partition, offset)
            except Exception as e:
                log.error(f"Failed to seek Kafka consumer: {e}")

    def commit(self):
        """
        Manually commit offsets.
        """
        if self.consumer:
            try:
                self.consumer.commit()
            except Exception as e:
                log.error(f"Failed to commit offsets: {e}")

    def filter_messages(self, filter_func: Callable):
        """
        Filter messages from the Kafka consumer based on a filter function.

        Args:
            filter_func (callable): A function that takes a Kafka message and returns a boolean.

        Yields:
            Kafka message: The next message from the Kafka consumer that passes the filter.
        """
        if self.consumer:
            try:
                for message in self.consumer:
                    if filter_func(message):
                        yield message
            except Exception as e:
                log.error(f"Failed to filter messages from Kafka consumer: {e}")
        else:
            log.error("No Kafka consumer available.")
