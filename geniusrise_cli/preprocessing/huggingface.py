from itertools import chain
from datasets import load_dataset
from typing import Optional


class HuggingFacePreprocessor:
    """
    A class to preprocess data for fine-tuning huggingface models.
    """

    @staticmethod
    def preprocess_for_fine_tuning(
        tokenizer,
        data_dir: str,
        train_test_split: Optional[float] = 0.0,
        cache_dir: Optional[str] = None,
        use_auth_token: Optional[bool] = None,
        block_size: int = 128,
        preprocessing_num_workers: Optional[int] = 1,
        overwrite_cache: bool = False,
    ):
        # Load the dataset
        data_files = {}
        if train_file is not None:
            data_files["train"] = train_file
        if validation_file is not None:
            data_files["validation"] = validation_file
        extension = train_file.split(".")[-1] if train_file is not None else validation_file.split(".")[-1]
        if extension == "txt":
            extension = "text"
        raw_datasets = load_dataset(
            extension,
            data_files=data_files,
            cache_dir=cache_dir,
            use_auth_token=True if use_auth_token else None,
        )

        # Tokenize the text
        def tokenize_function(examples):
            return tokenizer(examples[text_column_name])

        tokenized_datasets = raw_datasets.map(
            tokenize_function,
            batched=True,
            num_proc=preprocessing_num_workers,
            remove_columns=list(raw_datasets["train"].features),
            load_from_cache_file=not overwrite_cache,
        )

        # Group texts into chunks
        def group_texts(examples):
            concatenated_examples = {k: list(chain(*examples[k])) for k in examples.keys()}
            total_length = len(concatenated_examples[list(examples.keys())[0]])
            total_length = (total_length // block_size) * block_size
            result = {
                k: [t[i : i + block_size] for i in range(0, total_length, block_size)]
                for k, t in concatenated_examples.items()
            }
            result["labels"] = result["input_ids"].copy()
            return result

        lm_datasets = tokenized_datasets.map(
            group_texts,
            batched=True,
            num_proc=preprocessing_num_workers,
            load_from_cache_file=not overwrite_cache,
        )

        return lm_datasets
