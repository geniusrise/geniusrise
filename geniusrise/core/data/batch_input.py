# geniusrise
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

log = logging.getLogger(__name__)


class BatchInputConfig(InputConfig):
    """
    Class for managing batch input configurations.

    Attributes:
        input_folder (str): Folder to read input files.
    """

    def __init__(self, input_folder: str, bucket: str, s3_folder: str):
        """
        Initialize a new batch input configuration.

        Args:
            input_folder (str): Folder to read input files.
        """
        self.input_folder = input_folder
        self.bucket = bucket
        self.s3_folder = s3_folder

    def get(self):
        """
        Get the input folder location.

        Returns:
            str: The input folder location.
        """
        if self.input_folder:
            return self.input_folder
        else:
            log.error("No input folder specified.")
            return None

    def copy_from_remote(self):
        """
        Copy contents from a given S3 bucket and location to the input folder.

        Args:
            bucket (str): The name of the S3 bucket.
            s3_folder (str): The folder in the S3 bucket.
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
            log.error("No input folder specified.")

    def list_files(self):
        """
        List all files in the input folder.

        Returns:
            list: A list of file paths.
        """
        if self.input_folder:
            return [
                os.path.join(self.input_folder, f)
                for f in os.listdir(self.input_folder)
                if os.path.isfile(os.path.join(self.input_folder, f))
            ]
        else:
            log.error("No input folder specified.")
            return []

    def read_file(self, filename):
        """
        Read a file from the input folder.

        Args:
            filename (str): The name of the file.

        Returns:
            str: The contents of the file.
        """
        if self.input_folder:
            with open(os.path.join(self.input_folder, filename), "r") as file:
                return file.read()
        else:
            log.error("No input folder specified.")
            return None

    def delete_file(self, filename):
        """
        Delete a file from the input folder.

        Args:
            filename (str): The name of the file.
        """
        if self.input_folder:
            os.remove(os.path.join(self.input_folder, filename))
        else:
            log.error("No input folder specified.")

    def copy_to_remote(self, filename, bucket, s3_folder):
        """
        Copy a file from the input folder to an S3 bucket.

        Args:
            filename (str): The name of the file.
            bucket (str): The name of the S3 bucket.
            s3_folder (str): The folder in the S3 bucket.
        """
        if self.input_folder:
            s3 = boto3.resource("s3")
            s3.meta.client.upload_file(
                os.path.join(self.input_folder, filename), bucket, os.path.join(s3_folder, filename)
            )
        else:
            log.error("No input folder specified.")
