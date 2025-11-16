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

import logging
from typing import Any, Dict

import cherrypy
from geniusrise import BatchInput, BatchOutput, State
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, pipeline

from geniusrise.inference.text.base import TextAPI

log = logging.getLogger(__name__)


class TranslationAPI(TextAPI):
    r"""
    A class for serving a Hugging Face-based translation model as a web API.
    This API allows users to submit text for translation and receive translated text
    in the specified target language using advanced machine learning models.

    Args:
        input (BatchInput): Configurations and data inputs for the batch process.
        output (BatchOutput): Configurations for output data handling.
        state (State): State management for the translation task.
        **kwargs: Additional keyword arguments for extended configurations.

    Example CLI Usage for interacting with the API:

    To start the API server:
    ```bash
    genius TranslationAPI rise \
        batch \
            --input_folder ./input \
        batch \
            --output_folder ./output \
        none \
        --id facebook/mbart-large-50-many-to-many-mmt-lol \
        listen \
            --args \
                model_name="facebook/mbart-large-50-many-to-many-mmt" \
                model_class="AutoModelForSeq2SeqLM" \
                tokenizer_class="AutoTokenizer" \
                use_cuda=True \
                precision="float" \
                quantization=0 \
                device_map="cuda:0" \
                max_memory=None \
                torchscript=False \
                endpoint="*" \
                port=3000 \
                cors_domain="http://localhost:3000" \
                username="user" \
                password="password"
    ```

    To translate text using the API:
    ```bash
    curl -X POST localhost:8080/translate \
        -H "Content-Type: application/json" \
        -d '{
            "text": "Hello, world!",
            "source_lang": "en",
            "target_lang": "fr",
            "decoding_strategy": "beam_search",
            "num_beams": 5
        }'
    ```
    """

    def __init__(
        self,
        input: BatchInput,
        output: BatchOutput,
        state: State,
        **kwargs: Any,
    ) -> None:
        super().__init__(input=input, output=output, state=state)
        log.info("Loading Hugging Face translation API server")

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    @cherrypy.tools.allow(methods=["POST"])
    def translate(self, **kwargs: Any) -> Dict[str, Any]:
        r"""
        Translates text to a specified target language using the underlying Hugging Face model.

        This endpoint accepts JSON data with the text and language details,
        processes it through the machine learning model, and returns the translated text.

        Args:
            **kwargs: Arbitrary keyword arguments, usually empty as parameters are in the POST body.

        POST body parameters:
            text (str): The text to be translated.
            decoding_strategy (str): Strategy to use for decoding text; e.g., 'beam_search', 'greedy'. Default is 'generate'.
            source_lang (str): Source language code.
            target_lang (str): Target language code. Default is 'en'.
            additional_params (dict): Other model-specific parameters for translation.

        Returns:
            Dict[str, Any]: A dictionary with the original text, target language, and translated text.

        Example CURL requests:

        To translate text from English to French:
        ```bash
        curl -X POST localhost:8080/translate \
            -H "Content-Type: application/json" \
            -d '{
                "text": "Hello, world!",
                "source_lang": "en",
                "target_lang": "fr",
                "decoding_strategy": "beam_search",
                "num_beams": 5
            }'
        ```

        To translate text from Spanish to German:
        ```bash
        /usr/bin/curl -X POST localhost:3000/api/v1/translate \
            -H "Content-Type: application/json" \
            -d '{
                "text": "संयुक्त राष्ट्र के प्रमुख का कहना है कि सीरिया में कोई सैन्य समाधान नहीं है",
                "source_lang": "hi_IN",
                "target_lang": "en_XX",
                "decoding_strategy": "generate",
                "decoder_start_token_id": 2,
                "early_stopping": true,
                "eos_token_id": 2,
                "forced_eos_token_id": 2,
                "max_length": 200,
                "num_beams": 5,
                "pad_token_id": 1
            }' | jq
        ```
        """

        data = cherrypy.request.json
        text = data.get("text")
        decoding_strategy = data.get("decoding_strategy", "generate")
        src_lang = data.get("source_lang")
        target_lang = data.get("target_lang", "en")

        generation_params = data
        if "decoding_strategy" in generation_params:
            del generation_params["decoding_strategy"]
        if "source_lang" in generation_params:
            del generation_params["source_lang"]
        if "target_lang" in generation_params:
            del generation_params["target_lang"]
        if "text" in generation_params:
            del generation_params["text"]

        # Tokenize the text
        if src_lang:
            self.tokenizer.src_lang = src_lang
        if target_lang != "en":
            generation_params = {
                **generation_params,
                **{"forced_bos_token_id": self.tokenizer.lang_code_to_id[target_lang]},
            }

        translated_text = self.generate(prompt=text, decoding_strategy=decoding_strategy, **generation_params)

        return {
            "text": text,
            "target_language": target_lang,
            "translated_text": translated_text,
        }

    def initialize_pipeline(self):
        """
        Lazy initialization of the translation Hugging Face pipeline.
        """
        if not self.hf_pipeline:
            model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
            tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.hf_pipeline = pipeline("translation", model=model, tokenizer=tokenizer)

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    @cherrypy.tools.allow(methods=["POST"])
    def translate_pipeline(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Endpoint for translating text using a pre-initialized Hugging Face translation pipeline.
        This method is designed to handle translation requests more efficiently by utilizing
        a preloaded model and tokenizer, reducing the overhead of loading these components for each request.

        Args:
            None - Expects input through the POST request's JSON body.

        Returns:
            Dict[str, Any]: A dictionary containing the original text, source language, target language,
                            and the translated text.

        Example CURL Request for translation:
        ```bash
        curl -X POST localhost:8080/translate_pipeline \
            -H "Content-Type: application/json" \
            -d '{
                "text": "Hello, world!",
                "source_lang": "en",
                "target_lang": "fr"
            }'
        ```
        """
        self.initialize_pipeline()  # Initialize the pipeline on first API hit

        data = cherrypy.request.json
        text = data.get("text")
        src_lang = data.get("source_lang")
        target_lang = data.get("target_lang", "en")
        generation_params = {k: v for k, v in data.items() if k not in ["text", "source_lang", "target_lang"]}

        # Set the source and target language for the tokenizer
        self.tokenizer.src_lang = src_lang
        if target_lang != "en":
            generation_params["forced_bos_token_id"] = self.tokenizer.lang_code_to_id[target_lang]

        result = self.hf_pipeline(text, **generation_params)  # type: ignore

        return {"text": text, "source_language": src_lang, "target_language": target_lang, "translated_text": result}
