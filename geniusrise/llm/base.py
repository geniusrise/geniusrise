from abc import ABC, abstractmethod
from typing import List, Optional

import pandas as pd

from geniusrise.llm.types import FineTuningData


class LLM(ABC):
    """
    Abstract base class for language models.
    """

    @abstractmethod
    def __init__(
        self,
        api_type: Optional[str] = None,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        api_version: Optional[str] = None,
    ) -> None:
        pass

    @abstractmethod
    def preprocess_for_fine_tuning(self, data: FineTuningData) -> pd.DataFrame:
        """
        Preprocess the given data for fine-tuning.
        """
        pass

    @abstractmethod
    def generate_prompts(self, data: List[str], model: str, what: str) -> pd.DataFrame:
        """
        Generate prompts from the data that can be used for fine tuning.
        """
        pass

    @abstractmethod
    def fine_tune(self, *args, **kwargs):
        """
        Fine-tune the model with the given parameters and training data.
        """
        pass

    @abstractmethod
    def get_fine_tuning_job(self, job_id: str):
        """
        Get the status of a fine-tuning job.
        """
        pass

    @abstractmethod
    def wait_for_fine_tuning(self, job_id: str, check_interval: int = 60):
        """
        Wait for a fine-tuning job to complete, checking the status every `check_interval` seconds.
        """
        pass

    @abstractmethod
    def delete_fine_tuned_model(self, model_id: str):
        """
        Delete a fine-tuned model.
        """
        pass
