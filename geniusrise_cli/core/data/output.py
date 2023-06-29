import json
import logging
import os
from typing import Any, Optional

import boto3
from kafka import KafkaProducer


class OutputConfig:
    """
    Class for managing output configurations.

    Attributes:
        output_folder (str, optional): Default folder to save output files.
        output_topic (str, optional): Default Kafka topic to ingest data.
        producer (KafkaProducer, optional): Kafka producer for ingesting data.
    """

    def __init__(self, output_folder: Optional[str] = None, output_topic: Optional[str] = None):
        """
        Initialize a new output configuration.

        Args:
            output_folder (str, optional): Default folder to save output files.
            output_topic (str, optional): Default Kafka topic to ingest data.
        """
        self.output_folder = output_folder
        self.output_topic = output_topic
        if self.output_topic:
            try:
                self.producer = KafkaProducer(bootstrap_servers="localhost:9092")
            except Exception as e:
                logging.error(f"Failed to create Kafka producer: {e}")
                self.producer = None

    def save(self, data: Any, filename: str):
        """
        Save data to a file or ingest it into a Kafka topic.

        If the output_folder is not None, it is saved to a file in the output folder with the given filename.
        If the output_folder is None, it is ingested into the output topic in Kafka.

        Args:
            data (Any): The data to save or ingest.
            filename (str): The filename to use when saving the data to a file.
        """
        if self.output_folder:
            try:
                with open(os.path.join(self.output_folder, filename), "w") as f:
                    f.write(json.dumps(data))
                logging.debug(f"Wrote the data into {self.output_folder}/{filename}.")
            except Exception as e:
                logging.error(f"Failed to write data to file: {e}")
        elif self.output_topic and self.producer:
            try:
                self.producer.send(self.output_topic, json.dumps(data))
                logging.debug(f"Inserted the data into {self.output_topic} topic.")
            except Exception as e:
                logging.error(f"Failed to send data to Kafka topic: {e}")
        else:
            logging.error("No output source specified.")

    def copy_to_s3(self, bucket: str, s3_folder: str):
        """
        Recursively copy all files and directories from the output folder to a given S3 bucket and folder.

        Args:
            bucket (str): The name of the S3 bucket.
            s3_folder (str): The folder in the S3 bucket.
        """
        s3 = boto3.client("s3")
        if self.output_folder:
            try:
                for root, _, files in os.walk(self.output_folder):
                    for filename in files:
                        local_path = os.path.join(root, filename)
                        relative_path = os.path.relpath(local_path, self.output_folder)
                        s3_key = os.path.join(s3_folder, relative_path)
                        s3.upload_file(local_path, bucket, s3_key)
            except Exception as e:
                logging.error(f"Failed to copy files to S3: {e}")
        else:
            logging.error("No output folder specified.")
