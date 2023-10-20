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
from typing import Any

from kafka import KafkaProducer

from .output import Output


class StreamingOutput(Output):
    """
    📡 **StreamingOutput**: Manages streaming output data.

    Attributes:
        output_topic (str): Kafka topic to ingest data.
        producer (KafkaProducer): Kafka producer for ingesting data.

    Usage:
    ```python
    config = StreamingOutput("my_topic", "localhost:9094")
    config.save({"key": "value"}, "ignored_filename")
    config.flush()
    ```

    Note:
    - Ensure the Kafka cluster is running and accessible.
    """

    def __init__(self, output_topic: str, kafka_servers: str) -> None:
        """
        Initialize a new streaming output data.

        Args:
            output_topic (str): Kafka topic to ingest data.
            kafka_servers (str): Kafka bootstrap servers.
        """
        self.output_topic = output_topic
        self.log = logging.getLogger(self.__class__.__name__)
        try:
            self.producer = KafkaProducer(bootstrap_servers=kafka_servers)
        except Exception as e:
            self.log.exception(f"🚫 Failed to create Kafka producer: {e}")
            raise
            self.producer = None

    def __del__(self):
        self.close()

    def save(self, data: Any, **kwargs) -> None:
        """
        📤 Ingest data into the Kafka topic.

        Args:
            data (Any): The data to ingest.
            filename (str): This argument is ignored for streaming outputs.

        Raises:
            Exception: If no Kafka producer is available or an error occurs.
        """
        if self.producer:
            try:
                self.producer.send(self.output_topic, bytes(json.dumps(data).encode("utf-8")))
                self.log.debug(f"✅ Inserted the data into {self.output_topic} topic.")
            except Exception as e:
                self.log.exception(f"🚫 Failed to send data to Kafka topic: {e}")
                raise
        else:
            self.log.exception("🚫 No Kafka producer available.")
            raise

    def flush(self) -> None:
        """
        🔄 Flush the output by flushing the Kafka producer.

        Raises:
            Exception: If no Kafka producer is available.
        """
        if self.producer:
            self.producer.flush()
        else:
            self.log.exception("🚫 No Kafka producer available.")
            raise

    def close(self) -> None:
        """
        🚪 Close the Kafka producer.

        Raises:
            Exception: If no Kafka producer is available.
        """
        try:
            if self.producer:
                self.producer.close()
                self.producer = None
        except Exception as e:
            self.log.debug(f"🚫 Could not close kafka connection {e}.")

    def partition_available(self, partition: int) -> bool:
        """
        🧐 Check if a partition is available in the Kafka topic.

        Args:
            partition (int): The partition to check.

        Returns:
            bool: True if the partition is available, False otherwise.

        Raises:
            Exception: If no Kafka producer is available.
        """
        if self.producer:
            return partition in self.producer.partitions_for(self.output_topic)
        else:
            self.log.exception("🚫 No Kafka producer available.")
            raise
            return False

    def save_to_partition(self, value: Any, partition: int) -> None:
        """
        🎯 Send a message to a specific partition in the Kafka topic.

        Args:
            value (Any): The value of the message.
            partition (int): The partition to send the message to.

        Raises:
            Exception: If no Kafka producer is available or an error occurs.
        """
        if self.producer:
            try:
                self.producer.send(
                    self.output_topic,
                    value=bytes(json.dumps(value).encode("utf-8")),
                    partition=partition,
                )
                self.log.debug(f"✅ Inserted the message into partition {partition} of {self.output_topic} topic.")
            except Exception as e:
                self.log.exception(f"🚫 Failed to send message to Kafka topic: {e}")
                raise
        else:
            self.log.exception("🚫 No Kafka producer available.")
            raise
