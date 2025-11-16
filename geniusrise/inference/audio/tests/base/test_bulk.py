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
from geniusrise.core import BatchInput, BatchOutput, InMemoryState

from geniusrise.inference.audio import AudioBulk


@pytest.fixture(scope="module")
def audio_bulk():
    input_dir = "./input_dir"
    output_dir = "./output_dir"

    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    input = BatchInput(input_dir, "geniusrise-test-bucket", "api_input")
    output = BatchOutput(output_dir, "geniusrise-test-bucket", "api_output")
    state = InMemoryState(1)

    audio_bulk = AudioBulk(
        input=input,
        output=output,
        state=state,
    )
    yield audio_bulk


@pytest.mark.parametrize(
    "model_name, processor_name, model_class, processor_class, use_cuda, precision, quantization, device_map, max_memory, torchscript, compile, flash_attention, better_transformers, use_whisper_cpp, use_faster_whisper",
    [
        # fmt: off
        ("facebook/wav2vec2-base-960h", "facebook/wav2vec2-base-960h", "Wav2Vec2ForCTC", "Wav2Vec2Processor", True, "float32", 0, "cuda:0", None, False, False, False, False, False, False),
        ("facebook/wav2vec2-base-960h", "facebook/wav2vec2-base-960h", "Wav2Vec2ForCTC", "Wav2Vec2Processor", False, "float32", 0, None, None, False, False, False, False, False, False),
        ("openai/whisper-small", "openai/whisper-small", "WhisperForConditionalGeneration", "AutoProcessor", False, "float32", 4, None, None, False, False, False, False, False, False),
        ("openai/whisper-medium", "openai/whisper-medium", "WhisperForConditionalGeneration", "AutoProcessor", True, "float16", 0, "cuda:0", None, False, True, False, False, False, False),
        ("openai/whisper-large-v2", "openai/whisper-large-v2", "WhisperForConditionalGeneration", "AutoProcessor", True, "bfloat16", 0, "cuda:0", None, False, False, True, False, False, False),
        ("openai/whisper-large-v2", "openai/whisper-large-v2", "WhisperForConditionalGeneration", "AutoProcessor", True, "bfloat16", 0, "cuda:0", None, False, False, False, True, False, False),
        ("large", "large", "WhisperForConditionalGeneration", "AutoProcessor", True, "bfloat16", 0, "cuda:0", None, False, False, False, False, False, True),
        # fmt: on
    ],
)
def test_load_models(
    audio_bulk,
    model_name,
    processor_name,
    model_class,
    processor_class,
    use_cuda,
    precision,
    quantization,
    device_map,
    max_memory,
    torchscript,
    compile,
    flash_attention,
    better_transformers,
    use_whisper_cpp,
    use_faster_whisper,
):
    model, processor = audio_bulk.load_models(
        model_name=model_name,
        processor_name=processor_name,
        model_class=model_class,
        processor_class=processor_class,
        use_cuda=use_cuda,
        precision=precision,
        quantization=quantization,
        device_map=device_map,
        max_memory=max_memory,
        torchscript=torchscript,
        compile=compile,
        flash_attention=flash_attention,
        better_transformers=better_transformers,
        use_whisper_cpp=use_whisper_cpp,
        use_faster_whisper=use_faster_whisper,
    )
    assert model is not None
    if not use_whisper_cpp and not use_faster_whisper:
        assert processor is not None
        assert len(list(model.named_modules())) > 0
    else:
        assert processor is None

    del model
    del processor
    torch.cuda.empty_cache()
