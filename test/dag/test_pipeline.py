from moto import mock_s3
from geniusrise_cli.dag.task import Source, Sink
from airflow import DAG
from airflow.utils.dates import days_ago
import boto3
from typing import Any


class TestSource(Source):
    def read(self) -> Any:
        with open("./input.txt", "r") as f:
            return f.read()


class TestSink(Sink):
    def write(self) -> None:
        with open("./output.txt", "w") as f:
            f.write("⏹️ test data ⏹️")


@mock_s3
def test_pipeline():
    # Create a mock S3 bucket
    conn = boto3.resource("s3", region_name="us-east-1")
    conn.create_bucket(Bucket="test_bucket")

    # Create a DAG
    dag = DAG(
        dag_id="test_dag",
        start_date=days_ago(1),
        schedule_interval="@daily",
    )

    # Create a Source and a Sink
    source = TestSource(task_id="test_source", bucket="test_bucket", name="test_source", source="test_source", dag=dag)
    sink = TestSink(task_id="test_sink", bucket="test_bucket", name="test_sink", sink="test_sink", dag=dag)

    # Set up the pipeline
    source >> sink

    # Test reading data from the source
    with open("input.txt", "w") as f:
        f.write("⏹️ test data ⏹️")
    conn.Object("test_bucket", f"{source.input_folder}/input.txt").upload_file("input.txt")
    assert source.read() == "⏹️ test data ⏹️"

    # Test writing data to the sink
    sink.input_folder = source.output_folder
    sink.write()

    data = open("./output.txt").read()
    assert data == "⏹️ test data ⏹️"
