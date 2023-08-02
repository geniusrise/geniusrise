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

from typing import Any

from datasets import DatasetDict, load_from_disk
from transformers import DataCollatorForSeq2Seq

from .base import HuggingFaceBatchFineTuner


class TranslationFineTuner(HuggingFaceBatchFineTuner):
    """
    A bolt for fine-tuning Hugging Face models on translation tasks.

    This bolt extends the HuggingFaceBatchFineTuner to handle the specifics of translation tasks,
    such as the specific format of the datasets and the specific metrics for evaluation.

    The dataset should be in the following format:
    - Each example is a dictionary with the following keys:
        - 'translation': a dictionary with two keys:
            - 'en': a string representing the English text.
            - 'fr': a string representing the French text.
    """

    def load_dataset(self, dataset_path: str, **kwargs: Any) -> DatasetDict:
        """
        Load a dataset from a directory.

        Args:
            dataset_path (str): The path to the directory containing the dataset files.
            **kwargs: Additional keyword arguments to pass to the `load_dataset` method.

        Returns:
            Dataset: The loaded dataset.
        """
        # Load the dataset from the directory
        dataset = load_from_disk(dataset_path)

        # Preprocess the dataset
        tokenized_dataset = dataset.map(self.prepare_train_features, batched=True, remove_columns=dataset.column_names)

        return tokenized_dataset

    def prepare_train_features(self, examples):
        """
        Tokenize the examples and prepare the features for training.

        Args:
            examples (dict): A dictionary of examples.

        Returns:
            dict: The processed features.
        """
        # Tokenize the examples
        tokenized_inputs = self.tokenizer(
            [x["en"] for x in examples["translation"]], truncation=True, padding="max_length", max_length=512
        )
        tokenized_targets = self.tokenizer(
            [x["fr"] for x in examples["translation"]], truncation=True, padding="max_length", max_length=512
        )

        # Replace padding token id by -100
        labels = [
            [(lbl if lbl != self.tokenizer.pad_token_id else -100) for lbl in label]
            for label in tokenized_targets["input_ids"]
        ]

        # Prepare the labels
        tokenized_inputs["labels"] = labels

        return tokenized_inputs

    def data_collator(self, examples):
        """
        Customize the data collator.

        Args:
            examples: The examples to collate.

        Returns:
            dict: The collated data.
        """
        return DataCollatorForSeq2Seq(self.tokenizer, model=self.model)(examples)
