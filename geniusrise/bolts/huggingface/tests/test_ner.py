import os
import tempfile

import numpy as np
import pytest
from datasets import Dataset
from transformers import BertForTokenClassification, BertTokenizerFast, EvalPrediction

from geniusrise.bolts.huggingface.ner import NamedEntityRecognitionFineTuner
from geniusrise.core import BatchInputConfig, BatchOutputConfig, InMemoryStateManager


def create_synthetic_data(size: int, temp_dir: str):
    # Generate synthetic data
    data = {
        "tokens": [["This", "is", "a", "synthetic", "text", "example", str(i)] for i in range(size)],
        "ner_tags": [[i % 2 for _ in range(7)] for i in range(size)],  # Alternating 0s and 1s for labels
    }

    # Create a Hugging Face Dataset object from the data
    dataset = Dataset.from_dict(data)

    # Save the dataset to disk
    dataset.save_to_disk(os.path.join(temp_dir, "train"))
    dataset.save_to_disk(os.path.join(temp_dir, "eval"))


@pytest.fixture
def ner_bolt():
    model = BertForTokenClassification.from_pretrained("bert-base-uncased")
    tokenizer = BertTokenizerFast.from_pretrained("bert-base-uncased")

    # Use temporary directories for input and output
    input_dir = tempfile.mkdtemp()
    output_dir = tempfile.mkdtemp()

    # Create synthetic data
    create_synthetic_data(100, input_dir)

    input_config = BatchInputConfig(input_dir, "geniusrise-test-bucket", "test-🤗-input")
    output_config = BatchOutputConfig(output_dir, "geniusrise-test-bucket", "test-🤗-output")
    state_manager = InMemoryStateManager()

    return NamedEntityRecognitionFineTuner(
        model=model,
        tokenizer=tokenizer,
        input_config=input_config,
        output_config=output_config,
        state_manager=state_manager,
        label_list=[0, 1],
        eval=True,
    )


def test_ner_bolt_init(ner_bolt):
    assert ner_bolt.model is not None
    assert ner_bolt.tokenizer is not None
    assert ner_bolt.input_config is not None
    assert ner_bolt.output_config is not None
    assert ner_bolt.state_manager is not None


def test_load_dataset(ner_bolt):
    train_dataset = ner_bolt.load_dataset(ner_bolt.input_config.get() + "/train")
    assert train_dataset is not None

    eval_dataset = ner_bolt.load_dataset(ner_bolt.input_config.get() + "/eval")
    assert eval_dataset is not None


def test_ner_bolt_compute_metrics(ner_bolt):
    # Mocking an EvalPrediction object
    logits = np.array([[0.6, 0.4], [0.4, 0.6]])
    labels = np.array([0, 1])
    eval_pred = EvalPrediction(predictions=logits, label_ids=labels)

    metrics = ner_bolt.compute_metrics(eval_pred)

    assert "precision" in metrics
    assert "recall" in metrics
    assert "f1" in metrics
    assert "accuracy" in metrics


def test_ner_bolt_create_optimizer_and_scheduler(ner_bolt):
    optimizer, scheduler = ner_bolt.create_optimizer_and_scheduler(10)
    assert optimizer is not None
    assert scheduler is not None


def test_ner_bolt_fine_tune(ner_bolt):
    with tempfile.TemporaryDirectory() as tmpdir:
        # Fine-tuning with minimum epochs and batch size for speed
        ner_bolt.fine_tune(output_dir=tmpdir, num_train_epochs=1, per_device_train_batch_size=1)

        # Check that model files are created in the output directory
        assert os.path.isfile(os.path.join(tmpdir, "pytorch_model.bin"))
        assert os.path.isfile(os.path.join(tmpdir, "config.json"))
        assert os.path.isfile(os.path.join(tmpdir, "training_args.bin"))
