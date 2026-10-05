# 🧠 Geniusrise
# Copyright (C) 2023-2025  geniusrise.ai
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

from .input import Input
from .output import Output
from .input_registry import (
    register_input_backend,
    INPUT_BACKENDS,
    discover_input_backends
)
from .output_registry import (
    register_output_backend,
    OUTPUT_BACKENDS,
    discover_output_backends
)

# For backwards compatibility
class BatchInput(Input):
    def __new__(cls, *args, **kwargs):
        raise ImportError(
            "BatchInput with S3 support is not available. Install with: pip install geniusrise-data-s3"
        )

class BatchOutput(Output):
    def __new__(cls, *args, **kwargs):
        raise ImportError(
            "BatchOutput with S3 support is not available. Install with: pip install geniusrise-data-s3"
        )

class StreamingInput(Input):
    def __new__(cls, *args, **kwargs):
        raise ImportError(
            "StreamingInput is not available. Install with: pip install geniusrise-data-kafka"
        )

class StreamingOutput(Output):
    def __new__(cls, *args, **kwargs):
        raise ImportError(
            "StreamingOutput is not available. Install with: pip install geniusrise-data-kafka"
        )

__all__ = [
    "Input",
    "Output",
    "BatchInput",
    "BatchOutput",
    "StreamingInput",
    "StreamingOutput",
    "register_input_backend",
    "INPUT_BACKENDS",
    "discover_input_backends",
    "register_output_backend",
    "OUTPUT_BACKENDS",
    "discover_output_backends"
]
