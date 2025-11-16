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

from typing import Any, Dict

import cherrypy
import torch
from geniusrise import BatchInput, BatchOutput, State
from geniusrise.logging import setup_logger
from transformers import AutoModelForTokenClassification, AutoTokenizer, pipeline

from geniusrise.inference.text.base import TextAPI


class NamedEntityRecognitionAPI(TextAPI):
    r"""
    NamedEntityRecognitionAPI serves a Named Entity Recognition (NER) model using the Hugging Face transformers library.
    It is designed to recognize and classify named entities in text into predefined categories such as the names of persons,
    organizations, locations, expressions of times, quantities, monetary values, percentages, etc.

    Attributes:
        model (Any): The loaded NER model, typically a Hugging Face transformer model specialized for token classification.
        tokenizer (Any): The tokenizer for preprocessing text compatible with the loaded model.

    Example CLI Usage:
    ```bash
    genius NamedEntityRecognitionAPI rise \
        batch \
            --input_folder ./input \
        batch \
            --output_folder ./output \
        none \
        --id dslim/bert-large-NER-lol \
        listen \
            --args \
                model_name="dslim/bert-large-NER" \
                model_class="AutoModelForTokenClassification" \
                tokenizer_class="AutoTokenizer" \
                use_cuda=True \
                precision="float" \
                quantization=0 \
                device_map="cuda:0" \
                max_memory=None \
                torchscript=False \
                endpoint="0.0.0.0" \
                port=3000 \
                cors_domain="http://localhost:3000" \
                username="user" \
                password="password"
    ```
    """

    def __init__(
        self,
        input: BatchInput,
        output: BatchOutput,
        state: State,
        **kwargs: Any,
    ) -> None:
        """
        Initializes the NamedEntityRecognitionAPI class.

        Args:
            input (BatchInput): The input data.
            output (BatchOutput): The output data.
            state (State): The state data.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(input=input, output=output, state=state)
        self.log = setup_logger(self)
        self.hf_pipeline = None

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    @cherrypy.tools.allow(methods=["POST"])
    def recognize_entities(self, **kwargs: Any) -> Dict[str, Any]:
        r"""
        Endpoint for recognizing named entities in the input text using the loaded NER model.

        Args:
            **kwargs (Any): Arbitrary keyword arguments, typically containing 'text' for the input text.

        Returns:
            Dict[str, Any]: A dictionary containing the original input text and a list of recognized entities
                            with their respective types.

        Example CURL Requests:
        ```bash
        curl -X POST localhost:3000/api/v1/recognize_entities \
            -H "Content-Type: application/json" \
            -d '{"text": "John Doe works at OpenAI in San Francisco."}' | jq
        ```

        ```bash
        curl -X POST localhost:3000/api/v1/recognize_entities \
            -H "Content-Type: application/json" \
            -d '{"text": "Alice is going to visit the Eiffel Tower in Paris next summer."}' | jq
        ```
        """
        data = cherrypy.request.json
        text = data.get("text")
        generation_args = data

        if "text" in generation_args:
            del generation_args["text"]

        inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True)

        if next(self.model.parameters()).is_cuda:
            inputs = {k: v.cuda() for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs, **generation_args)
            predictions = outputs.logits.argmax(dim=-1).squeeze().tolist()

        entities = [
            {"token": self.tokenizer.convert_ids_to_tokens(i), "class": self.model.config.id2label[x]}
            for (x, i) in zip(predictions, inputs["input_ids"].squeeze().tolist())
        ]

        return {"input": text, "entities": entities}

    def initialize_pipeline(self):
        """
        Lazy initialization of the NER Hugging Face pipeline.
        """
        if not self.hf_pipeline:
            model = AutoModelForTokenClassification.from_pretrained(self.model_name)
            tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.hf_pipeline = pipeline("ner", model=model, tokenizer=tokenizer)

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    @cherrypy.tools.allow(methods=["POST"])
    def ner_pipeline(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Recognizes named entities in the input text using the Hugging Face pipeline.

        This method leverages a pre-trained NER model to identify and classify entities in text into categories such as
        names, organizations, locations, etc. It's suitable for processing various types of text content.

        Args:
            **kwargs (Any): Arbitrary keyword arguments, typically containing 'text' for the input text.

        Returns:
            Dict[str, Any]: A dictionary containing the original input text and a list of recognized entities.

        Example CURL Request for NER:
        ```bash
        curl -X POST localhost:3000/api/v1/ner_pipeline \
            -H "Content-Type: application/json" \
            -d '{"text": "John Doe works at OpenAI in San Francisco."}' | jq
        ```
        """
        self.initialize_pipeline()  # Initialize the pipeline on first API hit

        data = cherrypy.request.json
        text = data.get("text")

        result = self.hf_pipeline(text)  # type: ignore

        return {"input": text, "entities": result}
