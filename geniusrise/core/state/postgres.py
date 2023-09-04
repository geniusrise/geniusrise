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

import json
from typing import Dict, Optional
from datetime import datetime

import jsonpickle
import psycopg2

from geniusrise.core.state import State


class PostgresState(State):
    """
    🗄️ **PostgresState**: A state manager that stores state in a PostgreSQL database.

    This manager provides a persistent storage solution using a PostgreSQL database.

    ## Attributes:
    - `conn` (psycopg2.extensions.connection): The PostgreSQL connection.

    ## Usage:
    ```python
    manager = PostgresState(host="localhost", port=5432, user="admin", password="password", database="mydb")
    manager.set_state("user123", {"status": "active"})
    state = manager.get_state("user123")
    print(state)  # Outputs: {"status": "active"}
    ```


    Ensure PostgreSQL is accessible and the table exists.
    """

    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        database: str,
        table: str = "geniusrise_state",
    ) -> None:
        """
        💥 Initialize a new PostgreSQL state manager.

        Args:
            host (str): The host of the PostgreSQL server.
            port (int): The port of the PostgreSQL server.
            user (str): The user to connect as.
            password (str): The user's password.
            database (str): The database to connect to.
            table (str, optional): The table to use. Defaults to "geniusrise_state".
        """
        super().__init__()
        self.table = table
        try:
            self.conn = psycopg2.connect(host=host, port=port, user=user, password=password, database=database)
        except psycopg2.Error as e:
            self.log.exception(f"🚫 Failed to connect to PostgreSQL: {e}")
            raise
            self.conn = None
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {self.table} (
                        key TEXT PRIMARY KEY,
                        value JSONB,
                        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                    );
                    """
                )
            self.conn.commit()
        except psycopg2.Error as e:
            self.log.exception(f"🚫 Failed to create table in PostgreSQL: {e}")
            raise

    def get(self, key: str) -> Optional[Dict]:
        """
        📖 Get the state associated with a key.

        Args:
            key (str): The key to get the state for.

        Returns:
            Dict: The state associated with the key, or None if not found.

        Raises:
            Exception: If there's an error accessing PostgreSQL.
        """
        if self.conn:
            try:
                with self.conn.cursor() as cur:
                    cur.execute(f"SELECT value FROM {self.table} WHERE key = %s", (key,))
                    result = cur.fetchone()
                    return jsonpickle.decode(result[0]["data"]) if result else None
            except psycopg2.Error as e:
                self.log.exception(f"🚫 Failed to get state from PostgreSQL: {e}")
                raise
        else:
            self.log.exception("🚫 No PostgreSQL connection.")
            raise

    def set(self, key: str, value: Dict) -> None:
        """
        📝 Set the state associated with a key.

        Args:
            key (str): The key to set the state for.
            value (Dict): The state to set.

        Raises:
            Exception: If there's an error accessing PostgreSQL.
        """
        if self.conn:
            try:
                with self.conn.cursor() as cur:
                    data = {"data": jsonpickle.encode(value)}
                    cur.execute(
                        f"""
                        INSERT INTO {self.table} (key, value, created_at, updated_at)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (key)
                        DO UPDATE SET value = EXCLUDED.value, updated_at = %s;
                        """,
                        (key, json.dumps(data), datetime.utcnow(), datetime.utcnow(), datetime.utcnow()),
                    )
                self.conn.commit()
            except psycopg2.Error as e:
                self.log.exception(f"🚫 Failed to set state in PostgreSQL: {e}")
                raise
        else:
            self.log.error("🚫 No PostgreSQL connection.")
