# 🧠 Geniusrise
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

from unittest.mock import MagicMock, patch

from vertexai.preview.language_models import ChatModel

from geniusrise.preprocessing.google_palm import FineTuningData, PaLMPreprocessor


def test_generate_prompts():
    # Mock the ChatModel and its methods
    with patch.object(ChatModel, "from_pretrained", return_value=MagicMock()) as mock_model:
        mock_model.return_value.start_chat.return_value.send_message.return_value.text = "Test response"

        # Define test data
        what = "Test"
        strings = ["Test string 1", "Test string 2"]
        model = "chat-bison@001"

        # Call the method
        result = PaLMPreprocessor.generate_prompts(what, strings, model)

        # Check the result
        assert isinstance(result, FineTuningData)
        assert len(result.data) == 20  # 10 prompts per string
