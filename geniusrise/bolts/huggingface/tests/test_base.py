import os
import tempfile

import pytest
from datasets import load_dataset
from transformers import BertForSequenceClassification, BertTokenizer

from geniusrise.bolts.huggingface.base import HuggingFaceBatchFineTuner
from geniusrise.core import BatchInputConfig, BatchOutputConfig, InMemoryStateManager, StateManager


class TestHuggingFaceBatchFineTuner(HuggingFaceBatchFineTuner):
    def __init__(
        self, input_config: BatchInputConfig, output_config: BatchOutputConfig, state_manager: StateManager, **kwargs
    ):
        self.model = BertForSequenceClassification.from_pretrained("bert-base-uncased")
        self.tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
        super().__init__(
            model=self.model,
            tokenizer=self.tokenizer,
            input_config=input_config,
            output_config=output_config,
            state_manager=state_manager,
            **kwargs
        )

    def load_dataset(self, dataset_path, **kwargs):
        # Load the 'train' split of the MRPC dataset
        dataset = load_dataset("glue", "mrpc", split="train[:100]")  # using only first 100 samples for speed
        dataset = dataset.map(
            lambda examples: self.tokenizer(
                examples["sentence1"], examples["sentence2"], truncation=True, padding="max_length"
            ),
            batched=True,
        ).map(lambda examples: {"labels": examples["label"]}, batched=True)
        return dataset


@pytest.fixture
def bolt():
    # Use temporary directories for input and output
    input_dir = tempfile.mkdtemp()
    output_dir = tempfile.mkdtemp()

    input_config = BatchInputConfig(input_dir, "geniusrise-test-bucket", "test-🤗-input")
    output_config = BatchOutputConfig(output_dir, "geniusrise-test-bucket", "test-🤗-output")
    state_manager = InMemoryStateManager()

    return TestHuggingFaceBatchFineTuner(
        input_config=input_config,
        output_config=output_config,
        state_manager=state_manager,
        eval=False,
    )


def test_bolt_init(bolt):
    assert bolt.model is not None
    assert bolt.tokenizer is not None
    assert bolt.input_config is not None
    assert bolt.output_config is not None
    assert bolt.state_manager is not None


def test_load_dataset(bolt):
    dataset = bolt.load_dataset("fake_path")
    assert dataset is not None


def test_compute_metrics(bolt):
    import numpy as np
    from transformers import EvalPrediction

    # Mocking an EvalPrediction object
    logits = np.array([[0.6, 0.4], [0.4, 0.6]])
    labels = np.array([0, 1])
    eval_pred = EvalPrediction(predictions=logits, label_ids=labels)

    metrics = bolt.compute_metrics(eval_pred)

    assert "accuracy" in metrics
    assert "precision" in metrics
    assert "recall" in metrics
    assert "f1" in metrics


def test_create_optimizer_and_scheduler(bolt):
    optimizer, scheduler = bolt.create_optimizer_and_scheduler(10)
    assert optimizer is not None
    assert scheduler is not None


def test_fine_tune(bolt):
    with tempfile.TemporaryDirectory() as tmpdir:
        # Fine-tuning with minimum epochs and batch size for speed
        bolt.fine_tune(output_dir=tmpdir, num_train_epochs=1, per_device_train_batch_size=1)

        # Check that model files are created in the output directory
        assert os.path.isfile(os.path.join(tmpdir, "pytorch_model.bin"))
        assert os.path.isfile(os.path.join(tmpdir, "config.json"))
        assert os.path.isfile(os.path.join(tmpdir, "training_args.bin"))
