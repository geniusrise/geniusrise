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

from typing import Dict, Optional

import boto3
import jsonpickle

from geniusrise.core.state import State


class DynamoDBState(State):
    """
    🗄️ **DynamoDBState**: A state manager that stores state in DynamoDB.

    Attributes:
        dynamodb (boto3.resources.factory.dynamodb.ServiceResource): The DynamoDB service resource.
        table (boto3.resources.factory.dynamodb.Table): The DynamoDB table.

    Usage:
    ```python
    manager = DynamoDBState("my_table", "us-west-1")
    manager.set_state("key123", {"status": "active"})
    state = manager.get_state("key123")
    print(state)  # Outputs: {"status": "active"}
    ```

    Note:
    - Ensure DynamoDB is accessible and the table exists.
    """

    def __init__(self, table_name: str, region_name: str) -> None:
        """
        💥 Initialize a new DynamoDB state manager.

        Args:
            table_name (str): The name of the DynamoDB table.
            region_name (str): The name of the AWS region.
        """
        super().__init__()
        try:
            self.dynamodb = boto3.resource("dynamodb", region_name=region_name)
            self.table = self.dynamodb.Table(table_name)
        except Exception as e:
            self.log.exception(f"🚫 Failed to connect to DynamoDB: {e}")
            raise
            self.dynamodb = None
            self.table = None

    def get(self, key: str) -> Optional[Dict]:
        """
        📖 Get the state associated with a key.

        Args:
            key (str): The key to get the state for.

        Returns:
            Dict: The state associated with the key, or None if not found.

        Raises:
            Exception: If there's an error accessing DynamoDB.
        """
        if self.table:
            try:
                response = self.table.get_item(Key={"id": key})
                return jsonpickle.decode(response["Item"]["value"]) if "Item" in response else None
            except Exception as e:
                self.log.exception(f"🚫 Failed to get state from DynamoDB: {e}")
                raise
        else:
            self.log.exception("🚫 No DynamoDB table.")
            raise

    def set(self, key: str, value: Dict) -> None:
        """
        📝 Set the state associated with a key.

        Args:
            key (str): The key to set the state for.
            value (Dict): The state to set.

        Raises:
            Exception: If there's an error accessing DynamoDB.
        """
        if self.table:
            try:
                self.table.put_item(Item={"id": key, "value": jsonpickle.encode(value)})
            except Exception as e:
                self.log.exception(f"🚫 Failed to set state in DynamoDB: {e}")
                raise
        else:
            self.log.exception("🚫 No DynamoDB table.")
            raise
