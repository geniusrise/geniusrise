# import json
# from typing import Optional, Any
# from .streaming_output import StreamingOutput
# from .batch_output import BatchOutput

# TODO: this seems fucking useless, why would anyone want to do this

# class BatchToStreamingOutput(StreamingOutput, BatchOutput):
#     """
#     🔄 BatchToStreamingOutput: Manages converting batch data to streaming output.

#     Inherits:
#         StreamingOutput: For Kafka streaming capabilities.
#         BatchOutput: For batch-like file operations.

#     Usage:
#     ```python
#     config = BatchToStreamingOutput("my_topic", "localhost:9094", "/path/to/output", "my_bucket", "s3/folder")
#     config.save_batch_to_stream("example.json")
#     ```

#     Note:
#     - Ensure the Kafka cluster is running and accessible.
#     """

#     def __init__(self, output_topic: str, kafka_servers: str, output_folder: str, bucket: str, s3_folder: str) -> None:
#         """
#         Initialize a new batch to streaming output data.

#         Args:
#             output_topic (str): Kafka topic to ingest data.
#             kafka_servers (str): Kafka bootstrap servers.
#             output_folder (str): Folder to save output files.
#             bucket (str): S3 bucket name.
#             s3_folder (str): Folder within the S3 bucket.
#         """
#         StreamingOutput.__init__(self, output_topic, kafka_servers)
#         BatchOutput.__init__(self, output_folder, bucket, s3_folder)

#     def save(self, data: Any, filename: Optional[str] = None) -> None:
#         """
#         🔄 Convert batch data from a file to streaming data.

#         Args:
#             filename (str): The filename containing batch data.

#         Raises:
#             Exception: If no Kafka producer is available or an error occurs.
#         """
#         # Read the batch data from the file
#         if not filename:
#             raise Exception("No filename specified to save.")

#         batch_data_str = BatchOutput.read_file(self, filename)
#         batch_data = json.loads(batch_data_str)

#         # Send each item in the batch data to the Kafka topic
#         for item in batch_data:
#             super(StreamingOutput, self).save(item)
