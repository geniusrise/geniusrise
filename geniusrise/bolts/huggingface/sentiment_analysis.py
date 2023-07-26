from datasets import load_from_disk
from transformers import DataCollatorWithPadding

from .base import HuggingFaceBatchFineTuner


class SentimentAnalysisFineTuner(HuggingFaceBatchFineTuner):
    """
    A bolt for fine-tuning Hugging Face models on sentiment analysis tasks.

    This bolt extends the HuggingFaceBatchFineTuner to handle the specifics of sentiment analysis tasks,
    such as the specific format of the datasets and the specific metrics for evaluation.

    The dataset should be in the following format:
    - Each example is a dictionary with the following keys:
        - 'text': a string representing the text to classify.
        - 'label': an integer representing the sentiment of the text.
    """

    def load_dataset(self, dataset_path, **kwargs):
        """
        Load a dataset from a directory.

        Args:
            dataset_path (str): The path to the directory containing the dataset files.
            **kwargs: Additional keyword arguments to pass to the `load_dataset` method.

        Returns:
            Dataset: The loaded dataset.
        """
        # Load the dataset from the directory
        dataset = load_from_disk(dataset_path)

        # Preprocess the dataset
        tokenized_dataset = dataset.map(self.prepare_train_features, batched=True, remove_columns=dataset.column_names)

        return tokenized_dataset

    def prepare_train_features(self, examples):
        """
        Tokenize the examples and prepare the features for training.

        Args:
            examples (dict): A dictionary of examples.

        Returns:
            dict: The processed features.
        """
        # Tokenize the examples
        tokenized_inputs = self.tokenizer(examples["text"], truncation=True, padding=False)

        # Prepare the labels
        tokenized_inputs["labels"] = examples["label"]

        return tokenized_inputs

    def data_collator(self, examples):
        """
        Customize the data collator.

        Args:
            examples: The examples to collate.

        Returns:
            dict: The collated data.
        """
        return DataCollatorWithPadding(self.tokenizer)(examples)
