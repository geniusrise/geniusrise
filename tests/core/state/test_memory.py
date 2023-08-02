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
