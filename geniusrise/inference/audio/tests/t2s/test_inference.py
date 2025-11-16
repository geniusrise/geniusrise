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

import numpy as np
import pytest
from geniusrise.core import BatchInput, BatchOutput

from geniusrise.inference.audio.t2s.inference import TextToSpeechInference


@pytest.fixture(scope="module")
def t2s_inference():
    input_dir = "./tests/input_dir"
    output_dir = "./tests/output_dir"

    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    input = BatchInput(input_dir, "geniusrise-test-bucket", "api_input")
    output = BatchOutput(output_dir, "geniusrise-test-bucket", "api_output")
    state = None

    t2s_inference = TextToSpeechInference(
        input=input,
        output=output,
        state=state,
    )
    yield t2s_inference

    # Clean up the test directories
    os.rmdir(input_dir)
    os.rmdir(output_dir)


@pytest.mark.parametrize(
    "model_name, model_class, processor_class, use_cuda, precision, quantization, device_map, torchscript, compile",
    [
        # fmt: off
        ("facebook/mms-tts-eng", "VitsModel", "VitsTokenizer", True, "float32", 0, "cuda:0", False, False),
        ("facebook/mms-tts-multilingual", "VitsModel", "VitsTokenizer", True, "float16", 0, "cuda:0", False, True),
        # fmt: on
    ],
)
def test_process_mms(
    t2s_inference,
    model_name,
    model_class,
    processor_class,
    use_cuda,
    precision,
    quantization,
    device_map,
    torchscript,
    compile,
):
    t2s_inference.load_models(
        model_name=model_name,
        model_class=model_class,
        processor_class=processor_class,
        use_cuda=use_cuda,
        precision=precision,
        quantization=quantization,
        device_map=device_map,
        torchscript=torchscript,
        compile=compile,
    )

    text_input = "This is a test."
    result = t2s_inference.process_mms(text_input=text_input, generate_args={})

    assert isinstance(result, np.ndarray)
    assert len(result) > 0


@pytest.mark.parametrize(
    "model_name, model_class, processor_class, use_cuda, precision, quantization, device_map, torchscript, compile",
    [
        # fmt: off
        ("suno/bark", "BarkModel", "BarkProcessor", True, "float32", 0, "cuda:0", False, False),
        # fmt: on
    ],
)
def test_process_bark(
    t2s_inference,
    model_name,
    model_class,
    processor_class,
    use_cuda,
    precision,
    quantization,
    device_map,
    torchscript,
    compile,
):
    t2s_inference.load_models(
        model_name=model_name,
        model_class=model_class,
        processor_class=processor_class,
        use_cuda=use_cuda,
        precision=precision,
        quantization=quantization,
        device_map=device_map,
        torchscript=torchscript,
        compile=compile,
    )

    text_input = "This is a test."
    voice_preset = "0"
    result = t2s_inference.process_bark(text_input=text_input, voice_preset=voice_preset, generate_args={})

    assert isinstance(result, np.ndarray)
    assert len(result) > 0


@pytest.mark.parametrize(
    "model_name, model_class, processor_class, use_cuda, precision, quantization, device_map, torchscript, compile",
    [
        # fmt: off
        ("microsoft/speecht5_tts", "SpeechT5ForTextToSpeech", "SpeechT5Processor", True, "float32", 0, "cuda:0", False, False),
        # fmt: on
    ],
)
def test_process_speecht5_tts(
    t2s_inference,
    model_name,
    model_class,
    processor_class,
    use_cuda,
    precision,
    quantization,
    device_map,
    torchscript,
    compile,
):
    t2s_inference.load_models(
        model_name=model_name,
        model_class=model_class,
        processor_class=processor_class,
        use_cuda=use_cuda,
        precision=precision,
        quantization=quantization,
        device_map=device_map,
        torchscript=torchscript,
        compile=compile,
    )

    text_input = "This is a test."
    voice_preset = "0"
    result = t2s_inference.process_speecht5_tts(text_input=text_input, voice_preset=voice_preset, generate_args={})

    assert isinstance(result, np.ndarray)
    assert len(result) > 0


@pytest.mark.parametrize(
    "model_name, model_class, processor_class, use_cuda, precision, quantization, device_map, torchscript, compile",
    [
        # fmt: off
        ("facebook/seamless-m4t-v2-large", "SeamlessM4Tv2ForTextToSpeech", "AutoProcessor", True, "float32", 0, "cuda:0", False, False),
        # fmt: on
    ],
)
def test_process_seamless(
    t2s_inference,
    model_name,
    model_class,
    processor_class,
    use_cuda,
    precision,
    quantization,
    device_map,
    torchscript,
    compile,
):
    t2s_inference.load_models(
        model_name=model_name,
        model_class=model_class,
        processor_class=processor_class,
        use_cuda=use_cuda,
        precision=precision,
        quantization=quantization,
        device_map=device_map,
        torchscript=torchscript,
        compile=compile,
    )

    text_input = "This is a test."
    voice_preset = "0"
    result = t2s_inference.process_seamless(text_input=text_input, voice_preset=voice_preset, generate_args={})

    assert isinstance(result, np.ndarray)
    assert len(result) > 0
