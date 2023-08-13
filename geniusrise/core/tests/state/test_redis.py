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
