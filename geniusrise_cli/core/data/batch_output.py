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

    def __init__(self, output_folder: str):
        """
        Initialize a new batch output configuration.

        Args:
            output_folder (str): Folder to save output files.
        """
        self.output_folder = output_folder

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
            log.error(f"Failed to write data to file: {e}")

    def copy_to_s3(self, bucket: str, s3_folder: str):
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
                    s3_key = os.path.join(s3_folder, relative_path)
                    s3.upload_file(local_path, bucket, s3_key)
        except Exception as e:
            log.error(f"Failed to copy files to S3: {e}")

    def flush(self):
        """
        Flush the output by copying all files and directories from the output folder to a given S3 bucket and folder.
        """
        # Replace 'bucket' and 's3_folder' with your actual bucket and folder
        self.copy_to_s3(bucket="your_bucket", s3_folder="your_folder")
