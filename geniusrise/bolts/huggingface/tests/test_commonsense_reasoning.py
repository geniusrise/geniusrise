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

import os
import tempfile

import pytest
from datasets import Dataset
from transformers import BertForSequenceClassification, BertTokenizer

from geniusrise.bolts.huggingface.commonsense_reasoning import CommonsenseReasoningFineTuner
from geniusrise.core import BatchInputConfig, BatchOutputConfig, InMemoryStateManager


def create_synthetic_data(directory, num_examples):
    # Generate synthetic data
    data = {
        "premise": ["This is a synthetic premise example." for _ in range(num_examples)],
        "hypothesis": ["This is a synthetic hypothesis example." for _ in range(num_examples)],
        "label": [0 for _ in range(num_examples)],
    }

    # Create a Hugging Face Dataset object from the data
    dataset = Dataset.from_dict(data)

    # Save the dataset to disk
    dataset.save_to_disk(directory)


@pytest.fixture
def commonsense_bolt():
    model = BertForSequenceClassification.from_pretrained("bert-base-uncased")
    tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")

    # Use temporary directories for input and output
    input_dir = tempfile.mkdtemp()
    output_dir = tempfile.mkdtemp()

    # Create synthetic data
    create_synthetic_data(input_dir + "/train", 10)
    create_synthetic_data(input_dir + "/eval", 10)

    input_config = BatchInputConfig(input_dir, "geniusrise-test-bucket", "test-🤗-input")
    output_config = BatchOutputConfig(output_dir, "geniusrise-test-bucket", "test-🤗-output")
    state_manager = InMemoryStateManager()

    return CommonsenseReasoningFineTuner(
        model=model,
        tokenizer=tokenizer,
        input_config=input_config,
        output_config=output_config,
        state_manager=state_manager,
    )


def test_commonsense_bolt_init(commonsense_bolt):
    assert commonsense_bolt.model is not None
    assert commonsense_bolt.tokenizer is not None
    assert commonsense_bolt.input_config is not None
    assert commonsense_bolt.output_config is not None
    assert commonsense_bolt.state_manager is not None


def test_commonsense_load_dataset(commonsense_bolt):
    dataset = commonsense_bolt.load_dataset(commonsense_bolt.input_config.get() + "/train")
    assert dataset is not None

    eval_dataset = commonsense_bolt.load_dataset(commonsense_bolt.input_config.get() + "/eval")
    assert eval_dataset is not None


def test_commonsense_bolt_fine_tune(commonsense_bolt):
    with tempfile.TemporaryDirectory() as tmpdir:
        # Fine-tuning with minimum epochs and batch size for speed
        commonsense_bolt.fine_tune(output_dir=tmpdir, num_train_epochs=1, per_device_train_batch_size=1)

        # Check that model files are created in the output directory
        assert os.path.isfile(os.path.join(tmpdir, "pytorch_model.bin"))
        assert os.path.isfile(os.path.join(tmpdir, "config.json"))
        assert os.path.isfile(os.path.join(tmpdir, "training_args.bin"))


def test_commonsense_prepare_train_features(commonsense_bolt):
    # Mocking examples
    examples = {"premise": ["This is a premise."], "hypothesis": ["This is a hypothesis."], "label": [0]}

    features = commonsense_bolt.prepare_train_features(examples)

    assert "input_ids" in features
    assert "token_type_ids" in features
    assert "attention_mask" in features
    assert "labels" in features

    assert len(features["input_ids"]) == 1
    assert len(features["token_type_ids"]) == 1
    assert len(features["attention_mask"]) == 1
    assert len(features["labels"]) == 1


def test_commonsense_data_collator(commonsense_bolt):
    # Mocking examples
    examples = {
        "input_ids": [[101, 2023, 2003, 1037, 12559, 1012, 102]],
        "token_type_ids": [[0, 0, 0, 0, 0, 0, 0]],
        "attention_mask": [[1, 1, 1, 1, 1, 1, 1]],
        "labels": [0],
    }

    collated_data = commonsense_bolt.data_collator(examples)

    assert "input_ids" in collated_data
    assert "token_type_ids" in collated_data
    assert "attention_mask" in collated_data
    assert "labels" in collated_data

    assert len(collated_data["input_ids"]) == 1
    assert len(collated_data["token_type_ids"]) == 1
    assert len(collated_data["attention_mask"]) == 1
    assert len(collated_data["labels"]) == 1
