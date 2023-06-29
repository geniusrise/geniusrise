from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import uuid
import os
from kafka import KafkaProducer
import json
import boto3
from kafka import KafkaConsumer
import logging


class Task(ABC):
    """
    Abstract base class for a task.

    Attributes:
        id (uuid.UUID): Unique identifier for the task.
        output_folder (str): Default folder to save output files.
        output_topic (str): Default Kafka topic to ingest data.
        producer (KafkaProducer): Kafka producer for ingesting data.
    """

    def __init__(
        self,
        input_folder: Optional[str] = None,
        input_topic: Optional[str] = None,
        output_folder: Optional[str] = None,
        output_topic: Optional[str] = None,
    ) -> None:
        """
        Initialize a new task.

        Args:
            output_folder (str, optional): Default folder to save output files. Defaults to "/tmp".
            output_topic (str, optional): Default Kafka topic to ingest data. Defaults to "default".
        """
        self.id = uuid.uuid4()
        self.output_folder = output_folder
        self.output_topic = output_topic
        self.input_folder = input_folder
        self.input_topic = input_topic

        if self.input_topic:
            self.consumer = KafkaConsumer(self.input_topic, bootstrap_servers="localhost:9092") if input_topic else None

        if self.output_topic:
            self.producer = KafkaProducer(bootstrap_servers="localhost:9092")

        self.log = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def run(self) -> None:
        """
        Run the task. This method should be implemented by subclasses.
        """
        raise NotImplementedError

    @abstractmethod
    def destroy(self) -> None:
        """
        Destroy the task. This method should be implemented by subclasses.
        """
        raise NotImplementedError

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """
        Get the status of the task. This method should be implemented by subclasses.

        Returns:
            Dict[str, Any]: The status of the task.
        """
        raise NotImplementedError

    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get the statistics of the task. This method should be implemented by subclasses.

        Returns:
            Dict[str, Any]: The statistics of the task.
        """
        raise NotImplementedError

    @abstractmethod
    def get_logs(self) -> Dict[str, Any]:
        """
        Get the logs of the task. This method should be implemented by subclasses.

        Returns:
            Dict[str, Any]: The logs of the task.
        """
        raise NotImplementedError

    def get(self):
        """
        Read a message from the input topic or return the input folder location.

        Returns:
            str: The message from the input topic or the input folder location.
        """
        if self.input_topic:
            # Return the topic consumer
            return self.consumer
        elif self.input_folder:
            # Return the input folder location
            return self.input_folder
        else:
            self.log.error("No input source specified.")
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

            # Define the bucket
            _bucket = s3.Bucket(bucket)

            # Define the prefix
            prefix = s3_folder if s3_folder.endswith("/") else s3_folder + "/"

            # Download each file individually
            for obj in _bucket.objects.filter(Prefix=prefix):
                # Create the directory if it doesn't exist
                if not os.path.exists(os.path.dirname(self.input_folder + "/" + obj.key)):
                    os.makedirs(os.path.dirname(self.input_folder + "/" + obj.key))

                # Download the file
                _bucket.download_file(obj.key, self.input_folder + "/" + obj.key)
        else:
            self.log.error("No input folder specified.")

    def save(self, data: Any, filename: str):
        """
        Save data to a file or ingest it into a Kafka topic.

        If the data is a string, it is saved to a file in the output folder with the given filename.
        If the data is not a string, it is ingested into the output topic in Kafka.

        Args:
            data (Any): The data to save or ingest.
            filename (str): The filename to use when saving the data to a file.
        """
        # Determine whether to save to a file or to a Kafka topic based on the type of data
        if self.output_folder:
            # Save to a file
            with open(os.path.join(self.output_folder, filename), "w") as f:
                f.write(json.dumps(data))
                self.log.debug(f"Wrote the data into {self.output_folder}/{filename}.")
        else:
            # Ingest into a Kafka topic
            self.producer.send(self.output_topic, json.dumps(data))
            self.log.debug(f"Inserted the data into {self.output_topic} topic.")

    def copy_to_s3(self, bucket: str, s3_folder: str):
        """
        Recursively copy all files and directories from the output folder to a given S3 bucket and folder.

        Args:
            bucket (str): The name of the S3 bucket.
            s3_folder (str): The folder in the S3 bucket.
        """
        s3 = boto3.client("s3")

        if self.output_folder:
            # Recursively walk through all directories and files in the output folder
            for root, _, files in os.walk(self.output_folder):
                for filename in files:
                    # Get the full path of the file
                    local_path = os.path.join(root, filename)

                    # Get the relative path of the file from the output folder
                    relative_path = os.path.relpath(local_path, self.output_folder)

                    # Define the key for the file in S3
                    s3_key = os.path.join(s3_folder, relative_path)

                    # Upload the file to S3
                    s3.upload_file(local_path, bucket, s3_key)
        else:
            self.log.error("No output folder specified.")

    def __repr__(self):
        """
        Return a string representation of the task.

        Returns:
            str: A string representation of the task.
        """
        return f"Task(id={self.id}, output_folder={self.output_folder}, output_topic={self.output_topic})"
