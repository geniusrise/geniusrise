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

from typing import Any, Dict, List, Union

import torch
from datasets import DatasetDict, load_from_disk
from torch.utils.data import Dataset
from transformers import DataCollatorWithPadding

from .base import HuggingFaceBatchFineTuner


class SentimentAnalysisFineTuner(HuggingFaceBatchFineTuner):
    """
    A bolt for fine-tuning Hugging Face models on sentiment analysis tasks.

    This bolt extends the HuggingFaceBatchFineTuner to handle the specifics of sentiment analysis tasks,
    such as the specific format of the datasets and the specific metrics for evaluation.

    The dataset should be in the following format:
    - Each example is a dictionary with the following keys:
        - 'text': a string representing the text to classify.
        - 'label': an integer representing the sentiment of the text.
    """

    def load_dataset(self, dataset_path: str, **kwargs: Any) -> Dataset | DatasetDict:
        """
        Load a dataset from a directory.

        Args:
            dataset_path (str): The path to the directory containing the dataset files.

        Returns:
            DatasetDict: The loaded dataset.
        """
        dataset = load_from_disk(dataset_path)
        tokenized_dataset = dataset.map(self.prepare_train_features, batched=True, remove_columns=dataset.column_names)
        return tokenized_dataset

    def prepare_train_features(self, examples: Dict[str, Union[str, int]]) -> Dict[str, Union[List[int], int]]:
        """
        Tokenize the examples and prepare the features for training.

        Args:
            examples (Dict[str, Union[str, int]]): A dictionary of examples.

        Returns:
            Dict[str, Union[List[int], int]]: The processed features.
        """
        tokenized_inputs = self.tokenizer(examples["text"], truncation=True, padding=False)
        tokenized_inputs["labels"] = examples["label"]
        return tokenized_inputs

    def data_collator(
        self, examples: List[Dict[str, Union[List[int], int]]]
    ) -> Dict[str, Union[torch.Tensor, List[torch.Tensor]]]:
        """
        Customize the data collator.

        Args:
            examples (List[Dict[str, Union[List[int], int]]]): The examples to collate.

        Returns:
            Dict[str, Union[torch.Tensor, List[torch.Tensor]]]: The collated data.
        """
        return DataCollatorWithPadding(self.tokenizer)(examples)
