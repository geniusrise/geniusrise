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

import numpy as np
import pytest
from datasets import Dataset
from transformers import BartForConditionalGeneration, BartTokenizerFast, EvalPrediction

from geniusrise.bolts.huggingface.summarization import SummarizationFineTuner
from geniusrise.core import BatchInputConfig, BatchOutputConfig, InMemoryStateManager


def create_synthetic_data(size: int, temp_dir: str):
    # Generate synthetic data
    data = {
        "document": [f"This is a synthetic text example {i}" for i in range(size)],
        "summary": [f"Synthetic text {i}" for i in range(size)],
    }

    # Create a Hugging Face Dataset object from the data
    dataset = Dataset.from_dict(data)

    # Save the dataset to disk
    dataset.save_to_disk(os.path.join(temp_dir, "train"))
    dataset.save_to_disk(os.path.join(temp_dir, "eval"))


@pytest.fixture
def summarization_bolt():
    model = BartForConditionalGeneration.from_pretrained("facebook/bart-base")
    tokenizer = BartTokenizerFast.from_pretrained("facebook/bart-base")

    # Use temporary directories for input and output
    input_dir = tempfile.mkdtemp()
    output_dir = tempfile.mkdtemp()

    # Create synthetic data
    create_synthetic_data(100, input_dir)

    input_config = BatchInputConfig(input_dir, "geniusrise-test-bucket", "test-🤗-input")
    output_config = BatchOutputConfig(output_dir, "geniusrise-test-bucket", "test-🤗-output")
    state_manager = InMemoryStateManager()

    return SummarizationFineTuner(
        model=model,
        tokenizer=tokenizer,
        input_config=input_config,
        output_config=output_config,
        state_manager=state_manager,
        eval=True,
    )


def test_summarization_bolt_init(summarization_bolt):
    assert summarization_bolt.model is not None
    assert summarization_bolt.tokenizer is not None
    assert summarization_bolt.input_config is not None
    assert summarization_bolt.output_config is not None
    assert summarization_bolt.state_manager is not None


def test_load_dataset(summarization_bolt):
    train_dataset = summarization_bolt.load_dataset(summarization_bolt.input_config.get() + "/train")
    assert train_dataset is not None

    eval_dataset = summarization_bolt.load_dataset(summarization_bolt.input_config.get() + "/eval")
    assert eval_dataset is not None


def test_summarization_bolt_compute_metrics(summarization_bolt):
    # Mocking an EvalPrediction object
    logits = np.array([[0.6, 0.4], [0.4, 0.6]])
    labels = np.array([0, 1])
    eval_pred = EvalPrediction(predictions=logits, label_ids=labels)

    metrics = summarization_bolt.compute_metrics(eval_pred)

    # Check for appropriate summarization metrics, like ROUGE scores
    assert "rouge1" in metrics
    assert "rouge2" in metrics
    assert "rougeL" in metrics


def test_summarization_bolt_create_optimizer_and_scheduler(summarization_bolt):
    optimizer, scheduler = summarization_bolt.create_optimizer_and_scheduler(10)
    assert optimizer is not None
    assert scheduler is not None


def test_summarization_bolt_fine_tune(summarization_bolt):
    with tempfile.TemporaryDirectory() as tmpdir:
        # Fine-tuning with minimum epochs and batch size for speed
        summarization_bolt.fine_tune(output_dir=tmpdir, num_train_epochs=1, per_device_train_batch_size=1)

        # Check that model files are created in the output directory
        assert os.path.isfile(os.path.join(tmpdir, "pytorch_model.bin"))
        assert os.path.isfile(os.path.join(tmpdir, "config.json"))
        assert os.path.isfile(os.path.join(tmpdir, "training_args.bin"))
