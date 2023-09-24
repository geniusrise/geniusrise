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
import os
import shutil
import time
from typing import Dict, Generator, Optional, Union

import boto3
import pyspark
from pyspark.sql import Row, SparkSession
from retrying import retry

from .input import Input  # Assuming Input is in the same package


class FileNotExistError(Exception):
    """❌ Custom exception for file not existing."""


class BatchInput(Input):
    """
    📁 BatchInput: Manages batch input data.

    Attributes:
        input_folder (str): Folder to read input files.
        bucket (str): S3 bucket name.
        s3_folder (str): Folder within the S3 bucket.
        partition_scheme (Optional[str]): Partitioning scheme for S3, e.g., "year/month/day".

    Usage:
        config = BatchInput("/path/to/input", "my_bucket", "s3/folder")
        files = list(config.list_files())
        content = config.read_file("example.txt")

    Raises:
        FileNotExistError: If the file does not exist.

    Args:
        input_folder (str): Folder to read input files from.
        bucket (str): S3 bucket name.
        s3_folder (str): Folder within the S3 bucket.
        partition_scheme (Optional[str]): Partitioning scheme for S3, e.g., "year/month/day".
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
        self._metrics: Dict[str, float] = {}  # Initialize metrics dictionary

    def get(self) -> str:
        """
        Get the input folder path.

        Returns:
            str: The path to the input folder.
        """
        return self.input_folder

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
            files = glob.glob(f"{self.input_folder}/*")
            for file in files:
                with open(file, "r") as f:
                    content = f.read()
                yield Row(filename=file, content=content)

        rdd = spark.sparkContext.parallelize(file_generator())
        df = spark.createDataFrame(rdd)

        return df

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
            self.log.error(f"❌ Error during composition: {e}")
            return str(e)

    def _validate_file(self, filename: str) -> bool:
        """
        Validate if the file exists and is a file.

        Args:
            filename (str): The name of the file to validate.

        Returns:
            bool: True if the file is valid, False otherwise.
        """
        file_path = os.path.join(self.input_folder, filename)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return True
        self.log.error(f"❌ Invalid file: {filename}")
        return False

    def list_files(self, start: Optional[int] = None, limit: Optional[int] = None) -> Generator[str, None, None]:
        """
        List all files in the input folder with optional pagination.

        Args:
            start (Optional[int]): The starting index for pagination.
            limit (Optional[int]): The maximum number of files to return.

        Yields:
            str: The next file path in the input folder.
        """
        start_time = time.time()
        count = 0
        for f in os.listdir(self.input_folder):
            file_path = os.path.join(self.input_folder, f)
            if os.path.isfile(file_path):
                if start is not None and count < start:
                    count += 1
                    continue
                if limit is not None and count >= (start or 0) + limit:
                    break
                yield file_path
                count += 1
        end_time = time.time()
        self._metrics["list_time"] = end_time - start_time  # Record time taken to list files

    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def read_file(self, filename: str) -> str:
        """
        Read the content of a file.

        Args:
            filename (str): The name of the file to read.

        Returns:
            str: The content of the file.

        Raises:
            FileNotExistError: If the file does not exist.
        """
        start_time = time.time()
        if self._validate_file(filename):
            with open(os.path.join(self.input_folder, filename), "r") as file:
                content = file.read()
            end_time = time.time()
            self._metrics["read_time"] = end_time - start_time  # Record time taken to read a file
            return content
        else:
            raise FileNotExistError(f"❌ Invalid file: {filename}")

    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def delete_file(self, filename: str) -> None:
        """
        Delete a file.

        Args:
            filename (str): The name of the file to delete.

        Raises:
            FileNotExistError: If the file does not exist.
        """
        start_time = time.time()
        if self._validate_file(filename):
            os.remove(os.path.join(self.input_folder, filename))
            end_time = time.time()
            self._metrics["delete_time"] = end_time - start_time  # Record time taken to delete a file
        else:
            raise FileNotExistError(f"❌ Invalid file: {filename}")

    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def copy_from_remote(self) -> None:
        """
        Copy contents from a given S3 bucket and location to the input folder.

        Raises:
            Exception: If the input folder is not specified.
        """
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
            self._metrics["copy_from_remote_time"] = end_time - start_time  # Record time taken to copy from remote
        else:
            raise Exception("❌ Input folder not specified.")

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
