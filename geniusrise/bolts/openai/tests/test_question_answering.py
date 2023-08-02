import os
import tempfile
import pandas as pd
import pytest
from datasets import Dataset

from geniusrise.core import BatchInputConfig, BatchOutputConfig, InMemoryStateManager
from geniusrise.bolts.openai.question_answering import OpenAIQuestionAnsweringFineTuner

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

    # Create a sample JSONL file with question and answer data
    with open(os.path.join(train_dataset_path, "What is the capital of France?.jsonl"), "w") as f:
        f.write(
            '{"text": "The capital of France is Paris.", "question": "What is the capital of France?", "answer": "Paris"}'
        )

    input_config = BatchInputConfig(input_dir, "geniusrise-test-bucket", "test-openai-input")
    output_config = BatchOutputConfig(output_dir, "geniusrise-test-bucket", "test-openai-output")
    state_manager = InMemoryStateManager()

    return OpenAIQuestionAnsweringFineTuner(
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
    with open(os.path.join(dataset_dir, "What is the capital of France?.jsonl"), "w") as f:
        f.write(
            '{"text": "The capital of France is Paris.", "question": "What is the capital of France?", "answer": "Paris"}'
        )

    # Load the dataset
    dataset = bolt.load_dataset(dataset_dir)
    assert dataset is not None
    assert len(dataset) == 1
    print(dataset[0])
    assert dataset[0]["text"] == "The capital of France is Paris."
    assert dataset[0]["question"] == "What is the capital of France?"
    assert dataset[0]["answer"] == "Paris"


def test_prepare_fine_tuning_data(bolt):
    # Create a sample dataset
    data = [
        {"text": "The capital of France is Paris.", "question": "What is the capital of France?", "answer": "Paris"},
        {"text": "The capital of India is Delhi.", "question": "What is the capital of India?", "answer": "Delhi"},
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
    assert (
        train_data[0]
        == '{"prompt":"The capital of France is Paris.\\n\\nWhat is the capital of France?","completion":"Paris"}'
    )


def test_fine_tune(bolt):
    # Create a sample dataset
    data = [
        {"text": "The capital of France is Paris.", "question": "What is the capital of France?", "answer": "Paris"},
        {"text": "The capital of India is Delhi.", "question": "What is the capital of India?", "answer": "Delhi"},
    ]
    data_df = pd.DataFrame(data)

    # Convert data_df to a Dataset
    dataset = Dataset.from_pandas(data_df)

    # Prepare the fine-tuning data
    bolt.prepare_fine_tuning_data(dataset)

    # Initiate the fine-tuning process
    fine_tune_job = bolt.fine_tune(
        model="ada",
        suffix="test",
        n_epochs=1,
        batch_size=1,
        learning_rate_multiplier=0.5,
        prompt_loss_weight=1,
    )

    # Check that the job ID is returned and has the expected prefix
    assert "ft-" in fine_tune_job.id
