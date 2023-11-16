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
from datetime import datetime
from typing import Dict, Optional

import jsonpickle  # type: ignore
import psycopg2  # type: ignore
from geniusrise.core.state import State


class PostgresState(State):
    """
    🗄️ PostgresState: A state manager that stores state in a PostgreSQL database.

    This manager provides a persistent storage solution using a PostgreSQL database.

    Attributes:
        conn (psycopg2.extensions.connection): The PostgreSQL connection.
        table (str): The table to use for storing state data.
    """

    def __init__(
        self,
        task_id: str,
        host: str,
        port: int,
        user: str,
        password: str,
        database: str,
        table: str = "geniusrise_state",
    ) -> None:
        """
        Initialize a new PostgreSQL state manager.

        Args:
            task_id (str): The identifier for the task.
            host (str): The host of the PostgreSQL server.
            port (int): The port of the PostgreSQL server.
            user (str): The user to connect as.
            password (str): The user's password.
            database (str): The database to connect to.
            table (str, optional): The table to use. Defaults to "geniusrise_state".
        """
        super().__init__(task_id)
        self.table = table
        try:
            self.conn = psycopg2.connect(host=host, port=port, user=user, password=password, database=database)
        except psycopg2.Error as e:
            self.log.exception(f"Failed to connect to PostgreSQL: {e}")
            raise
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {self.table} (
                        task_id TEXT,
                        key TEXT,
                        value JSONB,
                        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (task_id, key)
                    );
                    """
                )
            self.conn.commit()
        except psycopg2.Error as e:
            self.log.exception(f"Failed to create table in PostgreSQL: {e}")
            raise

    def get(self, task_id: str, key: str) -> Optional[Dict]:
        """
        Get the state associated with a task and key.

        Args:
            task_id (str): The task identifier.
            key (str): The key to get the state for.

        Returns:
            Optional[Dict]: The state associated with the task and key, or None if not found.
        """
        if self.conn:
            try:
                with self.conn.cursor() as cur:
                    cur.execute(
                        f"SELECT value FROM {self.table} WHERE task_id = %s AND key = %s",
                        (task_id, key),
                    )
                    result = cur.fetchone()
                    return jsonpickle.decode(result[0]) if result else None
            except psycopg2.Error as e:
                self.log.exception(f"Failed to get state from PostgreSQL: {e}")
                raise
        else:
            self.log.exception("No PostgreSQL connection.")
            raise

    def set(self, task_id: str, key: str, value: Dict) -> None:
        """
        Set the state associated with a task and key.

        Args:
            task_id (str): The task identifier.
            key (str): The key to set the state for.
            value (Dict): The state to set.
        """
        if self.conn:
            try:
                with self.conn.cursor() as cur:
                    data = jsonpickle.encode(value)
                    cur.execute(
                        f"""
                        INSERT INTO {self.table} (task_id, key, value, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (task_id, key)
                        DO UPDATE SET value = EXCLUDED.value, updated_at = CURRENT_TIMESTAMP;
                        """,
                        (
                            task_id,
                            key,
                            json.dumps(data),
                            datetime.utcnow(),
                            datetime.utcnow(),
                        ),
                    )
                self.conn.commit()
            except psycopg2.Error as e:
                self.log.exception(f"Failed to set state in PostgreSQL: {e}")
                raise
        else:
            self.log.exception("No PostgreSQL connection.")
