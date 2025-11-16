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
import itertools
import json
import os
import sqlite3
import tempfile
import xml.etree.ElementTree as ET

import pandas as pd
import pytest
import torch
import yaml  # type: ignore
from datasets import Dataset
from geniusrise.core import BatchInput, BatchOutput
from pyarrow import feather
from pyarrow import parquet as pq

from geniusrise.inference.text.bulk.instruction import InstructionBulk


@pytest.fixture(
    params=[
        # model_name, model_class, tokenizer_class, use_cuda, precision, quantization, device_map, max_memory, torchscript
        # fmt: off
        ("gpt2", "AutoModelForCausalLM", "AutoTokenizer", True, "float16", 0, None, None, False),
        ("gpt2", "AutoModelForCausalLM", "AutoTokenizer", False, "float32", 0, None, None, False),
        ("bigscience/bloom-560m", "AutoModelForCausalLM", "AutoTokenizer", True, "bfloat16", 0, None, None, False),
        ("meta-llama/Llama-2-7b-hf", "AutoModelForCausalLM", "AutoTokenizer", True, "bfloat16", 4, None, None, False),
        ("mistralai/Mistral-7B-v0.1", "AutoModelForCausalLM", "AutoTokenizer", True, "bfloat16", 0, "cuda:0", None, False),
        ("mistralai/Mistral-7B-v0.1", "AutoModelForCausalLM", "AutoTokenizer", True, "bfloat16", 4, "cuda:0", None, False),
        ("mistralai/Mistral-7B-v0.1", "AutoModelForCausalLM", "AutoTokenizer", True, "bfloat16", 8, "cuda:0", None, False),
        ("mistralai/Mistral-7B-v0.1", "AutoModelForCausalLM", "AutoTokenizer", True, "bfloat16", 0, "auto", None, True),
        ("mistralai/Mistral-7B-v0.1", "AutoModelForCausalLM", "AutoTokenizer", True, "bfloat16", 4, "auto", None, True),
        ("mistralai/Mistral-7B-v0.1", "AutoModelForCausalLM", "AutoTokenizer", True, "bfloat16", 8, "auto", None, True),
        # mistral
        ("TheBloke/Mistral-7B-Instruct-v0.1-GPTQ:gptq-4bit-32g-actorder_True", "AutoModelForCausalLM", "AutoTokenizer", True, "bfloat16", None, "cuda:0", None, False),
        ("TheBloke/Mistral-7B-Instruct-v0.1-GPTQ:gptq-8bit-32g-actorder_True", "AutoModelForCausalLM", "AutoTokenizer", True, "bfloat16", None, "cuda:0", None, False),
        ("TheBloke/Mistral-7B-Code-16K-qlora-GPTQ:gptq-4bit-32g-actorder_True", "AutoModelForCausalLM", "AutoTokenizer", True, "bfloat16", None, "cuda:0", None, False),
        ("TheBloke/Mistral-7B-Phibrarian-32K-GPTQ", "AutoModelForCausalLM", "AutoTokenizer", True, "bfloat16", None, "cuda:0", None, False),
        # zephyr
        ("TheBloke/zephyr-7B-beta-GPTQ:gptq-4bit-32g-actorder_True", "AutoModelForCausalLM", "AutoTokenizer", True, "bfloat16", None, "cuda:0", None, False),
        ("TheBloke/zephyr-7B-beta-GPTQ:gptq-8bit-32g-actorder_True", "AutoModelForCausalLM", "AutoTokenizer", True, "bfloat16", None, "cuda:0", None, False),
        # falcon
        # ("TheBloke/falcon-7b-instruct-GPTQ", "AutoModelForCausalLM", "AutoTokenizer", True, "bfloat16", None, "auto", None, False),
        # llama-based
        ("TheBloke/Llama-2-7b-Chat-GPTQ:gptq-4bit-32g-actorder_True", "AutoModelForCausalLM", "AutoTokenizer", True, "float16", None, "cuda:0", None, False),
        ("TheBloke/Llama-2-7B-32K-Instruct-GPTQ:gptq-4bit-32g-actorder_True", "AutoModelForCausalLM", "AutoTokenizer", True, "float16", None, "cuda:0", None, False),
        ("TheBloke/WizardLM-7B-uncensored-GPTQ", "AutoModelForCausalLM", "AutoTokenizer", True, "bfloat16", None, "cuda:0", None, False),
        ("TheBloke/vicuna-7B-v1.5-GPTQ:gptq-4bit-32g-actorder_True", "AutoModelForCausalLM", "AutoTokenizer", True, "bfloat16", None, "cuda:0", None, False),
        ("TheBloke/Wizard-Vicuna-7B-Uncensored-GPTQ", "AutoModelForCausalLM", "AutoTokenizer", True, "bfloat16", None, "cuda:0", None, False),
        ("TheBloke/Yarn-Llama-2-7B-64K-GPTQ:gptq-4bit-32g-actorder_True", "AutoModelForCausalLM", "AutoTokenizer", True, "float16", None, "cuda:0", None, False),
        ("TheBloke/Yarn-Llama-2-7B-128K-GPTQ:gptq-4bit-32g-actorder_True", "AutoModelForCausalLM", "AutoTokenizer", True, "float16", None, "cuda:0", None, False),
        # fmt: on
    ]
)
def model_config(request):
    return request.param


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


# Fixtures for each file type
@pytest.fixture(
    params=[
        "huggingface",
        "csv",
        "jsonl",
        "parquet",
        "json",
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
    create_dataset_in_format(tmpdir, ext)
    return tmpdir, ext


# Fixtures to initialize InstructionBulk instance
@pytest.fixture
def chatbot():
    input_dir = tempfile.mkdtemp()
    output_dir = tempfile.mkdtemp()

    input = BatchInput(input_dir, "geniusrise-test", "api_input")
    output = BatchOutput(output_dir, "geniusrise-test", "api_output")
    state = None

    chatbot = InstructionBulk(
        input=input,
        output=output,
        state=state,
    )
    yield chatbot


# Define strategies and associated parameters
strategies = {
    "generate": {},
    "greedy_search": {},
    "beam_search": {"num_beams": 4},
    "beam_sample": {"num_beams": 4, "temperature": 0.7, "top_k": 20},
    "group_beam_search": {"num_beams": 4, "num_beam_groups": 2},
}

# Define other parameters
length_params = {
    "max_length": [20, 30],
    "min_length": [0, 10],
    "early_stopping": [False, True],
}
gen_strategy_params = {
    "do_sample": [False, True],
}
logit_params = {
    "temperature": [1.0, 0.7],
    "top_k": [50, 20],
    "top_p": [1.0, 0.9],
    "repetition_penalty": [1.0, 1.5],
    "length_penalty": [1.0, 0.5],
    "no_repeat_ngram_size": [0, 2],
}
# Merge all the parameters into one dictionary for itertools.product
all_params = {**length_params, **gen_strategy_params, **logit_params}


@pytest.mark.parametrize("strategy", list(strategies.keys()))
def test_generate_strategies(chatbot, model_config, dataset_file, strategy):
    (
        model_name,
        model_class,
        tokenizer_class,
        use_cuda,
        precision,
        quantization,
        device_map,
        max_memory,
        torchscript,
    ) = model_config

    tmpdir, ext = dataset_file
    chatbot.input.input_folder = tmpdir

    if ":" in model_name:
        _model_name = model_name
        model_revision = _model_name.split(":")[1]
        model_name = _model_name.split(":")[0]
        tokenizer_revision = _model_name.split(":")[1]
        tokenizer_name = _model_name.split(":")[0]
    else:
        model_revision = None
        tokenizer_revision = None

    # Strategy-specific params
    strategy_params = strategies[strategy]

    # All possible combinations for the current strategy
    param_combinations = [
        {**dict(zip(all_params.keys(), values)), **strategy_params}
        for values in itertools.product(*all_params.values())
    ]

    if strategy != "generate" and (
        "32k" in model_name.lower() or "64k" in model_name.lower() or "128k" in model_name.lower()
    ):
        return

    for param_set in param_combinations:
        param_set = {f"generation_{k}": v for k, v in param_set.items()}

        generated_text = chatbot.perform(
            model_name=model_name,
            model_revision=model_revision,
            tokenizer_name=model_name,
            tokenizer_revision=tokenizer_revision,
            model_class=model_class,
            tokenizer_class=tokenizer_class,
            use_cuda=use_cuda,
            precision=precision,
            quantization=quantization,
            device_map=device_map,
            max_memory=max_memory,
            torchscript=torchscript,
            decoding_strategy=strategy,
            model_trust_remote_code=True,
            **param_set,  # Unpack params into function arguments
        )
        files = glob.glob(f"{chatbot.output.output_folder}/completions-*.json")
        assert len(files) > 0
        break

    # Cleanup
    del chatbot.model
    del chatbot.tokenizer
    torch.cuda.empty_cache()
