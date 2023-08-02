import os
import tempfile
import pandas as pd
import pytest
from datasets import Dataset

from geniusrise.core import BatchInputConfig, BatchOutputConfig, InMemoryStateManager
from geniusrise.bolts.openai.translation import OpenAITranslationFineTuner

# Retrieve environment variables
api_key = os.getenv("OPENAI_API_KEY")
api_type = os.getenv("OPENAI_API_TYPE")
api_base_url = os.getenv("OPENAI_API_BASE_URL")
api_version = os.getenv("OPENAI_API_VERSION")


@pytest.fixture
def translation_bolt():
    # Use temporary directories for input and output
    input_dir = tempfile.mkdtemp()
    output_dir = tempfile.mkdtemp()

    # Create the expected directory structure for the train and eval datasets
    train_dataset_path = os.path.join(input_dir, "train")
    eval_dataset_path = os.path.join(input_dir, "eval")
    os.makedirs(train_dataset_path)
    os.makedirs(eval_dataset_path)

    with open(os.path.join(train_dataset_path, "source.txt"), "w") as f:
        f.write("This is a source text.")
    with open(os.path.join(train_dataset_path, "target.txt"), "w") as f:
        f.write("This is a target text.")

    with open(os.path.join(eval_dataset_path, "source.txt"), "w") as f:
        f.write("This is a source text.")
    with open(os.path.join(eval_dataset_path, "target.txt"), "w") as f:
        f.write("This is a target text.")

    input_config = BatchInputConfig(input_dir, "geniusrise-test-bucket", "test-openai-input")
    output_config = BatchOutputConfig(output_dir, "geniusrise-test-bucket", "test-openai-output")
    state_manager = InMemoryStateManager()

    return OpenAITranslationFineTuner(
        input_config=input_config,
        output_config=output_config,
        state_manager=state_manager,
        api_type=api_type,
        api_key=api_key,
        api_base=api_base_url,
        api_version=api_version,
        eval=False,
    )


def test_load_dataset(translation_bolt):
    # Create a temporary directory with source and target text files
    dataset_dir = tempfile.mkdtemp()
    with open(os.path.join(dataset_dir, "source.txt"), "w") as f:
        f.write("This is a source text.")
    with open(os.path.join(dataset_dir, "target.txt"), "w") as f:
        f.write("This is a target text.")

    # Load the dataset
    dataset = translation_bolt.load_dataset(dataset_dir)
    assert dataset is not None
    assert len(dataset) == 1
    assert dataset[0]["source"] == "This is a source text."
    assert dataset[0]["target"] == "This is a target text."


def test_prepare_fine_tuning_data(translation_bolt):
    # Create a sample dataset
    data = [
        {"source": "Hello", "target": "Bonjour"},
        {"source": "Goodbye", "target": "Au revoir"},
    ]
    data_df = pd.DataFrame(data)

    # Convert data_df to a Dataset
    dataset = Dataset.from_pandas(data_df)

    translation_bolt.prepare_fine_tuning_data(dataset)

    # Check that the train and eval files were created
    assert os.path.isfile(translation_bolt.train_file)
    assert os.path.isfile(translation_bolt.eval_file)

    # Check the content of the train file
    with open(translation_bolt.train_file, "r") as f:
        train_data = [line.strip() for line in f.readlines()]
    assert train_data[0] == '{"prompt":"Hello","completion":"Bonjour"}'
    assert train_data[1] == '{"prompt":"Goodbye","completion":"Au revoir"}'


def test_fine_tune(translation_bolt):
    # Create a sample dataset
    data = [
        {"source": "Hello", "target": "Bonjour"},
        {"source": "Goodbye", "target": "Au revoir"},
    ]
    data_df = pd.DataFrame(data)

    # Convert data_df to a Dataset
    dataset = Dataset.from_pandas(data_df)

    # Prepare the fine-tuning data
    translation_bolt.prepare_fine_tuning_data(dataset)

    fine_tune_job = translation_bolt.fine_tune(
        model="ada",
        suffix="test",
        n_epochs=1,
        batch_size=1,
        learning_rate_multiplier=0.5,
        prompt_loss_weight=1,
    )
    assert "ft-" in fine_tune_job.id
