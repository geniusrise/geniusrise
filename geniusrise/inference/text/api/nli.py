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

from typing import Any, Dict, List

import cherrypy
import numpy as np
import torch
from geniusrise import BatchInput, BatchOutput, State
from geniusrise.logging import setup_logger
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

from geniusrise.inference.text.base import TextAPI


class NLIAPI(TextAPI):
    r"""
    Represents a Natural Language Inference (NLI) API leveraging Hugging Face's transformer models. This class is capable of
    handling various NLI tasks such as entailment, classification, similarity checking, and more. Utilizes CherryPy for exposing
    API endpoints that can be interacted with via standard HTTP requests.

    Attributes:
        model (AutoModelForSequenceClassification): The loaded Hugging Face model for sequence classification tasks.
        tokenizer (AutoTokenizer): The tokenizer corresponding to the model, used for processing input text.

    CLI Usage Example:
    For interacting with the NLI API, you would typically start the server using a command similar to one listed in the provided examples.
    After the server is running, you can use CURL commands to interact with the different endpoints.

    Example:

    ```bash
    genius NLIAPI rise \
        batch \
            --input_folder ./input \
        batch \
            --output_folder ./output \
        none \
        --id "MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7-lol" \
        listen \
            --args \
                model_name="MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7" \
                model_class="AutoModelForSequenceClassification" \
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
    """

    model: Any
    tokenizer: Any

    def __init__(
        self,
        input: BatchInput,
        output: BatchOutput,
        state: State,
        **kwargs: Any,
    ):
        """
        Initializes the NLIAPI with configurations for handling input, output, and state management.

        Args:
            input (BatchInput): Configuration for the input data.
            output (BatchOutput): Configuration for the output data.
            state (State): State management for the API.
            **kwargs (Any): Additional keyword arguments for extended functionality.
        """
        super().__init__(input=input, output=output, state=state)
        self.log = setup_logger(self)
        self.hf_pipeline = None

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    @cherrypy.tools.allow(methods=["POST"])
    def entailment(self, **kwargs: Any) -> Dict[str, Any]:
        r"""
        Endpoint for evaluating the entailment relationship between a premise and a hypothesis. It returns the relationship
        scores across possible labels like entailment, contradiction, and neutral.

        Args:
            **kwargs (Any): Arbitrary keyword arguments, typically containing 'premise' and 'hypothesis'.

        Returns:
            Dict[str, Any]: A dictionary containing the premise, hypothesis, and their relationship scores.

        Example CURL Request:
        ```bash
        /usr/bin/curl -X POST localhost:3000/api/v1/entailment \
            -H "Content-Type: application/json" \\\
            -d '{
                "premise": "This a very good entry level smartphone, battery last 2-3 days after fully charged when connected to the internet. No memory lag issue when playing simple hidden object games. Performance is beyond my expectation, i bought it with a good bargain, couldnt ask for more!",
                "hypothesis": "the phone has an awesome battery life"
            }' | jq
        ```
        ```
        """
        data = cherrypy.request.json
        premise = data.get("premise", "")
        hypothesis = data.get("hypothesis", "The statement is true")

        inputs = self.tokenizer(
            premise,
            hypothesis,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )

        if next(self.model.parameters()).is_cuda:
            inputs = {k: v.cuda() for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits if hasattr(outputs, "logits") else outputs[0]
            if next(self.model.parameters()).is_cuda:
                logits = logits.cpu()
            softmax = torch.nn.functional.softmax(logits, dim=-1)
            scores = softmax.numpy().tolist()  # Convert scores to list

        id_to_label = dict(enumerate(self.model.config.id2label.values()))  # type: ignore
        label_scores = {id_to_label[label_id]: score for label_id, score in enumerate(scores[0])}

        return {
            "premise": premise,
            "hypothesis": hypothesis,
            "label_scores": label_scores,
        }

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    @cherrypy.tools.allow(methods=["POST"])
    def classify(self, **kwargs: Any) -> Dict[str, Any]:
        r"""
        Endpoint for classifying the input text into one of the provided candidate labels using zero-shot classification.

        Args:
            **kwargs (Any): Arbitrary keyword arguments, typically containing 'text' and 'candidate_labels'.

        Returns:
            Dict[str, Any]: A dictionary containing the input text, candidate labels, and classification scores.

        Example CURL Request:
        ```bash
        curl -X POST localhost:3000/api/v1/classify \
            -H "Content-Type: application/json" \
            -d '{
                "text": "The new movie is a thrilling adventure in space",
                "candidate_labels": ["entertainment", "politics", "business"]
            }'
        ```
        """
        data = cherrypy.request.json
        text = data.get("text", "")
        candidate_labels = data.get("candidate_labels", [])

        label_scores = {}
        for label in candidate_labels:
            # Construct hypothesis for each label
            hypothesis = f"This example is {label}."

            # Tokenize the text and hypothesis
            inputs = self.tokenizer(text, hypothesis, return_tensors="pt", padding=True, truncation=True)

            # Move inputs to GPU if CUDA is enabled
            if self.use_cuda:
                inputs = {k: v.cuda() for k, v in inputs.items()}

            # Perform inference
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                softmax = torch.nn.functional.softmax(logits, dim=-1)
                scores = softmax.cpu().numpy().tolist()

            # Consider 'entailment' score as the label score
            entailment_idx = self.model.config.label2id.get("entailment", 0)
            contradiction_idx = self.model.config.label2id.get("contradiction", 0)
            label_scores[label] = np.exp(scores[0][entailment_idx]) / np.exp(
                scores[0][entailment_idx] + scores[0][contradiction_idx]
            )

        sum_scores = sum(label_scores.values())
        label_scores = {k: v / sum_scores for k, v in label_scores.items()}
        return {"text": text, "label_scores": label_scores}

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    @cherrypy.tools.allow(methods=["POST"])
    def textual_similarity(self, **kwargs: Any) -> Dict[str, Any]:
        r"""
        Evaluates the textual similarity between two texts.

        Args:
            text1 (str): The first text.
            text2 (str): The second text.

        Returns:
            Dict[str, Any]: A dictionary containing similarity score.

        Example CURL Request:
        ```bash
        /usr/bin/curl -X POST localhost:3000/api/v1/textual_similarity \
            -H "Content-Type: application/json" \
            -d '{
                "text1": "Theres something magical about Recurrent Neural Networks (RNNs). I still remember when I trained my first recurrent network for Image Captioning. Within a few dozen minutes of training my first baby model (with rather arbitrarily-chosen hyperparameters) started to generate very nice looking descriptions of images that were on the edge of making sense. Sometimes the ratio of how simple your model is to the quality of the results you get out of it blows past your expectations, and this was one of those times. What made this result so shocking at the time was that the common wisdom was that RNNs were supposed to be difficult to train (with more experience Ive in fact reached the opposite conclusion). Fast forward about a year: Im training RNNs all the time and Ive witnessed their power and robustness many times, and yet their magical outputs still find ways of amusing me.",
                "text2": "There is something magical about training neural networks. Their simplicity coupled with their power is astonishing."
            }' | jq
        ```
        """
        data = cherrypy.request.json
        text1 = data.get("text1", "")
        text2 = data.get("text2", "")

        # Using the same text as premise and hypothesis for similarity
        scores = self._get_entailment_scores(text1, [text2])
        return {"text1": text1, "text2": text2, "similarity_score": scores[text2]}

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    @cherrypy.tools.allow(methods=["POST"])
    def fact_checking(self, **kwargs: Any) -> Dict[str, Any]:
        r"""
        Performs fact checking on a statement given a context.

        Args:
            context (str): The context or background information.
            statement (str): The statement to fact check.

        Returns:
            Dict[str, Any]: A dictionary containing fact checking scores.

        Example CURL Request:
        ```bash
        /usr/bin/curl -X POST localhost:3000/api/v1/fact_checking \
            -H "Content-Type: application/json" \
            -d '{
                "context": "Theres something magical about Recurrent Neural Networks (RNNs). I still remember when I trained my first recurrent network for Image Captioning. Within a few dozen minutes of training my first baby model (with rather arbitrarily-chosen hyperparameters) started to generate very nice looking descriptions of images that were on the edge of making sense. Sometimes the ratio of how simple your model is to the quality of the results you get out of it blows past your expectations, and this was one of those times. What made this result so shocking at the time was that the common wisdom was that RNNs were supposed to be difficult to train (with more experience Ive in fact reached the opposite conclusion). Fast forward about a year: Im training RNNs all the time and Ive witnessed their power and robustness many times, and yet their magical outputs still find ways of amusing me.",
                "statement": "The author is looking for a home loan"
            }' | jq
        ```
        """
        data = cherrypy.request.json
        context = data.get("context", "")
        statement = data.get("statement", "")

        scores = self._get_entailment_scores(context, [statement])
        return {
            "context": context,
            "statement": statement,
            "fact_checking_score": scores[statement],
        }

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    @cherrypy.tools.allow(methods=["POST"])
    def question_answering(self, **kwargs: Any) -> Dict[str, Any]:
        r"""
        Performs question answering for multiple choice questions.

        Args:
            question (str): The question text.
            choices (List[str]): A list of possible answers.

        Returns:
            Dict[str, Any]: A dictionary containing the scores for each answer choice.

        Example CURL Request:
        ```bash
        /usr/bin/curl -X POST localhost:3000/api/v1/question_answering \
            -H "Content-Type: application/json" \
            -d '{
                "question": "[ML-1T-2] is the dimensional formula of",
                "choices": ["force", "coefficient of friction", "modulus of elasticity", "energy"]
            }' | jq
        ```
        """
        data = cherrypy.request.json
        question = data.get("question", "")
        choices = data.get("choices", [])

        scores = self._get_entailment_scores(question, choices)
        return {"question": question, "choices": choices, "scores": scores}

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    @cherrypy.tools.allow(methods=["POST"])
    def detect_intent(self, **kwargs: Any) -> Dict[str, Any]:
        r"""
        Detects the intent of the input text from a list of possible intents.

        Args:
            text (str): The input text.
            intents (List[str]): A list of possible intents.

        Returns:
            Dict[str, Any]: A dictionary containing the input text and detected intent with its score.

        Example CURL Request:
        ```bash
        /usr/bin/curl -X POST localhost:3000/api/v1/detect_intent \
            -H "Content-Type: application/json" \
            -d '{
                "text": "Theres something magical about Recurrent Neural Networks (RNNs). I still remember when I trained my first recurrent network for Image Captioning. Within a few dozen minutes of training my first baby model (with rather arbitrarily-chosen hyperparameters) started to generate very nice looking descriptions of images that were on the edge of making sense. Sometimes the ratio of how simple your model is to the quality of the results you get out of it blows past your expectations, and this was one of those times. What made this result so shocking at the time was that the common wisdom was that RNNs were supposed to be difficult to train (with more experience Ive in fact reached the opposite conclusion). Fast forward about a year: Im training RNNs all the time and Ive witnessed their power and robustness many times, and yet their magical outputs still find ways of amusing me.",
                "intents": ["teach","sell","note","advertise","promote"]
            }' | jq
        ```
        """
        data = cherrypy.request.json
        text = data.get("text", "")
        intents = data.get("intents", [])

        # Zero-shot classification for intent detection
        scores = self._get_entailment_scores(text, intents)
        return {"text": text, "intents": intents, "scores": scores}

    def _get_entailment_scores(self, premise: str, hypotheses: List[str]) -> Dict[str, float]:
        """
        Helper method to get entailment scores for multiple hypotheses.

        Args:
            premise (str): The input premise text.
            hypotheses (List[str]): A list of hypothesis texts.

        Returns:
            Dict[str, float]: A dictionary mapping each hypothesis to its entailment score.
        """
        label_scores = {}
        for hypothesis in hypotheses:
            inputs = self.tokenizer(premise, hypothesis, return_tensors="pt", padding=True, truncation=True)
            if self.use_cuda:
                inputs = {k: v.cuda() for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                softmax = torch.nn.functional.softmax(logits, dim=-1)
                scores = softmax.cpu().numpy().tolist()

            entailment_idx = self.model.config.label2id.get("entailment", 0)
            contradiction_idx = self.model.config.label2id.get("contradiction", 0)
            label_scores[hypothesis] = np.exp(scores[0][entailment_idx]) / np.exp(
                scores[0][entailment_idx] + scores[0][contradiction_idx]
            )

        return label_scores

    def initialize_pipeline(self):
        """
        Lazy initialization of the NLI Hugging Face pipeline.
        """
        if not self.hf_pipeline:
            model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.hf_pipeline = pipeline("zero-shot-classification", model=model, tokenizer=tokenizer)

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    @cherrypy.tools.allow(methods=["POST"])
    def zero_shot_classification(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Performs zero-shot classification using the Hugging Face pipeline.
        It allows classification of text without explicitly provided labels.

        Args:
            **kwargs (Any): Arbitrary keyword arguments, typically containing 'premise' and 'hypothesis'.

        Returns:
            Dict[str, Any]: A dictionary containing the premise, hypothesis, and their classification scores.

        Example CURL Request for zero-shot classification:
        ```bash
        curl -X POST localhost:3000/api/v1/zero_shot_classification \
            -H "Content-Type: application/json" \
            -d '{
                "premise": "A new study shows that the Mediterranean diet is good for heart health.",
                "hypothesis": "The study is related to diet and health."
            }' | jq
        ```
        """
        self.initialize_pipeline()  # Initialize the pipeline on first API hit

        data = cherrypy.request.json
        premise = data.get("premise", "")
        hypothesis = data.get("hypothesis", "")

        result = self.hf_pipeline(  # type: ignore
            premise, candidate_labels=["entailment", "contradiction", "neutral"], hypothesis=hypothesis
        )

        return {"premise": premise, "hypothesis": hypothesis, "label_scores": result["scores"]}
