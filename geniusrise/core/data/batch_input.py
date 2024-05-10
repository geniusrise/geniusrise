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

import os
import shutil
import time
from typing import Dict, Optional, Union

import boto3

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

        if not self.bucket or self.bucket == "None":
            self.log.warn("S3 Bucket is None, not fetching.")
            return

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

    def compose(self, *inputs: "Input") -> Union[bool, str]:
        """
        Compose multiple BatchInput instances by merging their input folders.

        Args:
            inputs (Input): Variable number of BatchInput instances.

        Returns:
            Union[bool, str]: True if successful, error message otherwise.
        """
        # TODO: try shutil.copytree
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
