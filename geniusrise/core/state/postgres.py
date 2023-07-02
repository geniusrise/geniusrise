import psycopg2
from typing import Dict, Optional
import logging
import json

from geniusrise.core.state import StateManager

log = logging.getLogger(__name__)


class PostgresStateManager(StateManager):
    """
    A state manager that stores state in a PostgreSQL database.

    Attributes:
        conn (psycopg2.extensions.connection): The PostgreSQL connection.
    """

    def __init__(self, host: str, port: int, user: str, password: str, database: str, table: str = "geniusrise_state"):
        """
        Initialize a new PostgreSQL state manager.

        Args:
            host (str): The host of the PostgreSQL server.
            port (int): The port of the PostgreSQL server.
            user (str): The user to connect as.
            password (str): The user's password.
            database (str): The database to connect to.
        """
        super().__init__()
        self.table = table
        try:
            self.conn = psycopg2.connect(host=host, port=port, user=user, password=password, database=database)
        except psycopg2.Error as e:
            log.error(f"Failed to connect to PostgreSQL: {e}")
            self.conn = None

    def get_state(self, key: str) -> Optional[Dict]:
        """
        Get the state associated with a key.

        Args:
            key (str): The key to get the state for.

        Returns:
            Dict: The state associated with the key.
        """
        if self.conn:
            try:
                with self.conn.cursor() as cur:
                    cur.execute(
                        "SELECT value FROM %s WHERE id = %s",
                        (
                            self.table,
                            key,
                        ),
                    )
                    result = cur.fetchone()
                    return json.loads(result[0]) if result else None
            except psycopg2.Error as e:
                log.error(f"Failed to get state from PostgreSQL: {e}")
                return None
        else:
            log.error("No PostgreSQL connection.")
            return None

    def set_state(self, key: str, value: Dict) -> None:
        """
        Set the state associated with a key.

        Args:
            key (str): The key to set the state for.
            value (Dict): The state to set.
        """
        if self.conn:
            try:
                with self.conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO %s (key, value) VALUES (%s, %s)",
                        (self.table, key, json.dumps(value)),
                    )
                self.conn.commit()
            except psycopg2.Error as e:
                log.error(f"Failed to set state in PostgreSQL: {e}")
        else:
            log.error("No PostgreSQL connection.")
