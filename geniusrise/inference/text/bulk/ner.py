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

import glob
import json
import os
import sqlite3
import uuid
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional

import pandas as pd
import yaml  # type: ignore
from datasets import Dataset, load_from_disk
from geniusrise import BatchInput, BatchOutput, State
from pyarrow import feather
from pyarrow import parquet as pq

from geniusrise.inference.text.base import TextBulk


class NamedEntityRecognitionBulk(TextBulk):
    r"""
    NamedEntityRecognitionBulk is a class designed for bulk processing of Named Entity Recognition (NER) tasks.
    It leverages state-of-the-art NER models from Hugging Face's transformers library to identify and classify entities
    such as person names, locations, organizations, and other types of entities from a large corpus of text.

    This class provides functionalities to load large datasets, configure NER models, and perform entity recognition
    in bulk, making it suitable for processing large volumes of text data efficiently.

    Attributes:
        model (Any): The NER model loaded for entity recognition tasks.
        tokenizer (Any): The tokenizer used for text pre-processing in alignment with the model.

    Example CLI Usage:
    ```bash
    genius NamedEntityRecognitionBulk rise \
        batch \
            --input_folder ./input \
        batch \
            --output_folder ./output \
        none \
        --id dslim/bert-large-NER-lol \
        recognize_entities \
            --args \
                model_name="dslim/bert-large-NER" \
                model_class="AutoModelForTokenClassification" \
                tokenizer_class="AutoTokenizer" \
                use_cuda=True \
                precision="float" \
                quantization=0 \
                device_map="cuda:0" \
                max_memory=None \
                torchscript=False
    ```
    """

    def __init__(self, input: BatchInput, output: BatchOutput, state: State, **kwargs: Any) -> None:
        """
        Initializes the NamedEntityRecognitionBulk class with specified input, output, and state configurations.
        Sets up the NER model and tokenizer for bulk entity recognition tasks.

        Args:
            input (BatchInput): The input data configuration.
            output (BatchOutput): The output data configuration.
            state (State): The state management for the API.
            **kwargs (Any): Additional keyword arguments for extended functionality.
        """
        super().__init__(input, output, state, **kwargs)

    def load_dataset(self, dataset_path: str, **kwargs: Any) -> Optional[Dataset]:
        r"""
        Loads a dataset from the specified directory path. The method supports various data formats and structures,
        ensuring that the dataset is properly formatted for NER tasks.

        Args:
            dataset_path (str): The path to the dataset directory.
            **kwargs: Additional keyword arguments to handle specific dataset loading scenarios.

        Returns:
            Optional[Dataset]: The loaded dataset or None if an error occurs during loading.

        ## Supported Data Formats and Structures:

        ### Hugging Face Dataset
        Dataset files saved by the Hugging Face datasets library.

        ### JSONL
        Each line is a JSON object representing an example.
        ```json
        {"tokens": ["token1", "token2", ...]}
        ```

        ### CSV
        Should contain 'tokens' columns.
        ```csv
        tokens
        "['token1', 'token2', ...]"
        ```

        ### Parquet
        Should contain 'tokens' columns.

        ### JSON
        An array of dictionaries with 'tokens' keys.
        ```json
        [{"tokens": ["token1", "token2", ...]}]
        ```

        ### XML
        Each 'record' element should contain 'tokens' child elements.
        ```xml
        <record>
            <tokens>token1 token2 ...</tokens>
        </record>
        ```

        ### YAML
        Each document should be a dictionary with 'tokens' keys.
        ```yaml
        - tokens: ["token1", "token2", ...]
        ```

        ### TSV
        Should contain 'tokens' columns separated by tabs.

        ### Excel (.xls, .xlsx)
        Should contain 'tokens' columns.

        ### SQLite (.db)
        Should contain a table with 'tokens' columns.

        ### Feather
        Should contain 'tokens' columns.
        """
        self.log.info(f"Loading dataset from {dataset_path}")
        try:
            if os.path.isfile(os.path.join(dataset_path, "dataset_info.json")):
                return load_from_disk(dataset_path)
            else:
                data = []
                for filename in glob.glob(f"{dataset_path}/**/*", recursive=True):
                    filepath = os.path.join(dataset_path, filename)
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
                            text = record.find("text").text.split()  # type: ignore
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

                return Dataset.from_pandas(pd.DataFrame(data))
        except Exception as e:
            self.log.exception(f"Error occurred when loading dataset from {dataset_path}. Error: {e}")
            raise

    def recognize_entities(
        self,
        model_name: str,
        max_length: int = 512,
        model_class: str = "AutoModelForSeq2SeqLM",
        tokenizer_class: str = "AutoTokenizer",
        use_cuda: bool = False,
        precision: str = "float16",
        quantization: int = 0,
        device_map: str | Dict | None = "auto",
        max_memory={0: "24GB"},
        torchscript: bool = False,
        compile: bool = False,
        awq_enabled: bool = False,
        flash_attention: bool = False,
        batch_size: int = 32,
        notification_email: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Performs bulk named entity recognition on the loaded dataset. The method processes the text in batches,
        applying the NER model to recognize entities.

        Args:
            model_name (str): The name or path of the NER model.
            max_length (int): The maximum sequence length for the tokenizer.
            model_class (str): The class of the model, defaults to "AutoModelForTokenClassification".
            tokenizer_class (str): The class of the tokenizer, defaults to "AutoTokenizer".
            use_cuda (bool): Whether to use CUDA for model inference, defaults to False.
            precision (str): Model computation precision, defaults to "float16".
            quantization (int): Level of quantization for model size and speed optimization, defaults to 0.
            device_map (str | Dict | None): Specific device configuration for computation, defaults to "auto".
            max_memory (Dict): Maximum memory configuration for the devices.
            torchscript (bool, optional): Whether to use a TorchScript-optimized version of the pre-trained language model. Defaults to False.
            compile (bool, optional): Whether to compile the model before fine-tuning. Defaults to True.
            awq_enabled (bool): Whether to enable AWQ optimization, defaults to False.
            flash_attention (bool): Whether to use flash attention optimization, defaults to False.
            batch_size (int): Number of documents to process simultaneously, defaults to 32.
            **kwargs: Arbitrary keyword arguments for additional configuration.

        Returns:
            None: The method processes the dataset and saves the predictions without returning any value.
        """
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
        self.tokenizer_name = tokenizer_name
        self.model_revision = model_revision
        self.tokenizer_revision = tokenizer_revision
        self.model_class = model_class
        self.tokenizer_class = tokenizer_class
        self.use_cuda = use_cuda
        self.precision = precision
        self.quantization = quantization
        self.device_map = device_map
        self.max_memory = max_memory
        self.torchscript = torchscript
        self.awq_enabled = awq_enabled
        self.flash_attention = flash_attention
        self.batch_size = batch_size
        self.notification_email = notification_email
        self.compile = compile

        model_args = {k.replace("model_", ""): v for k, v in kwargs.items() if "model_" in k}
        self.model_args = model_args

        generation_args = {k.replace("generation_", ""): v for k, v in kwargs.items() if "generation_" in k}
        self.generation_args = generation_args

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
            awq_enabled=self.awq_enabled,
            flash_attention=self.flash_attention,
            compile=self.compile,
            **self.model_args,
        )

        dataset_path = self.input.input_folder
        output_path = self.output.output_folder

        # Load dataset
        dataset = self.load_dataset(dataset_path)
        if dataset is None:
            self.log.error("Failed to load dataset.")
            return
        if dataset:
            dataset = dataset["text"]

        # Process data in batches
        for i in range(0, len(dataset), batch_size):
            batch = dataset[i : i + batch_size]
            inputs = self.tokenizer(batch, return_tensors="pt", padding=True, truncation=True)

            if next(self.model.parameters()).is_cuda:
                inputs = {k: v.cuda() for k, v in inputs.items()}

            predictions = self.model(**inputs, **generation_args)
            predictions = predictions[0] if isinstance(predictions, tuple) else predictions.logits
            predictions = predictions.argmax(dim=-1).squeeze().tolist()

            self._save_predictions(inputs["input_ids"].tolist(), predictions, batch, output_path, i)
        self.done()

    def _save_predictions(
        self, inputs: list, predictions: list, input_batch: List[str], output_path: str, batch_idx: int
    ) -> None:
        """
        Saves the NER predictions to the specified output path.

        Args:
            inputs (list): List of input tokens.
            predictions (list): List of prediction tensors from the NER model.
            input_batch (List[str]): The input text batch.
            output_path (str): The path to save the prediction results.
            batch_idx (int): The index of the current batch, used for naming the output files.

        Returns:
            None: The method saves the predictions to files and does not return any value.
        """
        # Convert tensor of label ids to list of label strings
        label_predictions = [
            [
                {
                    "label": self.model.config.id2label[label_id],
                    "position": i,
                    "token": self.tokenizer.convert_ids_to_tokens(inp[i]),
                }
                for i, label_id in enumerate(pred)
            ]
            for pred, inp in zip(predictions, inputs)
        ]

        # Prepare data for saving
        data_to_save = [
            {"input": input_text, "labels": label} for input_text, label in zip(input_batch, label_predictions)
        ]
        with open(os.path.join(output_path, f"predictions-{batch_idx}-{str(uuid.uuid4())}.jsonl"), "w") as f:
            for item in data_to_save:
                f.write(json.dumps(item) + "\n")

        self.log.info(f"Saved predictions for batch {batch_idx} to {output_path}")
