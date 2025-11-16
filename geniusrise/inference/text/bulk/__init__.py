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

from geniusrise.inference.text.bulk.classification import TextClassificationBulk
from geniusrise.inference.text.bulk.embeddings import EmbeddingsBulk
from geniusrise.inference.text.bulk.instruction import InstructionBulk
from geniusrise.inference.text.bulk.language_model import LanguageModelBulk
from geniusrise.inference.text.bulk.ner import NamedEntityRecognitionBulk
from geniusrise.inference.text.bulk.nli import NLIBulk
from geniusrise.inference.text.bulk.qa import QABulk
from geniusrise.inference.text.bulk.translation import TranslationBulk

__all__ = [
    "TextClassificationBulk",
    "EmbeddingsBulk",
    "InstructionBulk",
    "LanguageModelBulk",
    "NamedEntityRecognitionBulk",
    "NLIBulk",
    "QABulk",
    "TranslationBulk",
]
