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

import time
import logging
import threading
import socket
import GPUtil
import platform
from datetime import datetime
import psutil
from abc import ABC, abstractmethod
from typing import Dict, Optional, Any, Callable
from prometheus_client import Counter, Gauge, Summary, CollectorRegistry


class State(ABC):
    """
    Abstract base class for a state manager.

    A state manager is responsible for getting and setting state, capturing metrics, and logging.
    It provides an interface for state management and also captures various system metrics.

    Attributes:
        read_ops (Counter): Counter for read operations.
        write_ops (Counter): Counter for write operations.
        process_time (Summary): Summary for time spent in processing.
        cpu_usage (Gauge): Gauge for CPU usage.
        memory_usage (Gauge): Gauge for memory usage.
        python_version (str): Python version.
        cpu_count (str): Count of CPUs visible.
        virtual_memory (str): virtual memory available.
        gpu_count (str):  GPU count visible.
        gpu_memory (str):  GPU memory available.
        buffer (Dict[str, Any]): Buffer for state data.
        log (logging.Logger): Logger for capturing logs.
    """

    def __init__(self) -> None:
        # Logger
        self.log = logging.getLogger(self.__class__.__name__)

        # Prometheus metrics
        self.registry = CollectorRegistry()

        # Basic Metrics
        self.read_ops = Counter("read_operations", "Number of read operations", registry=self.registry)
        self.write_ops = Counter("write_operations", "Number of write operations", registry=self.registry)
        self.process_time = Summary("process_time", "Time spent processing", registry=self.registry)
        self.cpu_usage = Gauge("cpu_usage", "CPU usage", registry=self.registry)
        self.memory_usage = Gauge("memory_usage", "Memory usage", registry=self.registry)

        # Python VM Metrics
        self.python_version = platform.python_version()
        self.cpu_count = psutil.cpu_count()
        self.virtual_memory = psutil.virtual_memory().total / (1024**3)

        # PyTorch and GPU Metrics
        try:
            gpus = GPUtil.getgpus()
        except Exception as e:
            gpus = None
            self.log.debug(f"Nvidia gpus not available {e}")
        if gpus:
            self.gpu_count = len(gpus)
            self.gpu_memory = [x.memoryTotal for x in gpus]
        else:
            self.gpu_count = 0
            self.gpu_memory = [0]

        # Buffer for periodic flush or destructor
        self.buffer: Dict[str, Any] = {}

        # Metrics capture thread and buffer
        self.metrics_buffer: Dict[str, Any] = {}
        self.metrics_capture_thread = threading.Thread(target=self.capture_metrics_periodically)
        self.metrics_capture_thread.daemon = True
        self.metrics_capture_thread.start()

        self.hostname = socket.gethostname()
        self.system_info = platform.uname()

    @abstractmethod
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Abstract method to get the state associated with a key.

        Args:
            key (str): The key to get the state for.

        Returns:
            Optional[Dict[str, Any]]: The state associated with the key.
        """
        pass

    @abstractmethod
    def set(self, key: str, value: Dict[str, Any]) -> None:
        """
        Abstract method to set the state associated with a key.

        Args:
            key (str): The key to set the state for.
            value (Dict[str, Any]): The state to set.
        """
        pass

    def get_state(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get the state associated with a key and capture metrics.

        This method wraps the abstract `get` method to provide additional functionality like metrics capturing.

        Args:
            key (str): The key to get the state for.

        Returns:
            Optional[Dict[str, Any]]: The state associated with the key.
        """
        self.read_ops.inc()
        state = self.get(key)
        self.capture_metrics()
        return state

    def set_state(self, key: str, value: Dict[str, Any]) -> None:
        """
        Set the state associated with a key and capture metrics.

        This method wraps the abstract `set` method to provide additional functionality like metrics capturing.

        Args:
            key (str): The key to set the state for.
            value (Dict[str, Any]): The state to set.
        """
        # TODO: I mean we need to avoid at least basic race conditions
        # Most have an atomic update but i guess none have an atomic update inside a json?
        # Otherwise we need to be content with the assumption that each task will have a unique uuid task id and hence a single instance
        self.write_ops.inc()
        value["metrics"] = self.metrics_buffer.get("metrics_history", [])
        self.buffer[key] = value
        self.flush_buffer()
        self.flush_metrics()

    def flush_buffer(self) -> None:
        """
        Flush the buffer to the state storage.

        This method is responsible for writing the buffered state data to the underlying storage mechanism.
        """
        if hasattr(self, "buffer"):
            for key, value in self.buffer.items():
                self.set(key, value)
        # we never clear the buffer, we assume the user keeps setting different values
        # self.buffer.clear()

    def __del__(self) -> None:
        """
        Destructor to flush the buffer before object deletion.

        This ensures that any buffered state data is not lost when the object is deleted.
        """
        self.flush_buffer()

    def capture_metrics(self) -> None:
        """
        Capture system metrics.

        This method captures various system metrics like CPU usage, memory usage, etc., and stores them in a buffer.
        """
        metrics = {
            "cpu_usage": psutil.cpu_percent(),
            "memory_usage": psutil.virtual_memory().percent,
            "hostname": socket.gethostname(),
            "system_info": platform.uname(),
            "timestamp": datetime.utcnow().isoformat(),
            "python_version": self.python_version,
            "cpu_count": self.cpu_count,
            "virtual_memory": self.virtual_memory,
            "gpu_count": self.gpu_count,
            "gpu_memory": self.gpu_memory,
        }
        self.metrics_buffer.setdefault("metrics_history", []).append(metrics)

    def capture_metrics_periodically(self, interval=1):
        """
        Periodically capture metrics.

        This method runs in a separate thread and captures system metrics at regular intervals.

        Args:
            interval (int): Time interval in seconds.
        """
        while True:
            self.capture_metrics()
            time.sleep(interval)

    def flush_metrics(self) -> None:
        """
        Flush the metrics buffer to the state storage.

        This method is responsible for writing the buffered metrics data to the underlying storage mechanism.
        """
        self.metrics_buffer.clear()

    def capture_log(self, log_entry: str) -> None:
        """
        Capture log entries.

        This method captures log entries and timestamps, storing them in a buffer for later use.

        Args:
            log_entry (str): The log entry to capture.
        """
        self.metrics_buffer.setdefault("logs", []).append(
            {"log": log_entry, "timestamp": datetime.utcnow().isoformat()}
        )

    def time_function(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        Time the execution of a function and capture metrics.

        This method times the execution of a given function and captures the time spent in a Summary metric.

        Args:
            func (Any): The function to time.
            *args (Any): Positional arguments for the function.
            **kwargs (Any): Keyword arguments for the function.

        Returns:
            Any: The result of the function execution.
        """
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        self.process_time.observe(end_time - start_time)
        self.capture_metrics()
        return result
