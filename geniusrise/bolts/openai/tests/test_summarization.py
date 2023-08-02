import os
import tempfile
import pandas as pd
import pytest
from datasets import Dataset

from geniusrise.core import BatchInputConfig, BatchOutputConfig, InMemoryStateManager
from geniusrise.bolts.openai.summarization import OpenAISummarizationFineTuner

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
    os.makedirs(train_dataset_path)

    # Create sample document and summary files
    with open(os.path.join(train_dataset_path, "document.txt"), "w") as f:
        f.write("This is a sample document.")
    with open(os.path.join(train_dataset_path, "summary.txt"), "w") as f:
        f.write("This is a summary.")

    input_config = BatchInputConfig(input_dir, "geniusrise-test-bucket", "test-openai-input")
    output_config = BatchOutputConfig(output_dir, "geniusrise-test-bucket", "test-openai-output")
    state_manager = InMemoryStateManager()

    return OpenAISummarizationFineTuner(
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
    with open(os.path.join(dataset_dir, "document.txt"), "w") as f:
        f.write("This is a sample document.")
    with open(os.path.join(dataset_dir, "summary.txt"), "w") as f:
        f.write("This is a summary.")

    # Load the dataset
    dataset = bolt.load_dataset(dataset_dir)
    assert dataset is not None
    assert len(dataset) == 1
    assert dataset[0]["document"] == "This is a sample document."
    assert dataset[0]["summary"] == "This is a summary."


def test_prepare_fine_tuning_data(bolt):
    # Create a sample dataset
    data = [
        {"document": "Document 1", "summary": "Summary 1"},
        {"document": "Document 2", "summary": "Summary 2"},
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
    assert train_data[0] == '{"prompt":"Document 1","completion":"Summary 1"}'
    assert train_data[1] == '{"prompt":"Document 2","completion":"Summary 2"}'


def test_fine_tune(bolt):
    # Create a sample dataset
    data = [
        {"document": "Document 1", "summary": "Summary 1"},
        {"document": "Document 2", "summary": "Summary 2"},
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
