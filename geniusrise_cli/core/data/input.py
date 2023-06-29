import logging
import os
from typing import Optional

import boto3
from kafka import KafkaConsumer


class InputConfig:
    """
    Class for managing input configurations.

    Attributes:
        input_folder (str, optional): Default folder to read input files.
        input_topic (str, optional): Default Kafka topic to consume data.
        consumer (KafkaConsumer, optional): Kafka consumer for consuming data.
    """

    def __init__(self, input_folder: Optional[str] = None, input_topic: Optional[str] = None):
        """
        Initialize a new input configuration.

        Args:
            input_folder (str, optional): Default folder to read input files.
            input_topic (str, optional): Default Kafka topic to consume data.
        """
        self.input_folder = input_folder
        self.input_topic = input_topic
        if self.input_topic:
            try:
                self.consumer = KafkaConsumer(self.input_topic, bootstrap_servers="localhost:9092")
            except Exception as e:
                logging.error(f"Failed to create Kafka consumer: {e}")
                self.consumer = None

    def get(self):
        """
        Get data from the input topic or return the input folder location.

        Returns:
            str: The message from the input topic or the input folder location.
        """
        if self.input_topic and self.consumer:
            try:
                return self.consumer
            except Exception as e:
                logging.error(f"Failed to consume from Kafka topic {self.input_topic}: {e}")
                return None
        elif self.input_folder:
            return self.input_folder
        else:
            logging.error("No input source specified.")
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
            logging.error("No input folder specified.")
