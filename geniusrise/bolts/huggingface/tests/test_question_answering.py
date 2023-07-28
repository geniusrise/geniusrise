import os
import tempfile
from transformers import BertForQuestionAnswering, BertTokenizerFast, EvalPrediction
from geniusrise.bolts.huggingface.question_answering import QuestionAnsweringFineTuner
from geniusrise.core import BatchInputConfig, BatchOutputConfig, InMemoryStateManager
from datasets import Dataset
import numpy as np
import pytest


def create_synthetic_data(size: int, temp_dir: str):
    # Generate synthetic data
    data = {
        "context": [f"This is a synthetic context example {i}" for i in range(size)],
        "question": [f"What is example {i}?" for i in range(size)],
        "answers": [{"text": [f"Example {i}"], "answer_start": [0]} for i in range(size)],
    }

    # Create a Hugging Face Dataset object from the data
    dataset = Dataset.from_dict(data)

    # Save the dataset to disk
    dataset.save_to_disk(os.path.join(temp_dir, "train"))
    dataset.save_to_disk(os.path.join(temp_dir, "eval"))


@pytest.fixture
def qa_bolt():
    model = BertForQuestionAnswering.from_pretrained("bert-base-uncased")
    tokenizer = BertTokenizerFast.from_pretrained("bert-base-uncased")

    # Use temporary directories for input and output
    input_dir = tempfile.mkdtemp()
    output_dir = tempfile.mkdtemp()

    # Create synthetic data
    create_synthetic_data(100, input_dir)

    input_config = BatchInputConfig(input_dir, "geniusrise-test-bucket", "test-🤗-input")
    output_config = BatchOutputConfig(output_dir, "geniusrise-test-bucket", "test-🤗-output")
    state_manager = InMemoryStateManager()

    return QuestionAnsweringFineTuner(
        model=model,
        tokenizer=tokenizer,
        input_config=input_config,
        output_config=output_config,
        state_manager=state_manager,
        pad_on_right=True,
        max_length=384,
        doc_stride=128,
        eval=True,
    )


def test_qa_bolt_init(qa_bolt):
    assert qa_bolt.model is not None
    assert qa_bolt.tokenizer is not None
    assert qa_bolt.input_config is not None
    assert qa_bolt.output_config is not None
    assert qa_bolt.state_manager is not None


def test_load_dataset(qa_bolt):
    train_dataset = qa_bolt.load_dataset(qa_bolt.input_config.get() + "/train", True, 384, 128)
    assert train_dataset is not None

    eval_dataset = qa_bolt.load_dataset(qa_bolt.input_config.get() + "/eval", True, 384, 128)
    assert eval_dataset is not None


def test_qa_bolt_compute_metrics(qa_bolt):
    # Mocking an EvalPrediction object
    logits = np.array([[0.6, 0.4], [0.4, 0.6]])
    labels = np.array([0, 1])
    eval_pred = EvalPrediction(predictions=logits, label_ids=labels)

    metrics = qa_bolt.compute_metrics(eval_pred)

    # Check for appropriate metrics
    assert "accuracy" in metrics


def test_qa_bolt_create_optimizer_and_scheduler(qa_bolt):
    optimizer, scheduler = qa_bolt.create_optimizer_and_scheduler(10)
    assert optimizer is not None
    assert scheduler is not None


def test_qa_bolt_fine_tune(qa_bolt):
    with tempfile.TemporaryDirectory() as tmpdir:
        # Fine-tuning with minimum epochs and batch size for speed
        qa_bolt.fine_tune(output_dir=tmpdir, num_train_epochs=1, per_device_train_batch_size=1)

        # Check that model files are created in the output directory
        assert os.path.isfile(os.path.join(tmpdir, "pytorch_model.bin"))
        assert os.path.isfile(os.path.join(tmpdir, "config.json"))
        assert os.path.isfile(os.path.join(tmpdir, "training_args.bin"))
