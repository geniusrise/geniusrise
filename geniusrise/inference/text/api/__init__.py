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

from geniusrise.inference.text.api.classification import TextClassificationAPI
from geniusrise.inference.text.api.embeddings import EmbeddingsAPI
from geniusrise.inference.text.api.instruction import InstructionAPI
from geniusrise.inference.text.api.language_model import LanguageModelAPI
from geniusrise.inference.text.api.ner import NamedEntityRecognitionAPI
from geniusrise.inference.text.api.nli import NLIAPI
from geniusrise.inference.text.api.qa import QAAPI
from geniusrise.inference.text.api.translation import TranslationAPI

__all__ = [
    "TextClassificationAPI",
    "EmbeddingsAPI",
    "InstructionAPI",
    "LanguageModelAPI",
    "NamedEntityRecognitionAPI",
    "NLIAPI",
    "QAAPI",
    "TranslationAPI",
]
