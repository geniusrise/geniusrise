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

import logging
from typing import Any, AsyncIterator, Callable, Dict, Iterator, Union

from kafka import KafkaConsumer, TopicPartition

from .input import Input

KafkaMessage = dict


class KafkaConnectionError(Exception):
    """❌ Custom exception for kafka connection problems."""

    pass


class StreamingInput(Input):
    """
    📡 **StreamingInput**: Manages streaming input data.

    Attributes:
        input_topic (str): Kafka topic to consume data.
        consumer (KafkaConsumer): Kafka consumer for consuming data.

    Usage:
    ```python
    config = StreamingInput("my_topic", "localhost:9094")
    for message in config.iterator():
        print(message.value)
    ```

    Note:
    - Ensure the Kafka cluster is running and accessible.
    - Adjust the `group_id` if needed.
    """

    def __init__(
        self,
        input_topic: str,
        kafka_cluster_connection_string: str,
        group_id: str = "geniusrise",
        **kwargs,
    ) -> None:
        """
        💥 Initialize a new streaming input data.

        Args:
            input_topic (str): Kafka topic to consume data.
            kafka_cluster_connection_string (str): Kafka cluster connection string.
            group_id (str, optional): Kafka consumer group id. Defaults to "geniusrise".
        """
        super(Input, self).__init__()
        self.log = logging.getLogger(self.__class__.__name__)
        self.input_topic = input_topic
        self.kafka_cluster_connection_string = kafka_cluster_connection_string
        self.group_id = group_id

        try:
            self.consumer = KafkaConsumer(
                self.input_topic,
                bootstrap_servers=self.kafka_cluster_connection_string,
                group_id=self.group_id,
                max_poll_interval_ms=600000,  # 10 minutes
                session_timeout_ms=10000,  # 10 seconds
                **kwargs,
            )
        except Exception as e:
            self.log.exception(f"🚫 Failed to create Kafka consumer: {e}")
            raise KafkaConnectionError("Failed to connect to Kafka.")

    def __del__(self):
        self.close()

    def get(self) -> KafkaConsumer:
        """
        📥 Get data from the input topic.

        Returns:
            KafkaConsumer: The Kafka consumer.

        Raises:
            Exception: If no input source or consumer is specified.
        """
        if self.input_topic and self.consumer:
            try:
                return self.consumer
            except Exception as e:
                self.log.exception(f"🚫 Failed to consume from Kafka topic {self.input_topic}: {e}")
                raise
        else:
            raise KafkaConnectionError("No Kafka consumer available.")

    def iterator(self) -> Iterator:
        """
        🔄 Iterator method for yielding data from the Kafka consumer.

        Yields:
            Kafka message: The next message from the Kafka consumer.

        Raises:
            Exception: If no Kafka consumer is available.
        """
        if self.consumer:
            try:
                for message in self.consumer:
                    yield message
            except Exception as e:
                self.log.exception(f"🚫 Failed to iterate over Kafka consumer: {e}")
                raise
        else:
            raise KafkaConnectionError("No Kafka consumer available.")

    async def async_iterator(self) -> AsyncIterator[KafkaMessage]:
        """
        🔄 Asynchronous iterator method for yielding data from the Kafka consumer.

        Yields:
            KafkaMessage: The next message from the Kafka consumer.

        Raises:
            Exception: If no Kafka consumer is available.
        """
        if self.consumer:
            try:
                async for message in self.consumer:
                    yield message
            except Exception as e:
                self.log.exception(f"🚫 Failed to iterate over Kafka consumer: {e}")
                raise
        else:
            raise KafkaConnectionError("No Kafka consumer available.")

    def ack(self) -> None:
        """
        ✅ Acknowledge the processing of a Kafka message.

        Args:
            message (KafkaMessage): The Kafka message to acknowledge.

        Raises:
            Exception: If an error occurs while acknowledging the message.
        """
        try:
            self.consumer.commit()
            self.log.info("Acknowledged")
        except Exception as e:
            raise KafkaConnectionError(f"🚫 Failed to acknowledge message: {e}")

    def __iter__(self) -> Iterator:
        """
        🔄 Make the class iterable.
        """
        return self

    def __next__(self) -> Any:
        """
        🔥 Get the next message from the Kafka consumer.

        Raises:
            Exception: If no Kafka consumer is available or an error occurs.
        """
        if self.consumer:
            try:
                return next(self.consumer)
            except StopIteration:
                raise
            except Exception as e:
                self.log.exception(f"🚫 Failed to get next message from Kafka consumer: {e}")
                raise
        else:
            raise KafkaConnectionError("🚫 No Kafka consumer available.")

    def close(self) -> None:
        """
        🚪 Close the Kafka consumer.

        Raises:
            Exception: If an error occurs while closing the consumer.
        """
        if self.consumer:
            try:
                self.consumer.close()
            except Exception as e:
                self.log.debug(f"🚫 Failed to close Kafka consumer: {e}")

    def seek(self, target_offset: int) -> None:
        if self.consumer:
            try:
                # Check if consumer is subscribed to the topic
                if not self.consumer.subscription():
                    raise KafkaConnectionError("Consumer is not subscribed to any topic.")

                # Get topic partitions
                partitions = self.consumer.partitions_for_topic(self.input_topic)

                # Check if partitions are assigned
                if not partitions:
                    raise KafkaConnectionError("No partitions are assigned to the consumer.")

                assigned_partitions = self.consumer.assignment()

                # Iterate through partitions to find the one with the target offset
                for partition in partitions:
                    tp = TopicPartition(self.input_topic, partition)

                    # Check if the partition is assigned
                    if tp not in assigned_partitions:
                        continue

                    beginning_offsets = self.consumer.beginning_offsets([tp])
                    end_offsets = self.consumer.end_offsets([tp])

                    if beginning_offsets[tp] <= target_offset <= end_offsets[tp]:
                        self.consumer.seek(tp, target_offset)
                        return

                raise Exception(f"Offset {target_offset} not found in any assigned partition.")

            except Exception as e:
                raise KafkaConnectionError(f"Failed to seek Kafka consumer: {e}")

    def commit(self) -> None:
        """
        ✅ Manually commit offsets.

        Raises:
            Exception: If an error occurs while committing offsets.
        """
        if self.consumer:
            try:
                self.consumer.commit()
            except Exception as e:
                raise KafkaConnectionError(f"🚫 Failed to commit offsets: {e}")

    def filter_messages(self, filter_func: Callable) -> Iterator:
        """
        🔍 Filter messages from the Kafka consumer based on a filter function.

        Args:
            filter_func (callable): A function that takes a Kafka message and returns a boolean.

        Yields:
            Kafka message: The next message from the Kafka consumer that passes the filter.

        Raises:
            Exception: If no Kafka consumer is available or an error occurs.
        """
        if self.consumer:
            try:
                for message in self.consumer:
                    if filter_func(message):
                        yield message
            except Exception as e:
                self.log.exception(f"🚫 Failed to filter messages from Kafka consumer: {e}")
                raise
        else:
            raise KafkaConnectionError("🚫 No Kafka consumer available.")

    def collect_metrics(self) -> Dict[str, Union[int, float]]:
        """
        📊 Collect metrics related to the Kafka consumer.

        Returns:
            Dict[str, Union[int, float]]: A dictionary containing metrics like latency.
        """
        if self.consumer:
            kafka_metrics = self.consumer.metrics()
            # Extract relevant latency metrics
            request_latency_avg = kafka_metrics.get("request-latency-avg", 0)
            request_latency_max = kafka_metrics.get("request-latency-max", 0)

            return {
                "request_latency_avg": request_latency_avg,
                "request_latency_max": request_latency_max,
            }
        else:
            raise KafkaConnectionError("No Kafka consumer available.")
