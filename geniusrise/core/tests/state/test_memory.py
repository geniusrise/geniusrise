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

from geniusrise.core.state import InMemoryState


# Define a fixture for your InMemoryState
@pytest.fixture
def in_memory_state_manager():
    task_id = "test_task"
    return InMemoryState(task_id=task_id)


# Test that the InMemoryState can be initialized
def test_in_memory_state_manager_init(in_memory_state_manager):
    assert in_memory_state_manager.store == {}


# Test that the InMemoryState can get state
def test_in_memory_state_manager_get_state(in_memory_state_manager):
    # First, set some state
    key = "test_key"
    value = {"test": "buffer"}
    in_memory_state_manager.set_state(key, value)

    # Then, get the state and check that it's correct
    assert in_memory_state_manager.get_state(key) == value


# Test that the InMemoryState can set state
def test_in_memory_state_manager_set_state(in_memory_state_manager):
    key = "test_key"
    value = {"test": "buffer"}
    in_memory_state_manager.set_state(key, value)

    # Check that the state was set correctly
    assert in_memory_state_manager.store[key] == value
