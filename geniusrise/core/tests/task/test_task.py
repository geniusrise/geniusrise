# 🧠 Geniusrise
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

# # 🧠 Geniusrise
# # Copyright (C) 2023  geniusrise.ai
# #
# # This program is free software: you can redistribute it and/or modify
# # it under the terms of the GNU Affero General Public License as published by
# # the Free Software Foundation, either version 3 of the License, or
# # (at your option) any later version.
# #
# # This program is distributed in the hope that it will be useful,
# # but WITHOUT ANY WARRANTY; without even the implied warranty of
# # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# # GNU Affero General Public License for more details.
# #
# # You should have received a copy of the GNU Affero General Public License
# # along with this program.  If not, see <http://www.gnu.org/licenses/>.

# import uuid

# import pytest

# from geniusrise.core.data import BatchInput, BatchOutput
# from geniusrise.core.task import Task

# BUCKET = "geniusrise-test-bucket"
# S3_FOLDER = "whatever"


# class TestTask(Task):
#     def fetch_test(self):
#         """This is a test method."""
#         return "test"


# # Define a fixture for your Task
# @pytest.fixture
# def task(tmpdir):
#     task = TestTask()
#     task.input = BatchInput(tmpdir, BUCKET, S3_FOLDER)
#     task.output = BatchOutput(tmpdir, BUCKET, S3_FOLDER)
#     return task


# # Test that the Task can be initialized
# def test_task_init(task):
#     assert isinstance(task.id, uuid.UUID)
#     assert isinstance(task.input, BatchInput)
#     assert isinstance(task.output, BatchOutput)


# # Test that the Task can execute a method
# def test_task_execute(task):
#     # Define a method for the task to execute
#     def fetch_test():
#         return "test"

#     task.fetch_test = fetch_test

#     # Execute the method and check that it returns the correct result
#     assert task.execute("fetch_test") == "test"


# # Test that the TestTask can get its methods
# def test_test_task_get_methods(task):
#     # Get the methods and check that they include the test method
#     methods = task.get_methods()

#     assert any(name == "fetch_test" for name, _, _ in methods)


# # Test that the TestTask can print its help
# def test_test_task_print_help(task, capsys):
#     # Print the help and check that it includes the test method
#     task.print_help()
#     captured = capsys.readouterr()
#     assert "fetch_test" in captured.out
