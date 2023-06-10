# import pytest
import os

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from moto import mock_s3
from typing import Any

from geniusrise_cli.dag.task import Sink, Source, Task

# Set AWS credentials for moto
os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
os.environ["AWS_SECURITY_TOKEN"] = "testing"
os.environ["AWS_SESSION_TOKEN"] = "testing"


class TestSource(Source):
    def read(self) -> Any:
        with open(f"{self.input_folder}/input.txt", "r") as f:
            return f.read()


class TestSink(Sink):
    def write(self) -> None:
        with open(f"{self.input_folder}/output.txt", "w") as f:
            f.write("🟣 test data 🟣")


class PrintSink(Sink):
    """
    A Sink subclass for testing purposes that prints the data from its input folder.
    """

    def write(self) -> None:
        """
        Reads data from the input folder and prints it.
        """
        s3 = boto3.resource("s3")
        try:
            print(self.input_folder)
            obj = s3.Object(self.bucket, f"{self.input_folder}/data.txt")
            data = obj.get()["Body"].read().decode("utf-8")
            assert data == "⭕ test data ⭕"
        except (BotoCoreError, ClientError) as e:
            self.trace.error(f"Error reading data from S3: {e}")
            raise


@mock_s3
def test_task():
    # Create a mock S3 bucket
    conn = boto3.resource("s3", region_name="us-east-1")
    conn.create_bucket(Bucket="test_bucket")

    # Create a Task
    task = Task(task_id="test_task", bucket="test_bucket", name="test_task")

    # Test creating an output folder
    task.create_output_folder("test_bucket", "test_folder")
    assert "test_folder/" in [obj.key for obj in conn.Bucket("test_bucket").objects.all()]


@mock_s3
def test_source():
    # Create a mock S3 bucket
    conn = boto3.resource("s3", region_name="us-east-1")
    conn.create_bucket(Bucket="test_bucket")

    # Create a Source
    source = Source(task_id="test_source", bucket="test_bucket", name="test_source", source="test_source")

    # Test creating an output folder
    source.create_output_folder("test_bucket", "test_folder")
    assert "test_folder/" in [obj.key for obj in conn.Bucket("test_bucket").objects.all()]


@mock_s3
def test_file_source():
    # Create a mock S3 bucket
    conn = boto3.resource("s3", region_name="us-east-1")
    conn.create_bucket(Bucket="test_bucket")

    # Create a Source
    source = TestSource(task_id="test_source", bucket="test_bucket", name="test_source", source="test_source")
    source.input_folder = "."

    # Test reading data from the source
    with open("input.txt", "w") as f:
        f.write("🟣 test data 🟣")
    conn.Object("test_bucket", f"{source.input_folder}/input.txt").upload_file("input.txt")
    assert source.read() == "🟣 test data 🟣"


@mock_s3
def test_sink():
    # Create a mock S3 bucket
    conn = boto3.resource("s3", region_name="us-east-1")
    conn.create_bucket(Bucket="test_bucket")

    # Create a PrintSink
    sink = PrintSink(task_id="test_sink", bucket="test_bucket", name="test_sink", sink="test_sink")
    sink.input_folder = "test_folder"

    # Test creating an output folder
    sink.create_output_folder("test_bucket", "test_folder")
    assert "test_folder/" in [obj.key for obj in conn.Bucket("test_bucket").objects.all()]

    # Test writing data to the sink
    with open("test_file.txt", "w") as f:
        f.write("⭕ test data ⭕")

    conn.Object("test_bucket", f"{sink.input_folder}/data.txt").upload_file("test_file.txt")
    sink.write()


@mock_s3
def test_file_sink():
    # Create a mock S3 bucket
    conn = boto3.resource("s3", region_name="us-east-1")
    conn.create_bucket(Bucket="test_bucket")

    # Create a Sink
    sink = TestSink(task_id="test_sink", bucket="test_bucket", name="test_sink", sink="test_sink")
    sink.input_folder = "."

    # Test writing data to the sink
    sink.write()
    data = open(f"{sink.input_folder}/output.txt").read()
    assert data == "🟣 test data 🟣"
