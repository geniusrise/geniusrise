import boto3
import pytest
from botocore.exceptions import ClientError

from geniusrise.core.state import DynamoDBStateManager

# Define your DynamoDB connection details as constants
TABLE_NAME = "test_table"
REGION_NAME = "ap-south-1"


# Define a fixture for your DynamoDBStateManager
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

    # Yield the DynamoDBStateManager
    yield DynamoDBStateManager(TABLE_NAME, REGION_NAME)

    # # Tear down the DynamoDB table
    # table = dynamodb.Table(TABLE_NAME)
    # table.delete()


# Test that the DynamoDBStateManager can be initialized
def test_dynamodb_state_manager_init(dynamodb_state_manager):
    assert dynamodb_state_manager.dynamodb is not None
    assert dynamodb_state_manager.table is not None


# Test that the DynamoDBStateManager can get state
def test_dynamodb_state_manager_get_state(dynamodb_state_manager):
    # First, set some state
    key = "test_key"
    value = {"test": "data"}
    dynamodb_state_manager.set_state(key, value)

    # Then, get the state and check that it's correct
    assert dynamodb_state_manager.get_state(key) == value


# Test that the DynamoDBStateManager can set state
def test_dynamodb_state_manager_set_state(dynamodb_state_manager):
    key = "test_key"
    value = {"test": "data"}
    dynamodb_state_manager.set_state(key, value)

    # Check that the state was set correctly
    assert dynamodb_state_manager.get_state(key) == value
