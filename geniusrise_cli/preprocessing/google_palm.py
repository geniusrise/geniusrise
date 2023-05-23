from typing import List
from vertexai.preview.language_models import ChatModel
from geniusrise_cli.preprocessing.prompts import generate_prompts_from_x
from geniusrise_cli.llm.types import FineTuningData, FineTuningDataItem


class PaLMPreprocessor:
    """
    A class to preprocess data for fine-tuning Google's PaLM model.
    """

    @staticmethod
    def generate_prompts(what: str, strings: List[str], model: str = "chat-bison@001"):
        """
        Generate prompts for fine-tuning using Google's PaLM model.
        """
        fine_tuning_data = []
        chat_model = ChatModel.from_pretrained(model)

        for string in strings:
            chat = chat_model.start_chat(
                context="You are a helpful assistant.",
                examples=[],
            )
            for _ in range(10):
                prompt = FineTuningDataItem(
                    prompt=string, completion=chat.send_message(f"{generate_prompts_from_x(x=what)}{string}").text
                )
                fine_tuning_data.append(prompt)
        return FineTuningData(data=fine_tuning_data)
