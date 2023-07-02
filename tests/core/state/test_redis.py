import pytest
from geniusrise.core.state import RedisStateManager

# Define your Redis connection details as constants
HOST = "localhost"
PORT = 6379
DB = 0


# Define a fixture for your RedisStateManager
@pytest.fixture
def redis_state_manager():
    return RedisStateManager(HOST, PORT, DB)


# Test that the RedisStateManager can be initialized
def test_redis_state_manager_init(redis_state_manager):
    assert redis_state_manager.redis is not None


# Test that the RedisStateManager can get state
def test_redis_state_manager_get_state(redis_state_manager):
    # First, set some state
    key = "test_key"
    value = {"test": "data"}
    redis_state_manager.set_state(key, value)

    # Then, get the state and check that it's correct
    assert redis_state_manager.get_state(key) == value


# Test that the RedisStateManager can set state
def test_redis_state_manager_set_state(redis_state_manager):
    key = "test_key"
    value = {"test": "data"}
    redis_state_manager.set_state(key, value)

    # Check that the state was set correctly
    assert redis_state_manager.get_state(key) == value
