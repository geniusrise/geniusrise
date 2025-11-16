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

import pytest
from sentence_transformers import SentenceTransformer
from transformers import AutoModel, AutoTokenizer

from geniusrise.inference.text.utils.embeddings import (
    generate_combination_embeddings,
    generate_contiguous_embeddings,
    generate_embeddings,
    generate_permutation_embeddings,
    generate_sentence_transformer_embeddings,
)

# List of models to test
MODEL_NAMES = [
    "bert-base-uncased",
    "gpt2",
    "intfloat/multilingual-e5-base",
    "NeuML/pubmedbert-base-embeddings",
    "thenlper/gte-large",
]

SENTENCE_TRANSFORMERS_MODELS = [
    "sentence-transformers/all-MiniLM-L6-v2",
    "sentence-transformers/all-mpnet-base-v2",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    "sentence-transformers/LaBSE",
    "sentence-transformers/clip-ViT-B-32-multilingual-v1",
    "sentence-transformers/paraphrase-xlm-r-multilingual-v1",
]


@pytest.mark.parametrize("model_name", SENTENCE_TRANSFORMERS_MODELS)
def test_generate_sentence_transformer_embeddings(model_name):
    model = SentenceTransformer(model_name, device="cuda")
    _model = AutoModel.from_pretrained(model_name)
    sentences = ["This is a test sentence.", "Another test sentence."]
    embeddings = generate_sentence_transformer_embeddings(sentences=sentences, model=model)
    assert all(
        [
            x.shape[0] == _model.config.hidden_size or x.shape[0] == _model.config.max_position_embeddings
            for x in embeddings
        ]
    )


@pytest.mark.parametrize("model_name", MODEL_NAMES)
def test_generate_embeddings(model_name):
    model = AutoModel.from_pretrained(model_name).to("cuda:0")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    sentence = "This is a test sentence."
    embeddings = generate_embeddings(sentence=sentence, model=model, tokenizer=tokenizer)
    assert embeddings.shape == (1, model.config.hidden_size)


@pytest.mark.parametrize("model_name", MODEL_NAMES)
def test_generate_contiguous_embeddings(model_name):
    model = AutoModel.from_pretrained(model_name).to("cuda:0")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    sentence = "This is a test sentence."
    embeddings_list = generate_contiguous_embeddings(sentence=sentence, model=model, tokenizer=tokenizer)
    assert all(embeddings.shape == (1, model.config.hidden_size) for embeddings, _ in embeddings_list)


@pytest.mark.parametrize("model_name", MODEL_NAMES)
def test_generate_combination_embeddings(model_name):
    model = AutoModel.from_pretrained(model_name).to("cuda:0")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    sentence = "This is a test sentence."
    embeddings_list = generate_combination_embeddings(sentence=sentence, model=model, tokenizer=tokenizer)
    assert all(embeddings.shape == (1, model.config.hidden_size) for embeddings, _ in embeddings_list)


@pytest.mark.parametrize("model_name", MODEL_NAMES)
def test_generate_permutation_embeddings(model_name):
    model = AutoModel.from_pretrained(model_name).to("cuda:0")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    sentence = "This is a test sentence."
    embeddings_list = generate_permutation_embeddings(sentence=sentence, model=model, tokenizer=tokenizer)
    assert all(embeddings.shape == (1, model.config.hidden_size) for embeddings, _ in embeddings_list)
