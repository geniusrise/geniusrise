import pytest

from geniusrise.core.state import InMemoryStateManager


# Define a fixture for your InMemoryStateManager
@pytest.fixture
def in_memory_state_manager():
    return InMemoryStateManager()


# Test that the InMemoryStateManager can be initialized
def test_in_memory_state_manager_init(in_memory_state_manager):
    assert in_memory_state_manager.store == {}


# Test that the InMemoryStateManager can get state
def test_in_memory_state_manager_get_state(in_memory_state_manager):
    # First, set some state
    key = "test_key"
    value = {"test": "data"}
    in_memory_state_manager.set_state(key, value)

    # Then, get the state and check that it's correct
    assert in_memory_state_manager.get_state(key) == value


# Test that the InMemoryStateManager can set state
def test_in_memory_state_manager_set_state(in_memory_state_manager):
    key = "test_key"
    value = {"test": "data"}
    in_memory_state_manager.set_state(key, value)

    # Check that the state was set correctly
    assert in_memory_state_manager.store[key] == value
