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

import logging
from typing import Dict, Optional

import boto3
import jsonpickle

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
            log.exception(f"Failed to connect to DynamoDB: {e}")
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
                return jsonpickle.decode(response["Item"]["value"]) if "Item" in response else None
            except Exception as e:
                log.exception(f"Failed to get state from DynamoDB: {e}")
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
                self.table.put_item(Item={"id": key, "value": jsonpickle.encode(value)})
            except Exception as e:
                log.exception(f"Failed to set state in DynamoDB: {e}")
        else:
            log.error("No DynamoDB table.")
