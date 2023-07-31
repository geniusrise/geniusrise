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
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from datasets import DatasetDict, load_from_disk, load_metric
from transformers import AdamW, DataCollatorForSeq2Seq, EvalPrediction, get_linear_schedule_with_warmup

from .base import HuggingFaceBatchFineTuner

# Set up logging
logger = logging.getLogger(__name__)


class SummarizationFineTuner(HuggingFaceBatchFineTuner):
    """
    A bolt for fine-tuning Hugging Face models on summarization tasks.

    This bolt extends the HuggingFaceBatchFineTuner to handle the specifics of summarization tasks,
    such as the specific format of the datasets and the specific metrics for evaluation.

    The dataset should be in the following format:
    - Each example is a dictionary with the following keys:
        - 'document': a string representing the document to be summarized.
        - 'summary': a string representing the summary of the document.
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

    def prepare_train_features(self, examples: Dict[str, Union[str, List[str]]]) -> Optional[Dict[str, List[int]]]:
        """
        Tokenize the examples and prepare the features for training.

        Args:
            examples (dict): A dictionary of examples.

        Returns:
            dict: The processed features.
        """
        # Tokenize the examples
        try:
            tokenized_inputs = self.tokenizer(examples["document"], truncation=True, padding=False)
            tokenized_targets = self.tokenizer(examples["summary"], truncation=True, padding=False)
        except Exception as e:
            logger.error(f"Error tokenizing examples: {e}")
            return None

        # Prepare the labels
        tokenized_inputs["labels"] = tokenized_targets["input_ids"]

        return tokenized_inputs

    def data_collator(
        self, examples: List[Dict[str, Union[str, List[int]]]]
    ) -> Dict[str, Union[List[int], List[List[int]]]]:
        """
        Customize the data collator.

        Args:
            examples: The examples to collate.

        Returns:
            dict: The collated data.
        """
        return DataCollatorForSeq2Seq(self.tokenizer, model=self.model)(examples)

    def compute_metrics(self, pred: EvalPrediction) -> Dict[str, float]:
        """
        Compute ROUGE metrics.

        Args:
            pred (EvalPrediction): The predicted results.

        Returns:
            dict: A dictionary with ROUGE-1, ROUGE-2, and ROUGE-L scores.
        """
        rouge = load_metric("rouge")

        preds = pred.predictions
        if isinstance(preds, tuple):
            preds = preds[0]

        # Initialize lists to store the decoded predictions and labels
        decoded_preds = []
        decoded_labels = []

        # Process each example in the batch individually
        for prediction, label in zip(preds, pred.label_ids):
            # Convert the logits into token IDs by taking the argmax along the last dimension
            pred_id = np.argmax(prediction, axis=-1)

            # Decode the token IDs into text using the tokenizer
            decoded_pred = self.tokenizer.decode(pred_id, skip_special_tokens=True)
            decoded_label = self.tokenizer.decode(label, skip_special_tokens=True)

            # Add the decoded text to the lists
            decoded_preds.append(decoded_pred)
            decoded_labels.append(decoded_label)

        # Compute the ROUGE scores
        rouge_output = rouge.compute(predictions=decoded_preds, references=decoded_labels)

        return {
            "rouge1": rouge_output["rouge1"].mid.fmeasure,
            "rouge2": rouge_output["rouge2"].mid.fmeasure,
            "rougeL": rouge_output["rougeL"].mid.fmeasure,
        }

    def create_optimizer_and_scheduler(self, num_training_steps: int) -> Tuple[AdamW, Any]:
        """
        Create an optimizer and a learning rate scheduler.

        Args:
            num_training_steps (int): The total number of training steps.

        Returns:
            tuple: The optimizer and the scheduler.
        """
        optimizer = AdamW(self.model.parameters(), lr=5e-5)
        scheduler = get_linear_schedule_with_warmup(
            optimizer, num_warmup_steps=0, num_training_steps=num_training_steps
        )
        return optimizer, scheduler
