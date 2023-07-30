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

# # import pytest
# import os
# import tempfile
# from typing import Any

# import boto3
# from botocore.exceptions import BotoCoreError, ClientError
# from moto import mock_s3

# from geniusrise.dag.task import Sink, Source, Task

# # Set AWS credentials for moto
# os.environ["AWS_ACCESS_KEY_ID"] = "testing"
# os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
# os.environ["AWS_SECURITY_TOKEN"] = "testing"
# os.environ["AWS_SESSION_TOKEN"] = "testing"


# class TestSource(Source):
#     def read(self) -> Any:
#         with open(f"{self.input_folder}/input.txt", "r") as f:
#             return f.read()


# class TestSink(Sink):
#     def write(self) -> None:
#         with open(f"{self.input_folder}/output.txt", "w") as f:
#             f.write("🟣 test data 🟣")


# class PrintSink(Sink):
#     """
#     A Sink subclass for testing purposes that prints the data from its input folder.
#     """

#     def write(self) -> None:
#         """
#         Reads data from the input folder and prints it.
#         """
#         s3 = boto3.resource("s3")
#         try:
#             print(self.input_folder)
#             obj = s3.Object(self.bucket, f"{self.input_folder}/data.txt")
#             data = obj.get()["Body"].read().decode("utf-8")
#             assert data == "⭕ test data ⭕"
#         except (BotoCoreError, ClientError) as e:
#             self.trace.error(f"Error reading data from S3: {e}")
#             raise


# @mock_s3
# def test_task():
#     # Create a mock S3 bucket
#     conn = boto3.resource("s3", region_name="us-east-1")
#     conn.create_bucket(Bucket="test_bucket")

#     # Create a Task
#     task = Task(task_id="test_task", bucket="test_bucket", name="test_task")

#     # Test creating an output folder
#     task.create_output_folder("test_bucket", "test_folder")
#     assert "test_folder/" in [obj.key for obj in conn.Bucket("test_bucket").objects.all()]


# @mock_s3
# def test_source():
#     # Create a mock S3 bucket
#     conn = boto3.resource("s3", region_name="us-east-1")
#     conn.create_bucket(Bucket="test_bucket")

#     # Create a Source
#     source = Source(task_id="test_source", bucket="test_bucket", name="test_source", source="test_source")

#     # Test creating an output folder
#     source.create_output_folder("test_bucket", "test_folder")
#     assert "test_folder/" in [obj.key for obj in conn.Bucket("test_bucket").objects.all()]


# @mock_s3
# def test_file_source():
#     # Create a mock S3 bucket
#     conn = boto3.resource("s3", region_name="us-east-1")
#     conn.create_bucket(Bucket="test_bucket")

#     # Create a Source
#     source = TestSource(task_id="test_source", bucket="test_bucket", name="test_source", source="test_source")
#     source.input_folder = "."

#     # Test reading data from the source
#     with open("input.txt", "w") as f:
#         f.write("🟣 test data 🟣")
#     conn.Object("test_bucket", f"{source.input_folder}/input.txt").upload_file("input.txt")
#     assert source.read() == "🟣 test data 🟣"


# @mock_s3
# def test_sink():
#     # Create a mock S3 bucket
#     conn = boto3.resource("s3", region_name="us-east-1")
#     conn.create_bucket(Bucket="test_bucket")

#     # Create a PrintSink
#     sink = PrintSink(task_id="test_sink", bucket="test_bucket", name="test_sink", sink="test_sink")
#     sink.input_folder = "test_folder"

#     # Test creating an output folder
#     sink.create_output_folder("test_bucket", "test_folder")
#     assert "test_folder/" in [obj.key for obj in conn.Bucket("test_bucket").objects.all()]

#     # Test writing data to the sink
#     with open("test_file.txt", "w") as f:
#         f.write("⭕ test data ⭕")

#     conn.Object("test_bucket", f"{sink.input_folder}/data.txt").upload_file("test_file.txt")
#     sink.write()


# @mock_s3
# def test_file_sink():
#     # Create a mock S3 bucket
#     conn = boto3.resource("s3", region_name="us-east-1")
#     conn.create_bucket(Bucket="test_bucket")

#     # Create a Sink
#     sink = TestSink(task_id="test_sink", bucket="test_bucket", name="test_sink", sink="test_sink")
#     sink.input_folder = "."

#     # Test writing data to the sink
#     sink.write()
#     data = open(f"{sink.input_folder}/output.txt").read()
#     assert data == "🟣 test data 🟣"


# @mock_s3
# def test_sync_to_s3():
#     # Create a mock S3 bucket
#     conn = boto3.resource("s3", region_name="us-east-1")
#     conn.create_bucket(Bucket="test_bucket")

#     # Create a Task
#     task = Task(task_id="test_task", bucket="test_bucket", name="test_task")

#     # Create a temporary directory and a file in it
#     with tempfile.TemporaryDirectory() as temp_dir:
#         with open(os.path.join(temp_dir, "test_file.txt"), "w") as f:
#             f.write("✳️ test data ✳️")

#         # Store the data in the S3 bucket
#         task.sync_to_s3(temp_dir)  # Check that the file was stored in the S3 bucket

#         s3_file = conn.Object("test_bucket", f"{task.output_folder}/test_file.txt")
#         assert s3_file.get()["Body"].read().decode("utf-8") == "✳️ test data ✳️"


# @mock_s3
# def test_sync_to_local():
#     # Create a mock S3 bucket
#     conn = boto3.resource("s3", region_name="us-east-1")
#     conn.create_bucket(Bucket="test_bucket")

#     # Create a Task
#     task = Task(task_id="test_task", bucket="test_bucket", name="test_task")

#     # Create a temporary directory and a file in it
#     with tempfile.TemporaryDirectory() as temp_dir:
#         with open(os.path.join(temp_dir, "test_file.txt"), "w") as f:
#             f.write("✳️ test data ✳️")

#         # Store the data in the S3 bucket
#         task.sync_to_s3(temp_dir)

#         # Read the data from the S3 bucket
#         task.input_folder = task.output_folder
#         read_dir = task.sync_to_local()

#         # Check that the file was read from the S3 bucket
#         with open(os.path.join(read_dir, "test_file.txt"), "r") as f:
#             assert f.read() == "✳️ test data ✳️"
