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

from typing import Any, Dict, Optional

import cherrypy
from sentence_transformers import SentenceTransformer

from geniusrise.inference.text.base import TextAPI
from geniusrise.inference.text.utils.embeddings import (
    generate_combination_embeddings,
    generate_contiguous_embeddings,
    generate_embeddings,
    generate_permutation_embeddings,
    generate_sentence_transformer_embeddings,
)


class EmbeddingsAPI(TextAPI):
    r"""
    A CherryPy API for generating various types of embeddings using Hugging Face and Sentence Transformer models.

    This API exposes endpoints for generating embeddings using Sentence-BERT, as well as Hugging Face models.
    It supports generating embeddings for individual terms, contiguous subsets of words, combinations of words,
    and permutations of words in a given sentence.

    Args:
        Inherits all arguments from TextAPI.

    CLI Usage:

    ```bash
    genius EmbeddingsAPI rise \
        listen \
            --model_name=bert-base-uncased \
            --model_class=AutoModelForCausalLM \
            --tokenizer_class=AutoTokenizer \
            --sentence_transformer_model=paraphrase-MiniLM-L6-v2 \
            --use_cuda=True \
            --precision=float16 \
            --device_map=auto \
            --max_memory={0: "24GB"} \
            --torchscript=True \
            --endpoint="*" \
            --port=3000 \
            --cors_domain="http://localhost:3000"
    ```

    YAML Configuration:

    ```yaml
    version: "1"
    bolts:
        my_embeddings_api:
            name: "EmbeddingsAPI"
            method: "listen"
            args:
                model_name: "bert-base-uncased"
                model_class: "AutoModelForCausalLM"
                tokenizer_class: "AutoTokenizer"
                sentence_transformer_model: "paraphrase-MiniLM-L6-v2"
                use_cuda: True
                precision: "float16"
                device_map: "auto"
                max_memory: {0: "24GB"}
                torchscript: True
                endpoint: "*"
                port: 3000
                cors_domain: "http://localhost:3000"
    ```

    Supported Endpoints:
    - POST /sbert_embeddings: Generate embeddings using Sentence-BERT.
    - POST /embeddings: Generate embeddings for a given term.
    - POST /embeddings_contiguous: Generate embeddings for contiguous subsets of words.
    - POST /embeddings_combinations: Generate embeddings for combinations of words.
    - POST /embeddings_permutations: Generate embeddings for permutations of words.
    """

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    @cherrypy.tools.allow(methods=["POST"])
    def sbert(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Generate embeddings using Sentence-BERT model.

        Parameters:
        - **kwargs (Any): Additional keyword arguments.

        Returns:
        Dict[str, Any]: A dictionary containing the generated embeddings.

        Usage:
        POST request with JSON payload containing 'sentences' and optional 'batch_size'.
        """
        data = cherrypy.request.json
        sentences = data.get("sentences")
        batch_size = data.get("batch_size", 32)

        embeddings = generate_sentence_transformer_embeddings(
            sentences=sentences, model=self.sentence_transformer_model, use_cuda=self.use_cuda, batch_size=batch_size
        )
        return {"embeddings": embeddings.tolist()}

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    @cherrypy.tools.allow(methods=["POST"])
    def sentence(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Generate embeddings for a given term using Hugging Face model.

        Parameters:
        - **kwargs (Any): Additional keyword arguments.

        Returns:
        Dict[str, Any]: A dictionary containing the generated embeddings.

        Usage:
        POST request with JSON payload containing 'term'.
        """
        data = cherrypy.request.json
        sentence = data.get("sentence")

        embeddings = generate_embeddings(
            sentence=sentence,
            model=self.model,
            tokenizer=self.tokenizer,
            output_key="last_hidden_state",
            use_cuda=self.use_cuda,
        )
        return {"embeddings": embeddings.tolist()}

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    @cherrypy.tools.allow(methods=["POST"])
    def sentence_windows(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Generate embeddings for all contiguous subsets of words in a given sentence.

        Parameters:
        - **kwargs (Any): Additional keyword arguments.

        Returns:
        Dict[str, Any]: A dictionary containing the generated embeddings.

        Usage:
        POST request with JSON payload containing 'sentence'.
        """
        data = cherrypy.request.json
        sentence = data.get("sentence")

        embeddings = generate_contiguous_embeddings(
            sentence=sentence,
            model=self.model,
            tokenizer=self.tokenizer,
            output_key="last_hidden_state",
            use_cuda=self.use_cuda,
        )
        return {"embeddings": embeddings}

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    @cherrypy.tools.allow(methods=["POST"])
    def sentence_combinations(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Generate embeddings for all combinations of words in a given sentence.

        Parameters:
        - **kwargs (Any): Additional keyword arguments.

        Returns:
        Dict[str, Any]: A dictionary containing the generated embeddings.

        Usage:
        POST request with JSON payload containing 'sentence'.
        """
        data = cherrypy.request.json
        sentence = data.get("sentence")

        embeddings = generate_combination_embeddings(
            sentence=sentence,
            model=self.model,
            tokenizer=self.tokenizer,
            output_key="last_hidden_state",
            use_cuda=self.use_cuda,
        )
        return {"embeddings": embeddings}

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    @cherrypy.tools.allow(methods=["POST"])
    def sentence_permutations(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Generate embeddings for all permutations of words in a given sentence.

        Parameters:
        - **kwargs (Any): Additional keyword arguments.

        Returns:
        Dict[str, Any]: A dictionary containing the generated embeddings.

        Usage:
        POST request with JSON payload containing 'sentence'.
        """
        data = cherrypy.request.json
        sentence = data.get("sentence")

        embeddings = generate_permutation_embeddings(
            sentence=sentence,
            model=self.model,
            tokenizer=self.tokenizer,
            output_key="last_hidden_state",
            use_cuda=self.use_cuda,
        )
        return {"embeddings": embeddings}

    def listen(  # type: ignore
        self,
        model_name: str,
        model_class: str = "AutoModelForCausalLM",
        tokenizer_class: str = "AutoTokenizer",
        use_cuda: bool = False,
        precision: str = "float16",
        quantization: int = 0,
        device_map: str | Dict | None = "auto",
        max_memory={0: "24GB"},
        torchscript: bool = False,
        compile: bool = False,
        endpoint: str = "*",
        port: int = 3000,
        cors_domain: str = "http://localhost:3000",
        username: Optional[str] = None,
        password: Optional[str] = None,
        **model_args: Any,
    ) -> None:
        """
        Initialize and start the API server.

        Parameters:
        - model_name (str): The name of the Hugging Face model to use.
        - model_class (str, optional): The class name of the model. Defaults to "AutoModelForCausalLM".
        - tokenizer_class (str, optional): The class name of the tokenizer. Defaults to "AutoTokenizer".
        - sentence_transformer_model (str, optional): The name of the Sentence Transformer model to use. Defaults to "paraphrase-MiniLM-L6-v2".
        - use_cuda (bool, optional): Whether to use CUDA for computation. Defaults to False.
        - precision (str, optional): The precision to use for computations. Defaults to "float16".
        - device_map (str | Dict | None, optional): The device map for distributed training. Defaults to "auto".
        - max_memory (Dict, optional): The maximum memory to allocate for each device. Defaults to {0: "24GB"}.
        - torchscript (bool, optional): Whether to use TorchScript. Defaults to True.
        - endpoint (str, optional): The API endpoint. Defaults to "*".
        - port (int, optional): The port to listen on. Defaults to 3000.
        - cors_domain (str, optional): The CORS domain. Defaults to "http://localhost:3000".
        - username (str, optional): The username for authentication. Defaults to None.
        - password (str, optional): The password for authentication. Defaults to None.
        - **model_args (Any): Additional arguments for the model.

        Returns:
        None
        """
        self.model_name = model_name
        self.model_class = model_class
        self.tokenizer_class = tokenizer_class
        self.use_cuda = use_cuda
        self.quantization = quantization
        self.precision = precision
        self.device_map = device_map
        self.max_memory = max_memory
        self.torchscript = torchscript
        self.model_args = model_args

        if ":" in model_name:
            model_revision = model_name.split(":")[1]
            tokenizer_revision = model_name.split(":")[1]
            model_name = model_name.split(":")[0]
            tokenizer_name = model_name
        else:
            model_revision = None
            tokenizer_revision = None
            tokenizer_name = model_name
        self.model_name = model_name
        self.model_revision = model_revision
        self.tokenizer_name = tokenizer_name
        self.tokenizer_revision = tokenizer_revision

        self.model, self.tokenizer = self.load_models(
            model_name=self.model_name,
            tokenizer_name=self.tokenizer_name,
            model_revision=self.model_revision,
            tokenizer_revision=self.tokenizer_revision,
            model_class=self.model_class,
            tokenizer_class=self.tokenizer_class,
            use_cuda=self.use_cuda,
            precision=self.precision,
            quantization=self.quantization,
            device_map=self.device_map,
            max_memory=self.max_memory,
            torchscript=self.torchscript,
            **self.model_args,
        )
        self.sentence_transformer_model = SentenceTransformer(model_name, device="cuda" if use_cuda else "cpu")

        def CORS():
            cherrypy.response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
            cherrypy.response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            cherrypy.response.headers["Access-Control-Allow-Headers"] = "Content-Type"
            cherrypy.response.headers["Access-Control-Allow-Credentials"] = "true"

            if cherrypy.request.method == "OPTIONS":
                cherrypy.response.status = 200
                return True

        cherrypy.config.update(
            {
                "server.socket_host": "0.0.0.0",
                "server.socket_port": port,
                "log.screen": False,
                "tools.CORS.on": True,
            }
        )

        cherrypy.tools.CORS = cherrypy.Tool("before_handler", CORS)
        cherrypy.tree.mount(self, "/api/v1/", {"/": {"tools.CORS.on": True}})
        cherrypy.tools.CORS = cherrypy.Tool("before_finalize", CORS)
        cherrypy.engine.start()
        cherrypy.engine.block()
