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
from typing import AsyncIterator, Union

import pyspark
from pyspark.sql import SparkSession
from pyspark.sql import Row
from streamz import Stream
from .batch_input import BatchInput
from .streaming_input import StreamingInput
from .batch_input import FileNotExistError
import pyflink
from pyflink.table import TableSchema, StreamTableEnvironment, EnvironmentSettings
from pyflink.datastream import StreamExecutionEnvironment

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

    def spark_df(self, spark: SparkSession) -> pyspark.sql.DataFrame:
        """
        Get a Spark DataFrame from the input folder.

        Returns:
            pyspark.sql.DataFrame: A Spark DataFrame where each row corresponds to a file in the input folder.

        Raises:
            FileNotExistError: If the input folder does not exist.
        """
        if not os.path.exists(self.input_folder):
            raise FileNotExistError(f"❌ Input folder {self.input_folder} does not exist.")

        def file_generator():
            for root, _, files in os.walk(self.input_folder):
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    with open(file_path, "r") as f:
                        content = f.read()
                    yield Row(filename=file_name, content=content)

        rdd = spark.sparkContext.parallelize(file_generator())
        df = spark.createDataFrame(rdd)

        return df

    def streamz_df(self):
        """
        Get a Streamz DataFrame from the input folder.

        Returns:
            streamz.dataframe.DataFrame: A Streamz DataFrame where each row corresponds to a file in the input folder.
        """
        stream = Stream()

        def emit_files():
            for root, _, files in os.walk(self.input_folder):
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    with open(file_path, "r") as f:
                        content = f.read()
                    stream.emit({"filename": file_name, "content": content})

        Thread(target=emit_files).start()

        sdf = stream.to_dataframe(example={"filename": "", "content": ""})

        return sdf

    def flink_table(self, table_schema: TableSchema) -> pyflink.table.Table:
        """
        Get a Flink Table from the input folder.

        Args:
            table_schema (TableSchema): The schema of the Flink table.

        Returns:
            pyflink.table.Table: A Flink Table where each row corresponds to a file in the input folder.

        Raises:
            FileNotExistError: If the input folder does not exist.
        """
        if not os.path.exists(self.input_folder):
            raise FileNotExistError(f"❌ Input folder {self.input_folder} does not exist.")

        try:
            # Initialize Flink environment
            env = StreamExecutionEnvironment.get_execution_environment()
            env_settings = EnvironmentSettings.new_instance().in_streaming_mode().use_blink_planner().build()
            table_env = StreamTableEnvironment.create(env, environment_settings=env_settings)

            # Create a Flink table based on the schema
            field_names = ",".join(table_schema.names)
            field_types = ",".join(table_schema.types)

            table_env.execute_sql(
                f"""
                CREATE TABLE batch_source (
                    {field_names} {field_types}
                ) WITH (
                    'connector' = 'filesystem',
                    'path' = '{self.input_folder}',
                    'format' = 'json'
                )
            """
            )

            # Create the Flink table
            flink_table = table_env.from_path("batch_source")

            return flink_table
        except Exception as e:
            self.log.error(f"❌ Failed to create Flink Table: {e}")
            raise

    def compose(self, *inputs: "StreamingInput") -> Union[bool, str]:  # type: ignore
        return False

    async def async_iterator(self) -> AsyncIterator[KafkaMessage]:  # type: ignore
        """
        🔄 Asynchronous iterator method for yielding data from the Kafka consumer.

        Yields:
            KafkaMessage: The next message from the Kafka consumer.

        Raises:
            Exception: If no Kafka consumer is available.
        """
        pass  # type: ignore

    def close(self) -> None:
        """
        🚪 Close the Kafka consumer.

        Raises:
            Exception: If an error occurs while closing the consumer.
        """

    def seek(self, target_offset: int) -> None:
        pass

    def commit(self) -> None:
        pass
