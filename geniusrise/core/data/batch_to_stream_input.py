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
import os
import time
from collections import namedtuple
from queue import Queue
from threading import Thread
from typing import AsyncIterator, Callable, Dict, Iterator, Union

from .batch_input import BatchInput
from .streaming_input import StreamingInput

KafkaMessage = namedtuple("KafkaMessage", ["key", "value"])


class BatchToStreamingInput(StreamingInput, BatchInput):
    """
    🔄 BatchToStreamingInput: Manages converting batch data to streaming input.

    Inherits:
        StreamingInput: For Kafka streaming capabilities.
        BatchInput: For batch-like file operations.

    Usage:
    ```python
    config = BatchToStreamingInput("my_topic", "localhost:9094", "/path/to/input", "my_bucket", "s3/folder")
    iterator = config.stream_batch("example.json")
    for message in iterator:
        print(message)
    ```

    Note:
    - Ensure the Kafka cluster is running and accessible.
    """

    def __init__(
        self,
        input_folder: str,
        bucket: str,
        s3_folder: str,
        input_topic: str = "",
        kafka_cluster_connection_string: str = "",
        group_id: str = "geniusrise",
    ) -> None:
        """
        Initialize a new batch to streaming input data.

        Args:
            input_topic (str): Kafka topic to consume data.
            kafka_cluster_connection_string (str): Kafka cluster connection string.
            input_folder (str): Folder to read input files.
            bucket (str): S3 bucket name.
            s3_folder (str): Folder within the S3 bucket.
            group_id (str, optional): Kafka consumer group id. Defaults to "geniusrise".
        """
        self.log = logging.getLogger(self.__class__.__name__)
        BatchInput.__init__(self, input_folder, bucket, s3_folder)
        self.queue = Queue()  # type: ignore

    def _enqueue_batch_data(self):
        input_folder = self.input_folder
        for root, _, files in os.walk(input_folder):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                if os.path.isfile(file_path):
                    with open(file_path) as f:
                        item = json.loads(f.read())
                        kafka_message = KafkaMessage(key=None, value=item)
                        self.queue.put(kafka_message)

    def get(self):
        """
        🔄 Convert batch data from a file to a streaming iterator.

        Yields:
            Any: The next item from the batch data.

        Raises:
            Exception: If no Kafka consumer is available or an error occurs.
        """
        # Read the batch data from the file
        thread = Thread(target=self._enqueue_batch_data)
        thread.start()

        time.sleep(1)
        while True:
            if not self.queue.empty():
                yield self.queue.get()
            else:
                break

    def iterator(self) -> Iterator:
        """
        🔄 Iterator method for yielding data from the Kafka consumer.

        Yields:
            Kafka message: The next message from the Kafka consumer.

        Raises:
            Exception: If no Kafka consumer is available.
        """
        # Use the existing iterator from StreamingInput if available
        return self.get()

    async def async_iterator(self) -> AsyncIterator[KafkaMessage]:  # type: ignore
        """
        🔄 Asynchronous iterator method for yielding data from the Kafka consumer.

        Yields:
            KafkaMessage: The next message from the Kafka consumer.

        Raises:
            Exception: If no Kafka consumer is available.
        """
        pass  # type: ignore

    def ack(self) -> None:
        """
        ✅ Acknowledge the processing of a Kafka message.

        Args:
            message (KafkaMessage): The Kafka message to acknowledge.

        Raises:
            Exception: If an error occurs while acknowledging the message.
        """
        pass

    def close(self) -> None:
        """
        🚪 Close the Kafka consumer.

        Raises:
            Exception: If an error occurs while closing the consumer.
        """
        pass

    def seek(self, target_offset: int) -> None:
        pass

    def commit(self) -> None:
        pass

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
        try:
            for message in self.get():
                if filter_func(message):
                    yield message
        except Exception as e:
            self.log.exception(f"🚫 Failed to filter messages from Kafka consumer: {e}")
            raise

    def collect_metrics(self) -> Dict[str, Union[int, float]]:
        """
        📊 Collect metrics related to the Kafka consumer.

        Returns:
            Dict[str, Union[int, float]]: A dictionary containing metrics like latency.
        """
        return {
            "request_latency_avg": 0,
            "request_latency_max": 0,
        }
