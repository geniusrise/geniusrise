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

import logging
from typing import Any, Dict, List, Optional, Union

import numpy as np
from datasets import Dataset, load_from_disk
from sklearn.metrics import accuracy_score
from transformers import EvalPrediction, PreTrainedModel, PreTrainedTokenizer

from geniusrise.core import BatchInputConfig, BatchOutputConfig, StateManager

from .base import HuggingFaceBatchFineTuner

# Set up logging
logger = logging.getLogger(__name__)


class QuestionAnsweringFineTuner(HuggingFaceBatchFineTuner):
    """
    A bolt for fine-tuning Hugging Face models on question answering tasks.

    This bolt extends the HuggingFaceBatchFineTuner to handle the specifics of question answering tasks,
    such as the specific format of the datasets and the specific metrics for evaluation.
    """

    def __init__(
        self,
        model: PreTrainedModel,
        tokenizer: PreTrainedTokenizer,
        input_config: BatchInputConfig,
        output_config: BatchOutputConfig,
        state_manager: StateManager,
        pad_on_right: bool,
        max_length: int,
        doc_stride: int,
        eval: bool = False,
        **kwargs: Dict[str, Any],
    ) -> None:
        """
        Initialize the bolt.

        Args:
            model (PreTrainedModel): The pre-trained model to fine-tune.
            tokenizer (PreTrainedTokenizer): The tokenizer associated with the model.
            input_config (BatchInputConfig): The batch input configuration.
            output_config (OutputConfig): The output configuration.
            state_manager (StateManager): The state manager.
            pad_on_right (bool): Whether to pad on the right.
            max_length (int): The maximum length of the sequences.
            doc_stride (int): The document stride.
            eval (bool, optional): Whether to evaluate the model after training. Defaults to False.
            **kwargs: Additional keyword arguments.
        """
        self.pad_on_right = pad_on_right
        self.max_length = max_length
        self.doc_stride = doc_stride
        super().__init__(
            model=model,
            tokenizer=tokenizer,
            input_config=input_config,
            output_config=output_config,
            state_manager=state_manager,
            eval=eval,
            **kwargs,
        )

    def load_dataset(
        self,
        dataset_path: str,
        pad_on_right: Optional[bool] = None,
        max_length: Optional[int] = None,
        doc_stride: Optional[int] = None,
        **kwargs: Dict[str, Any],
    ) -> Optional[Dataset]:
        """
        Load a dataset from a directory.

        Args:
            dataset_path (str): The path to the directory containing the dataset files.

        Returns:
            Dataset: The loaded dataset.
        """
        # Update padding, max_length, and doc_stride if provided
        self.pad_on_right = pad_on_right if pad_on_right is not None else self.pad_on_right
        self.max_length = max_length if max_length is not None else self.max_length
        self.doc_stride = doc_stride if doc_stride is not None else self.doc_stride

        # Load the dataset from the directory
        try:
            dataset = load_from_disk(dataset_path)
        except Exception as e:
            logger.error(f"Error loading dataset from {dataset_path}: {e}")
            return None

        # Preprocess the dataset
        try:
            tokenized_dataset = dataset.map(
                self.prepare_train_features, batched=True, remove_columns=dataset.column_names
            )
        except Exception as e:
            logger.error(f"Error tokenizing dataset: {e}")
            return None

        return tokenized_dataset

    def prepare_train_features(
        self, examples: Dict[str, Union[str, List[str]]]
    ) -> Optional[Dict[str, Union[List[int], List[List[int]]]]]:
        """
        Tokenize our examples with truncation and padding, but keep the overflows using a stride.

        Args:
            examples: The examples to be tokenized.

        Returns:
            The tokenized examples.
        """
        # Tokenize the examples
        try:
            tokenized_examples = self.tokenizer(
                examples["question" if self.pad_on_right else "context"],
                examples["context" if self.pad_on_right else "question"],
                truncation="only_second" if self.pad_on_right else "only_first",
                max_length=self.max_length,
                stride=self.doc_stride,
                return_overflowing_tokens=True,
                return_offsets_mapping=True,
                padding="max_length",
            )
        except Exception as e:
            logger.error(f"Error tokenizing examples: {e}")
            return None

        # Since one example might give us several features if it has a long context, we need a map from a feature to
        # its corresponding example. This key gives us just that.
        sample_mapping = tokenized_examples.pop("overflow_to_sample_mapping")

        # The offset mappings will give us a map from token to character position in the original context. This will
        # help us compute the start_positions and end_positions.
        offset_mapping = tokenized_examples.pop("offset_mapping")

        # Let's label those examples!
        tokenized_examples["start_positions"] = []
        tokenized_examples["end_positions"] = []

        for i, offsets in enumerate(offset_mapping):
            # We will label impossible answers with the index of the CLS token.
            input_ids = tokenized_examples["input_ids"][i]
            cls_index = input_ids.index(self.tokenizer.cls_token_id)

            # Grab the sequence corresponding to that example (to know what is the context and what is the question).
            sequence_ids = tokenized_examples.sequence_ids(i)

            # One example can give several spans, this is the index of the example containing this span of text.
            sample_index = sample_mapping[i]
            answers = examples["answers"][sample_index]
            # If no answers are given, set the cls_index as answer.
            if len(answers["answer_start"]) == 0:  # type: ignore
                tokenized_examples["start_positions"].append(cls_index)
                tokenized_examples["end_positions"].append(cls_index)
            else:
                # Start/end character index of the answer in the text.
                start_char = answers["answer_start"][0]  # type: ignore
                end_char = start_char + len(answers["text"][0])  # type: ignore

                # Start token index of the current span in the text.
                token_start_index = 0
                while sequence_ids[token_start_index] != (1 if self.pad_on_right else 0):
                    token_start_index += 1

                # End token index of the current span in the text.
                token_end_index = len(input_ids) - 1
                while sequence_ids[token_end_index] != (1 if self.pad_on_right else 0):
                    token_end_index -= 1

                # Detect if the answer is out of the span (in which case this feature is labeled with the CLS index).
                if not (offsets[token_start_index][0] <= start_char and offsets[token_end_index][1] >= end_char):
                    tokenized_examples["start_positions"].append(cls_index)
                    tokenized_examples["end_positions"].append(cls_index)
                else:
                    # Otherwise move the token_start_index and token_end_index to the two ends of the answer.
                    # Note: we could go after the last offset if the answer is the
                    # last word (edge case).
                    while token_start_index < len(offsets) and offsets[token_start_index][0] <= start_char:
                        token_start_index += 1
                    tokenized_examples["start_positions"].append(token_start_index - 1)
                    while offsets[token_end_index][1] >= end_char:
                        token_end_index -= 1
                    tokenized_examples["end_positions"].append(token_end_index + 1)

        return tokenized_examples

    def compute_metrics(self, eval_pred: EvalPrediction) -> Optional[Dict[str, float]]:
        """
        Compute the accuracy of the model's predictions.

        Args:
            eval_pred (tuple): A tuple containing two elements:
                - predictions (np.ndarray): The model's predictions.
                - label_ids (np.ndarray): The true labels.

        Returns:
            dict: A dictionary mapping metric names to computed values.
        """
        # Compute the metrics
        try:
            predictions, labels = eval_pred
            if isinstance(predictions, tuple):
                predictions = predictions[0]
            if isinstance(labels, tuple):
                labels = labels[0]

            # Convert predictions from list of 1D arrays to 1D array
            predictions = np.array([np.argmax(p) for p in predictions])

            return {"accuracy": accuracy_score(labels, predictions)}
        except Exception as e:
            logger.error(f"Error computing metrics: {e}")
            return None
