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
import logging
from typing import Dict, Optional

import jsonpickle
import psycopg2

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
            log.exception(f"Failed to connect to PostgreSQL: {e}")
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
                    cur.execute(f"SELECT value FROM {self.table} WHERE key = '{key}'")
                    result = cur.fetchone()
                    return jsonpickle.decode(result[0]["data"]) if result else None
            except psycopg2.Error as e:
                log.exception(f"Failed to get state from PostgreSQL: {e}")
                return None
        else:
            log.exception("No PostgreSQL connection.")
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
                    data = {"data": jsonpickle.encode(value)}
                    cur.execute(
                        f"""
                        INSERT INTO {self.table} (key, value)
                        VALUES (%s, %s)
                        ON CONFLICT (key)
                        DO UPDATE SET value = EXCLUDED.value;
                        """,
                        (key, json.dumps(data)),
                    )
                self.conn.commit()
            except psycopg2.Error as e:
                log.exception(f"Failed to set state in PostgreSQL: {e}")
        else:
            log.error("No PostgreSQL connection.")
