import redis  # type: ignore
import psycopg2
import boto3
from abc import ABC, abstractmethod
from typing import Any, Dict


class StateManager(ABC):
    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def get_state(self, key: str) -> Any:
        pass

    @abstractmethod
    def set_state(self, key: str, value: Any):
        pass


class InMemoryStateManager(StateManager):
    def __init__(self):
        self.store: Dict[str, str] = {}

    def get_state(self, key: str) -> str:
        return self.store.get(key, "")

    def set_state(self, key: str, value: str) -> None:
        self.store[key] = value


class RedisStateManager(StateManager):
    def __init__(self, host: str, port: int, db: int):
        super().__init__()
        self.redis = redis.Redis(host=host, port=port, db=db)

    def get_state(self, key: str) -> Any:
        return self.redis.get(key)

    def set_state(self, key: str, value: Any):
        self.redis.set(key, value)


class PostgresStateManager(StateManager):
    def __init__(self, host: str, port: int, user: str, password: str, database: str):
        super().__init__()
        self.conn = psycopg2.connect(host=host, port=port, user=user, password=password, database=database)

    def get_state(self, key: str) -> Any:
        with self.conn.cursor() as cur:
            cur.execute("SELECT value FROM state WHERE id = %s", (key))
            result = cur.fetchone()
            return result[0] if result else None

    def set_state(self, key: str, value: Any):
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO state (key, value) VALUES (%s, %s)",
                (key, value),
            )
        self.conn.commit()


class DynamoDBStateManager(StateManager):
    def __init__(self, table_name: str, region_name: str):
        super().__init__()
        self.dynamodb = boto3.resource("dynamodb", region_name=region_name)
        self.table = self.dynamodb.Table(table_name)

    def get_state(self, key: str) -> Any:
        response = self.table.get_item(Key={"id": key})
        return response["Item"]["value"] if "Item" in response else None

    def set_state(self, key: str, value: Any):
        self.table.put_item(Item={"id": key, "value": value})
