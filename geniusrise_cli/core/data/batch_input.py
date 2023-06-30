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

    def __init__(self, input_folder: str):
        """
        Initialize a new batch input configuration.

        Args:
            input_folder (str): Folder to read input files.
        """
        self.input_folder = input_folder

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

    def copy_from_s3(self, bucket: str, s3_folder: str):
        """
        Copy contents from a given S3 bucket and location to the input folder.

        Args:
            bucket (str): The name of the S3 bucket.
            s3_folder (str): The folder in the S3 bucket.
        """
        if self.input_folder:
            s3 = boto3.resource("s3")
            _bucket = s3.Bucket(bucket)
            prefix = s3_folder if s3_folder.endswith("/") else s3_folder + "/"
            for obj in _bucket.objects.filter(Prefix=prefix):
                if not os.path.exists(os.path.dirname(self.input_folder + "/" + obj.key)):
                    os.makedirs(os.path.dirname(self.input_folder + "/" + obj.key))
                _bucket.download_file(obj.key, self.input_folder + "/" + obj.key)
        else:
            log.error("No input folder specified.")
