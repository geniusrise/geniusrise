from typing import Any, Iterator
import json

from .streaming_input import StreamingInput
from .batch_input import BatchInput


class BatchToStreamingInput(StreamingInput, BatchInput):
    """
    🔄 BatchToStreamingInput: Manages converting batch data to streaming input.

    Inherits:
        StreamingInput: For Kafka streaming capabilities.
        BatchInput: For batch-like file operations.

    Usage:
    ```python
    config = BatchToStreamingInput("my_topic", "localhost:9092", "/path/to/input", "my_bucket", "s3/folder")
    iterator = config.stream_batch("example.json")
    for message in iterator:
        print(message)
    ```

    Note:
    - Ensure the Kafka cluster is running and accessible.
    """

    def __init__(
        self,
        input_topic: str,
        kafka_cluster_connection_string: str,
        input_folder: str,
        bucket: str,
        s3_folder: str,
        group_id: str = "geniusrise",
    ) -> None:
        """
        Initialize a new batch to streaming input configuration.

        Args:
            input_topic (str): Kafka topic to consume data.
            kafka_cluster_connection_string (str): Kafka cluster connection string.
            input_folder (str): Folder to read input files.
            bucket (str): S3 bucket name.
            s3_folder (str): Folder within the S3 bucket.
            group_id (str, optional): Kafka consumer group id. Defaults to "geniusrise".
        """
        StreamingInput.__init__(self, input_topic, kafka_cluster_connection_string, group_id)
        BatchInput.__init__(self, input_folder, bucket, s3_folder)

    def stream_batch(self, filename: str) -> Iterator[Any]:
        """
        🔄 Convert batch data from a file to a streaming iterator.

        Args:
            filename (str): The filename containing batch data.

        Yields:
            Any: The next item from the batch data.

        Raises:
            Exception: If no Kafka consumer is available or an error occurs.
        """
        # Read the batch data from the file
        batch_data_str = super(BatchInput, self).read_file(filename)  # type: ignore
        batch_data = json.loads(batch_data_str)

        # Yield each item in the batch data as a streaming iterator
        for item in batch_data:
            yield item
