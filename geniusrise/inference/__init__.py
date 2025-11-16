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
Unified inference module for vision, text, and audio models.

This module provides a simplified architecture for running inference on AI models:
- API mode: Serve models via HTTP/REST endpoints
- Batch mode: Process files from input folder to output folder
- Streaming mode: Real-time processing via Kafka

No training or fine-tuning - inference only.
"""

from geniusrise.inference.base import InferenceTask, InferenceMode

__all__ = [
    "InferenceTask",
    "InferenceMode",
]
