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

import pytest
import uuid

from geniusrise.core.state import RedisState

# Define your Redis connection details as constants
HOST = "localhost"
PORT = 6379
DB = 0

# Generate a unique task_id for testing
TASK_ID = str(uuid.uuid4())


# Define a fixture for your RedisState
@pytest.fixture
def redis_state_manager():
    return RedisState(task_id=TASK_ID, host=HOST, port=PORT, db=DB)


# Test that the RedisState can be initialized
def test_redis_state_manager_init(redis_state_manager):
    assert redis_state_manager.redis is not None


# Test that the RedisState can get state
def test_redis_state_manager_get_state(redis_state_manager):
    # First, set some state
    key = "test_key"
    value = {"test": "buffer"}
    redis_state_manager.set_state(key, value)

    # Then, get the state and check that it's correct
    assert redis_state_manager.get_state(key) == value


# Test that the RedisState can set state
def test_redis_state_manager_set_state(redis_state_manager):
    key = "test_key"
    value = {"test": "buffer"}
    redis_state_manager.set_state(key, value)

    # Check that the state was set correctly
    assert redis_state_manager.get_state(key) == value
