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

import base64
import os
import tempfile
import time

import pytest
import requests  # type: ignore
from geniusrise.core import BatchInput, BatchOutput

from geniusrise.inference.audio import SpeechToTextAPI


@pytest.fixture(scope="module")
def speech_to_text_api():
    input_dir = tempfile.mkdtemp()
    output_dir = tempfile.mkdtemp()

    input = BatchInput(input_dir, "geniusrise-test-bucket", "audio_input")
    output = BatchOutput(output_dir, "geniusrise-test-bucket", "text_output")
    state = None

    speech_to_text_api = SpeechToTextAPI(
        input=input,
        output=output,
        state=state,
    )
    yield speech_to_text_api

    # Clean up temporary directories
    for temp_dir in [input_dir, output_dir]:
        for file in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, file))
        os.rmdir(temp_dir)


@pytest.mark.parametrize(
    "model_name, model_class, processor_class, use_cuda, precision, quantization, device_map, torchscript, compile, endpoint, port, cors_domain, username, password, use_whisper_cpp, use_faster_whisper",
    [
        # fmt: off
        ("facebook/wav2vec2-large-960h-lv60-self", "Wav2Vec2ForCTC", "Wav2Vec2Processor", True, "float32", 0, "cuda:0", False, True, "*", 3000, "http://localhost:3000", None, None, False, False),
        ("openai/whisper-small", "WhisperForConditionalGeneration", "AutoProcessor", False, "float", 0, None, False, False, "0.0.0.0", 3001, "http://localhost:3000", None, None, False, False),
        ("openai/whisper-medium", "WhisperForConditionalGeneration", "AutoProcessor", True, "float16", 0, "cuda:0", False, True, "*", 3002, "https://geniusrise.ai", None, None, False, False),
        # ("large", None, None, None, None, None, None, None, None, "*", 3003, "http://localhost:3000", None, None, True, False),
        ("large-v3", None, None, None, "float32", 0, "cuda:0", None, None, "*", 3004, "http://localhost:3000", None, None, False, True),
        # fmt: on
    ],
)
def test_transcribe(
    speech_to_text_api,
    model_name,
    model_class,
    processor_class,
    use_cuda,
    precision,
    quantization,
    device_map,
    torchscript,
    compile,
    endpoint,
    port,
    cors_domain,
    username,
    password,
    use_whisper_cpp,
    use_faster_whisper,
):
    # Start the API server in a separate thread
    import threading

    server_thread = threading.Thread(
        target=speech_to_text_api.listen,
        kwargs={
            "model_name": model_name,
            "model_class": model_class,
            "processor_class": processor_class,
            "use_cuda": use_cuda,
            "precision": precision,
            "quantization": quantization,
            "device_map": device_map,
            "torchscript": torchscript,
            "compile": compile,
            "endpoint": endpoint,
            "port": port,
            "cors_domain": cors_domain,
            "username": username,
            "password": password,
            "use_whisper_cpp": use_whisper_cpp,
            "use_faster_whisper": use_faster_whisper,
        },
    )
    server_thread.start()

    # Wait for the server to start
    time.sleep(5)

    # Send a test request to the API
    url = f"http://localhost:{port}/api/v1/transcribe"
    headers = {"Content-Type": "application/json"}
    auth = (username, password) if username and password else None

    with open("./assets/sample.flac", "rb") as audio_file:
        audio_data = base64.b64encode(audio_file.read()).decode("utf-8")

    if use_faster_whisper:
        payload = {
            "audio_file": audio_data,
        }
    elif "whisper" in model_name:
        payload = {
            "audio_file": audio_data,
            "model_sampling_rate": 16000,
        }
    else:
        payload = {
            "audio_file": audio_data,
            "model_sampling_rate": 16000,
            "chunk_size": 1280000,
            "overlap_size": 213333,
            "do_sample": True,
            "num_beams": 4,
            "temperature": 0.6,
            "tgt_lang": "eng",
        }

    try:
        response = requests.post(url, json=payload, headers=headers, auth=auth)
        response.raise_for_status()
        assert "transcriptions" in response.json()
    except requests.exceptions.RequestException as e:
        pytest.fail(f"API request failed: {e}")
