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
from typing import Any, Callable, Iterator

from kafka import KafkaConsumer

from .input import Input


class StreamingInput(Input):
    """
    📡 **StreamingInput**: Manages streaming input configurations.

    Attributes:
        input_topic (str): Kafka topic to consume data.
        consumer (KafkaConsumer): Kafka consumer for consuming data.

    Usage:
    ```python
    config = StreamingInput("my_topic", "localhost:9092")
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
    ) -> None:
        """
        Initialize a new streaming input configuration.

        Args:
            input_topic (str): Kafka topic to consume data.
            kafka_cluster_connection_string (str): Kafka cluster connection string.
            group_id (str, optional): Kafka consumer group id. Defaults to "geniusrise".
        """
        self.input_topic = input_topic
        self.log = logging.getLogger(self.__class__.__name__)
        try:
            self.consumer = KafkaConsumer(
                self.input_topic,
                bootstrap_servers=kafka_cluster_connection_string,
                group_id=group_id,
            )
        except Exception as e:
            self.log.exception(f"🚫 Failed to create Kafka consumer: {e}")
            raise
            self.consumer = None

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
            self.log.exception("🚫 No input source specified.")
            raise

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
            self.log.exception("🚫 No Kafka consumer available.")
            raise

    async def async_iterator(self):
        async for message in self.consumer:
            yield message

    def __iter__(self) -> Iterator:
        """
        Make the class iterable.
        """
        return self

    def __next__(self) -> Any:
        """
        Get the next message from the Kafka consumer.

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
            self.log.exception("🚫 No Kafka consumer available.")
            raise

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
                self.log.exception(f"🚫 Failed to close Kafka consumer: {e}")
                raise

    def seek(self, partition: int, offset: int) -> None:
        """
        🔍 Change the position from which the Kafka consumer reads.

        Args:
            partition (int): The partition to seek.
            offset (int): The offset to seek to.

        Raises:
            Exception: If an error occurs while seeking.
        """
        if self.consumer:
            try:
                self.consumer.seek(partition, offset)
            except Exception as e:
                self.log.exception(f"🚫 Failed to seek Kafka consumer: {e}")
                raise

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
                self.log.exception(f"🚫 Failed to commit offsets: {e}")
                raise

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
            self.log.exception("🚫 No Kafka consumer available.")
            raise
