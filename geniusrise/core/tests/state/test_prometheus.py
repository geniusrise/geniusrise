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
from geniusrise.core.state import PrometheusState

# Define your Prometheus PushGateway URL as a constant
GATEWAY_URL = "http://localhost:9091"


# Define a fixture for your PrometheusState
@pytest.fixture
def prometheus_state_manager():
    yield PrometheusState(GATEWAY_URL)


# Test that the PrometheusState can be initialized
def test_prometheus_state_manager_init(prometheus_state_manager):
    assert prometheus_state_manager.registry is not None
    assert prometheus_state_manager.gateway == GATEWAY_URL


# Test that the PrometheusState can set state (metrics)
def test_prometheus_state_manager_set_state(prometheus_state_manager):
    key = "test_key"
    value = {"some_metric": 1}
    try:
        prometheus_state_manager.set_state(key, value)
    except Exception as e:
        pytest.fail(f"Failed to push metrics to Prometheus: {e}")


# Test that the PrometheusState get state returns None
def test_prometheus_state_manager_get_state(prometheus_state_manager):
    assert prometheus_state_manager.get("some_key") is None
