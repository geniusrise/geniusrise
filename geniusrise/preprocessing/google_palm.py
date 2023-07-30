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

from typing import List

from vertexai.preview.language_models import ChatModel

from geniusrise.llm.types import FineTuningData, FineTuningDataItem
from geniusrise.preprocessing.prompts import prompt_generate_prompts


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
                    prompt=string, completion=chat.send_message(f"{prompt_generate_prompts(x=what)}{string}").text
                )
                fine_tuning_data.append(prompt)
        return FineTuningData(data=fine_tuning_data)
