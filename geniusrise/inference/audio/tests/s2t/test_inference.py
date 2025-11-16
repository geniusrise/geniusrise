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

import io
import os

import numpy as np
import pytest
from geniusrise.core import BatchInput, BatchOutput

from geniusrise.inference.audio.s2t.inference import SpeechToTextInference


@pytest.fixture(scope="module")
def s2t_inference():
    input_dir = "./tests/input_dir"
    output_dir = "./tests/output_dir"

    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    input = BatchInput(input_dir, "geniusrise-test-bucket", "api_input")
    output = BatchOutput(output_dir, "geniusrise-test-bucket", "api_output")
    state = None

    s2t_inference = SpeechToTextInference(
        input=input,
        output=output,
        state=state,
    )
    yield s2t_inference

    # Clean up the test directories
    os.rmdir(input_dir)
    os.rmdir(output_dir)


@pytest.mark.parametrize(
    "model_name, model_class, processor_class, use_cuda, precision, quantization, device_map, torchscript, compile, use_whisper_cpp, use_faster_whisper",
    [
        # fmt: off
        ("small", "WhisperForConditionalGeneration", "AutoProcessor", True, "float32", 0, "cuda:0", False, False, False, True),
        ("medium", "WhisperForConditionalGeneration", "AutoProcessor", True, "float16", 0, "cuda:0", False, False, False, True),
        ("large", "WhisperForConditionalGeneration", "AutoProcessor", True, "bfloat16", 0, "cuda:0", False, False, False, True),
        # fmt: on
    ],
)
def test_process_faster_whisper(
    s2t_inference,
    model_name,
    model_class,
    processor_class,
    use_cuda,
    precision,
    quantization,
    device_map,
    torchscript,
    compile,
    use_whisper_cpp,
    use_faster_whisper,
):
    s2t_inference.load_models(
        model_name=model_name,
        model_class=model_class,
        processor_class=processor_class,
        use_cuda=use_cuda,
        precision=precision,
        quantization=quantization,
        device_map=device_map,
        torchscript=torchscript,
        compile=compile,
        use_whisper_cpp=use_whisper_cpp,
        use_faster_whisper=use_faster_whisper,
    )

    audio_input = io.BytesIO(open("./assets/sample.mp3", "b").read())
    result = s2t_inference.process_faster_whisper(
        audio_input=audio_input.getvalue(),
        model_sampling_rate=16000,
        chunk_size=0,
        generate_args={},
    )

    assert isinstance(result["transcriptions"], list)
    assert isinstance(result["transcription_info"], dict)


@pytest.mark.parametrize(
    "model_name, model_class, processor_class, use_cuda, precision, quantization, device_map, torchscript, compile",
    [
        # fmt: off
        ("openai/whisper-small", "WhisperForConditionalGeneration", "AutoProcessor", True, "float32", 0, "cuda:0", False, False),
        ("openai/whisper-medium", "WhisperForConditionalGeneration", "AutoProcessor", True, "float16", 0, "cuda:0", False, True),
        # fmt: on
    ],
)
def test_process_whisper(
    s2t_inference,
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
    s2t_inference.load_models(
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

    audio_input = io.BytesIO(open("./assets/sample.mp3", "b").read())
    result = s2t_inference.process_whisper(
        audio_input=audio_input.getvalue(),
        model_sampling_rate=16000,
        processor_args={},
        chunk_size=0,
        overlap_size=0,
        generate_args={},
    )

    assert isinstance(result["transcription"], str)
    assert isinstance(result["segments"], list)


@pytest.mark.parametrize(
    "model_name, model_class, processor_class, use_cuda, precision, quantization, device_map, torchscript, compile",
    [
        # fmt: off
        ("facebook/wav2vec2-base-960h", "Wav2Vec2ForCTC", "Wav2Vec2Processor", True, "float32", 0, "cuda:0", False, False),
        ("facebook/wav2vec2-large-960h-lv60-self", "Wav2Vec2ForCTC", "Wav2Vec2Processor", True, "float16", 0, "cuda:0", False, True),
        # fmt: on
    ],
)
def test_process_wav2vec2(
    s2t_inference,
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
    s2t_inference.load_models(
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

    audio_input = np.random.rand(16000)
    result = s2t_inference.process_wav2vec2(
        audio_input=audio_input,
        model_sampling_rate=16000,
        processor_args={},
        chunk_size=0,
        overlap_size=0,
    )

    assert isinstance(result["transcription"], str)
    assert isinstance(result["segments"], list)


@pytest.mark.parametrize(
    "model_name, model_class, processor_class, use_cuda, precision, quantization, device_map, torchscript, compile",
    [
        # fmt: off
        ("facebook/s2t-small-librispeech-asr", "AutoModelForSeq2SeqLM", "AutoProcessor", True, "float32", 0, "cuda:0", False, False),
        ("facebook/s2t-medium-librispeech-asr", "AutoModelForSeq2SeqLM", "AutoProcessor", True, "float16", 0, "cuda:0", False, True),
        # fmt: on
    ],
)
def test_process_seamless(
    s2t_inference,
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
    s2t_inference.load_models(
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

    audio_input = np.random.rand(16000)
    result = s2t_inference.process_seamless(
        audio_input=audio_input,
        model_sampling_rate=16000,
        processor_args={},
        chunk_size=0,
        overlap_size=0,
        generate_args={},
    )

    assert isinstance(result["transcription"], str)
    assert isinstance(result["segments"], list)
