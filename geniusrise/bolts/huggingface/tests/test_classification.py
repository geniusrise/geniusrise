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
from transformers import BertForSequenceClassification, BertTokenizer, EvalPrediction

from geniusrise.bolts.huggingface.classification import HuggingFaceClassificationFineTuner
from geniusrise.core import BatchInputConfig, BatchOutputConfig, InMemoryStateManager


# Create synthetic data
def create_synthetic_data(directory, classes, num_files):
    for c in classes:
        class_dir = os.path.join(directory, c)
        os.makedirs(class_dir, exist_ok=True)
        for i in range(num_files):
            with open(os.path.join(class_dir, f"{i}.txt"), "w") as f:
                f.write(f"This is a synthetic text file for class {c}.")


@pytest.fixture
def classification_bolt():
    model = BertForSequenceClassification.from_pretrained("bert-base-uncased")
    tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")

    # Use temporary directories for input and output
    input_dir = tempfile.mkdtemp()
    output_dir = tempfile.mkdtemp()

    # Create synthetic data
    create_synthetic_data(input_dir + "/train", ["class1", "class2"], 10)
    create_synthetic_data(input_dir + "/eval", ["class1", "class2"], 10)

    input_config = BatchInputConfig(input_dir, "geniusrise-test-bucket", "test-🤗-input")
    output_config = BatchOutputConfig(output_dir, "geniusrise-test-bucket", "test-🤗-output")
    state_manager = InMemoryStateManager()

    return HuggingFaceClassificationFineTuner(
        model=model,
        tokenizer=tokenizer,
        input_config=input_config,
        output_config=output_config,
        state_manager=state_manager,
    )


def test_classification_bolt_init(classification_bolt):
    assert classification_bolt.model is not None
    assert classification_bolt.tokenizer is not None
    assert classification_bolt.input_config is not None
    assert classification_bolt.output_config is not None
    assert classification_bolt.state_manager is not None


def test_load_dataset(classification_bolt):
    dataset = classification_bolt.load_dataset(classification_bolt.input_config.get() + "/train")
    assert dataset is not None
    assert len(dataset) == 20  # 2 classes * 10 files

    eval_dataset = classification_bolt.load_dataset(classification_bolt.input_config.get() + "/eval")
    assert eval_dataset is not None
    assert len(eval_dataset) == 20  # 2 classes * 10 files


def test_classification_bolt_fine_tune(classification_bolt):
    with tempfile.TemporaryDirectory() as tmpdir:
        # Fine-tuning with minimum epochs and batch size for speed
        classification_bolt.fine_tune(output_dir=tmpdir, num_train_epochs=1, per_device_train_batch_size=1)

        # Check that model files are created in the output directory
        assert os.path.isfile(os.path.join(tmpdir, "pytorch_model.bin"))
        assert os.path.isfile(os.path.join(tmpdir, "config.json"))
        assert os.path.isfile(os.path.join(tmpdir, "training_args.bin"))


def test_classification_bolt_compute_metrics(classification_bolt):
    # Mocking an EvalPrediction object
    logits = np.array([[0.6, 0.4], [0.4, 0.6]])
    labels = np.array([0, 1])
    eval_pred = EvalPrediction(predictions=logits, label_ids=labels)

    metrics = classification_bolt.compute_metrics(eval_pred)

    assert "accuracy" in metrics
    assert "precision" in metrics
    assert "recall" in metrics
    assert "f1" in metrics


def test_classification_bolt_create_optimizer_and_scheduler(classification_bolt):
    optimizer, scheduler = classification_bolt.create_optimizer_and_scheduler(10)
    assert optimizer is not None
    assert scheduler is not None
