import json
import os
from typing import Optional

import pandas as pd
from datasets import Dataset, DatasetDict, load_from_disk
from openai.validators import apply_necessary_remediation, apply_optional_remediation, get_validators

from .base import OpenAIFineTuner


class OpenAIInstructionFineTuner(OpenAIFineTuner):
    """
    A bolt for fine-tuning OpenAI models for instruction following tasks.

    This bolt uses the OpenAI API to fine-tune a pre-trained model for instruction following.

    The dataset should be in the following format:
    - Each example is a dictionary with the following keys:
        - 'instruction': a string representing the instruction.
        - 'output': a string representing the expected output after following the instruction.
    """

    def load_dataset(self, dataset_path: str, **kwargs) -> Dataset | DatasetDict | Optional[Dataset]:
        """
        Load an instruction following dataset from a directory.

        The directory can contain either:
        - Dataset files saved by the Hugging Face datasets library, or
        - JSONL files where each line is a JSON object representing an example. Each JSON object should have the
          following structure:
            {
                "instruction": "The instruction text",
                "output": "The expected output text"
            }

        Args:
            dataset_path (str): The path to the dataset directory.

        Returns:
            Dataset: The loaded dataset.

        Raises:
            Exception: If there was an error loading the dataset.
        """
        try:
            self.log.info(f"Loading dataset from {dataset_path}")
            if os.path.isfile(os.path.join(dataset_path, "dataset_info.json")):
                # Load dataset saved by Hugging Face datasets library
                return load_from_disk(dataset_path)
            else:
                # Load dataset from JSONL files
                data = []
                for filename in os.listdir(dataset_path):
                    with open(os.path.join(dataset_path, filename), "r") as f:
                        for line in f:
                            example = json.loads(line)
                            data.append(example)
                return Dataset.from_pandas(pd.DataFrame(data))
        except Exception as e:
            self.log.error(f"Error occurred when loading dataset from {dataset_path}. Error: {e}")
            raise

    def prepare_fine_tuning_data(
        self, data: Dataset | DatasetDict | Optional[Dataset], apply_optional_remediations: bool = False
    ) -> None:
        """
        Prepare the given data for fine-tuning.

        This method applies necessary and optional remediations to the data based on OpenAI's validators.
        The remediations are logged and the processed data is saved into two files.

        The data is converted into the format expected by OpenAI for fine-tuning:
        - The 'prompt' field is created from the 'instruction' field.
        - The 'completion' field is created from the 'output' field.

        Args:
            data (Dataset | DatasetDict | Optional[Dataset]): The data to prepare for fine-tuning. This should be a
            Dataset or DatasetDict object, or a pandas DataFrame. If it's a DataFrame, it should have the following
            columns: 'instruction', 'output'.
            apply_optional_remediations (bool, optional): Whether to apply optional remediations. Defaults to False.

        Raises:
            Exception: If there was an error preparing the data.
        """
        # Convert the data to a pandas DataFrame
        df = pd.DataFrame.from_records(data=data)

        # For instruction following tasks, we need to convert the data into the format expected by OpenAI
        df["prompt"] = df["instruction"]
        df["completion"] = df["output"]
        df = df[["prompt", "completion"]]

        # Apply necessary and optional remediations
        optional_remediations = []
        validators = get_validators()  # type: ignore
        for validator in validators:
            remediation = validator(df)
            if remediation is not None:
                optional_remediations.append(remediation)
                df = apply_necessary_remediation(df, remediation)  # type: ignore

        # Apply optional remediations if necessary
        any_optional_or_necessary_remediations = any(
            [
                remediation
                for remediation in optional_remediations
                if remediation.optional_msg is not None or remediation.necessary_msg is not None
            ]
        )
        if any_optional_or_necessary_remediations and apply_optional_remediations:
            self.log.info("Based on the analysis we will perform the following actions:")
            for remediation in optional_remediations:
                df, _ = apply_optional_remediation(df, remediation, auto_accept=True)  # type: ignore
        else:
            self.log.info("Validations passed, no remediations needed to be applied.")

        # Save the processed data into two files in JSONL format
        self.train_file = os.path.join(self.input_config.get(), "train.jsonl")  # type: ignore
        self.eval_file = os.path.join(self.input_config.get(), "eval.jsonl")  # type: ignore
        df.to_json(self.train_file, orient="records", lines=True)
        df.to_json(self.eval_file, orient="records", lines=True)
