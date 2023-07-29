import os
import tempfile

import pytest
from datasets import Dataset
from transformers import BartForConditionalGeneration, BartTokenizer

from geniusrise.bolts.huggingface.instruction_tuning import HuggingFaceInstructionTuningFineTuner
from geniusrise.core import BatchInputConfig, BatchOutputConfig, InMemoryStateManager


def create_synthetic_data(size: int, temp_dir: str):
    # Generate synthetic data
    data = {
        "instruction": [f"This is a synthetic instruction example {i}" for i in range(size)],
        "output": [f"This is a synthetic output example {i}" for i in range(size)],
    }

    # Create a Hugging Face Dataset object from the data
    dataset = Dataset.from_dict(data)

    # Save the dataset to disk
    dataset.save_to_disk(os.path.join(temp_dir, "train"))
    dataset.save_to_disk(os.path.join(temp_dir, "eval"))


@pytest.fixture
def instruction_tuning_bolt():
    model = BartForConditionalGeneration.from_pretrained("facebook/bart-base")
    tokenizer = BartTokenizer.from_pretrained("facebook/bart-base")

    # Use temporary directories for input and output
    input_dir = tempfile.mkdtemp()
    output_dir = tempfile.mkdtemp()

    # Create synthetic data
    create_synthetic_data(100, input_dir)

    input_config = BatchInputConfig(input_dir, "geniusrise-test-bucket", "test-🤗-input")
    output_config = BatchOutputConfig(output_dir, "geniusrise-test-bucket", "test-🤗-output")
    state_manager = InMemoryStateManager()

    return HuggingFaceInstructionTuningFineTuner(
        model=model,
        tokenizer=tokenizer,
        input_config=input_config,
        output_config=output_config,
        state_manager=state_manager,
        eval=True,
    )


def test_instruction_tuning_bolt_init(instruction_tuning_bolt):
    assert instruction_tuning_bolt.model is not None
    assert instruction_tuning_bolt.tokenizer is not None
    assert instruction_tuning_bolt.input_config is not None
    assert instruction_tuning_bolt.output_config is not None
    assert instruction_tuning_bolt.state_manager is not None


def test_load_dataset(instruction_tuning_bolt):
    train_dataset = instruction_tuning_bolt.load_dataset(instruction_tuning_bolt.input_config.get() + "/train")
    assert train_dataset is not None

    eval_dataset = instruction_tuning_bolt.load_dataset(instruction_tuning_bolt.input_config.get() + "/eval")
    assert eval_dataset is not None


def test_instruction_tuning_bolt_fine_tune(instruction_tuning_bolt):
    with tempfile.TemporaryDirectory() as tmpdir:
        # Fine-tuning with minimum epochs and batch size for speed
        instruction_tuning_bolt.fine_tune(output_dir=tmpdir, num_train_epochs=1, per_device_train_batch_size=1)

        # Check that model files are created in the output directory
        assert os.path.isfile(os.path.join(tmpdir, "pytorch_model.bin"))
        assert os.path.isfile(os.path.join(tmpdir, "config.json"))
        assert os.path.isfile(os.path.join(tmpdir, "training_args.bin"))
