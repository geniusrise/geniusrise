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
from typing import Any

import boto3

from .output import OutputConfig

log = logging.getLogger(__name__)


class BatchOutputConfig(OutputConfig):
    """
    Class for managing batch output configurations.

    Attributes:
        output_folder (str): Folder to save output files.
    """

    def __init__(self, output_folder: str, bucket: str, s3_folder: str):
        """
        Initialize a new batch output configuration.

        Args:
            output_folder (str): Folder to save output files.
        """
        self.output_folder = output_folder
        self.bucket = bucket
        self.s3_folder = s3_folder

    def save(self, data: Any, filename: str):
        """
        Save data to a file in the output folder.

        Args:
            data (Any): The data to save.
            filename (str): The filename to use when saving the data to a file.
        """
        try:
            with open(os.path.join(self.output_folder, filename), "w") as f:
                f.write(json.dumps(data))
            log.debug(f"Wrote the data into {self.output_folder}/{filename}.")
        except Exception as e:
            log.exception(f"Failed to write data to file: {e}")

    def copy_to_remote(self):
        """
        Recursively copy all files and directories from the output folder to a given S3 bucket and folder.

        Args:
            bucket (str): The name of the S3 bucket.
            s3_folder (str): The folder in the S3 bucket.
        """
        s3 = boto3.client("s3")
        try:
            for root, _, files in os.walk(self.output_folder):
                for filename in files:
                    local_path = os.path.join(root, filename)
                    relative_path = os.path.relpath(local_path, self.output_folder)
                    s3_key = os.path.join(self.s3_folder, relative_path)
                    s3.upload_file(local_path, self.bucket, s3_key)
        except Exception as e:
            log.exception(f"Failed to copy files to S3: {e}")

    def flush(self):
        """
        Flush the output by copying all files and directories from the output folder to a given S3 bucket and folder.
        """
        # Replace 'bucket' and 's3_folder' with your actual bucket and folder
        self.copy_to_remote()

    def list_files(self):
        """
        List all files in the output folder.

        Returns:
            list: The list of files in the output folder.
        """
        return [
            os.path.join(self.output_folder, f)
            for f in os.listdir(self.output_folder)
            if os.path.isfile(os.path.join(self.output_folder, f))
        ]

    def read_file(self, filename: str):
        """
        Read a file from the output folder.

        Args:
            filename (str): The name of the file to read.

        Returns:
            str: The contents of the file.
        """
        with open(os.path.join(self.output_folder, filename), "r") as f:
            return f.read()

    def delete_file(self, filename: str):
        """
        Delete a file from the output folder.

        Args:
            filename (str): The name of the file to delete.
        """
        os.remove(os.path.join(self.output_folder, filename))

    def copy_file_to_remote(self, filename: str):
        """
        Copy a specific file from the output folder to the S3 bucket.

        Args:
            filename (str): The name of the file to copy.
        """
        s3 = boto3.client("s3")
        try:
            s3.upload_file(
                os.path.join(self.output_folder, filename), self.bucket, os.path.join(self.s3_folder, filename)
            )
        except Exception as e:
            log.exception(f"Failed to copy file to S3: {e}")
