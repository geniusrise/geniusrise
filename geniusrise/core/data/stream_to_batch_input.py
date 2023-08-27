import tempfile
import os
import json
from typing import List
from kafka import KafkaMessage

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
    """

    def __init__(
        self,
        input_topic: str,
        kafka_cluster_connection_string: str,
        buffer_size: int = 1000,
        group_id: str = "geniusrise",
    ) -> None:
        """
        Initialize a new buffered streaming input configuration.

        Args:
            input_topic (str): Kafka topic to consume data.
            kafka_cluster_connection_string (str): Kafka cluster connection string.
            buffer_size (int): Number of messages to buffer.
            group_id (str, optional): Kafka consumer group id. Defaults to "geniusrise".
        """
        StreamingInput.__init__(self, input_topic, kafka_cluster_connection_string, group_id)
        self.buffer_size = buffer_size
        self.temp_folder = tempfile.mkdtemp()

    def buffer_messages(self) -> List[KafkaMessage]:
        """
        📥 Buffer messages from Kafka into local memory.

        Returns:
            List[KafkaMessage]: List of buffered Kafka messages.
        """
        buffered_messages = []
        for i, message in enumerate(self.iterator()):
            if i >= self.buffer_size:
                break
            buffered_messages.append(message)
        return buffered_messages

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

        Returns:
            str: The temporary folder containing buffered messages.

        Raises:
            Exception: If no input source or consumer is specified.
        """
        buffered_messages = self.buffer_messages()
        self.store_to_temp(buffered_messages)
        return self.temp_folder
