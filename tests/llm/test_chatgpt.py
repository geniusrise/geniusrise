# geniusrise
# Copyright (C) 2023  geniusrise.ai
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# type: ignore
from unittest.mock import MagicMock, patch

from geniusrise.llm.chatgpt import ChatGPT


def test_generate_prompts():
    chatgpt = ChatGPT()
    data = ["Hello, how are you?", "What's the weather like today?"]
    model = "gpt-3.5-turbo"
    what = "prompt"

    # Generate prompts
    df = chatgpt.generate_prompts(data=data, model=model, what=what)

    # Check the dataframe is not empty
    assert not df.empty

    # Check the dataframe has the correct columns
    assert set(df.columns) == {"prompt", "completion"}

    # Check the dataframe has the correct number of rows
    assert len(df) == len(data) * 10

    # Check the prompts in the dataframe match the input data
    for prompt in data:
        assert df[df["prompt"] == prompt].shape[0] == 10


def test_generate_prompts_empty_data():
    chatgpt = ChatGPT()
    data = []
    model = "gpt-3.5-turbo"
    what = "prompt"

    # Generate prompts
    df = chatgpt.generate_prompts(data=data, model=model, what=what)

    # Check the dataframe is empty
    assert df.empty


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
