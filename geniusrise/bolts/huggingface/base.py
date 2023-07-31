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
import os
from abc import abstractmethod
from typing import Dict, Optional

import numpy as np
from datasets import DatasetDict
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from torch.utils.data import Dataset
from transformers import (
    AdamW,
    EvalPrediction,
    PreTrainedModel,
    PreTrainedTokenizer,
    Trainer,
    TrainingArguments,
    get_linear_schedule_with_warmup,
)

from geniusrise.core import BatchInputConfig, BatchOutputConfig, Bolt, StateManager


class HuggingFaceBatchFineTuner(Bolt):
    """
    A bolt for fine-tuning Hugging Face models.

    This bolt uses the Hugging Face Transformers library to fine-tune a pre-trained model.
    It uses the `Trainer` class from the Transformers library to handle the training.
    """

    def __init__(
        self,
        model: PreTrainedModel,
        tokenizer: PreTrainedTokenizer,
        input_config: BatchInputConfig,
        output_config: BatchOutputConfig,
        state_manager: StateManager,
        eval: bool = False,
        **kwargs,
    ) -> None:
        """
        Initialize the bolt.

        Args:
            model (PreTrainedModel): The pre-trained model to fine-tune.
            tokenizer (PreTrainedTokenizer): The tokenizer associated with the model.
            input_config (BatchInputConfig): The batch input configuration.
            output_config (OutputConfig): The output configuration.
            state_manager (StateManager): The state manager.
            eval (bool, optional): Whether to evaluate the model after training. Defaults to False.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(
            input_config=input_config,
            output_config=output_config,
            state_manager=state_manager,
        )
        self.model = model
        self.tokenizer = tokenizer
        self.input_config = input_config
        self.output_config = output_config
        self.state_manager = state_manager
        self.eval = eval
        self.log = logging.getLogger(self.__class__.__name__)

        # Copy the datasets from S3 to the local input folder
        self.input_config.copy_from_remote()

        # Load the datasets from the local input folder
        train_dataset_path = os.path.join(self.input_config.get(), "train")
        eval_dataset_path = os.path.join(self.input_config.get(), "eval")
        self.train_dataset = self.load_dataset(train_dataset_path)
        if self.eval:
            self.eval_dataset = self.load_dataset(eval_dataset_path)

    @abstractmethod
    def load_dataset(self, dataset_path: str, **kwargs) -> Dataset | DatasetDict | Optional[Dataset]:
        """
        Load a dataset from a file.

        Args:
            dataset_path (str): The path to the dataset file.
            **kwargs: Additional keyword arguments to pass to the `load_dataset` method.

        Returns:
            Dataset: The loaded dataset.

        Raises:
            NotImplementedError: This method should be overridden by subclasses.
        """
        raise NotImplementedError("Subclasses should implement this!")

    def compute_metrics(self, eval_pred: EvalPrediction) -> Optional[Dict[str, float]] | Dict[str, float]:
        """
        Compute metrics for evaluation.

        Args:
            eval_pred (EvalPrediction): The evaluation predictions.

        Returns:
            dict: The computed metrics.
        """
        predictions, labels = eval_pred
        predictions = np.argmax(predictions, axis=1)

        return {
            "accuracy": accuracy_score(labels, predictions),
            "precision": precision_recall_fscore_support(labels, predictions, average="binary")[0],
            "recall": precision_recall_fscore_support(labels, predictions, average="binary")[1],
            "f1": precision_recall_fscore_support(labels, predictions, average="binary")[2],
        }

    def create_optimizer_and_scheduler(self, num_training_steps: int) -> tuple:
        """
        Customize the optimizer and the learning rate scheduler.

        Args:
            num_training_steps (int): The total number of training steps.

        Returns:
            tuple: The optimizer and the learning rate scheduler.
        """
        optimizer = AdamW(self.model.parameters(), lr=5e-5)
        scheduler = get_linear_schedule_with_warmup(
            optimizer, num_warmup_steps=0, num_training_steps=num_training_steps
        )

        return optimizer, scheduler

    def fine_tune(self, output_dir: str, num_train_epochs: int, per_device_train_batch_size: int, **kwargs):
        """
        Fine-tune the model.

        Args:
            output_dir (str): The output directory where the model predictions and checkpoints will be written.
            num_train_epochs (int): Total number of training epochs to perform.
            per_device_train_batch_size (int): Batch size per device during training.
            **kwargs: Additional keyword arguments for training.

        Raises:
            FileNotFoundError: If the output directory does not exist.
        """
        if not os.path.exists(output_dir):
            raise FileNotFoundError(f"Output directory {output_dir} does not exist.")

        # Define the training arguments
        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=num_train_epochs,
            per_device_train_batch_size=per_device_train_batch_size,
            **kwargs,
        )

        # Initialize the trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=self.train_dataset,
            eval_dataset=self.eval_dataset if self.eval else None,
            tokenizer=self.tokenizer,
            compute_metrics=self.compute_metrics,
        )

        # Train the model
        trainer.train()

        # Save the model
        trainer.save_model()

        # Evaluate the model
        if self.eval:
            eval_result = trainer.evaluate()

            # Log the evaluation results
            self.log.info(f"Evaluation results: {eval_result}")
