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

import boto3
import pytest
from botocore.exceptions import ClientError

from geniusrise.core.state import DynamoDBState

# Define your DynamoDB connection details as constants
TABLE_NAME = "test_table"
REGION_NAME = "ap-south-1"


# Define a fixture for your DynamoDBState
@pytest.fixture
def dynamodb_state_manager():
    # Set up the DynamoDB table
    dynamodb = boto3.resource("dynamodb", region_name=REGION_NAME)
    try:
        table = dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {"AttributeName": "id", "KeyType": "HASH"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "id", "AttributeType": "S"},
            ],
            ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
        )
        # Wait until the table exists, this will take a minute or so
        table.meta.client.get_waiter("table_exists").wait(TableName=TABLE_NAME)
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            pass
        else:
            raise

    # Yield the DynamoDBState
    yield DynamoDBState(TABLE_NAME, REGION_NAME)

    # # Tear down the DynamoDB table
    # table = dynamodb.Table(TABLE_NAME)
    # table.delete()


# Test that the DynamoDBState can be initialized
def test_dynamodb_state_manager_init(dynamodb_state_manager):
    assert dynamodb_state_manager.dynamodb is not None
    assert dynamodb_state_manager.table is not None


# Test that the DynamoDBState can get state
def test_dynamodb_state_manager_get_state(dynamodb_state_manager):
    # First, set some state
    key = "test_key"
    value = {"test": "data"}
    dynamodb_state_manager.set_state(key, value)

    # Then, get the state and check that it's correct
    assert dynamodb_state_manager.get_state(key) == value


# Test that the DynamoDBState can set state
def test_dynamodb_state_manager_set_state(dynamodb_state_manager):
    key = "test_key"
    value = {"test": "data"}
    dynamodb_state_manager.set_state(key, value)

    # Check that the state was set correctly
    assert dynamodb_state_manager.get_state(key) == value
