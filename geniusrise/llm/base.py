# geniusrise
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
