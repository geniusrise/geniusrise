# type: ignore
import pandas as pd

from geniusrise_cli.llm.types import FineTuningData, FineTuningDataItem
from geniusrise_cli.preprocessing.openai import OpenAIPreprocessor


def test_prepare_fine_tuning_data_empty():
    # Test with empty data
    data = FineTuningData(data=[])
    df = OpenAIPreprocessor.prepare_fine_tuning_data(data)
    assert df.empty


def test_prepare_fine_tuning_data():
    # Prepare some test data
    data = FineTuningData(
        data=[
            FineTuningDataItem(prompt="What is the capital of France?", completion="The capital of France is Paris."),
            FineTuningDataItem(prompt="What is the capital of Italy?", completion="The capital of Italy is Rome."),
        ]
    )

    # Call the method to test
    df = OpenAIPreprocessor.prepare_fine_tuning_data(data)

    # Check that the returned object is a pandas DataFrame
    assert isinstance(df, pd.DataFrame)

    # Check that the DataFrame has the correct shape
    assert df.shape == (2, 2)

    # Check that the DataFrame has the correct columns
    assert set(df.columns) == {"prompt", "completion"}

    # Check that the DataFrame has the correct data
    assert df.iloc[0]["prompt"] == "What is the capital of France?"
    assert df.iloc[0]["completion"] == "The capital of France is Paris."
    assert df.iloc[1]["prompt"] == "What is the capital of Italy?"
    assert df.iloc[1]["completion"] == "The capital of Italy is Rome."


def test_prepare_fine_tuning_data_multiple_items():
    # Test with multiple items
    data = FineTuningData(
        data=[
            FineTuningDataItem(prompt="What is the capital of France?", completion="The capital of France is Paris."),
            FineTuningDataItem(prompt="What is the capital of Italy?", completion="The capital of Italy is Rome."),
        ]
    )
    df = OpenAIPreprocessor.prepare_fine_tuning_data(data)
    assert df.shape == (2, 2)
    assert df.iloc[0]["prompt"] == "What is the capital of France?"
    assert df.iloc[0]["completion"] == "The capital of France is Paris."
    assert df.iloc[1]["prompt"] == "What is the capital of Italy?"
    assert df.iloc[1]["completion"] == "The capital of Italy is Rome."
