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
import tempfile
import time

import pytest
import requests  # type: ignore
from geniusrise.core import BatchInput, BatchOutput

from geniusrise.inference.audio import TextToSpeechAPI


@pytest.fixture(scope="module")
def text_to_speech_api():
    input_dir = tempfile.mkdtemp()
    output_dir = tempfile.mkdtemp()

    input = BatchInput(input_dir, "geniusrise-test-bucket", "text_input")
    output = BatchOutput(output_dir, "geniusrise-test-bucket", "audio_output")
    state = None

    text_to_speech_api = TextToSpeechAPI(
        input=input,
        output=output,
        state=state,
    )
    yield text_to_speech_api


@pytest.mark.parametrize(
    "model_name, model_class, processor_class, use_cuda, precision, quantization, device_map, torchscript, compile, endpoint, port, cors_domain, username, password",
    [
        # fmt: off
        ("facebook/mms-tts-eng", "VitsModel", "VitsTokenizer", True, "float32", 0, "cuda:0", False, False, "*", 3000, "http://localhost:3000", None, None),
        ("facebook/seamless-m4t-v2-large", "SeamlessM4Tv2ForTextToSpeech", "AutoProcessor", True, "float32", 0, "cuda:0", False, False, "0.0.0.0", 3001, "https://geniusrise.ai", None, None),
        ("microsoft/speecht5_tts", "SpeechT5ForTextToSpeech", "SpeechT5Processor", True, "float32", 0, "cuda:0", False, False, "*", 3002, "http://example.com", None, None),
        ("suno/bark", "BarkModel", "BarkProcessor", True, "float32", 0, "cuda:0", False, False, "*", 3003, "http://localhost:3000", None, None),
        # fmt: on
    ],
)
def test_synthesize(
    text_to_speech_api,
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
):
    # Start the API server in a separate thread
    import threading

    server_thread = threading.Thread(
        target=text_to_speech_api.listen,
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
        },
    )
    server_thread.start()

    # Wait for the server to start
    time.sleep(30)

    # Send a test request to the API
    url = f"http://localhost:{port}/api/v1/synthesize"
    headers = {"Content-Type": "application/json"}
    auth = (username, password) if username and password else None

    payload = {
        "text": "This is a test text for speech synthesis.",
        "output_type": "mp3",
    }

    if "seamless" in model_name:
        payload["voice_preset"] = 1
        payload["tgt_lang"] = "eng"
    if "tts" in model_name:
        payload["voice_preset"] = 7306

    try:
        response = requests.post(url, json=payload, headers=headers, auth=auth)
        response.raise_for_status()
        assert "audio_file" in response.json()
        assert "input" in response.json()
        assert response.json()["input"] == payload["text"]

        # Decode the base64 audio data
        audio_base64 = response.json()["audio_file"]
        audio_data = base64.b64decode(audio_base64.encode("utf-8"))

        # Save the audio data to a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.write(audio_data)
        temp_file.close()

        # TODO: Optionally, you can play the audio file or perform additional checks

    except requests.exceptions.RequestException as e:
        pytest.fail(f"API request failed: {e}")
