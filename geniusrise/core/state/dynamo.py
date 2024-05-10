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
