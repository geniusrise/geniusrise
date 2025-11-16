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

import itertools
import os

import pytest
import torch

# import transformers
from geniusrise.core import BatchInput, BatchOutput

from geniusrise.inference.text.base import TextBulk


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
        ("TheBloke/Mistral-7B-v0.1-GPTQ:gptq-4bit-32g-actorder_True", "AutoModelForCausalLM", "AutoTokenizer", True, "float16", None, "cuda:0", None, False),
        # fmt: on
    ]
)
def model_config(request):
    return request.param


# Fixtures to initialize TextBulk instance
@pytest.fixture
def hfa():
    input_dir = "./input_dir"
    output_dir = "./output_dir"

    input = BatchInput(input_dir, "geniusrise-test", "api_input")
    output = BatchOutput(output_dir, "geniusrise-test", "api_output")
    state = None

    hfa = TextBulk(
        input=input,
        output=output,
        state=state,
    )
    yield hfa  # provide the fixture value

    # cleanup
    if os.path.exists(input_dir):
        os.rmdir(input_dir)
    if os.path.exists(output_dir):
        os.rmdir(output_dir)


def test_load_models(hfa, model_config):
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

    if ":" in model_name:
        _model_name = model_name
        model_revision = _model_name.split(":")[1]
        model_name = _model_name.split(":")[0]
        tokenizer_revision = _model_name.split(":")[1]
        tokenizer_name = _model_name.split(":")[0]
    else:
        model_revision = None
        tokenizer_revision = None

    model, tokenizer = hfa.load_models(
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
    )
    assert model is not None
    assert tokenizer is not None
    assert len(list(model.named_modules())) > 0

    del model
    del tokenizer
    torch.cuda.empty_cache()


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
def test_generate_strategies(hfa, model_config, strategy):
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

    if ":" in model_name:
        _model_name = model_name
        model_revision = _model_name.split(":")[1]
        model_name = _model_name.split(":")[0]
        tokenizer_revision = _model_name.split(":")[1]
        tokenizer_name = _model_name.split(":")[0]
    else:
        model_revision = None
        tokenizer_revision = None

    model, tokenizer = hfa.load_models(
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
    )
    hfa.model = model
    hfa.tokenizer = tokenizer

    # Strategy-specific params
    strategy_params = strategies[strategy]

    # All possible combinations for the current strategy
    param_combinations = [
        {**dict(zip(all_params.keys(), values)), **strategy_params}
        for values in itertools.product(*all_params.values())
    ]

    for param_set in param_combinations:
        generated_text = hfa.generate(
            prompt="Once upon a time", decoding_strategy=strategy, **param_set  # Unpack params into function arguments
        )
        assert generated_text is not None
        assert isinstance(generated_text, str)
        break

    # Cleanup
    del model
    del tokenizer
    torch.cuda.empty_cache()
