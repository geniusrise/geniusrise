from geniusrise_cli.dag.task import Task, Source, Sink
from airflow import DAG
from airflow.utils.dates import days_ago
import boto3
import csv
import json
import os
import tempfile


class TestSource(Source):
    def __init__(self, input_path: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.input_folder = input_path  # type: ignore

    def read(self) -> None:
        s3 = boto3.client("s3")
        obj = s3.get_object(Bucket=self.bucket, Key=f"{self.input_folder}/input.csv")
        data = obj["Body"].read().decode("utf-8")

        reader = csv.DictReader(data.splitlines())
        # Save the data locally
        local_dir = tempfile.mkdtemp()
        with open(os.path.join(local_dir, "input.json"), "w") as f:
            f.write("\n".join([json.dumps(row) for row in reader]))
        # Sync the local directory to S3
        self.sync_to_s3(local_dir)


class CsvToJson(Task):
    def __call__(self, context: dict) -> None:
        local_dir = self.sync_to_local()
        # Read the data from the local directory
        with open(os.path.join(local_dir, "input.json"), "r") as f:
            data = json.load(f)
        # Save the data locally
        local_dir_output = tempfile.mkdtemp()
        with open(os.path.join(local_dir_output, "csv_to_json.json"), "w") as f:
            f.write("\n".join([json.dumps(row) for row in data]))
        # Sync the local directory to S3
        self.sync_to_s3(local_dir_output)


class TestSink(Sink):
    def write(self) -> None:
        local_dir = self.sync_to_local()
        # Read the data from the local directory
        with open(os.path.join(local_dir, "csv_to_json.json"), "r") as f:
            data = f.read()

        assert data == '"column1"\n"column2"'


def test_pipeline():
    # Create a DAG
    dag = DAG(
        dag_id="test_dag",
        start_date=days_ago(1),
        schedule_interval="@daily",
    )

    # Create a Source, a CsvToJson task, and a Sink
    source = TestSource(
        task_id="test_source",
        bucket="geniusrise-test-bucket",
        name="test_source",
        source="test_source",
        input_path="input_folder",
        dag=dag,
    )
    csv_to_json = CsvToJson(task_id="csv_to_json", bucket="geniusrise-test-bucket", name="csv_to_json", dag=dag)
    sink = TestSink(task_id="test_sink", bucket="geniusrise-test-bucket", name="test_sink", sink="test_sink", dag=dag)

    # Set up the pipeline
    source >> csv_to_json >> sink

    # Store the CSV file in S3
    s3 = boto3.client("s3")
    with open("input.csv", "w") as f:
        writer = csv.DictWriter(f, fieldnames=["column1", "column2"])
        writer.writeheader()
        writer.writerow({"column1": "value1", "column2": "value2"})
    # s3.upload_file("input.csv", "geniusrise-test-bucket", f"{source.input_folder}/input.csv")

    # Test reading data from the source
    source.read()
    local_dir = source.sync_to_local(source.output_folder)
    with open(os.path.join(local_dir, "input.json"), "r") as f:
        assert f.read() == '{"column1": "value1", "column2": "value2"}'

    # Test transforming data from CSV to JSON
    csv_to_json.input_folder = source.output_folder
    csv_to_json({})
    local_dir = csv_to_json.sync_to_local(csv_to_json.output_folder)
    with open(os.path.join(local_dir, "csv_to_json.json"), "r") as f:
        assert f.read() == '"column1"\n"column2"'

    # Test writing data to the sink
    sink.input_folder = csv_to_json.output_folder
    sink.write()
