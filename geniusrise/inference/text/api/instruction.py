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
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from vllm.entrypoints.openai.protocol import ChatCompletionRequest
from vllm.entrypoints.openai.serving_chat import OpenAIServingChat

from geniusrise.inference.text.base import TextAPI


class InstructionAPI(TextAPI):
    r"""
    InstructionAPI is designed for generating text based on prompts using instruction-tuned language models.
    It serves as an interface to Hugging Face's pre-trained instruction-tuned models, providing a flexible API
    for various text generation tasks. It can be used in scenarios ranging from generating creative content to
    providing instructions or answers based on the prompts.

    Attributes:
        model (Any): The loaded instruction-tuned language model.
        tokenizer (Any): The tokenizer for processing text suitable for the model.

    Methods:
        complete(**kwargs: Any) -> Dict[str, Any]:
            Generates text based on the given prompt and decoding strategy.

        listen(**model_args: Any) -> None:
            Starts a server to listen for text generation requests.

    CLI Usage Example:
    ```bash
    genius InstructionAPI rise \
        batch \
            --input_folder ./input \
        batch \
            --output_folder ./output \
        none \
        listen \
            --args \
                model_name="TheBloke/Mistral-7B-OpenOrca-AWQ" \
                model_class="AutoModelForCausalLM" \
                tokenizer_class="AutoTokenizer" \
                use_cuda=True \
                precision="float16" \
                quantization=0 \
                device_map="auto" \
                max_memory=None \
                torchscript=False \
                awq_enabled=True \
                flash_attention=True \
                endpoint="*" \
                port=3001 \
                cors_domain="http://localhost:3000" \
                username="user" \
                password="password"
    ```

    Or using VLLM:
    ```bash
    genius InstructionAPI rise \
        batch \
                --input_folder ./input \
        batch \
                --output_folder ./output \
        none \
        --id mistralai/Mistral-7B-Instruct-v0.1 \
        listen \
            --args \
                model_name="mistralai/Mistral-7B-Instruct-v0.1" \
                model_class="AutoModelForCausalLM" \
                tokenizer_class="AutoTokenizer" \
                use_cuda=True \
                precision="bfloat16" \
                quantization=0 \
                device_map="auto" \
                max_memory=None \
                torchscript=False \
                use_vllm=True \
                vllm_enforce_eager=True \
                vllm_max_model_len=1024 \
                concurrent_queries=False \
                endpoint="*" \
                port=3000 \
                cors_domain="http://localhost:3000" \
                username="user" \
                password="password"
    ```

    or using llama.cpp:
    ```bash
    genius InstructionAPI rise \
        batch \
                --input_folder ./input \
        batch \
                --output_folder ./output \
        none \
        listen \
            --args \
                model_name="TheBloke/Mistral-7B-Instruct-v0.2-GGUF" \
                model_class="AutoModelForCausalLM" \
                tokenizer_class="AutoTokenizer" \
                use_cuda=True \
                use_llama_cpp=True \
                llama_cpp_filename="mistral-7b-instruct-v0.2.Q4_K_M.gguf" \
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
        Initializes a new instance of the InstructionAPI class, setting up the necessary configurations
        for input, output, and state.

        Args:
            input (BatchInput): Configuration for the input data.
            output (BatchOutput): Configuration for the output data.
            state (State): The state of the API.
            **kwargs (Any): Additional keyword arguments for extended functionality.
        """
        super().__init__(input=input, output=output, state=state)
        self.log = setup_logger(self)
        self.hf_pipeline = None
        self.vllm_server: Optional[OpenAIServingChat] = None
        self.event_loop: Any = None
        self.executor = ThreadPoolExecutor(max_workers=4)

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    @cherrypy.tools.allow(methods=["POST"])
    def complete(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Handles POST requests to generate text based on the given prompt and decoding strategy. It uses the pre-trained
        model specified in the setup to generate a completion for the input prompt.

        Args:
            **kwargs (Any): Arbitrary keyword arguments containing the 'prompt' and other parameters for text generation.

        Returns:
            Dict[str, Any]: A dictionary containing the original prompt and the generated completion.

        Example CURL Requests:
        ```bash
        /usr/bin/curl -X POST localhost:3001/api/v1/complete \
            -H "Content-Type: application/json" \
            -d '{
                "prompt": "<|system|>\n<|end|>\n<|user|>\nHow do I sort a list in Python?<|end|>\n<|assistant|>",
                "decoding_strategy": "generate",
                "max_new_tokens": 100,
                "do_sample": true,
                "temperature": 0.7,
                "top_k": 50,
                "top_p": 0.95
            }' | jq
        ```
        """
        data = cherrypy.request.json
        prompt = data.get("prompt")
        decoding_strategy = data.get("decoding_strategy", "generate")

        generation_params = data
        if "decoding_strategy" in generation_params:
            del generation_params["decoding_strategy"]
        if "prompt" in generation_params:
            del generation_params["prompt"]

        return {
            "prompt": prompt,
            "args": data,
            "completion": self.generate(prompt=prompt, decoding_strategy=decoding_strategy, **generation_params),
        }

    def initialize_pipeline(self):
        """
        Lazy initialization of the Hugging Face pipeline for chat interaction.
        """
        if not self.hf_pipeline:
            model = AutoModelForCausalLM.from_pretrained(self.model_name)
            tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            if self.use_cuda:
                model.cuda()
            self.hf_pipeline = pipeline("conversational", model=model, tokenizer=tokenizer)

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    @cherrypy.tools.allow(methods=["POST"])
    def chat(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Handles chat interaction using the Hugging Face pipeline. This method enables conversational text generation,
        simulating a chat-like interaction based on user and system prompts.

        Args:
            **kwargs (Any): Arbitrary keyword arguments containing 'user_prompt' and 'system_prompt'.

        Returns:
            Dict[str, Any]: A dictionary containing the user prompt, system prompt, and chat interaction results.

        Example CURL Request for chat interaction:
        ```bash
        /usr/bin/curl -X POST localhost:3001/api/v1/chat \
            -H "Content-Type: application/json" \
            -d '{
                "user_prompt": "What is the capital of France?",
                "system_prompt": "The capital of France is"
            }' | jq
        ```
        """
        self.initialize_pipeline()  # Initialize the pipeline on first API hit

        data = cherrypy.request.json
        user_prompt = data.get("user_prompt")
        system_prompt = data.get("system_prompt")

        result = self.hf_pipeline(user_prompt, system_prompt)  # type: ignore

        return {"user_prompt": user_prompt, "system_prompt": system_prompt, "result": result}

    def initialize_vllm(self, chat_template: str, response_role: str = "assistant"):
        self.vllm_server = OpenAIServingChat(
            engine=self.model, served_model=self.model_name, response_role=response_role, chat_template=chat_template
        )
        self.event_loop = asyncio.new_event_loop()

    @cherrypy.expose(["completions"])
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    @cherrypy.tools.allow(methods=["POST"])
    def chat_vllm(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Handles POST requests to generate chat completions using the VLLM (Versatile Language Learning Model) engine.
        This method accepts various parameters for customizing the chat completion request, including message content,
        generation settings, and more.

        Args:
            messages (List[Dict[str, str]]): The chat messages for generating a response. Each message should include a 'role' (either 'user' or 'system') and 'content'.
            temperature (float, optional): The sampling temperature. Defaults to 0.7. Higher values generate more random completions.
            top_p (float, optional): The nucleus sampling probability. Defaults to 1.0. A smaller value leads to higher diversity.
            n (int, optional): The number of completions to generate. Defaults to 1.
            max_tokens (int, optional): The maximum number of tokens to generate. Controls the length of the generated response.
            stop (Union[str, List[str]], optional): Sequence(s) where the generation should stop. Can be a single string or a list of strings.
            stream (bool, optional): Whether to stream the response. Streaming may be useful for long completions.
            presence_penalty (float, optional): Adjusts the likelihood of tokens based on their presence in the conversation so far. Defaults to 0.0.
            frequency_penalty (float, optional): Adjusts the likelihood of tokens based on their frequency in the conversation so far. Defaults to 0.0.
            logit_bias (Dict[str, float], optional): Adjustments to the logits of specified tokens, identified by token IDs as keys and adjustment values as values.
            user (str, optional): An identifier for the user making the request. Can be used for logging or customization.
            best_of (int, optional): Generates 'n' completions server-side and returns the best one. Higher values incur more computation cost.
            top_k (int, optional): Filters the generated tokens to the top-k tokens with the highest probabilities. Defaults to -1, which disables top-k filtering.
            ignore_eos (bool, optional): Whether to ignore the end-of-sentence token in generation. Useful for more fluid continuations.
            use_beam_search (bool, optional): Whether to use beam search instead of sampling for generation. Beam search can produce more coherent results.
            stop_token_ids (List[int], optional): List of token IDs that should cause generation to stop.
            skip_special_tokens (bool, optional): Whether to skip special tokens (like padding or end-of-sequence tokens) in the output.
            spaces_between_special_tokens (bool, optional): Whether to insert spaces between special tokens in the output.
            add_generation_prompt (bool, optional): Whether to prepend the generation prompt to the output.
            echo (bool, optional): Whether to include the input prompt in the output.
            repetition_penalty (float, optional): Penalty applied to tokens that have been generated previously. Defaults to 1.0, which applies no penalty.
            min_p (float, optional): Sets a minimum threshold for token probabilities. Tokens with probabilities below this threshold are filtered out.
            include_stop_str_in_output (bool, optional): Whether to include the stop string(s) in the output.
            length_penalty (float, optional): Exponential penalty to the length for beam search. Only relevant if use_beam_search is True.

        Returns:
        Dict[str, Any]: A dictionary with the chat completion response or an error message.

        Example CURL Request:
        ```bash
        curl -X POST "http://localhost:3000/api/v1/chat_vllm" \
            -H "Content-Type: application/json" \
            -d '{
                "messages": [
                    {"role": "user", "content": "Whats the weather like in London?"}
                ],
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
        response_role = data.get("response_role", "assistant")
        chat_template = data.get("chat_template", None)

        # Initialize VLLM server with chat template and response role if not already initialized
        if not hasattr(self, "vllm_server") or self.vllm_server is None:
            self.initialize_vllm(chat_template=chat_template, response_role=response_role)

        # Prepare the chat completion request
        chat_request = ChatCompletionRequest(
            model=self.model_name,
            messages=data.get("messages"),
            temperature=data.get("temperature", 0.7),
            top_p=data.get("top_p", 1.0),
            n=data.get("n", 1),
            max_tokens=data.get("max_tokens"),
            stop=data.get("stop", []),
            # stream=data.get("stream", False),
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
            add_generation_prompt=data.get("add_generation_prompt", True),
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
                response = await self.vllm_server.create_chat_completion(
                    request=chat_request, raw_request=DummyObject()
                )
                return response

            chat_completion = asyncio.run(async_call())

            return chat_completion.model_dump() if chat_completion else {"error": "Failed to generate chat completion"}
        except Exception as e:
            self.log.exception("Error generating chat completion: %s", str(e))
            raise e

    @cherrypy.expose(["completion"])
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    @cherrypy.tools.allow(methods=["POST"])
    def chat_llama_cpp(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Handles POST requests to generate chat completions using the llama.cpp engine. This method accepts various
        parameters for customizing the chat completion request, including messages, sampling settings, and more.

        Args:
            messages (List[Dict[str, str]]): The chat messages for generating a response.
            functions (Optional[List[Dict]]): A list of functions to use for the chat completion (advanced usage).
            function_call (Optional[Dict]): A function call to use for the chat completion (advanced usage).
            tools (Optional[List[Dict]]): A list of tools to use for the chat completion (advanced usage).
            tool_choice (Optional[Dict]): A tool choice option for the chat completion (advanced usage).
            temperature (float): The temperature to use for sampling, controlling randomness.
            top_p (float): The nucleus sampling's top-p parameter, controlling diversity.
            top_k (int): The top-k sampling parameter, limiting the token selection pool.
            min_p (float): The minimum probability threshold for sampling.
            typical_p (float): The typical-p parameter for locally typical sampling.
            stream (bool): Flag to stream the results.
            stop (Optional[Union[str, List[str]]]): Tokens or sequences where generation should stop.
            seed (Optional[int]): Seed for random number generation to ensure reproducibility.
            response_format (Optional[Dict]): Specifies the format of the generated response.
            max_tokens (Optional[int]): Maximum number of tokens to generate.
            presence_penalty (float): Penalty for token presence to discourage repetition.
            frequency_penalty (float): Penalty for token frequency to discourage common tokens.
            repeat_penalty (float): Penalty applied to tokens that are repeated.
            tfs_z (float): Tail-free sampling parameter to adjust the likelihood of tail tokens.
            mirostat_mode (int): Mirostat sampling mode for dynamic adjustments.
            mirostat_tau (float): Tau parameter for mirostat sampling, controlling deviation.
            mirostat_eta (float): Eta parameter for mirostat sampling, controlling adjustment speed.
            model (Optional[str]): Specifies the model to use for generation.
            logits_processor (Optional[List]): List of logits processors for advanced generation control.
            grammar (Optional[Dict]): Specifies grammar rules for the generated text.
            logit_bias (Optional[Dict[str, float]]): Adjustments to the logits of specified tokens.
            logprobs (Optional[bool]): Whether to include log probabilities in the output.
            top_logprobs (Optional[int]): Number of top log probabilities to include.

        Returns:
            Dict[str, Any]: A dictionary containing the chat completion response or an error message.

        Example CURL Request:
        ```bash
        curl -X POST "http://localhost:3000/api/v1/chat_llama_cpp" \
            -H "Content-Type: application/json" \
            -d '{
                "messages": [
                    {"role": "user", "content": "What is the capital of France?"},
                    {"role": "system", "content": "The capital of France is"}
                ],
                "temperature": 0.2,
                "top_p": 0.95,
                "top_k": 40,
                "max_tokens": 50,
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
            handler = self.model.create_chat_completion

            response = (
                self.model.create_chat_completion(
                    messages=data.get("messages", []),
                    functions=data.get("functions"),
                    function_call=data.get("function_call"),
                    tools=data.get("tools"),
                    tool_choice=data.get("tool_choice"),
                    temperature=data.get("temperature", 0.2),
                    top_p=data.get("top_p", 0.95),
                    top_k=data.get("top_k", 40),
                    min_p=data.get("min_p", 0.05),
                    typical_p=data.get("typical_p", 1.0),
                    # stream=data.get("stream", False),
                    stop=data.get("stop", []),
                    seed=data.get("seed"),
                    response_format=data.get("response_format"),
                    max_tokens=data.get("max_tokens"),
                    presence_penalty=data.get("presence_penalty", 0.0),
                    frequency_penalty=data.get("frequency_penalty", 0.0),
                    repeat_penalty=data.get("repeat_penalty", 1.1),
                    tfs_z=data.get("tfs_z", 1.0),
                    mirostat_mode=data.get("mirostat_mode", 0),
                    mirostat_tau=data.get("mirostat_tau", 5.0),
                    mirostat_eta=data.get("mirostat_eta", 0.1),
                    model=data.get("model"),
                    logits_processor=data.get("logits_processor"),
                    grammar=data.get("grammar"),
                    logit_bias=data.get("logit_bias"),
                    logprobs=data.get("logprobs"),
                    top_logprobs=data.get("top_logprobs"),
                )
                if "messages" in data
                else self.model.create_completion(
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
            )
        except Exception as e:
            self.log.exception("Error generating chat completion using llama.cpp: %s", str(e))
            return {"error": str(e)}

        # Return the generated chat completion or stream of completions
        return response if not isinstance(response, Iterator) else list(response)
