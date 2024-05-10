# 🧠 Geniusrise
# Copyright (C) 2023  geniusrise.ai
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import logging
import os
import shutil
import time
from typing import Any, Dict, Optional, Union

import boto3
from retrying import retry
import shortuuid

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
        # TODO: try shutil.copytree
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

    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def to_s3(self) -> None:
        """
        ☁️ Recursively copy all files and directories from the output folder to a given S3 bucket and folder.
        """
        if self.bucket and self.bucket != "None":
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
        else:
            self.log.warn("S3 Bucket is None, not storing.")

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
