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
from typing import Any, List, Optional

import shortuuid

from .batch_output import BatchOutput
from .streaming_output import StreamingOutput


class StreamToBatchOutput(StreamingOutput, BatchOutput):
    """
    📦 StreamToBatchOutput: Manages buffered streaming output data.

    Inherits:
        StreamingOutput: For Kafka streaming capabilities.
        BatchOutput: For batch-like file operations.

    Attributes:
        buffer_size (int): Number of messages to buffer.
        buffered_messages (List[Any]): List of buffered messages.

    Usage:
    ```python
    config = StreamToBatchOutput("my_topic", "localhost:9094", "/path/to/output", "my_bucket", "s3/folder", buffer_size=100)
    config.save({"key": "value"})
    config.flush()
    ```
    """

    def __init__(
        self,
        output_folder: str,
        bucket: str,
        s3_folder: str,
        buffer_size: int,
        output_topic: str = "",
        kafka_servers: str = "",
    ) -> None:
        """
        💥 Initialize a new buffered streaming output data.

        Args:
            output_topic (str): Kafka topic to ingest data.
            kafka_servers (str): Kafka bootstrap servers.
            output_folder (str): Folder to save output files.
            bucket (str): S3 bucket name.
            s3_folder (str): Folder within the S3 bucket.
            buffer_size (int): Number of messages to buffer.
        """
        self.log = logging.getLogger(self.__class__.__name__)
        BatchOutput.__init__(self, output_folder=output_folder, bucket=bucket, s3_folder=s3_folder)
        self.buffer_size = buffer_size
        self.buffered_messages: List[Any] = []

    def save(self, data: Any, filename: Optional[str] = None) -> None:
        """
        📤 Buffer data into local memory until buffer size is reached.

        Args:
            data (Any): The data to buffer.
            filename (str): This argument is ignored for buffered streaming outputs.

        Raises:
            Exception: If no Kafka producer is available or an error occurs.
        """
        self.buffered_messages.append(data)
        if len(self.buffered_messages) >= self.buffer_size:
            self.flush()

    def flush(self) -> None:
        """
        🔄 Flush the output by saving buffered messages to a file and copying it to S3.

        Raises:
            Exception: If no Kafka producer is available or an error occurs.
        """
        if self.buffered_messages:
            # Generate a unique filename
            filename = str(shortuuid.uuid()) + ".json"
            # Save buffered messages to a file in the output folder
            BatchOutput.save(self, self.buffered_messages, filename)
            # Copy the file to S3
            self.copy_file_to_remote(filename)
            # Clear the buffer
            self.buffered_messages.clear()
