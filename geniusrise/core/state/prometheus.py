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

from prometheus_client import push_to_gateway
from geniusrise.core.state import State
import logging
from typing import Dict, Optional


class PrometheusState(State):
    """
    📊 **PrometheusState**: A state manager that pushes metrics to Prometheus.

    This manager is responsible for pushing metrics to a Prometheus PushGateway.

    ## Attributes:
    - `registry` (CollectorRegistry): The Prometheus CollectorRegistry.
    - `gateway` (str): The Prometheus PushGateway URL.

    ## Usage:
    ```python
    manager = PrometheusState(gateway="http://localhost:9091")
    manager.set_state("some_key", {"some_metric": 1})
    ```
    """

    def __init__(self, gateway: str) -> None:
        """
        💥 Initialize a new Prometheus state manager.

        Args:
            gateway (str): The URL of the Prometheus PushGateway.
        """
        super().__init__()
        self.log = logging.getLogger(self.__class__.__name__)
        self.gateway = gateway

    def get(self, key: str) -> Optional[Dict]:
        """
        📖 Get the state associated with a key.

        Since this is a metrics-only state manager, this method does nothing.

        Args:
            key (str): The key to get the state for.

        Returns:
            None
        """
        self.log.warning("🚫 Get operation is not supported.")
        return None

    def set(self, key: str, value: Dict) -> None:
        """
        📝 Set the state associated with a key.

        This method pushes metrics to the Prometheus PushGateway.

        Args:
            key (str): The key to set the state for.
            value (Dict): The state to set, which should contain metrics data.
        """
        try:
            push_to_gateway(self.gateway, job=key, registry=self.registry)
            self.log.info(f"✅ Metrics for key '{key}' pushed to Prometheus.")
        except Exception as e:
            self.log.exception(f"🚫 Failed to push metrics to Prometheus: {e}")
            raise
