import boto3
from typing import Dict, Optional
import logging
import json

from geniusrise.core.state import StateManager

log = logging.getLogger(__name__)


class DynamoDBStateManager(StateManager):
    """
    A state manager that stores state in DynamoDB.

    Attributes:
        dynamodb (boto3.resources.factory.dynamodb.ServiceResource): The DynamoDB service resource.
        table (boto3.resources.factory.dynamodb.Table): The DynamoDB table.
    """

    def __init__(self, table_name: str, region_name: str):
        """
        Initialize a new DynamoDB state manager.

        Args:
            table_name (str): The name of the DynamoDB table.
            region_name (str): The name of the AWS region.
        """
        super().__init__()
        try:
            self.dynamodb = boto3.resource("dynamodb", region_name=region_name)
            self.table = self.dynamodb.Table(table_name)
        except Exception as e:
            log.error(f"Failed to connect to DynamoDB: {e}")
            self.dynamodb = None
            self.table = None

    def get_state(self, key: str) -> Optional[Dict]:
        """
        Get the state associated with a key.

        Args:
            key (str): The key to get the state for.

        Returns:
            Dict: The state associated with the key.
        """
        if self.table:
            try:
                response = self.table.get_item(Key={"id": key})
                return json.loads(response["Item"]["value"]) if "Item" in response else None
            except Exception as e:
                log.error(f"Failed to get state from DynamoDB: {e}")
                return None
        else:
            log.error("No DynamoDB table.")
            return None

    def set_state(self, key: str, value: Dict) -> None:
        """
        Set the state associated with a key.

        Args:
            key (str): The key to set the state for.
            value (Dict): The state to set.
        """
        if self.table:
            try:
                self.table.put_item(Item={"id": key, "value": json.dumps(value)})
            except Exception as e:
                log.error(f"Failed to set state in DynamoDB: {e}")
        else:
            log.error("No DynamoDB table.")
