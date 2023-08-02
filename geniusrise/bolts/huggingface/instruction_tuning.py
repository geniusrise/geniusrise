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

import glob
import json
import logging
from typing import Dict

import torch
from datasets import Dataset as HFDataset
from torch.utils.data import Dataset
from transformers import PreTrainedTokenizerBase

from .base import HuggingFaceBatchFineTuner


class InstructionTuningDataset(Dataset):
    """
    A PyTorch Dataset for instruction tuning tasks.

    This class represents an instruction tuning dataset. It expects the dataset to be a collection of JSONL files or Hugging Face Dataset files in a directory where
    each line in each file is a JSON object with 'instruction' and 'output' fields.

    Args:
        dir_path (str): The path to the directory containing the JSONL files or Hugging Face Dataset files.
        tokenizer (PreTrainedTokenizerBase): The tokenizer to use for encoding the text.
        max_length (int, optional): The maximum length for the sequences. Defaults to 512.
    """

    def __init__(self, dir_path: str, tokenizer: PreTrainedTokenizerBase, max_length: int = 512):
        self.data = []
        for file_path in glob.glob(f"{dir_path}/*"):
            if file_path.endswith(".jsonl"):
                with open(file_path, "r") as file:
                    self.data.extend([json.loads(line) for line in file])
            elif file_path.endswith(".arrow"):
                dataset = HFDataset.from_file(file_path)
                self.data.extend(dataset)
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(f"Loaded {len(self.data)} examples from {dir_path}")

    def __len__(self) -> int:
        """Return the number of examples in the dataset."""
        return len(self.data)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        """
        Get an example from the dataset.

        Args:
            idx (int): The index of the example.

        Returns:
            Dict[str, torch.Tensor]: The encoded example.
        """
        example = self.data[idx]
        encoding = self.tokenizer(
            example["instruction"],
            example["output"],
            truncation=True,
            padding="max_length",
            max_length=self.max_length,
            return_tensors="pt",
        )
        # Remove the batch dimension from the tensors
        encoding = {key: tensor.squeeze(0) for key, tensor in encoding.items()}
        encoding["labels"] = encoding["input_ids"].clone()  # Assuming that 'output' is the labels
        return encoding


class HuggingFaceInstructionTuningFineTuner(HuggingFaceBatchFineTuner):
    """
    A bolt for fine-tuning Hugging Face models for instruction tuning tasks.

    This bolt uses the Hugging Face Transformers library to fine-tune a pre-trained model for instruction tuning.
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
        Load an instruction tuning dataset from a directory.

        Args:
            dataset_path (str): The path to the directory containing the dataset files.

        Returns:
            Dataset: The loaded dataset.
        """
        try:
            logging.info(f"Loading dataset from {dataset_path}")
            return InstructionTuningDataset(dataset_path, self.tokenizer)
        except Exception as e:
            logging.error(f"Error occurred when loading dataset from {dataset_path}. Error: {e}")
            raise
