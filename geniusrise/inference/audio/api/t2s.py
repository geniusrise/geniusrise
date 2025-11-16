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

import cherrypy
from geniusrise import BatchInput, BatchOutput, State
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from geniusrise.inference.audio.utils.t2s_inference import _TextToSpeechInference
from geniusrise.inference.audio.base import AudioAPI
from geniusrise.inference.audio.utils.t2s import convert_waveform_to_audio_file


class TextToSpeechAPI(AudioAPI, _TextToSpeechInference):
    r"""
    TextToSpeechAPI for converting text to speech using various TTS models.

    Attributes:
        model (AutoModelForSeq2SeqLM): The text-to-speech model.
        tokenizer (AutoTokenizer): The tokenizer for the model.

    Methods:
        synthesize(text_input: str) -> bytes:
            Converts the given text input to speech using the text-to-speech model.

    Example CLI Usage:

    ```
    genius TextToSpeechAPI rise \
    batch \
        --input_folder ./input \
    batch \
        --output_folder ./output \
    none \
        --id facebook/mms-tts-eng \
        listen \
            --args \
                model_name="facebook/mms-tts-eng" \
                model_class="VitsModel" \
                processor_class="VitsTokenizer" \
                use_cuda=True \
                precision="float32" \
                quantization=0 \
                device_map="cuda:0" \
                max_memory=None \
                torchscript=False \
                compile=False \
                endpoint="*" \
                port=3000 \
                cors_domain="http://localhost:3000" \
                username="user" \
                password="password"
    ```
    """

    model: AutoModelForSeq2SeqLM
    tokenizer: AutoTokenizer

    def __init__(
        self,
        input: BatchInput,
        output: BatchOutput,
        state: State,
        **kwargs,
    ):
        """
        Initializes the TextToSpeechAPI with configurations for text-to-speech processing.

        Args:
            input (BatchInput): The input data configuration.
            output (BatchOutput): The output data configuration.
            state (State): The state configuration.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(input=input, output=output, state=state, **kwargs)
        self.hf_pipeline = None
        self.vocoder = None
        self.embeddings_dataset = None

    @cherrypy.expose
    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    def synthesize(self):
        """
        API endpoint to convert text input to speech using the text-to-speech model.
        Expects a JSON input with 'text' as a key containing the text to be synthesized.

        Returns:
            Dict[str, str]: A dictionary containing the base64 encoded audio data.

        Example CURL Request:
        ```
        /usr/bin/curl -X POST localhost:3000/api/v1/synthesize \
            -H "Content-Type: application/json" \
            -u user:password \
            -d '{
                "text": "रीकरंट न्यूरल नेटवर्क्स (RNNs) के बारे में कुछ जादुई है। मैं अब भी याद करता हूँ जब मैंने अपना पहला रीकरंट नेटवर्क ट्रेन किया था इमेज कैप्शनिंग के लिए। ट्रेनिंग शुरू करने के कुछ ही मिनटों में, मेरी पहली बेबी मॉडल (जिसका मैंने बेतरतीब हाइपरपैरामीटर्स चुने थे) ने इमेजेज के बहुत अच्छे विवरण उत्पन्न करने शुरू कर दिए जो लगभग समझ में आने वाले थे। कभी-कभी आपकी मॉडल कितनी सरल है और उससे जो परिणाम आते हैं उनका अनुपात आपकी अपेक्षाओं से कहीं आगे निकल जाता है, और यह वही समय था। उस समय जो परिणाम आया था वह इतना चौंकाने वाला था क्योंकि सामान्य समझ यह थी कि RNNs को प्रशिक्षित करना मुश्किल होता है (लेकिन अधिक अनुभव होने के बाद, मैंने बिलकुल उल्टा निष्कर्ष निकाला)। एक साल आगे बढ़ो: मैं लगातार RNNs प्रशिक्षित कर रहा हूँ और मैंने उनकी शक्ति और मजबूती को कई बार देखा है, फिर भी उनके जादुई आउटपुट मुझे हमेशा मनोरंजन करते हैं।",
                "output_type": "mp3"
            }' | jq -r '.audio_file' | base64 -d > output.mp3 && vlc output.mp3
        ```
        """
        input_json = cherrypy.request.json
        text_data = input_json.get("text")
        output_type = input_json.get("output_type")
        voice_preset = input_json.get("voice_preset")

        generate_args = input_json.copy()

        if "text" in generate_args:
            del generate_args["text"]
        if "output_type" in generate_args:
            del generate_args["output_type"]
        if "voice_preset" in generate_args:
            del generate_args["voice_preset"]

        if not text_data:
            raise cherrypy.HTTPError(400, "No text data provided.")

        # Perform inference
        if self.model.config.model_type == "vits":
            audio_output = self.process_mms(text_data, generate_args=generate_args)
        elif self.model.config.model_type == "coarse_acoustics" or self.model.config.model_type == "bark":
            audio_output = self.process_bark(text_data, voice_preset=voice_preset, generate_args=generate_args)
        elif self.model.config.model_type == "speecht5":
            audio_output = self.process_speecht5_tts(text_data, voice_preset=voice_preset, generate_args=generate_args)
        elif self.model.config.model_type == "seamless_m4t_v2":
            audio_output = self.process_seamless(text_data, voice_preset=voice_preset, generate_args=generate_args)

        # Convert audio to base64 encoded data
        sample_rate = (
            self.model.generation_config.sample_rate if hasattr(self.model.generation_config, "sample_rate") else 16_000
        )
        audio_file = convert_waveform_to_audio_file(audio_output, format=output_type, sample_rate=sample_rate)
        audio_base64 = base64.b64encode(audio_file)

        return {"audio_file": audio_base64.decode("utf-8"), "input": text_data}
