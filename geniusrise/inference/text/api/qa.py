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
import pandas as pd
import torch
from geniusrise import BatchInput, BatchOutput, State
from geniusrise.logging import setup_logger
from transformers import AutoModelForQuestionAnswering, AutoModelForTableQuestionAnswering, AutoTokenizer, pipeline

from geniusrise.inference.text.base import TextAPI


class QAAPI(TextAPI):
    model: AutoModelForQuestionAnswering | AutoModelForTableQuestionAnswering
    tokenizer: AutoTokenizer

    r"""
    A class for handling different types of QA models, including traditional QA, TAPAS (Table-based QA), and TAPEX.
    It utilizes the Hugging Face transformers library to provide state-of-the-art question answering capabilities
    across various formats of data including plain text and tabular data.

    Attributes:
        model (AutoModelForQuestionAnswering | AutoModelForTableQuestionAnswering):
            The pre-trained QA model (traditional, TAPAS, or TAPEX).
        tokenizer (AutoTokenizer): The tokenizer used to preprocess input text.

    Methods:
        answer(self, **kwargs: Any) -> Dict[str, Any]:
            Answers questions based on the provided context (text or table).

    CLI Usage Example:
    ```bash
    genius QAAPI rise \
        batch \
            --input_folder ./input \
        batch \
            --output_folder ./output \
        none \
        --id distilbert-base-uncased-distilled-squad-lol \
        listen \
            --args \
                model_name="distilbert-base-uncased-distilled-squad" \
                model_class="AutoModelForQuestionAnswering" \
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

    ```bash
    genius QAAPI rise \
        batch \
            --input_folder ./input \
        batch \
            --output_folder ./output \
        none \
        --id google/tapas-base-finetuned-wtq-lol \
        listen \
            --args \
                model_name="google/tapas-base-finetuned-wtq" \
                model_class="AutoModelForTableQuestionAnswering" \
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

    ```bash
    genius QAAPI rise \
        batch \
            --input_folder ./input \
        batch \
            --output_folder ./output \
        none \
        --id microsoft/tapex-large-finetuned-wtq-lol \
        listen \
            --args \
                model_name="microsoft/tapex-large-finetuned-wtq" \
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
    """

    def __init__(
        self,
        input: BatchInput,
        output: BatchOutput,
        state: State,
        **kwargs: Any,
    ):
        """
        Initializes the QAAPI with configurations for input, output, and state management.

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
    def answer(self, **kwargs: Any) -> Dict[str, Any]:
        r"""
        Answers questions based on the provided context (text or table). It adapts to the model type (traditional, TAPAS, TAPEX)
        and provides answers accordingly.

        Args:
            **kwargs (Any): Arbitrary keyword arguments, typically containing the 'question' and 'data' (context or table).

        Returns:
            Dict[str, Any]: A dictionary containing the question, context/table, and answer(s).

        Example CURL Request for Text-based QA:
        ```bash
        curl -X POST localhost:3000/api/v1/answer \
            -H "Content-Type: application/json" \
            -d '{"question": "What is the capital of France?", "data": "France is a country in Europe. Its capital is Paris."}'
        ```

        Example CURL Requests:
        ```bash
        /usr/bin/curl -X POST localhost:3000/api/v1/answer \
            -H "Content-Type: application/json" \
            -d '{
                "data": "Theres something magical about Recurrent Neural Networks (RNNs). I still remember when I trained my first recurrent network for Image Captioning. Within a few dozen minutes of training my first baby model (with rather arbitrarily-chosen hyperparameters) started to generate very nice looking descriptions of images that were on the edge of making sense. Sometimes the ratio of how simple your model is to the quality of the results you get out of it blows past your expectations, and this was one of those times. What made this result so shocking at the time was that the common wisdom was that RNNs were supposed to be difficult to train (with more experience Ive in fact reached the opposite conclusion). Fast forward about a year: Im training RNNs all the time and Ive witnessed their power and robustness many times, and yet their magical outputs still find ways of amusing me.",
                "question": "What is the common wisdom about RNNs?"

            }' | jq
        ```

        ```bash
        /usr/bin/curl -X POST localhost:3000/api/v1/answer \
            -H "Content-Type: application/json" \
            -d '{
            "data": [
                {"Name": "Alice", "Age": "30"},
                {"Name": "Bob", "Age": "25"}
            ],
            "question": "what is their total age?"
        }
        ' | jq
        ```

        ```bash
        /usr/bin/curl -X POST localhost:3000/api/v1/answer \
            -H "Content-Type: application/json" \
            -d '{
            "data": {"Actors": ["Brad Pitt", "Leonardo Di Caprio", "George Clooney"], "Number of movies": ["87", "53", "69"]},
            "question": "how many movies does Leonardo Di Caprio have?"
        }
        ' | jq
        ```
        """
        data = cherrypy.request.json
        question = data.get("question")

        model_type = "traditional"
        if "tapas" in self.model_name.lower():
            model_type = "tapas"
        elif "tapex" in self.model_name.lower():
            model_type = "tapex"

        if model_type in ["tapas", "tapex"]:
            table = data.get("data")
            return {
                "data": table,
                "question": question,
                "answer": self.answer_table_question(table, question, model_type),
            }
        else:
            context = data.get("data")
            return {
                "data": context,
                "question": question,
                "answer": self.answer_text_question(context, question),
            }

    def answer_table_question(self, data: Dict[str, Any], question: str, model_type: str) -> dict:
        """
        Answers a question based on the provided table.

        Args:
            data (Dict[str, Any]): The table data and other parameters.
            question (str): The question to be answered.
            model_type (str): The type of the model ('tapas' or 'tapex').

        Returns:
            str: The answer derived from the table.
        """

        table = pd.DataFrame.from_dict(data)
        if model_type == "tapas":
            inputs = self.tokenizer(table=table, queries=[question], padding="max_length", return_tensors="pt")

            if next(self.model.parameters()).is_cuda:
                inputs = {k: v.cuda() for k, v in inputs.items()}
            outputs = self.model(**inputs)

            # Decode the predicted tokens
            if hasattr(outputs, "logits_aggregation") and outputs.logits_aggregation is not None:
                (
                    predicted_answer_coordinates,
                    predicted_aggregation_indices,
                ) = self.tokenizer.convert_logits_to_predictions(
                    {k: v.cpu() for k, v in inputs.items()},
                    outputs.logits.detach().cpu(),
                    outputs.logits_aggregation.detach().cpu(),
                )
            else:
                predicted_answer_coordinates = self.tokenizer.convert_logits_to_predictions(
                    {k: v.cpu() for k, v in inputs.items()},
                    outputs.logits.detach().cpu(),
                )
                predicted_aggregation_indices = None

            cell_answers = [self._convert_coordinates_to_answer(table, x) for x in predicted_answer_coordinates[0]]
            if type(cell_answers[0]) is list:
                cell_answers = [y for x in cell_answers for y in x]  # type: ignore

            if predicted_aggregation_indices:
                aggregation_answer = self._convert_aggregation_to_answer(predicted_aggregation_indices[0])
            else:
                aggregation_answer = "NONE"
            return {
                "answers": cell_answers,
                "aggregation": aggregation_answer,
            }

        elif model_type == "tapex":
            encoding = self.tokenizer(table, question, return_tensors="pt")
            if next(self.model.parameters()).is_cuda:
                encoding = {k: v.cuda() for k, v in encoding.items()}

            outputs = self.model.generate(**encoding)
            answers = self.tokenizer.batch_decode(outputs, skip_special_tokens=True)
            return {
                "answers": answers,
                "aggregation": "NONE",
            }
        else:
            raise ValueError("Unsupported model type for table-based QA.")

    def _convert_aggregation_to_answer(self, aggregation_index: int) -> str:
        """
        Converts the aggregation index predicted by TAPAS into an aggregation operation.

        Args:
            aggregation_index (int): The index of the aggregation operation.

        Returns:
            str: The string representation of the aggregation operation.
        """
        aggregation_operations = {
            0: "NONE",
            1: "SUM",
            2: "AVERAGE",
            3: "COUNT",
            4: "MIN",
            5: "MAX",
            6: "OR",
            7: "AND",
            8: "CONCAT",
            9: "FIRST",
            10: "LAST",
        }
        return aggregation_operations.get(aggregation_index, "NONE")

    def _convert_coordinates_to_answer(self, table: pd.DataFrame, coordinates: Any) -> List[str]:
        """
        Converts the coordinates predicted by TAPAS into an answer string.

        Args:
            table (pd.DataFrame): The table used for the QA.
            coordinates (Any): The coordinates of the cells predicted as part of the answer.

        Returns:
            List[str]: The answer strings.
        """
        if type(coordinates) is tuple:
            coordinates = [coordinates]
        return [table.iat[coord] for coord in coordinates]

    def answer_text_question(self, context: str, question: str) -> dict:
        inputs = self.tokenizer.encode_plus(question, context, add_special_tokens=True, return_tensors="pt")
        input_ids = inputs["input_ids"].tolist()[0]

        if next(self.model.parameters()).is_cuda:
            inputs = {k: v.cuda() for k, v in inputs.items()}

        outputs = self.model(**inputs)
        answer_start_scores, answer_end_scores = outputs.start_logits, outputs.end_logits

        answer_start = int(torch.argmax(answer_start_scores))
        answer_end = int(torch.argmax(answer_end_scores) + 1)

        answer = self.tokenizer.convert_tokens_to_string(
            self.tokenizer.convert_ids_to_tokens(input_ids[answer_start:answer_end])
        )

        return {
            "answers": [answer],
            "aggregation": "NONE",
        }

    def initialize_pipeline(self):
        """
        Lazy initialization of the QA Hugging Face pipeline.
        """
        self.model_type = "traditional"  # Default model type

        if "tapas" in self.model_name.lower():
            self.model_type = "tapas"
        elif "tapex" in self.model_name.lower():
            self.model_type = "tapex"

        if not self.hf_pipeline:
            if self.model_type == "tapas" or self.model_type == "tapex":
                model = AutoModelForTableQuestionAnswering.from_pretrained(self.model_name)
            else:
                model = AutoModelForQuestionAnswering.from_pretrained(self.model_name)

            tokenizer = AutoTokenizer.from_pretrained(self.model_name)

            if self.model_type == "tapas" or self.model_type == "tapex":
                self.hf_pipeline = pipeline("table-question-answering", model=model, tokenizer=tokenizer)
            else:
                self.hf_pipeline = pipeline("question-answering", model=model, tokenizer=tokenizer)

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    @cherrypy.tools.allow(methods=["POST"])
    def answer_pipeline(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Answers questions using the Hugging Face pipeline based on the provided context.

        Args:
            **kwargs (Any): Arbitrary keyword arguments, typically containing 'question' and 'data'.

        Returns:
            Dict[str, Any]: A dictionary containing the question, context, and the answer.

        Example CURL Request for QA:
        ```bash
        curl -X POST localhost:3000/api/v1/answer_pipeline \
            -H "Content-Type: application/json" \
            -d '{"question": "Who is the CEO of Tesla?", "data": "Elon Musk is the CEO of Tesla."}'
        ```
        """
        self.initialize_pipeline()  # Initialize the pipeline on first API hit

        data = cherrypy.request.json
        question = data.get("question")

        if self.model_type in ["tapas", "tapex"]:
            table = data.get("data")
            result = self.hf_pipeline(table=table, query=question)  # type: ignore
        else:
            context = data.get("data")
            result = self.hf_pipeline(question=question, context=context)  # type: ignore

        return {"question": question, "data": data.get("data"), "answer": result}
