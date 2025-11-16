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

import json
import os
import pickle
import sqlite3
import uuid
import xml.etree.ElementTree as ET
from typing import Any, Dict, Optional, Tuple

import pandas as pd
import pyarrow.feather as feather
import pyarrow.parquet as pq
import torch
import transformers
import yaml  # type: ignore
from datasets import Dataset
from geniusrise import BatchInput, BatchOutput, State
from geniusrise.logging import setup_logger
from sentence_transformers import SentenceTransformer
from transformers import AutoModelForCausalLM, AutoTokenizer

from geniusrise.inference.text.utils.embeddings import (
    generate_combination_embeddings,
    generate_contiguous_embeddings,
    generate_permutation_embeddings,
    generate_sentence_transformer_embeddings,
)


class EmbeddingsBulk:
    r"""
    The `EmbeddingsBulk` class is designed to generate embeddings in bulk for various types of text data.
    It supports multiple data formats: JSONL, CSV, Parquet, JSON, XML, YAML, TSV, Excel, SQLite, and Feather.

    Args:
        input (BatchInput): An instance of the BatchInput class for reading the data.
        output (BatchOutput): An instance of the BatchOutput class for saving the data.
        state (State): An instance of the State class for maintaining the state.
        **kwargs: Additional keyword arguments.

    CLI Usage:

    ```bash
    genius EmbeddingsBulk rise \
        batch \
            --bucket my_bucket \
            --s3_folder s3/input \
        batch \
            --bucket my_bucket \
            --s3_folder s3/output \
        none \
        process \
            --args model_name=bert-base-uncased tokenizer_name=bert-base-uncased use_cuda=true
    ```

    YAML Configuration:

    ```yaml
    version: "1"
    bolts:
        generate_embeddings:
            name: "EmbeddingsBulk"
            method: "process"
            args:
                model_name: "bert-base-uncased"
                tokenizer_name: "bert-base-uncased"
                use_cuda: true
            input:
                type: "batch"
                args:
                    bucket: "my_bucket"
                    s3_folder: "s3/input"
            output:
                type: "batch"
                args:
                    bucket: "my_bucket"
                    s3_folder: "s3/output"
    ```
    """

    def __init__(self, input: BatchInput, output: BatchOutput, state: State, **kwargs) -> None:
        self.input = input
        self.output = output
        self.state = state
        self.log = setup_logger(self.state)

    def load_models(
        self,
        model_name: str,
        tokenizer_name: str,
        model_revision: Optional[str] = None,
        tokenizer_revision: Optional[str] = None,
        model_class: str = "AutoModelForCausalLM",
        tokenizer_class: str = "AutoTokenizer",
        use_cuda: bool = False,
        precision: str = "float16",
        quantization: int = 0,
        device_map: str | Dict | None = "auto",
        max_memory={0: "24GB"},
        torchscript: bool = False,
        compile: bool = False,
        **model_args: Any,
    ) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
        """
        Loads a Hugging Face model and tokenizer optimized for inference.

        Parameters:
        - model_name (str): The name of the model to load.
        - model_class (str): The class name of the model to load. Default is "AutoModelForCausalLM".
        - tokenizer_class (str): The class name of the tokenizer to load. Default is "AutoTokenizer".
        - use_cuda (bool): Whether to use CUDA for GPU acceleration. Default is False.
        - precision (str): The bit precision for model and tokenizer. Options are 'float32', 'float16', 'bfloat16'. Default is 'float16'.
        - device_map (Union[str, Dict]): Device map for model placement. Default is "auto".
        - max_memory (Dict): Maximum GPU memory to be allocated.
        - model_args (Any): Additional keyword arguments for the model.

        Returns:
        Tuple[AutoModelForCausalLM, AutoTokenizer]: The loaded model and tokenizer.

        Usage:
        ```python
        model, tokenizer = load_models("gpt-2", use_cuda=True, precision='float32', quantize=True, quantize_bits=8)
        ```
        """
        self.log.info(f"Loading Hugging Face model: {model_name}")

        # Determine the torch dtype based on precision
        if precision == "float16":
            torch_dtype = torch.float16
        elif precision == "float32":
            torch_dtype = torch.float32
        elif precision == "bfloat16":
            torch_dtype = torch.bfloat16
        else:
            raise ValueError("Unsupported precision. Choose from 'float32', 'float16', 'bfloat16'.")

        if use_cuda and not device_map:
            device_map = "auto"

        ModelClass = getattr(transformers, model_class)
        TokenizerClass = getattr(transformers, tokenizer_class)

        # Load the model and tokenizer
        tokenizer = TokenizerClass.from_pretrained(tokenizer_name, revision=tokenizer_revision, torch_dtype=torch_dtype)

        self.log.info(f"Loading model from {model_name} {model_revision} with {model_args}")
        if quantization == 8:
            model = ModelClass.from_pretrained(
                model_name,
                revision=model_revision,
                torchscript=torchscript,
                max_memory=max_memory,
                device_map=device_map,
                load_in_8bit=True,
                **model_args,
            )
        elif quantization == 4:
            model = ModelClass.from_pretrained(
                model_name,
                revision=model_revision,
                torchscript=torchscript,
                max_memory=max_memory,
                device_map=device_map,
                load_in_4bit=True,
                **model_args,
            )
        else:
            model = ModelClass.from_pretrained(
                model_name,
                revision=model_revision,
                torch_dtype=torch_dtype,
                torchscript=torchscript,
                max_memory=max_memory,
                device_map=device_map,
                **model_args,
            )

        # Set to evaluation mode for inference
        model.eval()

        if tokenizer and tokenizer.eos_token and (not tokenizer.pad_token):
            tokenizer.pad_token = tokenizer.eos_token

        self.log.debug("Hugging Face model and tokenizer loaded successfully.")
        return model, tokenizer

    def generate(
        self,
        kind: str,
        model_name: str,
        model_class: str = "AutoModelForCausalLM",
        tokenizer_class: str = "AutoTokenizer",
        sentence_transformer_model: str = "paraphrase-MiniLM-L6-v2",
        use_cuda: bool = False,
        precision: str = "float16",
        quantization: int = 0,
        device_map: str | Dict | None = "auto",
        max_memory={0: "24GB"},
        torchscript: bool = False,
        compile: bool = False,
        batch_size: int = 32,
        **model_args: Any,
    ) -> None:
        """
        Generate embeddings in bulk for various types of text data.

        Args:
            **kwargs: Additional keyword arguments.

        This method reads text data from the specified input path, generates embeddings, and saves them to the specified output path.
        """
        self.model_name = model_name
        self.model_class = model_class
        self.tokenizer_class = tokenizer_class
        self.use_cuda = use_cuda
        self.quantization = quantization
        self.precision = precision
        self.device_map = device_map
        self.max_memory = max_memory
        self.torchscript = torchscript
        self.model_args = model_args

        if ":" in model_name:
            model_revision = model_name.split(":")[1]
            tokenizer_revision = model_name.split(":")[1]
            model_name = model_name.split(":")[0]
            tokenizer_name = model_name
        else:
            model_revision = None
            tokenizer_revision = None
            tokenizer_name = model_name
        self.model_name = model_name
        self.model_revision = model_revision
        self.tokenizer_name = tokenizer_name
        self.tokenizer_revision = tokenizer_revision

        if self.use_cuda and self.device_map is None:
            self.device_map = "cuda:0"

        if kind == "sentence":
            self.sentence_transformer_model = SentenceTransformer(model_name, device="cuda" if use_cuda else "cpu")
        else:
            self.model, self.tokenizer = self.load_models(
                model_name=self.model_name,
                tokenizer_name=self.tokenizer_name,
                model_revision=self.model_revision,
                tokenizer_revision=self.tokenizer_revision,
                model_class=self.model_class,
                tokenizer_class=self.tokenizer_class,
                use_cuda=self.use_cuda,
                precision=self.precision,
                quantization=self.quantization,
                device_map=self.device_map,
                max_memory=self.max_memory,
                torchscript=self.torchscript,
                **self.model_args,
            )

        dataset_path = self.input.input_folder
        output_path = self.output.output_folder

        # Load dataset
        _dataset = self._load_dataset(dataset_path)
        if _dataset is None:
            self.log.error("Failed to load dataset.")
            return
        dataset = _dataset["text"]

        # Generate embeddings
        embeddings: Any
        if kind == "sentence":
            embeddings = generate_sentence_transformer_embeddings(
                sentences=dataset,
                model=self.sentence_transformer_model,
                use_cuda=self.use_cuda,
                batch_size=batch_size,
            )
            return self._save_embeddings(embeddings, output_path)
        elif kind == "sentence_windows":
            embeddings = [
                generate_contiguous_embeddings(
                    sentence=sentence,
                    model=self.model,
                    tokenizer=self.tokenizer,
                    output_key="last_hidden_state",
                    use_cuda=self.use_cuda,
                )
                for sentence in dataset
            ]
            return self._save_embeddings(embeddings, output_path)
        elif kind == "sentence_combinations":
            embeddings = [
                generate_combination_embeddings(
                    sentence=sentence,
                    model=self.model,
                    tokenizer=self.tokenizer,
                    output_key="last_hidden_state",
                    use_cuda=self.use_cuda,
                )
                for sentence in dataset
            ]
            return self._save_embeddings(embeddings, output_path)
        elif kind == "sentence_permutations":
            embeddings = [
                generate_permutation_embeddings(
                    sentence=sentence,
                    model=self.model,
                    tokenizer=self.tokenizer,
                    output_key="last_hidden_state",
                    use_cuda=self.use_cuda,
                )
                for sentence in dataset
            ]
            return self._save_embeddings(embeddings, output_path)

    def _load_dataset(self, dataset_path: str) -> Optional[Dataset]:
        """
        Load a text dataset from a directory.

        Args:
            dataset_path (str): The path to the dataset directory.

        Returns:
            Dataset: The loaded dataset.

        Raises:
            Exception: If there was an error loading the dataset.
        """
        data = []
        for filename in os.listdir(dataset_path):
            filepath = os.path.join(dataset_path, filename)
            try:
                if filename.endswith(".jsonl"):
                    with open(filepath, "r") as f:
                        for line in f:
                            example = json.loads(line)
                            data.append(example)

                elif filename.endswith(".csv"):
                    df = pd.read_csv(filepath)
                    data.extend(df.to_dict("records"))

                elif filename.endswith(".parquet"):
                    df = pq.read_table(filepath).to_pandas()
                    data.extend(df.to_dict("records"))

                elif filename.endswith(".json"):
                    with open(filepath, "r") as f:
                        json_data = json.load(f)
                        data.extend(json_data)

                elif filename.endswith(".xml"):
                    tree = ET.parse(filepath)
                    root = tree.getroot()
                    for record in root.findall("record"):
                        text = record.find("text").text  # type: ignore
                        data.append({"text": text})

                elif filename.endswith(".yaml") or filename.endswith(".yml"):
                    with open(filepath, "r") as f:
                        yaml_data = yaml.safe_load(f)
                        data.extend(yaml_data)

                elif filename.endswith(".tsv"):
                    df = pd.read_csv(filepath, sep="\t")
                    data.extend(df.to_dict("records"))

                elif filename.endswith((".xls", ".xlsx")):
                    df = pd.read_excel(filepath)
                    data.extend(df.to_dict("records"))

                elif filename.endswith(".db"):
                    conn = sqlite3.connect(filepath)
                    query = "SELECT text FROM dataset_table;"
                    df = pd.read_sql_query(query, conn)
                    data.extend(df.to_dict("records"))

                elif filename.endswith(".feather"):
                    df = feather.read_feather(filepath)
                    data.extend(df.to_dict("records"))

            except Exception as e:
                self.log.exception(f"Error occurred when loading dataset from {filepath}. Error: {e}")
                raise

        if not data:
            self.log.error("No data found.")
            return None

        return Dataset.from_pandas(pd.DataFrame(data))

    def _save_embeddings(self, embeddings: Dict[str, Any], output_path: str) -> None:
        """
        Save the generated embeddings to the specified output path.

        Args:
            embeddings (Dict[str, Any]): A dictionary containing the generated embeddings.
            output_path (str): The path to save the embeddings.
        """
        with open(os.path.join(output_path, f"embeddings-{str(uuid.uuid4())}.json"), "wb") as f:
            pickle.dump(embeddings, f)
