# 🧠 Geniusrise
# Copyright (C) 2023  geniusrise.ai
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import boto3
import pytest
from botocore.exceptions import ClientError

from geniusrise.core.state import DynamoDBState

# Define your DynamoDB connection details as constants
TABLE_NAME = "test_table"
REGION_NAME = "ap-south-1"
TASK_ID = "test_task"


# Define a fixture for your DynamoDBState
@pytest.fixture
def dynamodb_state_manager():
    # Set up the DynamoDB table
    dynamodb = boto3.resource("dynamodb", region_name=REGION_NAME)
    try:
        table = dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
            ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
        )
        # Wait until the table exists
        table.meta.client.get_waiter("table_exists").wait(TableName=TABLE_NAME)
    except ClientError as e:
        if e.response["Error"]["Code"] != "ResourceInUseException":
            raise

    # Yield the DynamoDBState with a task_id
    yield DynamoDBState(task_id=TASK_ID, table_name=TABLE_NAME, region_name=REGION_NAME)

    # Tear down the DynamoDB table (optional)
    # table.delete()


# Test that the DynamoDBState can be initialized
def test_dynamodb_state_manager_init(dynamodb_state_manager):
    assert dynamodb_state_manager.dynamodb is not None
    assert dynamodb_state_manager.table is not None


# Test that the DynamoDBState can get state
def test_dynamodb_state_manager_get_state(dynamodb_state_manager):
    key = "test_key"
    value = {"test": "buffer"}
    dynamodb_state_manager.set_state(key, value)

    # Get the state and check that it's correct
    assert dynamodb_state_manager.get_state(key)["test"] == "buffer"


# Test that the DynamoDBState can set state
def test_dynamodb_state_manager_set_state(dynamodb_state_manager):
    key = "test_key"
    value = {"test": "buffer"}
    dynamodb_state_manager.set_state(key, value)

    # Check that the state was set correctly
    assert dynamodb_state_manager.get_state(key)["test"] == "buffer"
