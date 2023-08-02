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
from time import sleep
from typing import Optional

import openai
import pandas as pd
from datasets import Dataset, DatasetDict
from openai.cli import FineTune
from openai.validators import apply_necessary_remediation, apply_optional_remediation, get_validators
from tqdm import tqdm

from geniusrise.core import BatchInputConfig, BatchOutputConfig, Bolt, StateManager


class OpenAIFineTuner(Bolt):
    """
    A bolt for fine-tuning OpenAI models.

    This bolt uses the OpenAI API to fine-tune a pre-trained model.
    """

    def __init__(
        self,
        input_config: BatchInputConfig,
        output_config: BatchOutputConfig,
        state_manager: StateManager,
        api_type: Optional[str] = None,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        api_version: Optional[str] = None,
        eval: bool = False,
        **kwargs,
    ) -> None:
        """
        Initialize the bolt.

        Args:
            api_type (str, optional): The OpenAI API type.
            api_key (str, optional): The OpenAI API key.
            api_base (str, optional): The OpenAI API base URL.
            api_version (str, optional): The OpenAI API version.
            input_config (BatchInputConfig): The batch input configuration.
            output_config (BatchOutputConfig): The output configuration.
            state_manager (StateManager): The state manager.
            eval (bool, optional): Whether to evaluate the model after training. Defaults to False.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(
            input_config=input_config,
            output_config=output_config,
            state_manager=state_manager,
        )
        openai.api_type = api_type  # type: ignore
        openai.api_key = api_key  # type: ignore
        openai.api_base = api_base  # type: ignore
        openai.api_version = api_version  # type: ignore
        self.input_config = input_config
        self.output_config = output_config
        self.state_manager = state_manager
        self.eval = eval
        self.log = logging.getLogger(self.__class__.__name__)

        # Load the datasets from the local input folder
        train_dataset_path = os.path.join(self.input_config.get(), "train")
        eval_dataset_path = os.path.join(self.input_config.get(), "eval")
        self.train_dataset = self.load_dataset(train_dataset_path)
        if self.eval:
            self.eval_dataset = self.load_dataset(eval_dataset_path)
        self.train_file: Optional[str] = None
        self.eval_file: Optional[str] = None

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

    def prepare_fine_tuning_data(
        self, data: Dataset | DatasetDict | Optional[Dataset], apply_optional_remediations: bool = False
    ) -> None:
        """
        Prepare the given data for fine-tuning.

        This method applies necessary and optional remediations to the data based on OpenAI's validators.
        The remediations are logged and the processed data is saved into two files.
        """
        # Convert the data to a pandas DataFrame
        df = pd.DataFrame.from_records(data=data)

        # Initialize a list to store optional remediations
        optional_remediations = []

        # Get OpenAI's validators
        validators = get_validators()  # type: ignore

        # Apply necessary remediations and store optional remediations
        for validator in validators:
            remediation = validator(data)
            if remediation is not None:
                optional_remediations.append(remediation)
                data = apply_necessary_remediation(data, remediation)  # type: ignore

        # Check if there are any optional or necessary remediations
        any_optional_or_necessary_remediations = any(
            [
                remediation
                for remediation in optional_remediations
                if remediation.optional_msg is not None or remediation.necessary_msg is not None
            ]
        )

        # Apply optional remediations if there are any
        if any_optional_or_necessary_remediations and apply_optional_remediations:
            self.log.info("Based on the analysis we will perform the following actions:")
            for remediation in optional_remediations:
                data, _ = apply_optional_remediation(data, remediation, auto_accept=True)  # type: ignore
        else:
            self.log.info("Validations passed, no remediations needed to be applied.")

        # Save the processed data into two files in JSONL format
        self.train_file = os.path.join(self.input_config.get(), "train.jsonl")  # type: ignore
        self.eval_file = os.path.join(self.input_config.get(), "eval.jsonl")  # type: ignore
        df.to_json(self.train_file, orient="records", lines=True)
        df.to_json(self.eval_file, orient="records", lines=True)

    def fine_tune(
        self,
        model: str,
        suffix: str,
        n_epochs: int,
        batch_size: int,
        learning_rate_multiplier: int,
        prompt_loss_weight: int,
    ) -> FineTune:
        """
        Fine-tune the model with the given parameters and training data.
        The training data and optional validation data are uploaded to OpenAI's servers.
        The method returns the fine-tuning job.
        """
        # Upload the training and validation files to OpenAI's servers
        tf = FineTune._get_or_upload(self.train_file, check_if_file_exists=False)
        vf = FineTune._get_or_upload(self.eval_file, check_if_file_exists=False) if self.eval else None

        # Prepare the parameters for the fine-tuning request
        fine_tune_params = {
            "model": model,
            "suffix": suffix,
            "n_epochs": n_epochs,
            "batch_size": batch_size,
            "learning_rate_multiplier": learning_rate_multiplier,
            "prompt_loss_weight": prompt_loss_weight,
            "training_file": tf,
            "validation_file": vf,
        }

        # Remove None values from the parameters
        fine_tune_params = {k: v for k, v in fine_tune_params.items() if v is not None}

        # Make the fine-tuning request
        fine_tune_job = FineTune.create(**fine_tune_params)

        # Log the job ID
        self.log.info(f"🚀 Started fine-tuning job with ID {fine_tune_job.id}")

        return fine_tune_job

    def get_fine_tuning_job(self, job_id: str) -> FineTune:
        """
        Get the status of a fine-tuning job.
        """
        return FineTune.retrieve(job_id)

    def wait_for_fine_tuning(self, job_id: str, check_interval: int = 60) -> Optional[FineTune]:
        """Wait for a fine-tuning job to complete, checking the status every `check_interval` seconds."""
        while True:
            job = self.get_fine_tuning_job(job_id)
            if job.status == "succeeded":  # type: ignore
                self.log.info(f"🎉 Fine-tuning job {job_id} succeeded.")
                return job
            elif job.status == "failed":  # type: ignore
                self.log.info(f"😭 Fine-tuning job {job_id} failed.")
                return job
            else:
                for _ in tqdm(range(check_interval), desc="Waiting for fine-tuning to complete", ncols=100):
                    sleep(1)

    def delete_fine_tuned_model(self, model_id: str) -> FineTune:
        """Delete a fine-tuned model."""
        return FineTune.delete(model_id)
