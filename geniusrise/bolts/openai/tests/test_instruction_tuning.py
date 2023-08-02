import os
import json
import tempfile
import pandas as pd
import pytest
from datasets import Dataset

from geniusrise.core import BatchInputConfig, BatchOutputConfig, InMemoryStateManager
from geniusrise.bolts.openai.instruction_tuning import OpenAIInstructionFineTuner

# Retrieve environment variables
api_key = os.getenv("OPENAI_API_KEY")
api_type = os.getenv("OPENAI_API_TYPE")
api_base_url = os.getenv("OPENAI_API_BASE_URL")
api_version = os.getenv("OPENAI_API_VERSION")


@pytest.fixture
def bolt():
    # Use temporary directories for input and output
    input_dir = tempfile.mkdtemp()
    output_dir = tempfile.mkdtemp()

    # Create the expected directory structure for the train and eval datasets
    train_dataset_path = os.path.join(input_dir, "train")
    eval_dataset_path = os.path.join(input_dir, "eval")
    os.makedirs(train_dataset_path)
    os.makedirs(eval_dataset_path)

    input_config = BatchInputConfig(input_dir, "geniusrise-test-bucket", "test-openai-input")
    output_config = BatchOutputConfig(output_dir, "geniusrise-test-bucket", "test-openai-output")
    state_manager = InMemoryStateManager()

    return OpenAIInstructionFineTuner(
        input_config=input_config,
        output_config=output_config,
        state_manager=state_manager,
        api_type=api_type,
        api_key=api_key,
        api_base=api_base_url,
        api_version=api_version,
        eval=False,
    )


def create_test_dataset():
    # Create a temporary directory with a sample dataset
    dataset_dir = tempfile.mkdtemp()
    train_dir = os.path.join(dataset_dir, "train")
    os.makedirs(train_dir)
    with open(os.path.join(train_dir, "example1.jsonl"), "w") as f:
        examples = [
            {"instruction": "Write a greeting.", "output": "Hello!"},
            {"instruction": "Write a farewell.", "output": "Goodbye!"},
        ]
        for example in examples:
            f.write(json.dumps(example) + "\n")
    return dataset_dir


def test_load_dataset(bolt):
    dataset_dir = create_test_dataset()

    # Load the dataset
    dataset = bolt.load_dataset(dataset_dir + "/train")
    assert dataset is not None
    assert len(dataset) == 2
    assert dataset[0]["instruction"] == "Write a greeting."
    assert dataset[0]["output"] == "Hello!"
    assert dataset[1]["instruction"] == "Write a farewell."
    assert dataset[1]["output"] == "Goodbye!"


def test_prepare_fine_tuning_data(bolt):
    dataset_dir = create_test_dataset()

    # Load the dataset
    dataset = bolt.load_dataset(dataset_dir + "/train")

    bolt.prepare_fine_tuning_data(dataset)

    # Check that the train and eval files were created
    assert os.path.isfile(bolt.train_file)
    assert os.path.isfile(bolt.eval_file)

    # Check the content of the train file
    with open(bolt.train_file, "r") as f:
        train_data = [line.strip() for line in f.readlines()]
    assert train_data[0] == '{"prompt":"Write a greeting.","completion":"Hello!"}'
    assert train_data[1] == '{"prompt":"Write a farewell.","completion":"Goodbye!"}'


def test_fine_tune(bolt):
    # Create a sample dataset
    data = [
        {"instruction": "Write a greeting.", "output": "Hello!"},
        {"instruction": "Write a farewell.", "output": "Goodbye!"},
    ]
    data_df = pd.DataFrame(data)

    # Convert data_df to a Dataset
    dataset = Dataset.from_pandas(data_df)

    # Prepare the fine-tuning data
    bolt.prepare_fine_tuning_data(dataset)

    fine_tune_job = bolt.fine_tune(
        model="ada",
        suffix="test",
        n_epochs=1,
        batch_size=1,
        learning_rate_multiplier=0.5,
        prompt_loss_weight=1,
    )
    assert "ft-" in fine_tune_job.id
