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

import glob
import json
import logging
import os
import shutil
import time
from typing import Any, Dict, Optional, Union

import boto3
import pyspark
from pyspark.sql import SparkSession, Row
from retrying import retry
import shortuuid
from kafka import KafkaProducer

from .output import Output


class KafkaConnectionError(Exception):
    """❌ Custom exception for Kafka connection problems."""


class FileNotExistError(Exception):
    """❌ Custom exception for file not existing."""


class BatchOutput(Output):
    r"""
    📁 BatchOutput: Manages batch output data.

    Attributes:
        output_folder (str): Folder to save output files.
        bucket (str): S3 bucket name.
        s3_folder (str): Folder within the S3 bucket.
        partition_scheme (Optional[str]): Partitioning scheme for S3, e.g., "year/month/day".

    Raises:
        FileNotExistError: If the output folder does not exist.

    Args:
        output_folder (str): Folder to save output files.
        bucket (str): S3 bucket name.
        s3_folder (str): Folder within the S3 bucket.
        partition_scheme (Optional[str]): Partitioning scheme for S3, e.g., "year/month/day".


    Usage:
        ```python
        # Initialize the BatchOutput instance
        config = BatchOutput("/path/to/output", "my_bucket", "s3/folder", partition_scheme="%Y/%m/%d")

        # Save data to a file
        config.save({"key": "value"}, "example.json")

        # Compose multiple BatchOutput instances
        result = config1.compose(config2, config3)

        # Convert output to a Spark DataFrame
        spark_df = config.to_spark(spark_session)

        # Copy files to a remote S3 bucket
        config.to_s3()

        # Flush the output to S3
        config.flush()

        # Collect metrics
        metrics = config.collect_metrics()
        ```
    """

    def __init__(
        self,
        output_folder: str,
        bucket: str,
        s3_folder: str,
        partition_scheme: Optional[str] = None,
    ) -> None:
        """
        Initialize a new batch output data.

        Args:
            output_folder (str): Folder to save output files.
            bucket (str): S3 bucket name.
            s3_folder (str): Folder within the S3 bucket.
        """
        self.output_folder = output_folder
        self.bucket = bucket
        self.s3_folder = s3_folder
        self.partition_scheme = partition_scheme
        self.log = logging.getLogger(self.__class__.__name__)
        self._metrics: Dict[str, float] = {}

    def save(self, data: Any, filename: Optional[str] = None, **kwargs) -> None:
        """
        💾 Save data to a file in the output folder.

        Args:
            data (Any): The data to save.
            filename (Optional[str]): The filename to use when saving the data to a file.
        """
        filename = filename if filename else str(shortuuid.uuid())

        # Determine the target folder based on the partition scheme
        if self.partition_scheme:
            partitioned_folder = self._get_partitioned_key(self.s3_folder)
            target_folder = os.path.join(self.output_folder, partitioned_folder)
        else:
            target_folder = self.output_folder

        # Create the target folder if it doesn't exist
        os.makedirs(target_folder, exist_ok=True)

        # Save the file
        try:
            with open(os.path.join(target_folder, filename), "w") as f:
                f.write(json.dumps(data))
            self.log.debug(f"✅ Wrote the data into {target_folder}/{filename}.")
        except Exception as e:
            self.log.exception(f"🚫 Failed to write data to file: {e}")
            raise

    def compose(self, *outputs: "Output") -> Union[bool, str]:
        """
        Compose multiple BatchOutput instances by merging their output folders.

        Args:
            outputs (Output): Variable number of BatchOutput instances.

        Returns:
            Union[bool, str]: True if successful, error message otherwise.
        """
        try:
            for output_instance in outputs:
                if not isinstance(output_instance, BatchOutput):
                    return f"❌ Incompatible output type: {type(output_instance).__name__}"

                # on composing two outputs, we copy over all the data in one place
                src_folder = output_instance.output_folder
                for filename in os.listdir(src_folder):
                    src_path = os.path.join(src_folder, filename)
                    dest_path = os.path.join(self.output_folder, filename)

                    if os.path.isfile(src_path):
                        shutil.copy2(src_path, dest_path)

            return True
        except Exception as e:
            self.log.exception(f"❌ Error during composition: {e}")
            return str(e)

    def to_spark(self, spark: SparkSession) -> pyspark.sql.DataFrame:
        """
        Get a Spark DataFrame from the output folder.

        Returns:
            pyspark.sql.DataFrame: A Spark DataFrame where each row corresponds to a file in the output folder.

        Raises:
            FileNotExistError: If the output folder does not exist.
        """
        if not os.path.exists(self.output_folder):
            raise FileNotExistError(f"❌ Output folder {self.output_folder} does not exist.")

        def file_generator():
            try:
                if self.partition_scheme:
                    partitioned_folder = self._get_partitioned_key(self.s3_folder)
                    target_folder = os.path.join(self.output_folder, partitioned_folder)
                else:
                    target_folder = self.output_folder

                files = glob.glob(f"{target_folder}/*")
                for file in files:
                    with open(file, "r") as f:
                        content = f.read()
                    yield Row(filename=file, content=content)
            except Exception as e:
                self.log.exception(f"Failed to ingest the file {file} in spark: {e}")

        start_time = time.time()
        rdd = spark.sparkContext.parallelize(file_generator())
        df = spark.createDataFrame(rdd)

        end_time = time.time()
        self._metrics["from_s3_time"] = end_time - start_time

        return df

    def to_kafka(
        self,
        output_topic: str,
        kafka_cluster_connection_string: str,
    ) -> None:
        """
        Produce messages to a Kafka topic from the files in the output folder.

        Args:
            output_topic (str): Kafka topic to produce data to.
            kafka_cluster_connection_string (str): Connection string for the Kafka cluster.
            key_serializer (Optional[str]): Serializer for message keys. Defaults to None.

        Raises:
            KafkaConnectionError: If unable to connect to Kafka.
            Exception: If any other error occurs during processing.
        """
        start_time = time.time()
        try:
            producer = KafkaProducer(
                bootstrap_servers=kafka_cluster_connection_string,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
        except Exception as e:
            self.log.exception(f"🚫 Failed to create Kafka producer: {e}")
            raise KafkaConnectionError("Failed to connect to Kafka.")

        try:
            for root, _, files in os.walk(self.output_folder):
                for filename in files:
                    file_path = os.path.join(root, filename)
                    with open(file_path, "r") as f:
                        message = json.load(f)
                    producer.send(output_topic, value=message)
            producer.flush()
            end_time = time.time()
            self._metrics["to_kafka_time"] = end_time - start_time
        except Exception as e:
            self.log.exception(f"An error occurred: {e}")
            raise

    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def to_s3(self) -> None:
        """
        ☁️ Recursively copy all files and directories from the output folder to a given S3 bucket and folder.
        """
        start_time = time.time()
        s3 = boto3.client("s3")
        try:
            for root, _, files in os.walk(self.output_folder):
                for filename in files:
                    local_path = os.path.join(root, filename)
                    relative_path = os.path.relpath(local_path, self.output_folder)
                    s3_key = os.path.join(self.s3_folder, relative_path)
                    s3.upload_file(local_path, self.bucket, s3_key)
            end_time = time.time()
            self._metrics["to_s3_time"] = end_time - start_time  # Record time taken to copy to remote
        except Exception as e:
            self.log.exception(f"🚫 Failed to copy files to S3: {e}")
            raise

    def flush(self) -> None:
        """
        🔄 Flush the output by copying all files and directories from the output folder to a given S3 bucket and folder.
        """
        self.to_s3()

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
