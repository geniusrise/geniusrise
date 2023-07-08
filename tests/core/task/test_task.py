import uuid

import pytest

from geniusrise.core.data import BatchInputConfig, BatchOutputConfig
from geniusrise.core.task import Task

BUCKET = "geniusrise-test-bucket"
S3_FOLDER = "csv_to_json-6t7lqqpj"


class TestTask(Task):
    def fetch_test(self):
        """This is a test method."""
        return "test"


# Define a fixture for your Task
@pytest.fixture
def task(tmpdir):
    task = TestTask()
    task.input_config = BatchInputConfig(tmpdir, BUCKET, S3_FOLDER)
    task.output_config = BatchOutputConfig(tmpdir, BUCKET, S3_FOLDER)
    return task


# Test that the Task can be initialized
def test_task_init(task):
    assert isinstance(task.id, uuid.UUID)
    assert isinstance(task.input_config, BatchInputConfig)
    assert isinstance(task.output_config, BatchOutputConfig)


# Test that the Task can execute a method
def test_task_execute(task):
    # Define a method for the task to execute
    def fetch_test():
        return "test"

    task.fetch_test = fetch_test

    # Execute the method and check that it returns the correct result
    assert task.execute("fetch_test") == "test"


# Test that the TestTask can get its methods
def test_test_task_get_methods(task):
    # Get the methods and check that they include the test method
    methods = task.get_methods()

    assert any(name == "fetch_test" for name, _, _ in methods)


# Test that the TestTask can print its help
def test_test_task_print_help(task, capsys):
    # Print the help and check that it includes the test method
    task.print_help()
    captured = capsys.readouterr()
    assert "fetch_test" in captured.out
