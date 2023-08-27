import shortuuid
from typing import Any, Optional, List

from .streaming_output import StreamingOutput
from .batch_output import BatchOutput


class StreamToBatchOutput(StreamingOutput, BatchOutput):
    """
    📦 StreamToBatchOutput: Manages buffered streaming output configurations.

    Inherits:
        StreamingOutput: For Kafka streaming capabilities.
        BatchOutput: For batch-like file operations.

    Attributes:
        buffer_size (int): Number of messages to buffer.
        buffered_messages (List[Any]): List of buffered messages.

    Usage:
    ```python
    config = StreamToBatchOutput("my_topic", "localhost:9092", "/path/to/output", "my_bucket", "s3/folder", buffer_size=100)
    config.save({"key": "value"})
    config.flush()
    ```
    """

    def __init__(
        self, output_topic: str, kafka_servers: str, output_folder: str, bucket: str, s3_folder: str, buffer_size: int
    ) -> None:
        """
        💥 Initialize a new buffered streaming output configuration.

        Args:
            output_topic (str): Kafka topic to ingest data.
            kafka_servers (str): Kafka bootstrap servers.
            output_folder (str): Folder to save output files.
            bucket (str): S3 bucket name.
            s3_folder (str): Folder within the S3 bucket.
            buffer_size (int): Number of messages to buffer.
        """
        StreamingOutput.__init__(self, output_topic=output_topic, kafka_servers=kafka_servers)
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
