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
Legacy base class for backward compatibility with migrated inference code.
This provides the same interface as the old Bolt class for existing code.
"""

from geniusrise.core.data import BatchInput, BatchOutput, StreamingInput, StreamingOutput
from geniusrise.core.state import State
from typing import Union


class Bolt:
    """
    Legacy base class for backward compatibility.
    Provides input, output, and state management like the old Bolt class.

    This is kept for compatibility with migrated vision/text/audio inference code.
    New code should use InferenceTask instead.
    """

    def __init__(
        self,
        input: Union[BatchInput, StreamingInput, None] = None,
        output: Union[BatchOutput, StreamingOutput, None] = None,
        state: Union[State, None] = None,
    ):
        self.input = input
        self.output = output
        self.state = state
