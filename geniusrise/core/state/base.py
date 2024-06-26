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

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import threading
from prometheus_client import start_http_server, REGISTRY
from prometheus_client import process_collector, platform_collector


class PrometheusMetricsServer(threading.Thread):
    def __init__(self, port: int = 8282):
        super().__init__()
        self.port = port
        self.daemon = True
        self.log = logging.getLogger(self.__class__.__name__)

    def run(self):
        self.log.info(f"Starting prometheus server at port {self.port}")
        # Check if ProcessCollector and PlatformCollector have already been registered
        if not any(
            isinstance(collector, process_collector.ProcessCollector)
            for collector in REGISTRY._collector_to_names.keys()
        ):
            process_collector.ProcessCollector()

        if not any(
            isinstance(collector, platform_collector.PlatformCollector)
            for collector in REGISTRY._collector_to_names.keys()
        ):
            platform_collector.PlatformCollector()

        # Start HTTP server for Prometheus metrics
        start_http_server(self.port)


class State(ABC):
    """
    Abstract base class for a state manager.

    This class is responsible for managing task states.
    It provides an interface for state management and captures task-related metrics.

    Attributes:
        buffer (Dict[str, Any]): Buffer for state data.
        log (logging.Logger): Logger for capturing logs.
        task_id (str): Identifier for the task.
    """

    def __init__(self, task_id: str) -> None:
        self.log = logging.getLogger(self.__class__.__name__)
        self.buffer: Dict[str, Any] = {}
        self.task_id = task_id

    @abstractmethod
    def get(self, task_id: str, key: str) -> Optional[Dict[str, Any]]:
        """
        Abstract method to get the state associated with a task and key.

        Args:
            task_id (str): The task identifier.
            key (str): The key to get the state for.

        Returns:
            Optional[Dict[str, Any]]: The state associated with the task and key, if it exists.
        """

    @abstractmethod
    def set(self, task_id: str, key: str, value: Dict[str, Any]) -> None:
        """
        Abstract method to set the state associated with a task and key.

        Args:
            task_id (str): The task identifier.
            key (str): The key to set the state for.
            value (Dict[str, Any]): The state to set.
        """

    def get_state(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get the state associated with a key from the buffer or underlying storage.

        Args:
            key (str): The key to get the state for.

        Returns:
            Optional[Dict[str, Any]]: The state associated with the key.
        """
        if key in self.buffer:
            return self.buffer[key]
        value = self.get(task_id=self.task_id, key=key)
        self.buffer[key] = value
        return value

    def set_state(self, key: str, value: Dict[str, Any]) -> None:
        """
        Set the state associated with a key in the buffer.

        Args:
            key (str): The key to set the state for.
            value (Dict[str, Any]): The state to set.
        """
        self.buffer[key] = value
        self.set(task_id=self.task_id, key=key, value=value)

    def flush(self) -> None:
        """
        Flush the buffer to the state storage.

        This method is responsible for writing the buffered state data to the underlying storage mechanism.
        """
        if hasattr(self, "buffer"):
            for key, value in self.buffer.items():
                self.set(task_id=self.task_id, key=key, value=value)

    def __del__(self) -> None:
        """
        Destructor to flush the buffer before object deletion.

        This ensures that any buffered state data is not lost when the object is deleted.
        """
        try:
            self.flush()
        except Exception:
            self.log.debug("Could not flush output")
