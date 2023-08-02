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
from transformers import BertForMaskedLM, BertTokenizer

from geniusrise.bolts.huggingface.lanuage_model import LanguageModelingFineTuner
from geniusrise.core import BatchInputConfig, BatchOutputConfig, InMemoryStateManager


# Create synthetic data
def create_synthetic_data(directory, num_files):
    os.makedirs(directory, exist_ok=True)
    texts = []
    for i in range(num_files):
        text = f"This is a synthetic text file number {i}."
        texts.append({"text": text})

    # Create a Dataset from the synthetic data
    dataset = Dataset.from_dict({"text": texts})

    # Save the Dataset to disk
    dataset.save_to_disk(directory)


@pytest.fixture
def language_modeling_bolt():
    model = BertForMaskedLM.from_pretrained("bert-base-uncased")
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

    return LanguageModelingFineTuner(
        model=model,
        tokenizer=tokenizer,
        input_config=input_config,
        output_config=output_config,
        state_manager=state_manager,
    )


def test_language_modeling_bolt_init(language_modeling_bolt):
    assert language_modeling_bolt.model is not None
    assert language_modeling_bolt.tokenizer is not None
    assert language_modeling_bolt.input_config is not None
    assert language_modeling_bolt.output_config is not None
    assert language_modeling_bolt.state_manager is not None


def test_load_dataset(language_modeling_bolt):
    dataset = language_modeling_bolt.load_dataset(language_modeling_bolt.input_config.get() + "/train")
    assert dataset is not None
    assert len(dataset) == 10

    eval_dataset = language_modeling_bolt.load_dataset(language_modeling_bolt.input_config.get() + "/eval")
    assert eval_dataset is not None
    assert len(eval_dataset) == 10


def test_language_modeling_bolt_fine_tune(language_modeling_bolt):
    with tempfile.TemporaryDirectory() as tmpdir:
        # Fine-tuning with minimum epochs and batch size for speed
        language_modeling_bolt.fine_tune(output_dir=tmpdir, num_train_epochs=1, per_device_train_batch_size=1)

        # Check that model files are created in the output directory
        assert os.path.isfile(os.path.join(tmpdir, "pytorch_model.bin"))
        assert os.path.isfile(os.path.join(tmpdir, "config.json"))
        assert os.path.isfile(os.path.join(tmpdir, "training_args.bin"))
