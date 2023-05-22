import pandas as pd
from openai.validators import get_validators, apply_necessary_remediation, apply_optional_remediation
from geniusrise_cli.llm.types import FineTuningData
import logging

log = logging.getLogger(__name__)


class OpenAIPreprocessor:
    """
    A class to preprocess data for fine-tuning OpenAI's GPT-3 model.
    """

    @staticmethod
    def prepare_fine_tuning_data(data: FineTuningData, apply_optional_remediations: bool = False) -> pd.DataFrame:
        """
        Prepare the given data for fine-tuning.

        This method applies necessary and optional remediations to the data based on OpenAI's validators.
        The remediations are logged and the processed data is returned as a pandas DataFrame.
        """
        # Convert the data to a pandas DataFrame
        df = pd.DataFrame.from_records(data=data.dict()["data"])

        # If the DataFrame is empty, return an empty DataFrame with the expected columns
        if df.empty:
            return pd.DataFrame(columns=["prompt", "completion"])

        # Initialize a list to store optional remediations
        optional_remediations = []

        # Get OpenAI's validators
        validators = get_validators()  # type: ignore

        # Apply necessary remediations and store optional remediations
        for validator in validators:
            remediation = validator(df)
            if remediation is not None:
                optional_remediations.append(remediation)
                df = apply_necessary_remediation(df, remediation)  # type: ignore

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
            log.info("Based on the analysis we will perform the following actions:")
            for remediation in optional_remediations:
                df, optional_applied = apply_optional_remediation(df, remediation, auto_accept=True)  # type: ignore
        else:
            log.info("Validations passed, no remediations needed to be applied.")

        # Return the processed data
        return df
