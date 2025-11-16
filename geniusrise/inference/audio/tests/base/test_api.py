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

import tempfile
import time

import pytest
import requests  # type: ignore
from geniusrise.core import BatchInput, BatchOutput, InMemoryState

from geniusrise.inference.audio.base.api import AudioAPI


@pytest.fixture(scope="module")
def audio_api():
    input_dir = tempfile.mkdtemp()
    output_dir = tempfile.mkdtemp()

    input = BatchInput(input_dir, "geniusrise-test-bucket", "api_input")
    output = BatchOutput(output_dir, "geniusrise-test-bucket", "api_output")
    state = InMemoryState(1)

    audio_api = AudioAPI(
        input=input,
        output=output,
        state=state,
    )
    yield audio_api


@pytest.mark.parametrize(
    "model_name, model_class, processor_class, use_cuda, precision, quantization, device_map, torchscript, compile, concurrent_queries, use_whisper_cpp, use_faster_whisper, endpoint, port, cors_domain, username, password",
    [
        # fmt: off
        ("facebook/wav2vec2-base-960h", "Wav2Vec2ForCTC", "Wav2Vec2Processor", True, "float32", 0, "cuda:0", False, False, False, False, False, "*", 3000, "http://localhost:3000", "admin", "password"),
        ("openai/whisper-small", "WhisperForConditionalGeneration", "AutoProcessor", False, "float32", 4, None, False, False, True, False, False, "*", 3001, "http://example.com", "admin", "password"),
        ("openai/whisper-medium", "WhisperForConditionalGeneration", "AutoProcessor", True, "float16", 0, "cuda:0", False, True, False, False, False, "0.0.0.0", 3002, "https://geniusrise.ai", "admin", "password"),
        ("large-v3", None, None, None, "float32", 0, "cuda:0", None, None, False, False, True, "*", 3003, "http://localhost:3000", "admin", "password"),
        ("large", None, None, None, None, None, None, None, None, False, True, False, "*", 3004, "http://localhost:3000", "admin", "password"),
        # fmt: on
    ],
)
def test_listen(
    audio_api,
    model_name,
    model_class,
    processor_class,
    use_cuda,
    precision,
    quantization,
    device_map,
    torchscript,
    compile,
    concurrent_queries,
    use_whisper_cpp,
    use_faster_whisper,
    endpoint,
    port,
    cors_domain,
    username,
    password,
):
    # Start the API server in a separate thread
    import threading

    server_thread = threading.Thread(
        target=audio_api.listen,
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
            "concurrent_queries": concurrent_queries,
            "use_whisper_cpp": use_whisper_cpp,
            "use_faster_whisper": use_faster_whisper,
            "endpoint": endpoint,
            "port": port,
            "cors_domain": cors_domain,
            "username": username,
            "password": password,
        },
    )
    server_thread.start()

    # Wait for the server to start
    time.sleep(5)

    # Send a test request to the API
    url = f"http://localhost:{port}/api/v1/404"
    headers = {"Content-Type": "application/json"}
    auth = (username, password) if username and password else None

    try:
        response = requests.post(url, json={}, headers=headers, auth=auth)
        assert response.status_code == 404
    except requests.exceptions.RequestException as e:
        pytest.fail(f"API request failed: {e}")
