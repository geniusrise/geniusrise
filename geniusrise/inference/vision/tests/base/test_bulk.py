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

import os

import pytest
import torch

# import transformers
from geniusrise.core import BatchInput, BatchOutput, InMemoryState

from geniusrise.inference.vision.bulk import VisionBulk


@pytest.fixture(
    params=[
        # model_name, model_class, processor_class, device_map, max_memory, torchscript
        # fmt: off
        ("google/vit-base-patch16-224", "AutoModel", "AutoProcessor", None, None, False),
        ("google/vit-base-patch16-224", "AutoModel", "AutoProcessor", None, None, False),
        ("nateraw/vit-age-classifier", "AutoModel", "AutoProcessor", None, None, False),
        ("microsoft/resnet-50", "AutoModel", "AutoProcessor", None, None, False),
        ("nateraw/food", "AutoModel", "AutoProcessor", "auto", None, False),
        ("nateraw/food", "AutoModel", "AutoProcessor", "auto", None, True),
        ("google/vit-base-patch16-384", "AutoModel", "AutoProcessor", "auto", None, False),
        # fmt: on
    ]
)
def model_config(request):
    return request.param


# Fixtures to initialize VisionAPI instance
@pytest.fixture
def hfa():
    input_dir = "./input_dir"
    output_dir = "./output_dir"

    input = BatchInput(input_dir, "geniusrise-test", "api_input")
    output = BatchOutput(output_dir, "geniusrise-test", "api_output")
    state = InMemoryState()

    hfa = VisionBulk(
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
        processor_class,
        device_map,
        max_memory,
        torchscript,
    ) = model_config

    if ":" in model_name:
        _model_name = model_name
        model_revision = _model_name.split(":")[1]
        model_name = _model_name.split(":")[0]
        processor_revision = _model_name.split(":")[1]
        processor_name = _model_name.split(":")[0]
    else:
        model_revision = None
        processor_revision = None

    model, processor = hfa.load_models(
        model_name=model_name,
        model_revision=model_revision,
        processor_name=model_name,
        processor_revision=processor_revision,
        model_class=model_class,
        processor_class=processor_class,
        device_map=device_map,
        max_memory=max_memory,
        torchscript=torchscript,
    )
    assert model is not None
    assert processor is not None
    assert len(list(model.named_modules())) > 0

    del model
    del processor
    torch.cuda.empty_cache()
