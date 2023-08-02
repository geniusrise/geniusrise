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
from pathlib import Path
from typing import Dict

import torch
from torch.utils.data import Dataset
from transformers import PreTrainedTokenizerBase

from .base import HuggingFaceBatchFineTuner


class ClassificationDataset(Dataset):
    """
    A PyTorch Dataset for text classification tasks.

    This class represents a text classification dataset. It expects the dataset to be structured such that
    each subdirectory represents a class, and contains text files for that class.

    Args:
        root_dir (str): The root directory of the dataset.
        tokenizer (PreTrainedTokenizerBase): The tokenizer to use for encoding the text.
        max_length (int, optional): The maximum length for the sequences. Defaults to 512.
    """

    def __init__(self, root_dir: str, tokenizer: PreTrainedTokenizerBase, max_length: int = 512):
        self.root_dir = Path(root_dir)
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.classes = sorted(os.listdir(self.root_dir))
        self.files = [f for c in self.classes for f in (self.root_dir / c).iterdir()]
        self.labels = [self.classes.index(c) for c in self.classes for f in (self.root_dir / c).iterdir()]

    def __len__(self) -> int:
        """Return the number of examples in the dataset."""
        return len(self.files)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        """
        Get an example from the dataset.

        Args:
            idx (int): The index of the example.

        Returns:
            Dict[str, torch.Tensor]: The encoded example.

        Raises:
            Exception: If there was an error reading the file.
        """
        try:
            text = self.files[idx].read_text().strip()
            encoding = self.tokenizer(text, truncation=True, padding="max_length", max_length=self.max_length)
            encoding["labels"] = self.labels[idx]
            return {key: torch.tensor(val) for key, val in encoding.items()}
        except Exception as e:
            logging.error(f"Error occurred when getting item {idx} from the dataset. Error: {e}")
            raise


class HuggingFaceClassificationFineTuner(HuggingFaceBatchFineTuner):
    """
    A bolt for fine-tuning Hugging Face models for text classification tasks.

    This bolt uses the Hugging Face Transformers library to fine-tune a pre-trained model for text classification.
    It uses the `Trainer` class from the Transformers library to handle the training.

    Args:
        model: The pre-trained model to fine-tune.
        tokenizer: The tokenizer associated with the model.
        input_config (BatchInputConfig): The batch input configuration.
        output_config (OutputConfig): The output configuration.
        state_manager (StateManager): The state manager.
    """

    def load_dataset(self, dataset_path: str, **kwargs) -> Dataset:
        """
        Load a classification dataset from a directory.

        Args:
            dataset_path (str): The path to the dataset directory.

        Returns:
            Dataset: The loaded dataset.

        Raises:
            Exception: If there was an error loading the dataset.
        """
        try:
            logging.info(f"Loading dataset from {dataset_path}")
            return ClassificationDataset(dataset_path, self.tokenizer)
        except Exception as e:
            logging.error(f"Error occurred when loading dataset from {dataset_path}. Error: {e}")
            raise
