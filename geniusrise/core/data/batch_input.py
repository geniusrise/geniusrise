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

import os
import shutil
import time
from typing import Dict, Optional, Union

import boto3
from pyspark.sql import Row, DataFrame
import shortuuid
import json
from kafka import KafkaConsumer

from .input import Input


class KafkaConnectionError(Exception):
    """❌ Custom exception for kafka connection problems."""


class FileNotExistError(Exception):
    """❌ Custom exception for file not existing."""


class BatchInput(Input):
    r"""
    📁 BatchInput: Manages batch input data.

    Attributes:
        input_folder (str): Folder to read input files.
        bucket (str): S3 bucket name.
        s3_folder (str): Folder within the S3 bucket.
        partition_scheme (Optional[str]): Partitioning scheme for S3, e.g., "year/month/day".

    Raises:
        FileNotExistError: If the file does not exist.

    Args:
        input_folder (str): Folder to read input files from.
        bucket (str): S3 bucket name.
        s3_folder (str): Folder within the S3 bucket.
        partition_scheme (Optional[str]): Partitioning scheme for S3, e.g., "year/month/day".

    Usage:

        # Initialize BatchInput
        ```python
        input = BatchInput("/path/to/input", "my_bucket", "s3/folder")
        ```

        ### Get the input folder
        ```python
        folder = input.get()
        ```

        ### Save a Spark DataFrame to the input folder
        ```python
        input.from_spark(my_dataframe)
        ```

        ### Compose multiple BatchInput instances
        ```python
        composed = input.compose(input1, input2)
        ```

        ### Copy files from S3 to the input folder
        ```python
        input.from_s3()
        ```

        # Collect metrics
        ```python
        metrics = input.collect_metrics()
        ```
    """

    def __init__(
        self,
        input_folder: str,
        bucket: str,
        s3_folder: str,
        partition_scheme: Optional[str] = None,
    ) -> None:
        """Initialize a new BatchInput instance."""
        super().__init__()
        self.input_folder = input_folder
        self.bucket = bucket
        self.s3_folder = s3_folder
        self.partition_scheme = partition_scheme
        self._metrics: Dict[str, float] = {}

    def get(self) -> str:
        """
        Get the input folder path.

        Returns:
            str: The path to the input folder.
        """
        return self.input_folder

    def from_spark(self, df: DataFrame) -> None:
        """
        Save the contents of a Spark DataFrame to the input folder with optional partitioning.

        Args:
            df (DataFrame): The Spark DataFrame to save.

        Raises:
            FileNotExistError: If the input folder does not exist.
        """
        if not os.path.exists(self.input_folder):
            raise FileNotExistError(f"❌ Input folder {self.input_folder} does not exist.")

        start_time = time.time()

        def save_row(row: Row) -> None:
            filename = row.filename if hasattr(row, "filename") else str(shortuuid.uuid())
            content = row.content if hasattr(row, "content") else json.dumps(row.asDict())

            if self.partition_scheme:
                partitioned_folder = self._get_partitioned_key(self.s3_folder)
                target_folder = os.path.join(self.input_folder, partitioned_folder)
                if not os.path.exists(target_folder):
                    os.makedirs(target_folder)
            else:
                target_folder = self.input_folder

            file_path = os.path.join(target_folder, filename)
            with open(file_path, "w") as f:
                f.write(content)

        df.foreach(save_row)

        end_time = time.time()
        self._metrics["from_spark_time"] = end_time - start_time

    def from_s3(
        self,
        bucket: Optional[str] = None,
        s3_folder: Optional[str] = None,
    ) -> None:
        """
        Copy contents from a given S3 bucket and location to the input folder.

        Raises:
            Exception: If the input folder is not specified.
        """
        self.bucket = bucket if bucket else self.bucket
        self.s3_folder = s3_folder if s3_folder else self.s3_folder

        start_time = time.time()
        if self.input_folder:
            s3 = boto3.resource("s3")
            _bucket = s3.Bucket(self.bucket)
            prefix = self._get_partitioned_key(self.s3_folder)
            for obj in _bucket.objects.filter(Prefix=prefix):
                if not os.path.exists(os.path.dirname(f"{self.input_folder}/{obj.key}")):
                    os.makedirs(os.path.dirname(f"{self.input_folder}/{obj.key}"))
                _bucket.download_file(obj.key, f"{self.input_folder}/{obj.key}")
            end_time = time.time()
            self._metrics["from_s3_time"] = end_time - start_time
        else:
            raise Exception("❌ Input folder not specified.")

    def from_kafka(
        self,
        input_topic: str,
        kafka_cluster_connection_string: str,
        nr_messages: int = 1000,
        group_id: str = "geniusrise",
        partition_scheme: Optional[str] = None,
    ) -> str:
        """
        Consume messages from a Kafka topic and save them as JSON files in the input folder.
        Stops consuming after reaching the latest message or the specified number of messages.

        Args:
            input_topic (str): Kafka topic to consume data from.
            kafka_cluster_connection_string (str): Connection string for the Kafka cluster.
            nr_messages (int, optional): Number of messages to consume. Defaults to 1000.
            group_id (str, optional): Kafka consumer group ID. Defaults to "geniusrise".
            partition_scheme (Optional[str]): Optional partitioning scheme for Kafka, e.g., "year/month/day".

        Returns:
            str: The path to the folder where the consumed messages are saved as JSON files.

        Raises:
            KafkaConnectionError: If unable to connect to Kafka.
            Exception: If any other error occurs during processing.
        """
        self.input_topic = input_topic
        self.kafka_cluster_connection_string = kafka_cluster_connection_string
        self.group_id = group_id
        self.partition_scheme = partition_scheme

        start_time = time.time()
        try:
            self.consumer = KafkaConsumer(
                self.input_topic,
                bootstrap_servers=self.kafka_cluster_connection_string,
                group_id=self.group_id,
                max_poll_interval_ms=600000,  # 10 minutes
                session_timeout_ms=10000,  # 10 seconds
            )
        except Exception as e:
            self.log.exception(f"🚫 Failed to create Kafka consumer: {e}")
            raise KafkaConnectionError("Failed to connect to Kafka.")

        try:
            buffered_messages = []
            for i, message in enumerate(self.consumer):
                if i >= nr_messages:
                    break
                buffered_messages.append(json.loads(message.value.decode("utf-8")))  # type: ignore

            for i, message in enumerate(buffered_messages):
                with open(os.path.join(self.input_folder, f"message_{i}.json"), "w") as f:
                    json.dump(message, f)

            end_time = time.time()
            self._metrics["from_kafka_time"] = end_time - start_time
            return self.input_folder
        except Exception as e:
            self.log.exception(f"An error occurred: {e}")
            raise

    def compose(self, *inputs: "Input") -> Union[bool, str]:
        """
        Compose multiple BatchInput instances by merging their input folders.

        Args:
            inputs (Input): Variable number of BatchInput instances.

        Returns:
            Union[bool, str]: True if successful, error message otherwise.
        """
        try:
            for input_instance in inputs:
                if not isinstance(input_instance, BatchInput):
                    return f"❌ Incompatible input type: {type(input_instance).__name__}"

                src_folder = input_instance.get()
                for filename in os.listdir(src_folder):
                    src_path = os.path.join(src_folder, filename)
                    dest_path = os.path.join(self.input_folder, filename)

                    if os.path.isfile(src_path):
                        shutil.copy2(src_path, dest_path)

            return True
        except Exception as e:
            self.log.exception(f"❌ Error during composition: {e}")
            return str(e)

    def collect_metrics(self) -> Dict[str, float]:
        """
        Collect and return metrics, then clear them for future collection.

        Returns:
            Dict[str, float]: Dictionary containing metrics.
        """
        collected_metrics = self._metrics.copy()
        self._metrics.clear()
        return collected_metrics

    def _get_partitioned_key(self, prefix: str) -> str:
        """
        Generate a partitioned S3 key based on the partitioning scheme.

        Args:
            prefix (str): The s3 folder prefix to use

        Returns:
            str: The partitioned S3 key.
        """
        if self.partition_scheme:
            partitioned_key = time.strftime(self.partition_scheme)
            return f"{prefix}/{partitioned_key}"
        else:
            return self.s3_folder
