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
import os
from typing import Generator, Optional

import boto3
from retrying import retry

from .input import Input


class FileNotExistError(Exception):
    """❌ Custom exception for file not existing."""

    pass


class BatchInput(Input):
    """
    📁 BatchInput: Manages batch input data.

    Attributes:
        input_folder (str): Folder to read input files.
        bucket (str): S3 bucket name.
        s3_folder (str): Folder within the S3 bucket.

    Usage:
    ```python
    config = BatchInput("/path/to/input", "my_bucket", "s3/folder")
    files = list(config.list_files())
    content = config.read_file("example.txt")
    ```

    Raises:
        FileNotExistError: If the file does not exist.
    """

    def __init__(self, input_folder: str, bucket: str, s3_folder: str) -> None:
        """
        🛠 Initialize a new batch input data.

        Args:
            input_folder (str): Folder to read input files from.
            bucket (str): S3 bucket name.
            s3_folder (str): Folder within the S3 bucket.
        """
        super(Input, self).__init__()
        self.input_folder = input_folder
        self.bucket = bucket
        self.s3_folder = s3_folder
        self.log = logging.getLogger(self.__class__.__name__)

    def get(self) -> str:
        """
        📥 Returns the input folder path.

        Returns:
            str: The path to the input folder.
        """
        return self.input_folder

    def validate_file(self, filename: str) -> bool:
        """
        ✅ Validates if the file exists and is a file.

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
        📋 Lists all files in the input folder with optional pagination.

        Args:
            start (Optional[int]): The starting index for pagination.
            limit (Optional[int]): The maximum number of files to return.

        Yields:
            str: The next file path in the input folder.
        """
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

    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def read_file(self, filename: str) -> str:
        """
        📖 Reads the content of a file.

        Args:
            filename (str): The name of the file to read.

        Returns:
            str: The content of the file.

        Raises:
            FileNotExistError: If the file does not exist.
        """
        if self.validate_file(filename):
            with open(os.path.join(self.input_folder, filename), "r") as file:
                return file.read()
        else:
            raise FileNotExistError(f"❌ Invalid file: {filename}")

    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def delete_file(self, filename: str) -> None:
        """
        🗑 Deletes a file.

        Args:
            filename (str): The name of the file to delete.

        Raises:
            FileNotExistError: If the file does not exist.
        """
        if self.validate_file(filename):
            os.remove(os.path.join(self.input_folder, filename))
        else:
            raise FileNotExistError(f"❌ Invalid file: {filename}")

    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def copy_to_remote(self, filename: str, bucket: str, s3_folder: str) -> None:
        """
        📤 Copies a file to a remote S3 bucket.

        Args:
            filename (str): The name of the file to copy.
            bucket (str): The name of the S3 bucket.
            s3_folder (str): The folder within the S3 bucket.

        Raises:
            FileNotExistError: If the file does not exist.
        """
        if self.validate_file(filename):
            s3 = boto3.resource("s3")
            s3.meta.client.upload_file(
                os.path.join(self.input_folder, filename),
                bucket,
                os.path.join(s3_folder, filename),
            )
        else:
            raise FileNotExistError(f"❌ Invalid file: {filename}")

    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def copy_from_remote(self) -> None:
        """
        🔄 Copy contents from a given S3 bucket and location to the input folder.

        Raises:
            Exception: If no input folder is specified.
        """
        if self.input_folder:
            s3 = boto3.resource("s3")
            _bucket = s3.Bucket(self.bucket)
            prefix = self.s3_folder if self.s3_folder.endswith("/") else self.s3_folder + "/"
            for obj in _bucket.objects.filter(Prefix=prefix):
                if not os.path.exists(os.path.dirname(f"{self.input_folder}/{obj.key}")):
                    os.makedirs(os.path.dirname(f"{self.input_folder}/{obj.key}"))
                _bucket.download_file(obj.key, f"{self.input_folder}/{obj.key}")
        else:
            raise Exception("❌ Input folder not specified.")
