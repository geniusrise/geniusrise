import logging
import random
import string
from typing import Any
import os
import tempfile

import boto3
from airflow.models import BaseOperator
from airflow.utils.context import Context
from botocore.exceptions import BotoCoreError, ClientError


def rand_str():
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=8))


class Task(BaseOperator):
    """
    Base class for all tasks in the pipeline.
    """

    def __init__(self, name: str, bucket: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name
        self.trace = logging.getLogger(f"Task-{name}-{self.task_id}")
        self.bucket = bucket
        self.s3 = boto3.client("s3")
        self.input_folder = None
        self.output_folder = f"{self.name}-{rand_str()}"

    def create_output_folder(self, bucket: str, folder: str) -> None:
        """
        Creates an S3 folder for the task's output.

        Args:
            bucket (str): The name of the S3 bucket.
            folder (str): The name of the folder to create.
        """
        s3 = boto3.client("s3")
        try:
            s3.put_object(Bucket=bucket, Key=(folder + "/"))
            self.trace.info(f"Created output folder {folder} in bucket {bucket}")
        except (BotoCoreError, ClientError) as e:
            self.trace.error(f"Error creating output folder in S3: {e}")
            raise

    def execute(self, context: Context) -> Any:
        """
        Executes the task and logs the result.

        Args:
            context (dict): The execution context.

        Returns:
            Any: The result of the task.
        """
        try:
            self.create_output_folder(bucket=self.bucket, folder=self.output_folder)
            self.input_folder = context["task_instance"].xcom_pull(task_ids=self.upstream_task_ids, key="input_folder")
            result = self(context.__dict__)
            context["task_instance"].xcom_push(key="input_folder", value=self.output_folder)
            self.trace.info(f"Successfully executed task {self.task_id}")
            return result
        except Exception as e:
            self.trace.error(f"Error executing task {self.task_id}: {e}")
            raise

    def __call__(self, context: dict) -> Any:
        """
        The main logic of the task. This should be overridden in subclasses.

        Args:
            context (dict): The execution context.

        Returns:
            Any: The result of the task.
        """
        pass  # Override this method in subclasses

    def sync_to_s3(self, data_dir: str) -> None:
        """
        Stores the contents of the given directory in the output_folder in the S3 bucket.

        Args:
            data_dir (str): The directory containing the data to store.
        """
        if not self.output_folder:
            self.trace.error("Output folder not set")
            raise ValueError("Output folder not set")
        try:
            for root, _, files in os.walk(data_dir):
                for file in files:
                    local_file = os.path.join(root, file)
                    s3_file = os.path.join(self.output_folder, local_file.replace(data_dir + "/", ""))
                    self.s3.upload_file(local_file, self.bucket, s3_file)
            self.trace.info(f"Stored data in output folder {self.output_folder}")
        except (BotoCoreError, ClientError) as e:
            self.trace.error(f"Error storing data in S3: {e}")
            raise

    def sync_to_local(self) -> str:
        """
        Reads data from the input_folder of the S3 bucket, stores it locally, and returns the local directory name.

        Returns:
            str: The name of the local directory where the data was stored.
        """
        if not self.input_folder:
            self.trace.error("No input folder specified")
            raise Exception("No input folder specified")
        try:
            local_dir = tempfile.mkdtemp()
            paginator = self.s3.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=self.bucket, Prefix=self.input_folder):
                for obj in page.get("Contents", []):
                    local_file = os.path.join(local_dir, obj["Key"].replace(self.input_folder + "/", ""))
                    os.makedirs(os.path.dirname(local_file), exist_ok=True)
                    self.s3.download_file(self.bucket, obj["Key"], local_file)
            self.trace.info(f"Read data from input folder {self.input_folder}")
            return local_dir
        except (BotoCoreError, ClientError) as e:
            self.trace.error(f"Error reading data from S3: {e}")
            raise


class Source(Task):
    """
    Represents a data source in the pipeline.
    """

    def __init__(self, source: Any, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.source = source

    def __call__(self, context: dict) -> Any:
        """
        Reads data from the source.

        Args:
            context (dict): The execution context.

        Returns:
            Any: The data read from the source.
        """
        data = self.read()
        return data

    def read(self) -> Any:
        """
        The logic for reading data from the source. This should be overridden in subclasses.

        Returns:
            Any: The data read from the source.
        """
        pass  # Override this method in subclasses


class Sink(Task):
    """
    Represents a data sink in the pipeline.

    Args:
        sink (Any): The sink to write data to.
        *args: Variable length argument list.
        **kwargs: Arbitrary keyword arguments.
    """

    def __init__(self, sink: Any, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sink = sink

    def __call__(self, context: dict) -> None:
        """
        Writes data to the sink.

        Args:
            context (dict): The execution context.
        """
        self.write()

    def write(self) -> None:
        """
        The logic for writing data to the sink. This should be overridden in subclasses.

        Args:
            data (Any): The data to write to the sink.
        """
        pass  # Override this method in subclasses
