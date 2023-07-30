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

# from typing import Any

# import boto3
# from airflow import DAG
# from airflow.utils.dates import days_ago
# from moto import mock_s3

# from geniusrise.dag.task import Sink, Source


# class TestSource(Source):
#     def read(self) -> Any:
#         with open("./input.txt", "r") as f:
#             return f.read()


# class TestSink(Sink):
#     def write(self) -> None:
#         with open("./output.txt", "w") as f:
#             f.write("⏹️ test data ⏹️")


# @mock_s3
# def test_pipeline():
#     # Create a mock S3 bucket
#     conn = boto3.resource("s3", region_name="us-east-1")
#     conn.create_bucket(Bucket="test_bucket")

#     # Create a DAG
#     dag = DAG(
#         dag_id="test_dag",
#         start_date=days_ago(1),
#         schedule_interval="@daily",
#     )

#     # Create a Source and a Sink
#     source = TestSource(tas
# k_id="test_source", bucket="test_bucket", name="test_source", source="test_source", dag=dag)
#     sink = TestSink(task_id="test_sink", bucket="test_bucket", name="test_sink", sink="test_sink", dag=dag)

#     # Set up the pipeline
#     source >> sink

#     # Test reading data from the source
#     with open("input.txt", "w") as f:
#         f.write("⏹️ test data ⏹️")
#     conn.Object("test_bucket", f"{source.input_folder}/input.txt").upload_file("input.txt")
#     assert source.read() == "⏹️ test data ⏹️"

#     # Test writing data to the sink
#     sink.input_folder = source.output_folder
#     sink.write()

#     data = open("./output.txt").read()
#     assert data == "⏹️ test data ⏹️"
