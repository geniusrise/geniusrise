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

"""
Base inference task - unified architecture replacing Bolt/Spout pattern.
"""

import os
import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Optional
from pathlib import Path

from geniusrise.core.state.postgres import PostgresState


class InferenceMode(Enum):
    """Execution modes for inference tasks."""
    API = "api"
    BATCH = "batch"
    STREAMING = "streaming"


class InferenceTask(ABC):
    """
    Base class for all inference tasks.

    Replaces the old Bolt/Spout pattern with a simpler unified architecture:
    - API mode: Serve models via HTTP endpoints
    - Batch mode: Process files from input → output folders
    - Streaming mode: Real-time processing via Kafka

    Args:
        task_id: Unique identifier for this task
        state_config: PostgreSQL state configuration
        mode: Execution mode (api/batch/streaming)
    """

    def __init__(
        self,
        task_id: str,
        state_config: Optional[Dict[str, Any]] = None,
        mode: InferenceMode = InferenceMode.API,
    ):
        self.task_id = task_id
        self.mode = mode
        self.log = logging.getLogger(self.__class__.__name__)

        # Initialize state management (PostgreSQL only)
        if state_config:
            self.state = PostgresState(
                id=task_id,
                **state_config
            )
        else:
            self.state = None
            self.log.warning("No state configuration provided - running stateless")

    def set_state(self, key: str, value: Any) -> None:
        """Set state value."""
        if self.state:
            self.state.set_state(key, value)
        else:
            self.log.debug(f"State not configured, skipping set: {key}")

    def get_state(self, key: str) -> Optional[Any]:
        """Get state value."""
        if self.state:
            return self.state.get_state(key)
        return None

    @abstractmethod
    def load_model(self, **kwargs) -> None:
        """
        Load the model and prepare for inference.
        Must be implemented by subclasses.
        """
        pass

    @abstractmethod
    def run_api(self, **kwargs) -> None:
        """
        Run in API mode - serve HTTP endpoint.
        Must be implemented by subclasses.
        """
        pass

    @abstractmethod
    def run_batch(self, input_path: str, output_path: str, **kwargs) -> None:
        """
        Run in batch mode - process files from input to output.
        Must be implemented by subclasses.
        """
        pass

    def run_streaming(self, **kwargs) -> None:
        """
        Run in streaming mode - process from Kafka.
        Optional - override if needed.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support streaming mode"
        )

    def execute(self, **kwargs) -> None:
        """
        Execute the task based on the configured mode.
        """
        self.set_state("status", "loading_model")
        self.load_model(**kwargs)

        self.set_state("status", "running")

        try:
            if self.mode == InferenceMode.API:
                self.run_api(**kwargs)
            elif self.mode == InferenceMode.BATCH:
                input_path = kwargs.get("input_path", "./input")
                output_path = kwargs.get("output_path", "./output")
                self.run_batch(input_path, output_path, **kwargs)
            elif self.mode == InferenceMode.STREAMING:
                self.run_streaming(**kwargs)
            else:
                raise ValueError(f"Unknown mode: {self.mode}")

            self.set_state("status", "completed")
            self.log.info(f"Task {self.task_id} completed successfully")

        except Exception as e:
            self.set_state("status", "failed")
            self.set_state("error", str(e))
            self.log.error(f"Task {self.task_id} failed: {e}")
            raise
