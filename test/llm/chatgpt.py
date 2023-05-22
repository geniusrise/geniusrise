# type: ignore
# import pytest
from unittest.mock import patch, MagicMock

# from geniusrise_cli.preprocessing.openai import OpenAIPreprocessor
from geniusrise_cli.llm.chatgpt import ChatGPT


def test_fine_tune():
    # Mock the FineTune._get_or_upload method to return a dummy file ID
    with patch("openai.cli.FineTune._get_or_upload", return_value="file-id"):
        # Mock the openai.FineTune.create method to return a dummy job
        with patch("openai.FineTune.create", return_value=MagicMock(id="job-id")):
            chatgpt = ChatGPT(api_key="dummy-api-key")
            job = chatgpt.fine_tune(
                model="text-davinci-002",
                suffix="my-suffix",
                n_epochs="10",
                batch_size="2",
                learning_rate_multiplier="0.1",
                prompt_loss_weight="0.1",
                training_file="dummy-training-file.txt",
            )
            assert job.id == "job-id"


def test_get_fine_tuning_job():
    # Mock the openai.FineTune.retrieve method to return a dummy job
    with patch("openai.FineTune.retrieve", return_value=MagicMock(status="succeeded")):
        chatgpt = ChatGPT(api_key="dummy-api-key")
        job = chatgpt.get_fine_tuning_job("job-id")
        assert job.status == "succeeded"


def test_delete_fine_tuned_model():
    # Mock the openai.FineTune.delete method to return a dummy response
    with patch("openai.FineTune.delete", return_value=MagicMock()):
        chatgpt = ChatGPT(api_key="dummy-api-key")
        response = chatgpt.delete_fine_tuned_model("model-id")
        assert response is not None
