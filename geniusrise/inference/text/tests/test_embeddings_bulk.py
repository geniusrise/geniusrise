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
import xml.etree.ElementTree as ET

import pandas as pd
import pytest
import yaml  # type: ignore
from datasets import Dataset
from geniusrise.core import BatchInput, BatchOutput, InMemoryState
from pyarrow import feather
from pyarrow import parquet as pq

from geniusrise.inference.text.bulk.embeddings import EmbeddingsBulk


# Helper function to create synthetic data in different formats
def create_dataset_in_format(directory, ext):
    os.makedirs(directory, exist_ok=True)
    data = [{"text": f"text_{i}"} for i in range(10)]
    df = pd.DataFrame(data)

    if ext == "huggingface":
        dataset = Dataset.from_pandas(df)
        dataset.save_to_disk(directory)
    elif ext == "csv":
        df.to_csv(os.path.join(directory, "data.csv"), index=False)
    elif ext == "jsonl":
        with open(os.path.join(directory, "data.jsonl"), "w") as f:
            for item in data:
                f.write(json.dumps(item) + "\n")
    elif ext == "parquet":
        pq.write_table(feather.Table.from_pandas(df), os.path.join(directory, "data.parquet"))
    elif ext == "json":
        with open(os.path.join(directory, "data.json"), "w") as f:
            json.dump(data, f)
    elif ext == "xml":
        root = ET.Element("root")
        for item in data:
            record = ET.SubElement(root, "record")
            ET.SubElement(record, "text").text = item["text"]
        tree = ET.ElementTree(root)
        tree.write(os.path.join(directory, "data.xml"))
    elif ext == "yaml":
        with open(os.path.join(directory, "data.yaml"), "w") as f:
            yaml.dump(data, f)
    elif ext == "tsv":
        df.to_csv(os.path.join(directory, "data.tsv"), index=False, sep="\t")
    elif ext == "xlsx":
        df.to_excel(os.path.join(directory, "data.xlsx"), index=False)
    elif ext == "db":
        conn = sqlite3.connect(os.path.join(directory, "data.db"))
        df.to_sql("dataset_table", conn, if_exists="replace", index=False)
        conn.close()
    elif ext == "feather":
        feather.write_feather(df, os.path.join(directory, "data.feather"))

    return directory


# Fixtures for each file type
@pytest.fixture(
    params=[
        "csv",
        "json",
        "jsonl",
        "parquet",
        "xml",
        "yaml",
        "tsv",
        "xlsx",
        "db",
        "feather",
    ]
)
def dataset_file(request, tmpdir):
    ext = request.param
    directory = create_dataset_in_format(f"{tmpdir}/input", ext)
    return directory, ext


@pytest.fixture
def embeddings_bulk_bolt(tmpdir):
    input_dir = f"{tmpdir}/input"
    output_dir = f"{tmpdir}/output"
    os.makedirs(input_dir)
    os.makedirs(output_dir)
    input = BatchInput(input_dir, "geniusrise-test", "test-🤗-input")
    output = BatchOutput(output_dir, "geniusrise-test", "test-🤗-output")
    state = InMemoryState()
    bolt = EmbeddingsBulk(
        input=input,
        output=output,
        state=state,
    )
    return bolt


def test_generate_sentence_transformer_embeddings(embeddings_bulk_bolt, dataset_file):
    directory, ext = dataset_file
    embeddings_bulk_bolt.generate(
        kind="sentence",
        model_name="sentence-transformers/paraphrase-MiniLM-L6-v2",
        use_cuda=False,
    )
    files = glob.glob(f"{embeddings_bulk_bolt.output.output_folder}/embeddings-*.json")
    assert len(files) > 0


def test_generate_huggingface_embeddings(embeddings_bulk_bolt, dataset_file):
    directory, ext = dataset_file
    for kind in ["sentence_windows", "sentence_combinations", "sentence_permutations"]:
        embeddings_bulk_bolt.generate(kind=kind, model_name="bert-base-uncased", use_cuda=True, device_map="cuda:0")
        files = glob.glob(f"{embeddings_bulk_bolt.output.output_folder}/embeddings-*.json")
        assert len(files) > 0
