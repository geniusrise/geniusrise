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
from typing import Any, Dict, Optional

import pandas as pd
import pyarrow.parquet as pq
import torch
import yaml  # type: ignore
from datasets import Dataset, load_from_disk
from geniusrise import BatchInput, BatchOutput, State
from pyarrow import feather

from geniusrise.inference.text.base import TextBulk


class NLIBulk(TextBulk):
    r"""
    The NLIBulk class provides functionality for large-scale natural language inference (NLI) processing using Hugging Face
    transformers. It allows users to load datasets, configure models, and perform inference on batches of premise-hypothesis pairs.

    Attributes:
        input (BatchInput): Configuration and data inputs for the batch process.
        output (BatchOutput): Configurations for output data handling.
        state (State): State management for the inference task.

    Example CLI Usage:
    ```bash
    genius NLIBulk rise \
        batch \
            --input_s3_bucket geniusrise-test \
            --input_s3_folder input/nli \
        batch \
            --output_s3_bucket geniusrise-test \
            --output_s3_folder output/nli \
        postgres \
            --postgres_host 127.0.0.1 \
            --postgres_port 5432 \
            --postgres_user postgres \
            --postgres_password postgres \
            --postgres_database geniusrise\
            --postgres_table state \
        --id MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7-lol \
        infer \
            --args \
                model_name="MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7" \
                model_class="AutoModelForSequenceClassification" \
                tokenizer_class="AutoTokenizer" \
                use_cuda=True \
                precision="float" \
                quantization=0 \
                device_map="cuda:0" \
                max_memory=None \
                torchscript=False
    ```
    """

    def __init__(self, input: BatchInput, output: BatchOutput, state: State, **kwargs) -> None:
        """
        Initializes the NLIBulk class with the specified input, output, and state configurations.

        Args:
            input (BatchInput): The input data.
            output (BatchOutput): The output data.
            state (State): The state data.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(input, output, state, **kwargs)

    def load_dataset(self, dataset_path: str, max_length: int = 512, **kwargs) -> Optional[Dataset]:
        r"""
        Load a commonsense reasoning dataset from a directory.

        Args:
            dataset_path (str): The path to the dataset directory or file.
            max_length (int, optional): Maximum length of text sequences for tokenization purposes. Defaults to 512.
            **kwargs: Additional keyword arguments.

        Returns:
            Dataset: The loaded dataset.

        Raises:
            Exception: If there was an error loading the dataset.

        ## Supported Data Formats and Structures:

        ### Hugging Face Dataset
        Dataset files saved by the Hugging Face datasets library.

        ### JSONL
        Each line is a JSON object representing an example.
        ```json
        {"premise": "The premise text", "hypothesis": "The hypothesis text"}
        ```

        ### CSV
        Should contain 'premise' and 'hypothesis' columns.
        ```csv
        premise,hypothesis
        "The premise text","The hypothesis text"
        ```

        ### Parquet
        Should contain 'premise' and 'hypothesis' columns.

        ### JSON
        An array of dictionaries with 'premise' and 'hypothesis' keys.
        ```json
        [{"premise": "The premise text", "hypothesis": "The hypothesis text"}]
        ```

        ### XML
        Each 'record' element should contain 'premise' and 'hypothesis' child elements.
        ```xml
        <record>
            <premise>The premise text</premise>
            <hypothesis>The hypothesis text</hypothesis>
        </record>
        ```

        ### YAML
        Each document should be a dictionary with 'premise' and 'hypothesis' keys.
        ```yaml
        - premise: "The premise text"
          hypothesis: "The hypothesis text"
        ```

        ### TSV
        Should contain 'premise' and 'hypothesis' columns separated by tabs.

        ### Excel (.xls, .xlsx)
        Should contain 'premise' and 'hypothesis' columns.

        ### SQLite (.db)
        Should contain a table with 'premise' and 'hypothesis' columns.

        ### Feather
        Should contain 'premise' and 'hypothesis' columns.
        """
        self.max_length = max_length

        self.log.info(f"Loading dataset from {dataset_path}")
        try:
            if os.path.isfile(os.path.join(dataset_path, "dataset_info.json")):
                dataset = load_from_disk(dataset_path)
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
                            premise = record.find("premise").text  # type: ignore
                            hypothesis = record.find("hypothesis").text  # type: ignore
                            data.append({"premise": premise, "hypothesis": hypothesis})

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
                        query = "SELECT premise, hypothesis FROM dataset_table;"
                        df = pd.read_sql_query(query, conn)
                        data.extend(df.to_dict("records"))

                    elif filename.endswith(".feather"):
                        df = feather.read_feather(filepath)
                        data.extend(df.to_dict("records"))

            return Dataset.from_pandas(pd.DataFrame(data))

        except Exception as e:
            self.log.exception(f"Error occurred when loading dataset from {dataset_path}. Error: {e}")
            raise

    def infer(
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
        Performs NLI inference on a loaded dataset using the specified model. The method processes the data in batches and saves
        the results to the configured output path.

        Args:
            model_name (str): Name or path of the NLI model.
            max_length (int, optional): Maximum length of the sequences for tokenization purposes. Defaults to 512.
            model_class (str, optional): Class name of the model (e.g., "AutoModelForSequenceClassification"). Defaults to "AutoModelForSeq2SeqLM".
            tokenizer_class (str, optional): Class name of the tokenizer (e.g., "AutoTokenizer"). Defaults to "AutoTokenizer".
            use_cuda (bool, optional): Whether to use CUDA for model inference. Defaults to False.
            precision (str, optional): Precision for model computation (e.g., "float16"). Defaults to "float16".
            quantization (int, optional): Level of quantization for optimizing model size and speed. Defaults to 0.
            device_map (str | Dict | None, optional): Specific device to use for computation. Defaults to "auto".
            max_memory (Dict, optional): Maximum memory configuration for devices. Defaults to {0: "24GB"}.
            torchscript (bool, optional): Whether to use a TorchScript-optimized version of the pre-trained language model. Defaults to False.
            compile (bool, optional): Whether to compile the model before fine-tuning. Defaults to True.
            awq_enabled (bool, optional): Whether to enable AWQ optimization. Defaults to False.
            flash_attention (bool, optional): Whether to use flash attention optimization. Defaults to False.
            batch_size (int, optional): Number of premise-hypothesis pairs to process simultaneously. Defaults to 32.
            **kwargs: Arbitrary keyword arguments for model and generation configurations.
        ```
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

        predictions = []
        for i in range(0, len(dataset), batch_size):
            batch = dataset[i : i + batch_size]

            inputs = self.tokenizer(
                batch["premise"],
                batch["hypothesis"],
                padding=True,
                return_tensors="pt",
            )
            if next(self.model.parameters()).is_cuda:
                inputs = {k: v.cuda() for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits if hasattr(outputs, "logits") else outputs[0]
                if next(self.model.parameters()).is_cuda:
                    logits = logits.cpu()
                softmax = torch.nn.functional.softmax(logits, dim=-1)
                scores = softmax.numpy().tolist()

                for score in scores:
                    label_scores = {
                        self.model.config.id2label[label_id]: score for label_id, score in enumerate(scores[0])
                    }
                    predictions.append(label_scores)

        # Save results
        self.log.info(f"Saving results to {output_path}")
        os.makedirs(output_path, exist_ok=True)
        output_file = os.path.join(output_path, f"nli_results_{uuid.uuid4().hex}.jsonl")
        with open(output_file, "w") as f:
            for data, pred in zip(dataset, predictions):
                result = {
                    "premise": data["premise"],
                    "hypothesis": data["hypothesis"],
                    "prediction": pred,
                }
                f.write(json.dumps(result) + "\n")

        self.done()
        self.log.info("Inference completed.")
