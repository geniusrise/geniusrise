# type: ignore
import os
import tempfile
import pytest
import openai
from unittest.mock import patch

import pandas as pd
from datasets import Dataset
from geniusrise.core import BatchInputConfig, BatchOutputConfig, InMemoryStateManager

from geniusrise.bolts.openai.base import OpenAIFineTuner


# Retrieve environment variables
api_key = os.getenv("OPENAI_API_KEY")
api_type = os.getenv("OPENAI_API_TYPE")
api_base_url = os.getenv("OPENAI_API_BASE_URL")
api_version = os.getenv("OPENAI_API_VERSION")


class TestOpenAIFineTuner(OpenAIFineTuner):
    def load_dataset(self, dataset_path, **kwargs):
        # Load a simple dataset for testing
        data = [{"source": "Hello", "target": "Bonjour"}]
        return Dataset.from_pandas(pd.DataFrame(data))


@pytest.fixture
def bolt():
    # Use temporary directories for input and output
    input_dir = tempfile.mkdtemp()
    output_dir = tempfile.mkdtemp()

    input_config = BatchInputConfig(input_dir, "geniusrise-test-bucket", "test-openai-input")
    output_config = BatchOutputConfig(output_dir, "geniusrise-test-bucket", "test-openai-output")
    state_manager = InMemoryStateManager()

    return TestOpenAIFineTuner(
        input_config=input_config,
        output_config=output_config,
        state_manager=state_manager,
        api_type=api_type,
        api_key=api_key,
        api_base=api_base_url,
        api_version=api_version,
        eval=False,
    )


def test_bolt_init(bolt):
    assert bolt.input_config is not None
    assert bolt.output_config is not None
    assert bolt.state_manager is not None


def test_load_dataset(bolt):
    dataset = bolt.load_dataset("fake_path")
    assert dataset is not None
    assert len(dataset) == 1


def test_prepare_fine_tuning_data(bolt):
    data = [
        {"source": "Hello", "target": "Bonjour"},
        {"source": "Goodbye", "target": "Au revoir"},
    ]
    data_df = pd.DataFrame(data)
    data_df.rename(columns={"source": "prompt"}, inplace=True)
    data_df.rename(columns={"target": "completion"}, inplace=True)
    bolt.prepare_fine_tuning_data(data_df)
    assert os.path.isfile(bolt.train_file)
    assert os.path.isfile(bolt.eval_file)


# The following tests would interact with the actual OpenAI services
# Make sure you have the necessary permissions and are aware of the potential costs


def test_fine_tune(bolt):
    # Prepare the fine-tuning data first
    data = [
        {"source": "Hello", "target": "Bonjour"},
        {"source": "Goodbye", "target": "Au revoir"},
    ]
    data_df = pd.DataFrame(data)
    data_df.rename(columns={"source": "prompt"}, inplace=True)
    data_df.rename(columns={"target": "completion"}, inplace=True)
    bolt.prepare_fine_tuning_data(data_df)

    fine_tune_job = bolt.fine_tune(
        model="ada",
        suffix="test",
        n_epochs=1,
        batch_size=1,
        learning_rate_multiplier=0.5,
        prompt_loss_weight=1,
    )
    assert "ft-" in fine_tune_job.id


@patch.object(openai.FineTune, "retrieve")
def test_get_fine_tuning_job(mock_retrieve, bolt):
    mock_fine_tune = openai.FineTune(id="test_job_id")
    mock_fine_tune.status = "succeeded"
    mock_retrieve.return_value = mock_fine_tune
    job = bolt.get_fine_tuning_job("test_job_id")
    assert job.id == "test_job_id"
    assert job.status == "succeeded"


@patch.object(openai.FineTune, "delete")
def test_delete_fine_tuned_model(mock_delete, bolt):
    mock_fine_tune = openai.FineTune(id="test_model_id")
    mock_fine_tune.deleted = True
    mock_delete.return_value = mock_fine_tune
    result = bolt.delete_fine_tuned_model("test_model_id")
    assert result.id == "test_model_id"
    assert result.deleted
