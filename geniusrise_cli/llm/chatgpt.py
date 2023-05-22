import openai
from openai.cli import FineTune
from time import sleep
import pandas as pd
from tqdm import tqdm

from typing import Optional
import logging

from geniusrise_cli import config
from geniusrise_cli.llm.types import FineTuningData
from geniusrise_cli.preprocessing.openai import OpenAIPreprocessor

log = logging.getLogger(__name__)


class ChatGPT:
    """
    A class to interact with OpenAI's GPT models, including fine-tuning the models.
    """

    def __init__(
        self,
        api_type: Optional[str] = None,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        api_version: Optional[str] = None,
    ) -> None:
        """
        Initialize the ChatGPT class with the given OpenAI API parameters.
        If a parameter is not provided, it will be fetched from the configuration.
        """
        openai.api_type = api_type if api_type else config.OPENAI_API_TYPE
        openai.api_key = api_key if api_key else config.OPENAI_API_KEY
        openai.api_base = api_base if api_base else config.OPENAI_API_BASE_URL
        openai.api_version = api_version if api_version else config.OPENAI_API_VERSION

    def preprocess_for_fine_tuning(self, data: FineTuningData) -> pd.DataFrame:
        """
        Preprocess the given data for fine-tuning.
        """
        return OpenAIPreprocessor.prepare_fine_tuning_data(data=data)

    def fine_tune(
        self,
        model: str,
        suffix: str,
        n_epochs: str,
        batch_size: str,
        learning_rate_multiplier: str,
        prompt_loss_weight: str,
        training_file: str,
        validation_file: Optional[str] = None,
    ) -> openai.FineTune:
        """
        Fine-tune the model with the given parameters and training data.
        The training data and optional validation data are uploaded to OpenAI's servers.
        The method returns the fine-tuning job.
        """
        # Upload the training and validation files to OpenAI's servers
        tf = FineTune._get_or_upload(training_file, check_if_file_exists=True)
        vf = FineTune._get_or_upload(validation_file, check_if_file_exists=True) if validation_file else None

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
        fine_tune_job = openai.FineTune.create(**fine_tune_params)

        # Log the job ID
        log.info(f"🚀 Started fine-tuning job with ID {fine_tune_job.id}")

        return fine_tune_job

    def get_fine_tuning_job(self, job_id: str) -> openai.FineTune:
        """
        Get the status of a fine-tuning job.
        """
        return openai.FineTune.retrieve(job_id)

    def wait_for_fine_tuning(self, job_id: str, check_interval: int = 60) -> Optional[openai.FineTune]:
        """Wait for a fine-tuning job to complete, checking the status every `check_interval` seconds."""
        while True:
            job = self.get_fine_tuning_job(job_id)
            if job.status == "succeeded":
                log.info(f"🎉 Fine-tuning job {job_id} succeeded.")
                return job
            elif job.status == "failed":
                log.info(f"😭 Fine-tuning job {job_id} failed.")
                return job
            else:
                for _ in tqdm(range(check_interval), desc="Waiting for fine-tuning to complete", ncols=100):
                    sleep(1)

    def delete_fine_tuned_model(self, model_id: str) -> openai.FineTune:
        """Delete a fine-tuned model."""
        return openai.FineTune.delete(model_id)
