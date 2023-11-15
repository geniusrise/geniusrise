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

import jsonpickle
import boto3
from typing import Dict, Optional, Any

from geniusrise.core.state import State


class DynamoDBState(State):
    """
    DynamoDBState: A state manager that stores state in DynamoDB.

    Attributes:
        dynamodb (boto3.resources.factory.dynamodb.ServiceResource): The DynamoDB service resource.
        table (boto3.resources.factory.dynamodb.Table): The DynamoDB table.
    """

    def __init__(self, task_id: str, table_name: str, region_name: str) -> None:
        """
        Initialize a new DynamoDB state manager.

        Args:
            task_id (str): The task identifier.
            table_name (str): The name of the DynamoDB table.
            region_name (str): The name of the AWS region.
        """
        super().__init__(task_id=task_id)
        try:
            self.dynamodb = boto3.resource("dynamodb", region_name=region_name)
            self.table = self.dynamodb.Table(table_name)
        except Exception as e:
            self.log.exception(f"Failed to connect to DynamoDB: {e}")
            raise

    def get(self, task_id: str, key: str) -> Optional[Dict[str, Any]]:
        """
        Get the state associated with a task and key.

        Args:
            task_id (str): The task identifier.
            key (str): The key to get the state for.

        Returns:
            Optional[Dict[str, Any]]: The state associated with the task and key, if it exists.
        """
        if self.table:
            try:
                response = self.table.get_item(Key={"id": f"{task_id}:{key}"})
                return jsonpickle.decode(response["Item"]["value"]) if "Item" in response else None
            except Exception as e:
                self.log.exception(f"Failed to get state from DynamoDB: {e}")
                raise
        else:
            self.log.error("No DynamoDB table.")
            raise Exception("No DynamoDB table.")

    def set(self, task_id: str, key: str, value: Dict[str, Any]) -> None:
        """
        Set the state associated with a task and key.

        Args:
            task_id (str): The task identifier.
            key (str): The key to set the state for.
            value (Dict[str, Any]): The state to set.
        """
        if self.table:
            try:
                self.table.put_item(Item={"id": f"{task_id}:{key}", "value": jsonpickle.encode(value)})
            except Exception as e:
                self.log.exception(f"Failed to set state in DynamoDB: {e}")
                raise
        else:
            self.log.error("No DynamoDB table.")
            raise Exception("No DynamoDB table.")
