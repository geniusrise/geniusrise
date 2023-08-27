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

from typing import List
from kafka import KafkaMessage, KafkaError
import tempfile
import os
import json
from retrying import retry

from .streaming_input import StreamingInput
from .batch_input import BatchInput


class StreamToBatchInput(StreamingInput, BatchInput):
    """
    📦 StreamToBatchInput: Manages buffered streaming input configurations.

    Inherits:
        StreamingInput: For Kafka streaming capabilities.
        BatchInput: For batch-like file operations.

    Attributes:
        buffer_size (int): Number of messages to buffer.
        temp_folder (str): Temporary folder to store buffered messages.

    Usage:
    ```python
    config = StreamToBatchInput("my_topic", "localhost:9092", buffer_size=100)
    temp_folder = config.get()
    ```

    Note:
    - Ensure the Kafka cluster is running and accessible.
    - Adjust the `group_id` if needed.
    """

    def __init__(
        self,
        input_topic: str,
        kafka_cluster_connection_string: str,
        buffer_size: int = 1000,
        group_id: str = "geniusrise",
    ) -> None:
        """
        💥 Initialize a new buffered streaming input configuration.

        Args:
            input_topic (str): Kafka topic to consume data.
            kafka_cluster_connection_string (str): Kafka cluster connection string.
            buffer_size (int): Number of messages to buffer.
            group_id (str, optional): Kafka consumer group id. Defaults to "geniusrise".
        """
        StreamingInput.__init__(self, input_topic, kafka_cluster_connection_string, group_id)
        self.buffer_size = buffer_size
        self.temp_folder = tempfile.mkdtemp()

    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def buffer_messages(self) -> List[KafkaMessage]:
        """
        📥 Buffer messages from Kafka into local memory.
        ...
        """
        try:
            buffered_messages = []
            for i, message in enumerate(self.iterator()):
                if i >= self.buffer_size:
                    break
                buffered_messages.append(message)
            return buffered_messages
        except KafkaError as e:
            self.log.error(f"Kafka error occurred: {e}")
            raise

    def store_to_temp(self, messages: List[KafkaMessage]) -> None:
        """
        💾 Store buffered messages to temporary folder.

        Args:
            messages (List[KafkaMessage]): List of buffered Kafka messages.
        """
        for i, message in enumerate(messages):
            with open(os.path.join(self.temp_folder, f"message_{i}.json"), "w") as f:
                json.dump(message.value, f)

    def get(self) -> str:
        """
        📥 Get data from the input topic and buffer it into a temporary folder.
        ...
        """
        try:
            buffered_messages = self.buffer_messages()
            self.store_to_temp(buffered_messages)
            return self.temp_folder
        except Exception as e:
            self.log.error(f"An error occurred: {e}")
            raise

    def close(self) -> None:
        """
        🚪 Close the Kafka consumer and clean up resources.
        """
        try:
            self.consumer.close()
            # Additional resource cleanup logic here
        except Exception as e:
            self.log.error(f"Failed to close resources: {e}")
            raise
