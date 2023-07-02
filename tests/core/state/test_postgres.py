import pytest
import psycopg2
import uuid
from psycopg2 import sql
from geniusrise.core.state import PostgresStateManager

# Define your PostgreSQL connection details as constants
HOST = "localhost"
PORT = 5432
USER = "postgres"
PASSWORD = "postgres"
DATABASE = "geniusrise"
TABLE = "state"
KEY = str(uuid.uuid4())


# Define a fixture for your PostgresStateManager
@pytest.fixture
def postgres_state_manager():
    # Set up the database and table
    conn = psycopg2.connect(host=HOST, port=PORT, user=USER, password=PASSWORD, database=DATABASE)
    with conn.cursor() as cur:
        cur.execute(
            sql.SQL("CREATE TABLE IF NOT EXISTS {} (key TEXT PRIMARY KEY, value JSONB)").format(sql.Identifier(TABLE))
        )
    conn.commit()

    # Yield the PostgresStateManager
    yield PostgresStateManager(HOST, PORT, USER, PASSWORD, DATABASE, TABLE)

    # Tear down the database and table
    # with conn.cursor() as cur:
    #     cur.execute(sql.SQL("DROP TABLE {}").format(sql.Identifier(TABLE)))
    # conn.commit()
    # conn.close()


# Test that the PostgresStateManager can be initialized
def test_postgres_state_manager_init(postgres_state_manager):
    assert postgres_state_manager.conn is not None


# Test that the PostgresStateManager can get state
def test_postgres_state_manager_get_state(postgres_state_manager):
    # First, set some state
    key = KEY
    value = {"test": "data"}
    postgres_state_manager.set_state(key, value)

    # Then, get the state and check that it's correct
    assert postgres_state_manager.get_state(key) == value


# Test that the PostgresStateManager can set state
def test_postgres_state_manager_set_state(postgres_state_manager):
    key = str(uuid.uuid4())
    value = {"test": "data"}
    postgres_state_manager.set_state(key, value)

    # Check that the state was set correctly
    assert postgres_state_manager.get_state(key) == value
