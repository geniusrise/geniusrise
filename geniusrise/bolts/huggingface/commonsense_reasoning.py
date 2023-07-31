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

from typing import Any, Dict

from datasets import load_from_disk
from transformers import DataCollatorWithPadding

from .base import HuggingFaceBatchFineTuner


class CommonsenseReasoningFineTuner(HuggingFaceBatchFineTuner):
    """
    A bolt for fine-tuning Hugging Face models on commonsense reasoning tasks.

    This bolt extends the HuggingFaceBatchFineTuner to handle the specifics of commonsense reasoning tasks,
    such as the specific format of the datasets and the specific metrics for evaluation.

    The dataset should be in the following format:
    - Each example is a dictionary with the following keys:
        - 'premise': a string representing the premise.
        - 'hypothesis': a string representing the hypothesis.
        - 'label': an integer representing the label (0 for entailment, 1 for neutral, 2 for contradiction).
    """

    def load_dataset(self, dataset_path: str, **kwargs: Any) -> Dict:
        """
        Load a dataset from a directory.

        Args:
            dataset_path (str): The path to the directory containing the dataset files.
            **kwargs: Additional keyword arguments to pass to the `load_dataset` method.

        Returns:
            Dataset: The loaded dataset.
        """
        try:
            # Load the dataset from the directory
            dataset = load_from_disk(dataset_path)

            # Preprocess the dataset
            tokenized_dataset = dataset.map(
                self.prepare_train_features, batched=True, remove_columns=dataset.column_names
            )

            return tokenized_dataset
        except Exception as e:
            print(f"Error loading dataset: {e}")
            raise

    def prepare_train_features(self, examples: Dict) -> Dict:
        """
        Tokenize the examples and prepare the features for training.

        Args:
            examples (dict): A dictionary of examples.

        Returns:
            dict: The processed features.
        """
        try:
            # Tokenize the examples
            tokenized_inputs = self.tokenizer(
                examples["premise"], examples["hypothesis"], truncation=True, padding=False
            )

            # Prepare the labels
            tokenized_inputs["labels"] = examples["label"]

            return tokenized_inputs
        except Exception as e:
            print(f"Error preparing train features: {e}")
            raise

    def data_collator(self, examples: Dict) -> Dict:
        """
        Customize the data collator.

        Args:
            examples: The examples to collate.

        Returns:
            dict: The collated data.
        """
        try:
            return DataCollatorWithPadding(self.tokenizer)(examples)
        except Exception as e:
            print(f"Error in data collation: {e}")
            raise
