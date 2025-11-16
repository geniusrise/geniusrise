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
from geniusrise.core import BatchInput, BatchOutput, InMemoryState

from geniusrise.inference.audio import TextToSpeechBulk


@pytest.fixture(scope="module")
def text_to_speech_bulk():
    input_dir = "./assets"
    output_dir = "./output_dir"

    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    input = BatchInput(input_dir, "geniusrise-test-bucket", "t2s-inputs")
    output = BatchOutput(output_dir, "geniusrise-test-bucket", "t2s-outputs")
    state = InMemoryState(1)

    text_to_speech_bulk = TextToSpeechBulk(
        input=input,
        output=output,
        state=state,
    )
    yield text_to_speech_bulk


@pytest.mark.parametrize(
    "model_name, model_class, processor_class, use_cuda, precision, quantization, device_map, torchscript, compile, batch_size, notification_email, max_length, output_type, voice_preset, model_sampling_rate, generation_tgt_lang",
    [
        # fmt: off
        ("facebook/mms-tts-hin", "VitsModel", "VitsTokenizer", True, "float32", 0, "cuda:0", False, False, 8, "russi@geniusrise.ai", 512, "mp3", None, 16000, None),
        ("facebook/seamless-m4t-v2-large", "SeamlessM4Tv2ForTextToSpeech", "AutoProcessor", True, "float32", 0, "cuda:0", False, False, 8, "russi@geniusrise.ai", 512, "mp3", 0, 16000, "eng"),
        ("microsoft/speecht5_tts", "SpeechT5ForTextToSpeech", "SpeechT5Processor", True, "float32", 0, "cuda:0", False, False, 8, "russi@geniusrise.ai", 512, "mp3", 7306, 16000, None),
        ("suno/bark", "BarkModel", "BarkProcessor", True, "float32", 0, "cuda:0", False, False, 8, "russi@geniusrise.ai", 512, "mp3", "v2/en_speaker_6", 16000, None),
        # fmt: on
    ],
)
def test_synthesize_speech(
    text_to_speech_bulk,
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
    max_length,
    output_type,
    voice_preset,
    model_sampling_rate,
    generation_tgt_lang,
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
        "max_length": max_length,
        "output_type": output_type,
        "voice_preset": voice_preset,
        "model_sampling_rate": model_sampling_rate,
        "generation_tgt_lang": generation_tgt_lang,
    }
    if not generation_tgt_lang:
        del input_data["generation_tgt_lang"]

    # Call the synthesize_speech method
    text_to_speech_bulk.synthesize_speech(**input_data)

    # TODO: read the output files and verify contents
