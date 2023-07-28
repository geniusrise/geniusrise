from datasets import load_from_disk
from transformers import PreTrainedModel, PreTrainedTokenizer
from geniusrise.core import BatchInputConfig, BatchOutputConfig, StateManager
from .base import HuggingFaceBatchFineTuner
from sklearn.metrics import accuracy_score
import numpy as np


class QuestionAnsweringFineTuner(HuggingFaceBatchFineTuner):
    """
    A bolt for fine-tuning Hugging Face models on question answering tasks.

    This bolt extends the HuggingFaceBatchFineTuner to handle the specifics of question answering tasks,
    such as the specific format of the datasets and the specific metrics for evaluation.
    """

    def __init__(
        self,
        model: PreTrainedModel,
        tokenizer: PreTrainedTokenizer,
        input_config: BatchInputConfig,
        output_config: BatchOutputConfig,
        state_manager: StateManager,
        pad_on_right: bool,
        max_length: int,
        doc_stride: int,
        eval: bool = False,
        **kwargs,
    ) -> None:
        """
        Initialize the bolt.

        Args:
            model (PreTrainedModel): The pre-trained model to fine-tune.
            tokenizer (PreTrainedTokenizer): The tokenizer associated with the model.
            input_config (BatchInputConfig): The batch input configuration.
            output_config (OutputConfig): The output configuration.
            state_manager (StateManager): The state manager.
            pad_on_right (bool): Whether to pad on the right.
            max_length (int): The maximum length of the sequences.
            doc_stride (int): The document stride.
            eval (bool, optional): Whether to evaluate the model after training. Defaults to False.
            **kwargs: Additional keyword arguments.
        """
        self.pad_on_right = pad_on_right
        self.max_length = max_length
        self.doc_stride = doc_stride
        super().__init__(
            model=model,
            tokenizer=tokenizer,
            input_config=input_config,
            output_config=output_config,
            state_manager=state_manager,
            eval=eval,
            **kwargs,
        )

    def load_dataset(self, dataset_path, pad_on_right=None, max_length=None, doc_stride=None):
        """
        Load a dataset from a directory.

        The directory should contain one or multiple files in the following formats: .txt, .csv, .json, .jsonl, .parquet, .tfrecord.
        Each file should contain a list of examples. Each example should be a dictionary with the following keys:
        - 'context': a string representing the context in which the question is asked.
        - 'question': a string representing the question.
        - 'answers': a dictionary with the following keys:
            - 'text': a list of strings representing the possible answers to the question.
            - 'answer_start': a list of integers representing the start character position of each answer in the context.

        Args:
            dataset_path (str): The path to the directory containing the dataset files.

        Returns:
            Dataset: The loaded dataset.
        """
        self.pad_on_right = pad_on_right if pad_on_right else self.pad_on_right
        self.max_length = max_length if max_length else self.max_length
        self.doc_stride = doc_stride if doc_stride else self.doc_stride
        # Load the dataset from the directory
        dataset = load_from_disk(dataset_path)

        # Preprocess the dataset
        tokenized_dataset = dataset.map(self.prepare_train_features, batched=True, remove_columns=dataset.column_names)

        return tokenized_dataset

    def prepare_train_features(self, examples):
        """
        Tokenize our examples with truncation and padding, but keep the overflows using a stride. This results
        in one example possible giving several features when a context is long, each of those features having a
        context that overlaps a bit the context of the previous feature.
        """
        tokenized_examples = self.tokenizer(
            examples["question" if self.pad_on_right else "context"],
            examples["context" if self.pad_on_right else "question"],
            truncation="only_second" if self.pad_on_right else "only_first",
            max_length=self.max_length,
            stride=self.doc_stride,
            return_overflowing_tokens=True,
            return_offsets_mapping=True,
            padding="max_length",
        )

        # Since one example might give us several features if it has a long context, we need a map from a feature to
        # its corresponding example. This key gives us just that.
        sample_mapping = tokenized_examples.pop("overflow_to_sample_mapping")

        # The offset mappings will give us a map from token to character position in the original context. This will
        # help us compute the start_positions and end_positions.
        offset_mapping = tokenized_examples.pop("offset_mapping")

        # Let's label those examples!
        tokenized_examples["start_positions"] = []
        tokenized_examples["end_positions"] = []

        for i, offsets in enumerate(offset_mapping):
            # We will label impossible answers with the index of the CLS token.
            input_ids = tokenized_examples["input_ids"][i]
            cls_index = input_ids.index(self.tokenizer.cls_token_id)

            # Grab the sequence corresponding to that example (to know what is the context and what is the question).
            sequence_ids = tokenized_examples.sequence_ids(i)

            # One example can give several spans, this is the index of the example containing this span of text.
            sample_index = sample_mapping[i]
            answers = examples["answers"][sample_index]
            # If no answers are given, set the cls_index as answer.
            if len(answers["answer_start"]) == 0:
                tokenized_examples["start_positions"].append(cls_index)
                tokenized_examples["end_positions"].append(cls_index)
            else:
                # Start/end character index of the answer in the text.
                start_char = answers["answer_start"][0]
                end_char = start_char + len(answers["text"][0])

                # Start token index of the current span in the text.
                token_start_index = 0
                while sequence_ids[token_start_index] != (1 if self.pad_on_right else 0):
                    token_start_index += 1

                # End token index of the current span in the text.
                token_end_index = len(input_ids) - 1
                while sequence_ids[token_end_index] != (1 if self.pad_on_right else 0):
                    token_end_index -= 1

                # Detect if the answer is out of the span (in which case this feature is labeled with the CLS index).
                if not (offsets[token_start_index][0] <= start_char and offsets[token_end_index][1] >= end_char):
                    tokenized_examples["start_positions"].append(cls_index)
                    tokenized_examples["end_positions"].append(cls_index)
                else:
                    # Otherwise move the token_start_index and token_end_index to the two ends of the answer.
                    # Note: we could go after the last offset if the answer is the last word (edge case).
                    while token_start_index < len(offsets) and offsets[token_start_index][0] <= start_char:
                        token_start_index += 1
                    tokenized_examples["start_positions"].append(token_start_index - 1)
                    while offsets[token_end_index][1] >= end_char:
                        token_end_index -= 1
                    tokenized_examples["end_positions"].append(token_end_index + 1)

        return tokenized_examples

    def compute_metrics(self, eval_pred):
        """
        Compute the accuracy of the model's predictions.

        Args:
            eval_pred (tuple): A tuple containing two elements:
                - predictions (np.ndarray): The model's predictions.
                - label_ids (np.ndarray): The true labels.

        Returns:
            dict: A dictionary mapping metric names to computed values.
        """
        predictions, labels = eval_pred
        if isinstance(predictions, tuple):
            predictions = predictions[0]
        if isinstance(labels, tuple):
            labels = labels[0]

        # Convert predictions from list of 1D arrays to 1D array
        predictions = np.array([np.argmax(p) for p in predictions])

        print(labels, [x.shape for x in labels])
        print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
        print(predictions.shape)
        return {"accuracy": accuracy_score(labels, predictions)}
