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

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Iterator, Optional

import cherrypy
import llama_cpp
from geniusrise import BatchInput, BatchOutput, State
from geniusrise.logging import setup_logger
from vllm.entrypoints.openai.protocol import CompletionRequest
from vllm.entrypoints.openai.serving_completion import OpenAIServingCompletion

from geniusrise.inference.text.base import TextAPI


class LanguageModelAPI(TextAPI):
    r"""
    LanguageModelAPI is a class for interacting with pre-trained language models to generate text. It allows for
    customizable text generation via a CherryPy web server, handling requests and generating responses using
    a specified language model. This class is part of the GeniusRise ecosystem for facilitating NLP tasks.

    Attributes:
        model (Any): The loaded language model used for text generation.
        tokenizer (Any): The tokenizer corresponding to the language model, used for processing input text.

    Methods:
        complete(**kwargs: Any) -> Dict[str, Any]: Generates text based on provided prompts and model parameters.

    CLI Usage Example:
    ```bash
    genius LanguageModelAPI rise \
        batch \
            --input_folder ./input \
        batch \
            --output_folder ./output \
        none \
        --id mistralai/Mistral-7B-v0.1-lol \
        listen \
            --args \
                model_name="mistralai/Mistral-7B-v0.1" \
                model_class="AutoModelForCausalLM" \
                tokenizer_class="AutoTokenizer" \
                use_cuda=True \
                precision="float16" \
                quantization=0 \
                device_map="auto" \
                max_memory=None \
                torchscript=False \
                endpoint="*" \
                port=3000 \
                cors_domain="http://localhost:3000" \
                username="user" \
                password="password"
    ```

    or using VLLM:
    ```bash
    genius LanguageModelAPI rise \
        batch \
                --input_folder ./input \
        batch \
                --output_folder ./output \
        none \
        --id mistralai/Mistral-7B-v0.1 \
        listen \
            --args \
                model_name="mistralai/Mistral-7B-v0.1" \
                model_class="AutoModelForCausalLM" \
                tokenizer_class="AutoTokenizer" \
                use_cuda=True \
                precision="bfloat16" \
                use_vllm=True \
                vllm_enforce_eager=True \
                vllm_max_model_len=2048 \
                concurrent_queries=False \
                endpoint="*" \
                port=3000 \
                cors_domain="http://localhost:3000" \
                username="user" \
                password="password"
    ```

    or using llama.cpp:
    ```bash
    genius LanguageModelAPI rise \
        batch \
                --input_folder ./input \
        batch \
                --output_folder ./output \
        none \
        listen \
            --args \
                model_name="TheBloke/Mistral-7B-v0.1-GGUF" \
                model_class="AutoModelForCausalLM" \
                tokenizer_class="AutoTokenizer" \
                use_cuda=True \
                use_llama_cpp=True \
                llama_cpp_filename="mistral-7b-v0.1.Q4_K_M.gguf" \
                llama_cpp_n_gpu_layers=35 \
                llama_cpp_n_ctx=32768 \
                concurrent_queries=False \
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
        Initializes the LanguageModelAPI with configurations for the input, output, and state management,
        along with any additional model-specific parameters.

        Args:
            input (BatchInput): The configuration for input data handling.
            output (BatchOutput): The configuration for output data handling.
            state (State): The state management for the API.
            **kwargs (Any): Additional keyword arguments for model configuration and API setup.
        """
        super().__init__(input=input, output=output, state=state)
        self.log = setup_logger(self)
        self.vllm_server: Optional[OpenAIServingCompletion] = None
        self.event_loop: Any = None
        self.executor = ThreadPoolExecutor(max_workers=4)

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    @cherrypy.tools.allow(methods=["POST"])
    def complete(self, **kwargs: Any) -> Dict[str, Any]:
        r"""
        Handles POST requests to generate text based on a given prompt and model-specific parameters. This method
        is exposed as a web endpoint through CherryPy and returns a JSON response containing the original prompt,
        the generated text, and any additional returned information from the model.

        Args:
            **kwargs (Any): Arbitrary keyword arguments containing the prompt, and any additional parameters
            for the text generation model.

        Returns:
            Dict[str, Any]: A dictionary with the original prompt, generated text, and other model-specific information.

        Example CURL Request:
        ```bash
        /usr/bin/curl -X POST localhost:3000/api/v1/complete \
            -H "Content-Type: application/json" \
            -d '{
                "prompt": "Below is an instruction that describes a task. Write a response that appropriately completes the request.\n\n### Instruction:\nWrite a PRD for Oauth auth using keycloak\n\n### Response:",
                "decoding_strategy": "generate",
                "max_new_tokens": 1024,
                "do_sample": true
            }' | jq
        ```
        """
        data = cherrypy.request.json
        prompt = data.get("prompt")
        decoding_strategy = data.get("decoding_strategy", "generate")

        data = data
        if "decoding_strategy" in data:
            del data["decoding_strategy"]
        if "prompt" in data:
            del data["prompt"]

        return {
            "prompt": prompt,
            "args": data,
            "completion": self.generate(prompt=prompt, decoding_strategy=decoding_strategy, **data),
        }

    def initialize_vllm(self):
        self.vllm_server = OpenAIServingCompletion(engine=self.model, served_model=self.model_name)
        self.event_loop = asyncio.new_event_loop()

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    @cherrypy.tools.allow(methods=["POST"])
    def complete_vllm(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Handles POST requests to generate chat completions using the VLLM (Versatile Language Learning Model) engine.
        This method accepts various parameters for customizing the chat completion request, including message content,
        generation settings, and more.

        Parameters:
        - **kwargs (Any): Arbitrary keyword arguments. Expects data in JSON format containing any of the following keys:
            - messages (Union[str, List[Dict[str, str]]]): The messages for the chat context.
            - temperature (float, optional): The sampling temperature. Defaults to 0.7.
            - top_p (float, optional): The nucleus sampling probability. Defaults to 1.0.
            - n (int, optional): The number of completions to generate. Defaults to 1.
            - max_tokens (int, optional): The maximum number of tokens to generate.
            - stop (Union[str, List[str]], optional): Stop sequence to end generation.
            - stream (bool, optional): Whether to stream the response. Defaults to False.
            - presence_penalty (float, optional): The presence penalty. Defaults to 0.0.
            - frequency_penalty (float, optional): The frequency penalty. Defaults to 0.0.
            - logit_bias (Dict[str, float], optional): Adjustments to the logits of specified tokens.
            - user (str, optional): An identifier for the user making the request.
            - (Additional model-specific parameters)

        Returns:
        Dict[str, Any]: A dictionary with the chat completion response or an error message.

        Example CURL Request:
        ```bash
        curl -v -X POST "http://localhost:3000/api/v1/complete_vllm" \
            -H "Content-Type: application/json" \
            -u "user:password" \
            -d '{
                "messages": ["Whats the weather like in London?"],
                "temperature": 0.7,
                "top_p": 1.0,
                "n": 1,
                "max_tokens": 50,
                "stream": false,
                "presence_penalty": 0.0,
                "frequency_penalty": 0.0,
                "logit_bias": {},
                "user": "example_user"
            }'
        ```
        This request asks the VLLM engine to generate a completion for the provided chat context, with specified generation settings.
        """
        # Extract data from the POST request
        data = cherrypy.request.json

        # Initialize VLLM server with chat template and response role if not already initialized
        if not hasattr(self, "vllm_server") or self.vllm_server is None:
            self.initialize_vllm()

        # Prepare the chat completion request
        chat_request = CompletionRequest(
            model=self.model_name,
            prompt=data.get("messages"),
            temperature=data.get("temperature", 0.7),
            top_p=data.get("top_p", 1.0),
            n=data.get("n", 1),
            max_tokens=data.get("max_tokens"),
            stop=data.get("stop", []),
            stream=data.get("stream", False),
            logprobs=data.get("logprobs", None),
            presence_penalty=data.get("presence_penalty", 0.0),
            frequency_penalty=data.get("frequency_penalty", 0.0),
            logit_bias=data.get("logit_bias", {}),
            user=data.get("user"),
            best_of=data.get("best_of"),
            top_k=data.get("top_k", -1),
            ignore_eos=data.get("ignore_eos", False),
            use_beam_search=data.get("use_beam_search", False),
            stop_token_ids=data.get("stop_token_ids", []),
            skip_special_tokens=data.get("skip_special_tokens", True),
            spaces_between_special_tokens=data.get("spaces_between_special_tokens", True),
            echo=data.get("echo", False),
            repetition_penalty=data.get("repetition_penalty", 1.0),
            min_p=data.get("min_p", 0.0),
            include_stop_str_in_output=data.get("include_stop_str_in_output", False),
            length_penalty=data.get("length_penalty", 1.0),
        )

        # Generate chat completion using the VLLM engine
        try:

            class DummyObject:
                async def is_disconnected(self):
                    return False

            async def async_call():
                response = await self.vllm_server.create_completion(request=chat_request, raw_request=DummyObject())
                return response

            chat_completion = asyncio.run(async_call())

            return chat_completion.model_dump() if chat_completion else {"error": "Failed to generate lm completion"}
        except Exception as e:
            self.log.exception("Error generating chat completion: %s", str(e))
            raise e

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    @cherrypy.tools.allow(methods=["POST"])
    def complete_llama_cpp(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Handles POST requests to generate chat completions using the llama.cpp engine. This method accepts various
        parameters for customizing the chat completion request, including messages, sampling settings, and more.

        Args:
            prompt: The prompt to generate text from.
            suffix: A suffix to append to the generated text. If None, no suffix is appended.
            max_tokens: The maximum number of tokens to generate. If max_tokens <= 0 or None, the maximum number of tokens to generate is unlimited and depends on n_ctx.
            temperature: The temperature to use for sampling.
            top_p: The top-p value to use for nucleus sampling. Nucleus sampling described in academic paper "The Curious Case of Neural Text Degeneration" https://arxiv.org/abs/1904.09751
            min_p: The min-p value to use for minimum p sampling. Minimum P sampling as described in https://github.com/ggerganov/llama.cpp/pull/3841
            typical_p: The typical-p value to use for sampling. Locally Typical Sampling implementation described in the paper https://arxiv.org/abs/2202.00666.
            logprobs: The number of logprobs to return. If None, no logprobs are returned.
            echo: Whether to echo the prompt.
            stop: A list of strings to stop generation when encountered.
            frequency_penalty: The penalty to apply to tokens based on their frequency in the prompt.
            presence_penalty: The penalty to apply to tokens based on their presence in the prompt.
            repeat_penalty: The penalty to apply to repeated tokens.
            top_k: The top-k value to use for sampling. Top-K sampling described in academic paper "The Curious Case of Neural Text Degeneration" https://arxiv.org/abs/1904.09751
            stream: Whether to stream the results.
            seed: The seed to use for sampling.
            tfs_z: The tail-free sampling parameter. Tail Free Sampling described in https://www.trentonbricken.com/Tail-Free-Sampling/.
            mirostat_mode: The mirostat sampling mode.
            mirostat_tau: The target cross-entropy (or surprise) value you want to achieve for the generated text. A higher value corresponds to more surprising or less predictable text, while a lower value corresponds to less surprising or more predictable text.
            mirostat_eta: The learning rate used to update `mu` based on the error between the target and observed surprisal of the sampled word. A larger learning rate will cause `mu` to be updated more quickly, while a smaller learning rate will result in slower updates.
            model: The name to use for the model in the completion object.
            stopping_criteria: A list of stopping criteria to use.
            logits_processor: A list of logits processors to use.
            grammar: A grammar to use for constrained sampling.
            logit_bias: A logit bias to use.

        Returns:
            Dict[str, Any]: A dictionary containing the chat completion response or an error message.

        Example CURL Request:
        ```bash
        curl -X POST "http://localhost:3001/api/v1/complete_llama_cpp" \
            -H "Content-Type: application/json" \
            -d '{
                "prompt": "Whats the weather like in London?",
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_tokens": 50,
                "repeat_penalty": 1.1
            }'
        ```
        """
        # Ensure llama.cpp model and necessary configurations are loaded and initialized
        if not self.model or not isinstance(self.model, llama_cpp.Llama):
            raise ValueError(
                "llama.cpp model is not initialized. Please initialize the model before using chat_llama_cpp."
            )

        # Extract data from the POST request
        data = cherrypy.request.json

        # Convert the request data to the format expected by llama.cpp's create_chat_completion method
        try:
            response = self.model.create_completion(
                prompt=data.get("prompt"),
                suffix=data.get("suffix", None),
                max_tokens=data.get("max_tokens", 16),
                temperature=data.get("temperature", 0.8),
                top_p=data.get("top_p", 0.95),
                min_p=data.get("min_p", 0.05),
                typical_p=data.get("typical_p", 1.0),
                logprobs=data.get("logprobs", None),
                echo=data.get("echo", False),
                stop=data.get("stop", []),
                frequency_penalty=data.get("frequency_penalty", 0.0),
                presence_penalty=data.get("presence_penalty", 0.0),
                repeat_penalty=data.get("repeat_penalty", 1.1),
                top_k=data.get("top_k", 40),
                # stream=data.get("stream", False),
                seed=data.get("seed", None),
                tfs_z=data.get("tfs_z", 1.0),
                mirostat_mode=data.get("mirostat_mode", 0),
                mirostat_tau=data.get("mirostat_tau", 5.0),
                mirostat_eta=data.get("mirostat_eta", 0.1),
                model=data.get("model", None),
                stopping_criteria=data.get("stopping_criteria", None),
                logits_processor=data.get("logits_processor", None),
                grammar=data.get("grammar", None),
                logit_bias=data.get("logit_bias", None),
            )
        except Exception as e:
            self.log.exception("Error generating chat completion using llama.cpp: %s", str(e))
            return {"error": str(e)}

        # Return the generated chat completion or stream of completions
        return response if not isinstance(response, Iterator) else list(response)
