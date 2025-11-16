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
from geniusrise.core import BatchInput, BatchOutput

from geniusrise.inference.audio import SpeechToTextBulk


@pytest.fixture(scope="module")
def speech_to_text_bulk():
    input_dir = "./assets"
    output_dir = "./output_dir"

    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    input = BatchInput(input_dir, "geniusrise-test-bucket", "api_input")
    output = BatchOutput(output_dir, "geniusrise-test-bucket", "api_output")
    state = None

    speech_to_text_bulk = SpeechToTextBulk(
        input=input,
        output=output,
        state=state,
    )
    yield speech_to_text_bulk


@pytest.mark.parametrize(
    "model_name, model_class, processor_class, use_cuda, precision, quantization, device_map, torchscript, compile, batch_size, notification_email, model_sampling_rate, chunk_size, overlap_size, generation_tgt_lang, use_whisper_cpp, use_faster_whisper",
    [
        # fmt: off
        ("facebook/seamless-m4t-v2-large", "SeamlessM4Tv2ForSpeechToText", "AutoProcessor", True, "float32", 0, "cuda:0", False, False, 8, "russi@geniusrise.ai", 16_000, 16000, 1600, "eng", False, False),
        ("facebook/wav2vec2-large-960h-lv60-self", "Wav2Vec2ForCTC", "Wav2Vec2Processor", True, "float32", 0, "cuda:0", False, True, 8, "russi@geniusrise.ai", 16_000, 16000, 1600, None, False, False),
        ("openai/whisper-large-v3", "WhisperForConditionalGeneration", "AutoProcessor", True, "float32", 0, "cuda:0", False, False, 8, "russi@geniusrise.ai", 16_000, 0, 0, None, False, False),
        ("large-v3", None, None, None, "float32", 0, "cuda:0", None, None, None, None, None, None, None, None, False, True),
        ("large", None, None, None, None, None, None, None, None, None, None, None, None, None, None, True, False),
        # fmt: on
    ],
)
def test_transcribe(
    speech_to_text_bulk,
    model_name,
    model_class,
    processor_class,
    use_cuda,
    precision,
    quantization,
    device_map,
    torchscript,
    compile,
    batch_size,
    notification_email,
    model_sampling_rate,
    chunk_size,
    overlap_size,
    generation_tgt_lang,
    use_whisper_cpp,
    use_faster_whisper,
):
    # Prepare the input data
    input_data = {
        "model_name": model_name,
        "model_class": model_class,
        "processor_class": processor_class,
        "use_cuda": use_cuda,
        "precision": precision,
        "quantization": quantization,
        "device_map": device_map,
        "torchscript": torchscript,
        "compile": compile,
        "batch_size": batch_size,
        "notification_email": notification_email,
        "model_sampling_rate": model_sampling_rate,
        "chunk_size": chunk_size,
        "overlap_size": overlap_size,
        "generation_tgt_lang": generation_tgt_lang,
        "use_whisper_cpp": use_whisper_cpp,
        "use_faster_whisper": use_faster_whisper,
    }

    # Call the transcribe method
    speech_to_text_bulk.transcribe(**input_data)

    # TODO: read the output files and verify contents
