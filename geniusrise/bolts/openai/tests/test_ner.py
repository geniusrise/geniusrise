import os
import json
import tempfile
import pandas as pd
import pytest
from datasets import Dataset

from geniusrise.core import BatchInputConfig, BatchOutputConfig, InMemoryStateManager
from geniusrise.bolts.openai.ner import NamedEntityRecognitionFineTuner

# Retrieve environment variables
api_key = os.getenv("OPENAI_API_KEY")
api_type = os.getenv("OPENAI_API_TYPE")
api_base_url = os.getenv("OPENAI_API_BASE_URL")
api_version = os.getenv("OPENAI_API_VERSION")


@pytest.fixture
def ner_bolt():
    # Use temporary directories for input and output
    input_dir = tempfile.mkdtemp()
    output_dir = tempfile.mkdtemp()

    # Create the expected directory structure for the train and eval datasets
    train_dataset_path = os.path.join(input_dir, "train")
    eval_dataset_path = os.path.join(input_dir, "eval")
    os.makedirs(train_dataset_path)
    os.makedirs(eval_dataset_path)

    # Create sample NER data
    train_data = [{"tokens": ["Hello", "John"], "ner_tags": [0, 1]}]
    eval_data = [{"tokens": ["Goodbye", "Mike"], "ner_tags": [1, 0]}]

    # Save as JSONL files
    with open(os.path.join(train_dataset_path, "train.jsonl"), "w") as f:
        for item in train_data:
            f.write(json.dumps(item) + "\n")

    with open(os.path.join(eval_dataset_path, "eval.jsonl"), "w") as f:
        for item in eval_data:
            f.write(json.dumps(item) + "\n")

    input_config = BatchInputConfig(input_dir, "geniusrise-test-bucket", "test-openai-input")
    output_config = BatchOutputConfig(output_dir, "geniusrise-test-bucket", "test-openai-output")
    state_manager = InMemoryStateManager()

    return NamedEntityRecognitionFineTuner(
        input_config=input_config,
        output_config=output_config,
        state_manager=state_manager,
        api_type=api_type,
        api_key=api_key,
        api_base=api_base_url,
        api_version=api_version,
        eval=False,
    )


def test_load_dataset(ner_bolt):
    # Load the dataset
    dataset = ner_bolt.load_dataset(ner_bolt.input_config.input_folder + "/train")
    assert dataset is not None
    assert len(dataset) == 1
    assert dataset[0]["tokens"] == ["Hello", "John"]
    assert dataset[0]["ner_tags"] == [0, 1]


def test_prepare_fine_tuning_data(ner_bolt):
    # Create a sample dataset
    data = [
        {"tokens": json.dumps(["Hello", "John"]), "ner_tags": json.dumps([0, 1])},
        {"tokens": json.dumps(["Goodbye", "Mike"]), "ner_tags": json.dumps([1, 0])},
    ]
    data_df = pd.DataFrame(data)

    # Convert data_df to a Dataset
    dataset = Dataset.from_pandas(data_df)

    ner_bolt.prepare_fine_tuning_data(dataset)

    # Check that the train and eval files were created
    assert os.path.isfile(ner_bolt.train_file)
    assert os.path.isfile(ner_bolt.eval_file)

    # Check the content of the train file
    with open(ner_bolt.train_file, "r") as f:
        train_data = [line.strip() for line in f.readlines()]
    assert train_data[0] == '{"prompt":"[\\"Hello\\", \\"John\\"]","completion":"[0, 1]"}'
    assert train_data[1] == '{"prompt":"[\\"Goodbye\\", \\"Mike\\"]","completion":"[1, 0]"}'


def test_fine_tune(ner_bolt):
    # Create a sample dataset
    data = [
        {"tokens": json.dumps(["Hello", "John"]), "ner_tags": json.dumps([0, 1])},
        {"tokens": json.dumps(["Goodbye", "Mike"]), "ner_tags": json.dumps([1, 0])},
    ]
    data_df = pd.DataFrame(data)

    # Convert data_df to a Dataset
    dataset = Dataset.from_pandas(data_df)

    # Prepare the fine-tuning data
    ner_bolt.prepare_fine_tuning_data(dataset)

    fine_tune_job = ner_bolt.fine_tune(
        model="ada",
        suffix="test",
        n_epochs=1,
        batch_size=1,
        learning_rate_multiplier=0.5,
        prompt_loss_weight=1,
    )
    assert "ft-" in fine_tune_job.id
