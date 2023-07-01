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
