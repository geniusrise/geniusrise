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
import multiprocessing

import cherrypy
import torch
from geniusrise import BatchInput, BatchOutput, State
from transformers import AutoModelForCTC, AutoProcessor

from geniusrise.inference.audio.utils.s2t_inference import _SpeechToTextInference
from geniusrise.inference.audio.utils.s2t import decode_audio
from geniusrise.inference.audio.base import AudioAPI


class SpeechToTextAPI(AudioAPI, _SpeechToTextInference):
    r"""
    SpeechToTextAPI is a subclass of AudioAPI specifically designed for speech-to-text models.
    It extends the functionality to handle speech-to-text processing using various ASR models.

    Attributes:
        model (AutoModelForCTC): The speech-to-text model.
        processor (AutoProcessor): The processor to prepare input audio data for the model.

    Methods:
        transcribe(audio_input: bytes) -> str:
            Transcribes the given audio input to text using the speech-to-text model.

    Example CLI Usage:

    ```bash
    genius SpeechToTextAPI rise \
    batch \
        --input_folder ./input \
    batch \
        --output_folder ./output \
    none \
        --id facebook/wav2vec2-large-960h-lv60-self \
        listen \
            --args \
                model_name="facebook/wav2vec2-large-960h-lv60-self" \
                model_class="Wav2Vec2ForCTC" \
                processor_class="Wav2Vec2Processor" \
                use_cuda=True \
                precision="float32" \
                quantization=0 \
                device_map="cuda:0" \
                max_memory=None \
                torchscript=False \
                compile=True \
                endpoint="*" \
                port=3000 \
                cors_domain="http://localhost:3000" \
                username="user" \
                password="password"
    ```

    or using whisper.cpp:

    ```bash
    genius SpeechToTextAPI rise \
        batch \
                --input_folder ./input \
        batch \
                --output_folder ./output \
        none \
        listen \
            --args \
                model_name="large" \
                use_whisper_cpp=True \
                endpoint="*" \
                port=3000 \
                cors_domain="http://localhost:3000" \
                username="user" \
                password="password"
    ```
    """

    model: AutoModelForCTC
    processor: AutoProcessor

    def __init__(
        self,
        input: BatchInput,
        output: BatchOutput,
        state: State,
        **kwargs,
    ):
        """
        Initializes the SpeechToTextAPI with configurations for speech-to-text processing.

        Args:
            input (BatchInput): The input data configuration.
            output (BatchOutput): The output data configuration.
            state (State): The state configuration.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(input=input, output=output, state=state, **kwargs)
        self.hf_pipeline = None

    @cherrypy.expose
    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    def transcribe(self):
        r"""
        API endpoint to transcribe the given audio input to text using the speech-to-text model.
        Expects a JSON input with 'audio_file' as a key containing the base64 encoded audio data.

        Returns:
            Dict[str, str]: A dictionary containing the transcribed text.

        Example CURL Request for transcription:
        ```bash
        (base64 -w 0 sample.flac | awk '{print "{\"audio_file\": \""$0"\", \"model_sampling_rate\": 16000, \"chunk_size\": 1280000, \"overlap_size\": 213333, \"do_sample\": true, \"num_beams\": 4, \"temperature\": 0.6, \"tgt_lang\": \"eng\"}"}' > /tmp/payload.json)
        curl -X POST http://localhost:3000/api/v1/transcribe \
            -H "Content-Type: application/json" \
            -u user:password \
            -d @/tmp/payload.json | jq
        ```
        """
        input_json = cherrypy.request.json
        audio_data = input_json.get("audio_file")
        model_sampling_rate = input_json.get("model_sampling_rate", 16_000)
        processor_args = input_json.get("processor_args", {})
        chunk_size = input_json.get("chunk_size", 0)
        overlap_size = input_json.get("overlap_size", 0)

        generate_args = input_json.copy()

        if "audio_file" in generate_args:
            del generate_args["audio_file"]
        if "model_sampling_rate" in generate_args:
            del generate_args["model_sampling_rate"]
        if "processor_args" in generate_args:
            del generate_args["processor_args"]
        if "chunk_size" in generate_args:
            del generate_args["chunk_size"]
        if "overlap_size" in generate_args:
            del generate_args["overlap_size"]

        if chunk_size > 0 and overlap_size == 0:
            overlap_size = int(chunk_size / 6)

        # TODO: support voice presets

        if not audio_data:
            raise cherrypy.HTTPError(400, "No audio data provided.")

        # Convert base64 encoded data to bytes
        audio_bytes = base64.b64decode(audio_data)
        audio_input, input_sampling_rate = decode_audio(
            audio_bytes=audio_bytes,
            model_type=self.model.config.model_type if not (self.use_faster_whisper or self.use_whisper_cpp) else None,
            model_sampling_rate=model_sampling_rate,
        )

        # Perform inference
        with torch.no_grad():
            if self.use_whisper_cpp:
                transcription = self.model.transcribe(audio_input, num_proc=multiprocessing.cpu_count())
            elif self.use_faster_whisper:
                transcription = self.process_faster_whisper(audio_bytes, model_sampling_rate, chunk_size, generate_args)
            elif self.model.config.model_type == "whisper":
                transcription = self.process_whisper(
                    audio_input, model_sampling_rate, processor_args, chunk_size, overlap_size, generate_args
                )
            elif self.model.config.model_type == "seamless_m4t_v2":
                transcription = self.process_seamless(
                    audio_input, model_sampling_rate, processor_args, chunk_size, overlap_size, generate_args
                )
            elif self.model.config.model_type == "wav2vec2":
                transcription = self.process_wav2vec2(
                    audio_input, model_sampling_rate, processor_args, chunk_size, overlap_size
                )

        return {"transcriptions": transcription}
