# 🧠 Geniusrise
# Copyright (C) 2023  geniusrise.ai
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
from itertools import combinations, permutations
from typing import Any, List, Tuple, Union

import numpy as np
import torch
from transformers import PreTrainedModel, PreTrainedTokenizer

log = logging.getLogger(__name__)


def generate_sentence_transformer_embeddings(
    sentences: Union[str, List[str]], model: Any, use_cuda: bool = False, batch_size: int = 32
) -> np.ndarray:
    """
    Generates embeddings for given sentences using sentence-transformers.

    Parameters:
    - sentences (Union[str, List[str]]): The sentence(s) for which to generate the embeddings.
    - model (Any): The sentence-transformer model to use.
    - use_cuda (bool, optional): Whether to use CUDA for computation. Defaults to False.
    - batch_size (int, optional): Batch size for the sentence-transformer model. Defaults to 32.

    Returns:
    np.ndarray: The generated embeddings. If a single sentence was passed, returns a single embedding.

    Note:
    - The embeddings are directly from the sentence-transformer model.
    """

    # Check if input is a single sentence or a list of sentences
    is_single_sentence = isinstance(sentences, str)

    # Convert to list if it's a single sentence
    if is_single_sentence:
        sentences = [sentences]  # type: ignore

    # Generate embeddings
    embeddings = model.encode(sentences, convert_to_numpy=use_cuda, batch_size=batch_size)

    # Return the single embedding if a single sentence was passed
    if is_single_sentence:
        return embeddings[0]

    return embeddings


def generate_embeddings(
    sentence: str,
    model: PreTrainedModel,
    tokenizer: PreTrainedTokenizer,
    output_key: str = "last_hidden_state",
    use_cuda: bool = False,
) -> np.ndarray:
    """
    Generates embeddings for a given sentence using a Hugging Face model.

    Parameters:
    - sentence (str): The sentence for which to generate the embeddings.
    - model (PreTrainedModel): The Hugging Face model to use.
    - tokenizer (PreTrainedTokenizer): The tokenizer for the model.
    - output_key (str, optional): The key to use to extract embeddings from the model output. Defaults to 'last_hidden_state'.
    - use_cuda (bool, optional): Whether to use CUDA for computation. Defaults to False.

    Returns:
    np.ndarray: The generated embeddings, averaged along the sequence length dimension.
    """
    # Generate inputs
    inputs = tokenizer(sentence, return_tensors="pt")

    # Move inputs to the same device as the model
    inputs = {k: v.to(model.device) for k, v in inputs.items()}

    # Generate outputs
    with torch.no_grad():  # Deactivate autograd to reduce memory usage
        outputs = model(**inputs)

    # Extract embeddings
    if isinstance(outputs, dict):
        embeddings = outputs.get(output_key, None)
    elif isinstance(outputs, tuple):
        embeddings = outputs[0]
    else:
        raise ValueError("Unsupported model output type")

    if embeddings is None:
        raise ValueError(f"Could not find key '{output_key}' in model outputs")

    # Average along the sequence length dimension
    embeddings = embeddings.mean(dim=1)

    # Move to CPU and convert to NumPy
    if not use_cuda:
        embeddings = embeddings.cpu().numpy()
    return embeddings


def generate_contiguous_embeddings(
    sentence: str,
    model: PreTrainedModel,
    tokenizer: PreTrainedTokenizer,
    output_key: str = "last_hidden_state",
    use_cuda: bool = False,
) -> List[Tuple[np.ndarray, str]]:
    """
    Generates embeddings for all contiguous subsets of words in a given sentence using a Hugging Face model.

    Parameters:
    - sentence (str): The sentence for which to generate the embeddings. Can contain multiple words separated by space.
    - model (PreTrainedModel): The Hugging Face model to use.
    - tokenizer (PreTrainedTokenizer): The tokenizer for the model.
    - output_key (str, optional): The key to use to extract embeddings from the model output. Defaults to 'last_hidden_state'.
    - use_cuda (bool, optional): Whether to use CUDA for computation. Defaults to False.

    Returns:
    List[Tuple[np.ndarray, str]]: A list of tuples, each containing the generated embeddings and the term.
    """
    words = sentence.split()
    embeddings_list = []

    for end_idx in range(1, len(words) + 1):
        for start_idx in range(0, end_idx):
            sub_sentence = " ".join(words[start_idx:end_idx])

            # Generate inputs
            inputs = tokenizer(sub_sentence, return_tensors="pt")

            # Move inputs to the same device as the model
            inputs = {k: v.to(model.device) for k, v in inputs.items()}

            # Generate outputs
            with torch.no_grad():  # Deactivate autograd to reduce memory usage
                outputs = model(**inputs)

            # Extract embeddings
            if isinstance(outputs, dict):
                embeddings = outputs.get(output_key, None)
            elif isinstance(outputs, tuple):
                embeddings = outputs[0]
            else:
                raise ValueError("Unsupported model output type")

            if embeddings is None:
                raise ValueError(f"Could not find key '{output_key}' in model outputs")

            # Average along the sequence length dimension
            embeddings = embeddings.mean(dim=1)

            # Move to CPU and convert to NumPy
            if not use_cuda:
                embeddings = embeddings.cpu().numpy()

            # Append embeddings and term length to the list
            embeddings_list.append((embeddings, sub_sentence))

    return embeddings_list


def generate_combination_embeddings(
    sentence: str,
    model: PreTrainedModel,
    tokenizer: PreTrainedTokenizer,
    output_key: str = "last_hidden_state",
    use_cuda: bool = False,
) -> List[Tuple[np.ndarray, str]]:
    """
    Generates embeddings for all combinations of words in a given sentence using a Hugging Face model.

    Parameters:
    - sentence (str): The sentence for which to generate the embeddings. Can contain multiple words separated by space.
    - model (PreTrainedModel): The Hugging Face model to use.
    - tokenizer (PreTrainedTokenizer): The tokenizer for the model.
    - output_key (str, optional): The key to use to extract embeddings from the model output. Defaults to 'last_hidden_state'.
    - use_cuda (bool, optional): Whether to use CUDA for computation. Defaults to False.

    Returns:
    List[Tuple[np.ndarray, str]]: A list of tuples, each containing the generated embeddings and the term.
    """
    words = sentence.split()
    all_combinations = []
    for r in range(1, len(words) + 1):
        for subset in combinations(words, r):
            all_combinations.append(" ".join(subset))

    embeddings_list = []

    for comb_term in all_combinations:
        # Generate inputs
        inputs = tokenizer(comb_term, return_tensors="pt")

        # Move inputs to the same device as the model
        inputs = {k: v.to(model.device) for k, v in inputs.items()}

        # Generate outputs
        with torch.no_grad():  # Deactivate autograd to reduce memory usage
            outputs = model(**inputs)

        # Extract embeddings
        if isinstance(outputs, dict):
            embeddings = outputs.get(output_key, None)
        elif isinstance(outputs, tuple):
            embeddings = outputs[0]
        else:
            raise ValueError("Unsupported model output type")

        if embeddings is None:
            raise ValueError(f"Could not find key '{output_key}' in model outputs")

        # Average along the sequence length dimension
        embeddings = embeddings.mean(dim=1)

        # Move to CPU and convert to NumPy
        if not use_cuda:
            embeddings = embeddings.cpu().numpy()

        # Append embeddings and term length to the list
        embeddings_list.append((embeddings, comb_term))

    return embeddings_list


def generate_permutation_embeddings(
    sentence: str,
    model: PreTrainedModel,
    tokenizer: PreTrainedTokenizer,
    output_key: str = "last_hidden_state",
    use_cuda: bool = False,
) -> List[Tuple[np.ndarray, str]]:
    """
    Generates embeddings for all permutations of words in a given sentence using a Hugging Face model.

    Parameters:
    - sentence (str): The sentence for which to generate the embeddings. Can contain multiple words separated by space.
    - model (PreTrainedModel): The Hugging Face model to use.
    - tokenizer (PreTrainedTokenizer): The tokenizer for the model.
    - output_key (str, optional): The key to use to extract embeddings from the model output. Defaults to 'last_hidden_state'.
    - use_cuda (bool, optional): Whether to use CUDA for computation. Defaults to False.

    Returns:
    List[Tuple[np.ndarray, str]]: A list of tuples, each containing the generated embeddings and the term.
    """
    words = sentence.split()
    all_permutations = []
    for r in range(1, len(words) + 1):
        for subset in permutations(words, r):
            all_permutations.append(" ".join(subset))

    embeddings_list = []

    for comb_term in all_permutations:
        # Generate inputs
        inputs = tokenizer(comb_term, return_tensors="pt")

        # Move inputs to the same device as the model
        inputs = {k: v.to(model.device) for k, v in inputs.items()}

        # Generate outputs
        with torch.no_grad():  # Deactivate autograd to reduce memory usage
            outputs = model(**inputs)

        # Extract embeddings
        if isinstance(outputs, dict):
            embeddings = outputs.get(output_key, None)
        elif isinstance(outputs, tuple):
            embeddings = outputs[0]
        else:
            raise ValueError("Unsupported model output type")

        if embeddings is None:
            raise ValueError(f"Could not find key '{output_key}' in model outputs")

        # Average along the sequence length dimension
        embeddings = embeddings.mean(dim=1)

        # Move to CPU and convert to NumPy
        if not use_cuda:
            embeddings = embeddings.cpu().numpy()

        # Append embeddings and term length to the list
        embeddings_list.append((embeddings, comb_term))

    return embeddings_list
