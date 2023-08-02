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

import numpy as np
import torch
from datasets import DatasetDict, load_from_disk
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from transformers import DataCollatorForTokenClassification, EvalPrediction, PreTrainedModel, PreTrainedTokenizerBase

from geniusrise.core import BatchInputConfig, BatchOutputConfig, StateManager

from .base import HuggingFaceBatchFineTuner


class NamedEntityRecognitionFineTuner(HuggingFaceBatchFineTuner):
    """
    A bolt for fine-tuning Hugging Face models on named entity recognition tasks.

    This bolt extends the HuggingFaceBatchFineTuner to handle the specifics of named entity recognition tasks,
    such as the specific format of the datasets and the specific metrics for evaluation.

    The dataset should be in the following format:
    - Each example is a dictionary with the following keys:
        - 'tokens': a list of strings representing the tokens in a sentence.
        - 'ner_tags': a list of integers representing the NER tag for each token in 'tokens'.
    - The labels for special tokens are set to -100 so they are ignored in the loss function.
    """

    def __init__(
        self,
        model: PreTrainedModel,
        tokenizer: PreTrainedTokenizerBase,
        input_config: BatchInputConfig,
        output_config: BatchOutputConfig,
        state_manager: StateManager,
        label_list: List[str],
        **kwargs,
    ):
        """
        Initialize the NamedEntityRecognitionFineTuner.

        Args:
            model: The pre-trained model to fine-tune.
            tokenizer: The tokenizer associated with the model.
            input_config (BatchInputConfig): The batch input configuration.
            output_config (BatchOutputConfig): The batch output configuration.
            state_manager (StateManager): The state manager.
            label_list (List[str]): The list of labels for the NER task.
            **kwargs: Additional arguments for the superclass.
        """
        self.label_list = label_list
        self.label_to_id = {label: i for i, label in enumerate(self.label_list)}
        super().__init__(
            model=model,
            tokenizer=tokenizer,
            input_config=input_config,
            output_config=output_config,
            state_manager=state_manager,
            **kwargs,
        )

    def load_dataset(self, dataset_path: str, **kwargs: Any) -> DatasetDict:
        """
        Load a dataset from a directory.

        Args:
            dataset_path (str): The path to the directory containing the dataset files.

        Returns:
            DatasetDict: The loaded dataset.
        """
        # Load the dataset from the directory
        dataset = load_from_disk(dataset_path)

        # Preprocess the dataset
        tokenized_dataset = dataset.map(self.prepare_train_features, batched=True, remove_columns=dataset.column_names)

        return tokenized_dataset

    def prepare_train_features(
        self, examples: Dict[str, Union[List[str], List[int]]]
    ) -> Dict[str, Union[List[str], List[int]]]:
        """
        Tokenize the examples and prepare the features for training.

        Args:
            examples (Dict[str, Union[List[str], List[int]]]): A dictionary of examples.

        Returns:
            Dict[str, Union[List[str], List[int]]]: The processed features.
        """
        tokenized_inputs = self.tokenizer(examples["tokens"], truncation=True, is_split_into_words=True)
        labels = []
        for i, label in enumerate(examples["ner_tags"]):  # assuming the key in your examples dict is 'ner_tags'
            word_ids = tokenized_inputs.word_ids(batch_index=i)
            label_ids = []
            for word_idx in word_ids:
                # assign label of the word to all subwords
                if word_idx is not None:
                    label_ids.append(self.label_to_id[label[word_idx]])  # type: ignore
                else:
                    label_ids.append(-100)
            labels.append(label_ids)
        tokenized_inputs["labels"] = labels
        return tokenized_inputs

    def data_collator(self, examples: List[Dict[str, torch.Tensor]]) -> Dict[str, torch.Tensor]:
        """
        Customize the data collator.

        Args:
            examples (List[Dict[str, torch.Tensor]]): The examples to collate.

        Returns:
            Dict[str, torch.Tensor]: The collated data.
        """
        return DataCollatorForTokenClassification(self.tokenizer)(examples)

    def compute_metrics(self, eval_prediction: EvalPrediction, average: str = "micro"):
        predictions = np.argmax(eval_prediction.predictions, axis=-1)
        labels = eval_prediction.label_ids

        # Mask out ignored values
        mask = labels != -100
        labels = labels[mask]
        predictions = predictions[mask]

        return {
            "accuracy": accuracy_score(labels, predictions),
            "precision": precision_score(labels, predictions, average=average),
            "recall": recall_score(labels, predictions, average=average),
            "f1": f1_score(labels, predictions, average=average),
        }
