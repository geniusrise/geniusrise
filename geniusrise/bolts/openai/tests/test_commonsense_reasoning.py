import os
import json
import tempfile
import pandas as pd
import pytest
from datasets import Dataset

from geniusrise.core import BatchInputConfig, BatchOutputConfig, InMemoryStateManager
from geniusrise.bolts.openai.commonsense_reasoning import OpenAICommonsenseReasoningFineTuner

# Retrieve environment variables
api_key = os.getenv("OPENAI_API_KEY")
api_type = os.getenv("OPENAI_API_TYPE")
api_base_url = os.getenv("OPENAI_API_BASE_URL")
api_version = os.getenv("OPENAI_API_VERSION")


def create_mock_data(dataset_path):
    os.makedirs(dataset_path, exist_ok=True)
    data = [
        {"premise": "The premise text", "hypothesis": "The hypothesis text", "label": 0},
        # Add more examples as needed
    ]
    with open(os.path.join(dataset_path, "data.jsonl"), "w") as file:
        for item in data:
            file.write(json.dumps(item) + "\n")


@pytest.fixture
def bolt():
    # Use temporary directories for input and output
    input_dir = tempfile.mkdtemp()
    output_dir = tempfile.mkdtemp()

    # Create mock data in the input directory
    dataset_path = os.path.join(input_dir, "train")
    create_mock_data(dataset_path)

    input_config = BatchInputConfig(input_dir, "geniusrise-test-bucket", "test-openai-input")
    output_config = BatchOutputConfig(output_dir, "geniusrise-test-bucket", "test-openai-output")
    state_manager = InMemoryStateManager()

    return OpenAICommonsenseReasoningFineTuner(
        input_config=input_config,
        output_config=output_config,
        state_manager=state_manager,
        api_type=api_type,
        api_key=api_key,
        api_base=api_base_url,
        api_version=api_version,
        eval=False,
    )


def test_load_dataset(bolt):
    # Create a temporary directory with a sample dataset
    dataset_dir = tempfile.mkdtemp()
    with open(os.path.join(dataset_dir, "example.jsonl"), "w") as f:
        f.write('{"premise": "The sun is shining.", "hypothesis": "It is day.", "label": 0}\n')

    # Load the dataset
    dataset = bolt.load_dataset(dataset_dir)
    assert dataset is not None
    assert len(dataset) == 1
    assert dataset[0]["premise"] == "The sun is shining."
    assert dataset[0]["hypothesis"] == "It is day."
    assert dataset[0]["label"] == 0


def test_prepare_fine_tuning_data(bolt):
    # Create a sample dataset
    data = [
        {"premise": "The sun is shining.", "hypothesis": "It is day.", "label": 0},
        {"premise": "It is raining.", "hypothesis": "The ground is wet.", "label": 1},
    ]
    data_df = pd.DataFrame(data)

    # Convert data_df to a Dataset
    dataset = Dataset.from_pandas(data_df)

    bolt.prepare_fine_tuning_data(dataset)

    # Check that the train and eval files were created
    assert os.path.isfile(bolt.train_file)
    assert os.path.isfile(bolt.eval_file)

    # Check the content of the train file
    with open(bolt.train_file, "r") as f:
        train_data = [line.strip() for line in f.readlines()]
    assert train_data[0] == '{"prompt":"The sun is shining.\\nIt is day.","completion":"entailment"}'
    assert train_data[1] == '{"prompt":"It is raining.\\nThe ground is wet.","completion":"neutral"}'


def test_fine_tune(bolt):
    # Create a sample dataset
    data = [
        {"premise": "The sun is shining.", "hypothesis": "It is day.", "label": 0},
        {"premise": "It is raining.", "hypothesis": "The ground is wet.", "label": 1},
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
