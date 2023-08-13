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

import boto3

from .input import InputConfig


class BatchInputConfig(InputConfig):
    """
    📁 BatchInputConfig: Manages batch input configurations.

    Attributes:
        input_folder (str): Folder to read input files.
        bucket (str): S3 bucket name.
        s3_folder (str): Folder within the S3 bucket.

    Usage:
    ```python
    config = BatchInputConfig("/path/to/input", "my_bucket", "s3/folder")
    files = config.list_files()
    content = config.read_file("example.txt")
    ```
    """

    def __init__(self, input_folder: str, bucket: str, s3_folder: str) -> None:
        """
        Initialize a new batch input configuration.

        Args:
            input_folder (str): Folder to read input files.
            bucket (str): S3 bucket name.
            s3_folder (str): Folder within the S3 bucket.
        """
        self.input_folder = input_folder
        self.bucket = bucket
        self.s3_folder = s3_folder
        self.log = logging.getLogger(__name__)

    def get(self) -> str:
        """
        📍 Get the input folder location.

        Returns:
            str: The input folder location.

        Raises:
            Exception: If no input folder is specified.
        """
        if self.input_folder:
            return self.input_folder
        else:
            self.log.exception("🚫 No input folder specified.")
            raise Exception("Input folder not specified.")

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
            self.log.exception("🚫 No input folder specified.")
            raise Exception("Input folder not specified.")

    def list_files(self) -> list:
        """
        📜 List all files in the input folder.

        Returns:
            list: A list of file paths.

        Raises:
            Exception: If no input folder is specified.
        """
        if self.input_folder:
            return [
                os.path.join(self.input_folder, f)
                for f in os.listdir(self.input_folder)
                if os.path.isfile(os.path.join(self.input_folder, f))
            ]
        else:
            self.log.exception("🚫 No input folder specified.")
            raise Exception("Input folder not specified.")

    def read_file(self, filename: str) -> str:
        """
        📖 Read a file from the input folder.

        Args:
            filename (str): The name of the file.

        Returns:
            str: The contents of the file.

        Raises:
            Exception: If no input folder is specified.
        """
        if self.input_folder:
            with open(os.path.join(self.input_folder, filename), "r") as file:
                return file.read()
        else:
            self.log.exception("🚫 No input folder specified.")
            raise Exception("Input folder not specified.")

    def delete_file(self, filename: str) -> None:
        """
        🗑️ Delete a file from the input folder.

        Args:
            filename (str): The name of the file.

        Raises:
            Exception: If no input folder is specified.
        """
        if self.input_folder:
            os.remove(os.path.join(self.input_folder, filename))
        else:
            self.log.exception("🚫 No input folder specified.")
            raise Exception("Input folder not specified.")

    def copy_to_remote(self, filename: str, bucket: str, s3_folder: str) -> None:
        """
        ☁️ Copy a file from the input folder to an S3 bucket.

        Args:
            filename (str): The name of the file.
            bucket (str): The name of the S3 bucket.
            s3_folder (str): The folder in the S3 bucket.

        Raises:
            Exception: If no input folder is specified.
        """
        if self.input_folder:
            s3 = boto3.resource("s3")
            s3.meta.client.upload_file(
                os.path.join(self.input_folder, filename),
                bucket,
                os.path.join(s3_folder, filename),
            )
        else:
            self.log.exception("🚫 No input folder specified.")
            raise Exception("Input folder not specified.")
