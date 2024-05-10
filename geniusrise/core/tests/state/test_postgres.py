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

import uuid
import psycopg2
import pytest
from psycopg2 import sql

from geniusrise.core.state import PostgresState

# Define your PostgreSQL connection details as constants
HOST = "localhost"
PORT = 5432
USER = "postgres"
PASSWORD = "postgres"
DATABASE = "geniusrise"
TABLE = "state"
TASK_ID = str(uuid.uuid4())  # Unique task identifier for testing


# Define a fixture for your PostgresState
@pytest.fixture
def postgres_state_manager():
    # Set up the database and table
    conn = psycopg2.connect(host=HOST, port=PORT, user=USER, password=PASSWORD, database=DATABASE)
    with conn.cursor() as cur:
        cur.execute(
            sql.SQL(
                "CREATE TABLE IF NOT EXISTS {} (task_id TEXT, key TEXT, value JSONB, created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (task_id, key))"
            ).format(sql.Identifier(TABLE))
        )
    conn.commit()

    # Yield the PostgresState
    yield PostgresState(
        task_id=TASK_ID,
        host=HOST,
        port=PORT,
        user=USER,
        password=PASSWORD,
        database=DATABASE,
        table=TABLE,
    )

    # Tear down the database and table
    # with conn.cursor() as cur:
    #     cur.execute(sql.SQL("DROP TABLE {}").format(sql.Identifier(TABLE)))
    # conn.commit()
    # conn.close()


# Test that the PostgresState can be initialized
def test_postgres_state_manager_init(postgres_state_manager):
    assert postgres_state_manager.conn is not None


# Test that the PostgresState can get state
def test_postgres_state_manager_get_state(postgres_state_manager):
    key = str(uuid.uuid4())
    value = {"test": "data"}
    postgres_state_manager.set_state(key, value)

    # Then, get the state and check that it's correct
    assert postgres_state_manager.get_state(key)["test"] == "data"


# Test that the PostgresState can set state
def test_postgres_state_manager_set_state(postgres_state_manager):
    key = str(uuid.uuid4())
    value = {"test": "data"}
    postgres_state_manager.set_state(key, value)

    # Check that the state was set correctly
    assert postgres_state_manager.get_state(key)["test"] == "data"
