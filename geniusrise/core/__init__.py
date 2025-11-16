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

from geniusrise.core.bolt import Bolt  # Legacy compatibility
from geniusrise.core.data import (
    BatchInput,
    BatchOutput,
    Input,
    Output,
    StreamingInput,
    StreamingOutput,
)
from geniusrise.core.state import (
    InMemoryState,
    PostgresState,
    State,
)
from geniusrise.core.task import Task

__all__ = [
    # Data I/O
    "Input",
    "Output",
    "BatchInput",
    "BatchOutput",
    "StreamingInput",
    "StreamingOutput",
    # State
    "State",
    "PostgresState",
    "InMemoryState",  # For testing only
    # Task
    "Task",
    "Bolt",  # Legacy compatibility for migrated code
]
