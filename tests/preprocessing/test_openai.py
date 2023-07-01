# type: ignore
from unittest.mock import patch

import openai
import pandas as pd

from geniusrise.llm.types import FineTuningData, FineTuningDataItem
from geniusrise.preprocessing.openai import OpenAIPreprocessor
from geniusrise.preprocessing.prompts import prompt_generate_prompts

# import pytest


def test_generate_prompts():
    # Mock the openai.ChatCompletion.create method to return a predictable response
    with patch.object(openai.ChatCompletion, "create") as mock_create:
        mock_create.return_value = {"choices": [{"message": {"content": "Generated Prompt"}}]}

        # Call the method with a test string
        what = "code"
        strings = ["Test string 1", "Test string 2"]
        fine_tuning_data = OpenAIPreprocessor.generate_prompts(what, strings)

        # Check that the method was called with the expected parameters
        mock_create.assert_called_with(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"{prompt_generate_prompts(x=what)}Test string 2"},
            ],
        )

        # Check that the returned data is as expected
        assert fine_tuning_data == FineTuningData(
            data=[
                FineTuningDataItem(prompt="Test string 1", completion="Generated Prompt"),
                FineTuningDataItem(prompt="Test string 1", completion="Generated Prompt"),
                FineTuningDataItem(prompt="Test string 1", completion="Generated Prompt"),
                FineTuningDataItem(prompt="Test string 1", completion="Generated Prompt"),
                FineTuningDataItem(prompt="Test string 1", completion="Generated Prompt"),
                FineTuningDataItem(prompt="Test string 1", completion="Generated Prompt"),
                FineTuningDataItem(prompt="Test string 1", completion="Generated Prompt"),
                FineTuningDataItem(prompt="Test string 1", completion="Generated Prompt"),
                FineTuningDataItem(prompt="Test string 1", completion="Generated Prompt"),
                FineTuningDataItem(prompt="Test string 1", completion="Generated Prompt"),
                FineTuningDataItem(prompt="Test string 2", completion="Generated Prompt"),
                FineTuningDataItem(prompt="Test string 2", completion="Generated Prompt"),
                FineTuningDataItem(prompt="Test string 2", completion="Generated Prompt"),
                FineTuningDataItem(prompt="Test string 2", completion="Generated Prompt"),
                FineTuningDataItem(prompt="Test string 2", completion="Generated Prompt"),
                FineTuningDataItem(prompt="Test string 2", completion="Generated Prompt"),
                FineTuningDataItem(prompt="Test string 2", completion="Generated Prompt"),
                FineTuningDataItem(prompt="Test string 2", completion="Generated Prompt"),
                FineTuningDataItem(prompt="Test string 2", completion="Generated Prompt"),
                FineTuningDataItem(prompt="Test string 2", completion="Generated Prompt"),
            ]
        )


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
