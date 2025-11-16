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

import json
import os
import threading
from typing import Any, Dict, List, Optional, Tuple, Union

import boto3
import cherrypy
import llama_cpp
import torch
import transformers
from geniusrise import BatchInput, BatchOutput, State
from geniusrise.logging import setup_logger
from llama_cpp import Llama as LlamaCPP
from optimum.bettertransformer import BetterTransformer
from ray.util.placement_group import PlacementGroup
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BeamSearchScorer,
    LogitsProcessorList,
    MinLengthLogitsProcessor,
)
from transformers.tokenization_utils_base import PreTrainedTokenizerBase
from vllm import LLM, AsyncLLMEngine
from vllm.config import CacheConfig, DeviceConfig, LoRAConfig
from vllm.config import ModelConfig as VLLMModelConfig
from vllm.config import ParallelConfig, SchedulerConfig

# Define a global lock for sequential access control
sequential_lock = threading.Lock()


class TextBulk:
    """
    TextBulk is a foundational class for enabling bulk processing of text with various generation models.
    It primarily focuses on using Hugging Face models to provide a robust and efficient framework for
    large-scale text generation tasks. The class supports various decoding strategies to generate text
    that can be tailored to specific needs or preferences.

    Attributes:
        model (AutoModelForCausalLM): The language model for text generation.
        tokenizer (AutoTokenizer): The tokenizer for preparing input data for the model.

    Args:
        input (BatchInput): Configuration and data inputs for the batch process.
        output (BatchOutput): Configurations for output data handling.
        state (State): State management for the Bolt.
        **kwargs: Arbitrary keyword arguments for extended configurations.

    Methods:
        text(**kwargs: Any) -> Dict[str, Any]:
            Provides an API endpoint for text generation functionality.
            Accepts various parameters for customizing the text generation process.

        generate(prompt: str, decoding_strategy: str = "generate", **generation_params: Any) -> dict:
            Generates text based on the provided prompt and parameters. Supports multiple decoding strategies for diverse applications.

    The class serves as a versatile tool for text generation, supporting various models and configurations.
    It can be extended or used as is for efficient text generation tasks.
    """

    model: Any
    tokenizer: Any

    def __init__(
        self,
        input: BatchInput,
        output: BatchOutput,
        state: State,
        **kwargs,
    ):
        """
        Initializes the TextBulk with configurations and sets up logging. It prepares the environment for text generation tasks.

        Args:
            input (BatchInput): The input data configuration for the text generation task.
            output (BatchOutput): The output data configuration for the results of the text generation.
            state (State): The state configuration for the Bolt, managing its operational status.
            **kwargs: Additional keyword arguments for extended functionality and model configurations.
        """
        self.input = input
        self.output = output
        self.state = state
        self.notification_email = None
        self.log = setup_logger(self)

    def generate(
        self,
        prompt: str,
        decoding_strategy: str = "generate",
        **generation_params: Any,
    ) -> str:
        r"""
        Generate text completion for the given prompt using the specified decoding strategy.

        Args:
            prompt (str): The prompt to generate text completion for.
            decoding_strategy (str, optional): The decoding strategy to use. Defaults to "generate".
            **generation_params (Any): Additional parameters to pass to the decoding strategy.

        Returns:
            str: The generated text completion.

        Raises:
            Exception: If an error occurs during generation.

        Supported decoding strategies and their additional parameters:
            - "generate": Uses the model's default generation method. (Parameters: max_length, num_beams, etc.)
            - "greedy_search": Generates text using a greedy search decoding strategy.
            Parameters: max_length, eos_token_id, pad_token_id, output_attentions, output_hidden_states, output_scores, return_dict_in_generate, synced_gpus.
            - "contrastive_search": Generates text using contrastive search decoding strategy.
            Parameters: top_k, penalty_alpha, pad_token_id, eos_token_id, output_attentions, output_hidden_states, output_scores, return_dict_in_generate, synced_gpus, sequential.
            - "sample": Generates text using a sampling decoding strategy.
            Parameters: do_sample, temperature, top_k, top_p, max_length, pad_token_id, eos_token_id, output_attentions, output_hidden_states, output_scores, return_dict_in_generate, synced_gpus.
            - "beam_search": Generates text using beam search decoding strategy.
            Parameters: num_beams, max_length, pad_token_id, eos_token_id, output_attentions, output_hidden_states, output_scores, return_dict_in_generate, synced_gpus.
            - "beam_sample": Generates text using beam search with sampling decoding strategy.
            Parameters: num_beams, temperature, max_length, pad_token_id, eos_token_id, output_attentions, output_hidden_states, output_scores, return_dict_in_generate, synced_gpus.
            - "group_beam_search": Generates text using group beam search decoding strategy.
            Parameters: num_beams, diversity_penalty, max_length, pad_token_id, eos_token_id, output_attentions, output_hidden_states, output_scores, return_dict_in_generate, synced_gpus.
            - "constrained_beam_search": Generates text using constrained beam search decoding strategy.
            Parameters: num_beams, max_length, constraints, pad_token_id, eos_token_id, output_attentions, output_hidden_states, output_scores, return_dict_in_generate, synced_gpus.

        All generation parameters:
            - max_length: Maximum length the generated tokens can have
            - max_new_tokens: Maximum number of tokens to generate, ignoring prompt tokens
            - min_length: Minimum length of the sequence to be generated
            - min_new_tokens: Minimum number of tokens to generate, ignoring prompt tokens
            - early_stopping: Stopping condition for beam-based methods
            - max_time: Maximum time allowed for computation in seconds
            - do_sample: Whether to use sampling for generation
            - num_beams: Number of beams for beam search
            - num_beam_groups: Number of groups for beam search to ensure diversity
            - penalty_alpha: Balances model confidence and degeneration penalty in contrastive search
            - use_cache: Whether the model should use past key/values attentions to speed up decoding
            - temperature: Modulates next token probabilities
            - top_k: Number of highest probability tokens to keep for top-k-filtering
            - top_p: Smallest set of most probable tokens with cumulative probability >= top_p
            - typical_p: Conditional probability of predicting a target token next
            - epsilon_cutoff: Tokens with a conditional probability > epsilon_cutoff will be sampled
            - eta_cutoff: Eta sampling, a hybrid of locally typical sampling and epsilon sampling
            - diversity_penalty: Penalty subtracted from a beam's score if it generates a token same as any other group
            - repetition_penalty: Penalty for repetition of ngrams
            - encoder_repetition_penalty: Penalty on sequences not in the original input
            - length_penalty: Exponential penalty to the length for beam-based generation
            - no_repeat_ngram_size: All ngrams of this size can only occur once
            - bad_words_ids: List of token ids that are not allowed to be generated
            - force_words_ids: List of token ids that must be generated
            - renormalize_logits: Renormalize the logits after applying all logits processors
            - constraints: Custom constraints for generation
            - forced_bos_token_id: Token ID to force as the first generated token
            - forced_eos_token_id: Token ID to force as the last generated token
            - remove_invalid_values: Remove possible NaN and inf outputs
            - exponential_decay_length_penalty: Exponentially increasing length penalty after a certain number of tokens
            - suppress_tokens: Tokens that will be suppressed during generation
            - begin_suppress_tokens: Tokens that will be suppressed at the beginning of generation
            - forced_decoder_ids: Mapping from generation indices to token indices that will be forced
            - sequence_bias: Maps a sequence of tokens to its bias term
            - guidance_scale: Guidance scale for classifier free guidance (CFG)
            - low_memory: Switch to sequential topk for contrastive search to reduce peak memory
            - num_return_sequences: Number of independently computed returned sequences for each batch element
            - output_attentions: Whether to return the attentions tensors of all layers
            - output_hidden_states: Whether to return the hidden states of all layers
            - output_scores: Whether to return the prediction scores
            - return_dict_in_generate: Whether to return a ModelOutput instead of a plain tuple
            - pad_token_id: The id of the padding token
            - bos_token_id: The id of the beginning-of-sequence token
            - eos_token_id: The id of the end-of-sequence token
            - max_length: The maximum length of the sequence to be generated
            - eos_token_id: End-of-sequence token ID
            - pad_token_id: Padding token ID
            - output_attentions: Return attention tensors of all attention layers if True
            - output_hidden_states: Return hidden states of all layers if True
            - output_scores: Return prediction scores if True
            - return_dict_in_generate: Return a ModelOutput instead of a plain tuple if True
            - synced_gpus: Continue running the while loop until max_length for ZeRO stage 3 if True
            - top_k: Size of the candidate set for re-ranking in contrastive search
            - penalty_alpha: Degeneration penalty; active when larger than 0
            - eos_token_id: End-of-sequence token ID(s)
            - sequential: Switch to sequential topk hidden state computation to reduce memory if True
            - do_sample: Use sampling for generation if True
            - temperature: Temperature for sampling
            - top_p: Cumulative probability for top-p-filtering
            - diversity_penalty: Penalty for reducing similarity across different beam groups
            - constraints: List of constraints to apply during beam search
            - synced_gpus: Whether to continue running the while loop until max_length (needed for ZeRO stage 3)
        """
        results: Dict[int, Dict[str, Union[str, List[str]]]] = {}
        eos_token_id = self.model.config.eos_token_id
        pad_token_id = self.model.config.pad_token_id
        if not pad_token_id:
            pad_token_id = eos_token_id
            self.model.config.pad_token_id = pad_token_id

        # Default parameters for each strategy
        default_params = {
            "generate": {
                "max_length": 20,  # Maximum length the generated tokens can have
                "max_new_tokens": None,  # Maximum number of tokens to generate, ignoring prompt tokens
                "min_length": 0,  # Minimum length of the sequence to be generated
                "min_new_tokens": None,  # Minimum number of tokens to generate, ignoring prompt tokens
                "early_stopping": False,  # Stopping condition for beam-based methods
                "max_time": None,  # Maximum time allowed for computation in seconds
                "do_sample": False,  # Whether to use sampling for generation
                "num_beams": 1,  # Number of beams for beam search
                "num_beam_groups": 1,  # Number of groups for beam search to ensure diversity
                "penalty_alpha": None,  # Balances model confidence and degeneration penalty in contrastive search
                "use_cache": True,  # Whether the model should use past key/values attentions to speed up decoding
                "temperature": 1.0,  # Modulates next token probabilities
                "top_k": 50,  # Number of highest probability tokens to keep for top-k-filtering
                "top_p": 1.0,  # Smallest set of most probable tokens with cumulative probability >= top_p
                "typical_p": 1.0,  # Conditional probability of predicting a target token next
                "epsilon_cutoff": 0.0,  # Tokens with a conditional probability > epsilon_cutoff will be sampled
                "eta_cutoff": 0.0,  # Eta sampling, a hybrid of locally typical sampling and epsilon sampling
                "diversity_penalty": 0.0,  # Penalty subtracted from a beam's score if it generates a token same as any other group
                "repetition_penalty": 1.0,  # Penalty for repetition of ngrams
                "encoder_repetition_penalty": 1.0,  # Penalty on sequences not in the original input
                "length_penalty": 1.0,  # Exponential penalty to the length for beam-based generation
                "no_repeat_ngram_size": 0,  # All ngrams of this size can only occur once
                "bad_words_ids": None,  # List of token ids that are not allowed to be generated
                "force_words_ids": None,  # List of token ids that must be generated
                "renormalize_logits": False,  # Renormalize the logits after applying all logits processors
                "constraints": None,  # Custom constraints for generation
                "forced_bos_token_id": None,  # Token ID to force as the first generated token
                "forced_eos_token_id": None,  # Token ID to force as the last generated token
                "remove_invalid_values": False,  # Remove possible NaN and inf outputs
                "exponential_decay_length_penalty": None,  # Exponentially increasing length penalty after a certain number of tokens
                "suppress_tokens": None,  # Tokens that will be suppressed during generation
                "begin_suppress_tokens": None,  # Tokens that will be suppressed at the beginning of generation
                "forced_decoder_ids": None,  # Mapping from generation indices to token indices that will be forced
                "sequence_bias": None,  # Maps a sequence of tokens to its bias term
                "guidance_scale": None,  # Guidance scale for classifier free guidance (CFG)
                "low_memory": None,  # Switch to sequential topk for contrastive search to reduce peak memory
                "num_return_sequences": 1,  # Number of independently computed returned sequences for each batch element
                "output_attentions": False,  # Whether to return the attentions tensors of all layers
                "output_hidden_states": False,  # Whether to return the hidden states of all layers
                "output_scores": False,  # Whether to return the prediction scores
                "return_dict_in_generate": False,  # Whether to return a ModelOutput instead of a plain tuple
                "pad_token_id": None,  # The id of the padding token
                "bos_token_id": None,  # The id of the beginning-of-sequence token
                "eos_token_id": None,  # The id of the end-of-sequence token
            },
            "greedy_search": {
                "max_length": 4096,  # The maximum length of the sequence to be generated
                "eos_token_id": eos_token_id,  # End-of-sequence token ID
                "pad_token_id": pad_token_id,  # Padding token ID
                "output_attentions": False,  # Return attention tensors of all attention layers if True
                "output_hidden_states": False,  # Return hidden states of all layers if True
                "output_scores": False,  # Return prediction scores if True
                "return_dict_in_generate": False,  # Return a ModelOutput instead of a plain tuple if True
                "synced_gpus": False,  # Continue running the while loop until max_length for ZeRO stage 3 if True
            },
            "contrastive_search": {
                "top_k": 1,  # Size of the candidate set for re-ranking in contrastive search
                "penalty_alpha": 0,  # Degeneration penalty; active when larger than 0
                "pad_token_id": pad_token_id,  # Padding token ID
                "eos_token_id": eos_token_id,  # End-of-sequence token ID(s)
                "output_attentions": False,  # Return attention tensors of all attention layers if True
                "output_hidden_states": False,  # Return hidden states of all layers if True
                "output_scores": False,  # Return prediction scores if True
                "return_dict_in_generate": False,  # Return a ModelOutput instead of a plain tuple if True
                "synced_gpus": False,  # Continue running the while loop until max_length for ZeRO stage 3 if True
                "sequential": False,  # Switch to sequential topk hidden state computation to reduce memory if True
            },
            "sample": {
                "do_sample": True,  # Use sampling for generation if True
                "temperature": 0.6,  # Temperature for sampling
                "top_k": 50,  # Number of highest probability tokens to keep for top-k-filtering
                "top_p": 0.9,  # Cumulative probability for top-p-filtering
                "max_length": 4096,  # The maximum length of the sequence to be generated
                "pad_token_id": pad_token_id,  # Padding token ID
                "eos_token_id": eos_token_id,  # End-of-sequence token ID(s)
                "output_attentions": False,  # Return attention tensors of all attention layers if True
                "output_hidden_states": False,  # Return hidden states of all layers if True
                "output_scores": False,  # Return prediction scores if True
                "return_dict_in_generate": False,  # Return a ModelOutput instead of a plain tuple if True
                "synced_gpus": False,  # Continue running the while loop until max_length for ZeRO stage 3 if True
            },
            "beam_search": {
                "num_beams": 4,  # Number of beams for beam search
                "max_length": 4096,  # The maximum length of the sequence to be generated
                "pad_token_id": pad_token_id,  # Padding token ID
                "eos_token_id": eos_token_id,  # End-of-sequence token ID(s)
                "output_attentions": False,  # Return attention tensors of all attention layers if True
                "output_hidden_states": False,  # Return hidden states of all layers if True
                "output_scores": False,  # Return prediction scores if True
                "return_dict_in_generate": False,  # Return a ModelOutput instead of a plain tuple if True
                "synced_gpus": False,  # Continue running the while loop until max_length for ZeRO stage 3 if True
            },
            "beam_sample": {
                "num_beams": 4,  # Number of beams for beam search
                "temperature": 0.6,  # Temperature for sampling
                "max_length": 4096,  # The maximum length of the sequence to be generated
                "pad_token_id": pad_token_id,  # Padding token ID
                "eos_token_id": eos_token_id,  # End-of-sequence token ID(s)
                "output_attentions": False,  # Return attention tensors of all attention layers if True
                "output_hidden_states": False,  # Return hidden states of all layers if True
                "output_scores": False,  # Return prediction scores if True
                "return_dict_in_generate": False,  # Return a ModelOutput instead of a plain tuple if True
                "synced_gpus": False,  # Continue running the while loop until max_length for ZeRO stage 3 if True
            },
            "group_beam_search": {
                "num_beams": 4,  # Number of beams for beam search
                "diversity_penalty": 0.5,  # Penalty for reducing similarity across different beam groups
                "max_length": 4096,  # The maximum length of the sequence to be generated
                "pad_token_id": pad_token_id,  # Padding token ID
                "eos_token_id": eos_token_id,  # End-of-sequence token ID(s)
                "output_attentions": False,  # Return attention tensors of all attention layers if True
                "output_hidden_states": False,  # Return hidden states of all layers if True
                "output_scores": False,  # Return prediction scores if True
                "return_dict_in_generate": False,  # Return a ModelOutput instead of a plain tuple if True
                "synced_gpus": False,  # Continue running the while loop until max_length for ZeRO stage 3 if True
            },
            "constrained_beam_search": {
                "num_beams": 4,  # Number of beams for beam search
                "max_length": 4096,  # The maximum length of the sequence to be generated
                "constraints": None,  # List of constraints to apply during beam search
                "pad_token_id": pad_token_id,  # Padding token ID
                "eos_token_id": eos_token_id,  # End-of-sequence token ID(s)
                "output_attentions": False,  # Return attention tensors of all attention layers if True
                "output_hidden_states": False,  # Return hidden states of all layers if True
                "output_scores": False,  # Return prediction scores if True
                "return_dict_in_generate": False,  # Return a ModelOutput instead of a plain tuple if True
                "synced_gpus": False,  # Whether to continue running the while loop until max_length (needed for ZeRO stage 3)
            },
        }

        # Merge default params with user-provided params
        strategy_params = {**default_params.get(decoding_strategy, {})}
        for k, v in generation_params.items():
            if k in strategy_params:
                strategy_params[k] = v

        # Prepare LogitsProcessorList and BeamSearchScorer for beam search strategies
        if decoding_strategy in ["beam_search", "beam_sample", "group_beam_search"]:
            logits_processor = LogitsProcessorList(
                [MinLengthLogitsProcessor(min_length=strategy_params.get("min_length", 0), eos_token_id=eos_token_id)]
            )
            beam_scorer = BeamSearchScorer(
                batch_size=1,
                max_length=strategy_params.get("max_length", 20),
                num_beams=strategy_params.get("num_beams", 1),
                device=self.model.device,
                length_penalty=strategy_params.get("length_penalty", 1.0),
                do_early_stopping=strategy_params.get("early_stopping", False),
            )
            strategy_params.update({"logits_processor": logits_processor, "beam_scorer": beam_scorer})

            if decoding_strategy == "beam_sample":
                strategy_params.update({"logits_warper": LogitsProcessorList()})

        # Map of decoding strategy to method
        strategy_to_method = {
            "generate": self.model.generate,
            "greedy_search": self.model.greedy_search,
            "contrastive_search": self.model.contrastive_search,
            "sample": self.model.sample,
            "beam_search": self.model.beam_search,
            "beam_sample": self.model.beam_sample,
            "group_beam_search": self.model.group_beam_search,
            "constrained_beam_search": self.model.constrained_beam_search,
        }

        try:
            self.log.debug(f"Generating completion for prompt {prompt}")

            inputs = self.tokenizer(prompt, return_tensors="pt", padding=True, truncation=True)
            input_ids = inputs["input_ids"]
            input_ids = input_ids.to(self.model.device)

            # Replicate input_ids for beam search
            if decoding_strategy in ["beam_search", "beam_sample", "group_beam_search"]:
                num_beams = strategy_params.get("num_beams", 1)
                input_ids = input_ids.repeat(num_beams, 1)

            # Use the specified decoding strategy
            decoding_method = strategy_to_method.get(decoding_strategy, self.model.generate)
            generated_ids = decoding_method(input_ids, **strategy_params)

            generated_text = self.tokenizer.decode(generated_ids[0], skip_special_tokens=True)
            self.log.debug(f"Generated text: {generated_text}")

            return generated_text

        except Exception as e:
            self.log.exception(f"An error occurred: {e}")
            raise

    def _get_torch_dtype(self, precision: str) -> torch.dtype:
        """
        Determines the torch dtype based on the specified precision.

        Args:
            precision (str): The desired precision for computations.

        Returns:
            torch.dtype: The corresponding torch dtype.

        Raises:
            ValueError: If an unsupported precision is specified.
        """
        dtype_map = {
            "float32": torch.float32,
            "float": torch.float,
            "float64": torch.float64,
            "double": torch.double,
            "float16": torch.float16,
            "bfloat16": torch.bfloat16,
            "half": torch.half,
            "uint8": torch.uint8,
            "int8": torch.int8,
            "int16": torch.int16,
            "short": torch.short,
            "int32": torch.int32,
            "int": torch.int,
            "int64": torch.int64,
            "quint8": torch.quint8,
            "qint8": torch.qint8,
            "qint32": torch.qint32,
        }
        return dtype_map.get(precision, torch.float)

    def load_models(
        self,
        model_name: str,
        tokenizer_name: str,
        model_revision: Optional[str] = None,
        tokenizer_revision: Optional[str] = None,
        model_class: str = "AutoModelForCausalLM",
        tokenizer_class: str = "AutoTokenizer",
        use_cuda: bool = False,
        precision: str = "float16",
        quantization: int = 0,
        device_map: str | Dict | None = "auto",
        max_memory={0: "24GB"},
        torchscript: bool = False,
        compile: bool = False,
        awq_enabled: bool = False,
        flash_attention: bool = False,
        better_transformers: bool = False,
        **model_args: Any,
    ) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
        """
        Loads and configures the specified model and tokenizer for text generation. It ensures the models are optimized for inference.

        Args:
            model_name (str): The name or path of the model to load.
            tokenizer_name (str): The name or path of the tokenizer to load.
            model_revision (Optional[str]): The specific model revision to load (e.g., a commit hash).
            tokenizer_revision (Optional[str]): The specific tokenizer revision to load (e.g., a commit hash).
            model_class (str): The class of the model to be loaded.
            tokenizer_class (str): The class of the tokenizer to be loaded.
            use_cuda (bool): Flag to utilize CUDA for GPU acceleration.
            precision (str): The desired precision for computations ("float32", "float16", etc.).
            quantization (int): The bit level for model quantization (0 for none, 8 for 8-bit quantization).
            device_map (str | Dict | None): The specific device(s) to use for model operations.
            max_memory (Dict): A dictionary defining the maximum memory to allocate for the model.
            torchscript (bool): Flag to enable TorchScript for model optimization.
            compile (bool): Flag to enable JIT compilation of the model.
            awq_enabled (bool): Flag to enable AWQ (Adaptive Weight Quantization).
            flash_attention (bool): Flag to enable Flash Attention optimization for faster processing.
            better_transformers (bool): Flag to enable Better Transformers optimization for faster processing.
            **model_args (Any): Additional arguments to pass to the model during its loading.

        Returns:
            Tuple[AutoModelForCausalLM, AutoTokenizer]: The loaded model and tokenizer ready for text generation.
        """
        self.log.info(f"Loading Hugging Face model: {model_name}")

        # Determine the torch dtype based on precision
        torch_dtype = self._get_torch_dtype(precision)

        if use_cuda and not device_map:
            device_map = "auto"

        if awq_enabled:
            ModelClass = AutoModelForCausalLM
            self.log.info("AWQ Enabled: Loading AWQ Model")
        else:
            ModelClass = getattr(transformers, model_class)
        TokenizerClass = getattr(transformers, tokenizer_class)

        # Load the model and tokenizer
        if model_name == "local":
            tokenizer = TokenizerClass.from_pretrained(
                os.path.join(self.input.get(), "/model"), torch_dtype=torch_dtype
            )
        else:
            tokenizer = TokenizerClass.from_pretrained(
                tokenizer_name, revision=tokenizer_revision, torch_dtype=torch_dtype
            )

        if flash_attention:
            model_args = {**model_args, **{"attn_implementation": "flash_attention_2"}}

        self.log.info(f"Loading model from {model_name} {model_revision} with {model_args}")
        if awq_enabled and quantization > 0:
            if model_name == "local":
                model = ModelClass.from_pretrained(
                    os.path.join(self.input.get(), "/model"),
                    torch_dtype=torch_dtype,
                    **model_args,
                )
            else:
                model = ModelClass.from_pretrained(
                    model_name,
                    revision=model_revision,
                    torch_dtype=torch_dtype,
                    **model_args,
                )
        elif quantization == 8:
            if model_name == "local":
                model = ModelClass.from_pretrained(
                    os.path.join(self.input.get(), "/model"),
                    torchscript=torchscript,
                    max_memory=max_memory,
                    device_map=device_map,
                    load_in_8bit=True,
                    **model_args,
                )
            else:
                model = ModelClass.from_pretrained(
                    model_name,
                    revision=model_revision,
                    torchscript=torchscript,
                    max_memory=max_memory,
                    device_map=device_map,
                    load_in_8bit=True,
                    **model_args,
                )
        elif quantization == 4:
            if model_name == "local":
                model = ModelClass.from_pretrained(
                    os.path.join(self.input.get(), "/model"),
                    torchscript=torchscript,
                    max_memory=max_memory,
                    device_map=device_map,
                    load_in_4bit=True,
                    **model_args,
                )
            else:
                model = ModelClass.from_pretrained(
                    model_name,
                    revision=model_revision,
                    torchscript=torchscript,
                    max_memory=max_memory,
                    device_map=device_map,
                    load_in_4bit=True,
                    **model_args,
                )
        else:
            if model_name == "local":
                model = ModelClass.from_pretrained(
                    os.path.join(self.input.get(), "/model"),
                    torch_dtype=torch_dtype,
                    torchscript=torchscript,
                    max_memory=max_memory,
                    device_map=device_map,
                    **model_args,
                )
            else:
                model = ModelClass.from_pretrained(
                    model_name,
                    revision=model_revision,
                    torch_dtype=torch_dtype,
                    torchscript=torchscript,
                    max_memory=max_memory,
                    device_map=device_map,
                    **model_args,
                )

        if compile and not torchscript:
            model = torch.compile(model)

        if better_transformers:
            model = BetterTransformer.transform(model, keep_original_model=True)

        # Set to evaluation mode for inference
        model.eval()

        if tokenizer and tokenizer.eos_token and (not tokenizer.pad_token):
            tokenizer.pad_token = tokenizer.eos_token

        eos_token_id = model.config.eos_token_id
        pad_token_id = model.config.pad_token_id
        if not pad_token_id:
            model.config.pad_token_id = eos_token_id

        self.log.debug("Text model and tokenizer loaded successfully.")
        return model, tokenizer

    def load_models_vllm(
        self,
        model: str,
        tokenizer: str,
        tokenizer_mode: str = "auto",
        trust_remote_code: bool = True,
        download_dir: Optional[str] = None,
        load_format: str = "auto",
        dtype: Union[str, torch.dtype] = "auto",
        seed: int = 42,
        revision: Optional[str] = None,
        # code_revision: Optional[str] = None,
        tokenizer_revision: Optional[str] = None,
        max_model_len: int = 1024,
        quantization: Optional[str] = None,
        enforce_eager: bool = False,
        max_context_len_to_capture: int = 8192,
        block_size: int = 16,
        gpu_memory_utilization: float = 0.90,
        swap_space: int = 4,
        cache_dtype: str = "auto",
        sliding_window: Optional[int] = None,
        pipeline_parallel_size: int = 1,
        tensor_parallel_size: int = 1,
        worker_use_ray: bool = False,
        max_parallel_loading_workers: Optional[int] = None,
        disable_custom_all_reduce: bool = False,
        max_num_batched_tokens: Optional[int] = None,
        max_num_seqs: int = 64,
        max_paddings: int = 512,
        device: str = "cuda",
        max_lora_rank: Optional[int] = None,
        max_loras: Optional[int] = None,
        max_cpu_loras: Optional[int] = None,
        lora_dtype: Optional[torch.dtype] = None,
        lora_extra_vocab_size: int = 0,
        placement_group: Optional[PlacementGroup] = None,
        log_stats: bool = False,
        batched_inference: bool = False,
    ) -> AsyncLLMEngine | LLM:
        """
        Initializes and loads models using VLLM configurations with specific parameters.

        Args:
            model (str): Name or path of the Hugging Face model to use.
            tokenizer (str): Name or path of the Hugging Face tokenizer to use.
            tokenizer_mode (str): Tokenizer mode. "auto" will use the fast tokenizer if available, "slow" will always use the slow tokenizer.
            trust_remote_code (bool): Trust remote code (e.g., from Hugging Face) when downloading the model and tokenizer.
            download_dir (Optional[str]): Directory to download and load the weights, default to the default cache directory of Hugging Face.
            load_format (str): The format of the model weights to load. Options include "auto", "pt", "safetensors", "npcache", "dummy".
            dtype (Union[str, torch.dtype]): Data type for model weights and activations. Options include "auto", torch.float32, torch.float16, etc.
            seed (int): Random seed for reproducibility.
            revision (Optional[str]): The specific model version to use. Can be a branch name, a tag name, or a commit id.
            code_revision (Optional[str]): The specific revision to use for the model code on Hugging Face Hub.
            tokenizer_revision (Optional[str]): The specific tokenizer version to use.
            max_model_len (Optional[int]): Maximum length of a sequence (including prompt and output). If None, will be derived from the model.
            quantization (Optional[str]): Quantization method that was used to quantize the model weights. If None, we assume the model weights are not quantized.
            enforce_eager (bool): Whether to enforce eager execution. If True, disables CUDA graph and always execute the model in eager mode.
            max_context_len_to_capture (Optional[int]): Maximum context length covered by CUDA graphs. When larger, falls back to eager mode.
            block_size (int): Size of a cache block in number of tokens.
            gpu_memory_utilization (float): Fraction of GPU memory to use for the VLLM execution.
            swap_space (int): Size of the CPU swap space per GPU (in GiB).
            cache_dtype (str): Data type for KV cache storage.
            sliding_window (Optional[int]): Configuration for sliding window if applicable.
            pipeline_parallel_size (int): Number of pipeline parallel groups.
            tensor_parallel_size (int): Number of tensor parallel groups.
            worker_use_ray (bool): Whether to use Ray for model workers. Required if either pipeline_parallel_size or tensor_parallel_size is greater than 1.
            max_parallel_loading_workers (Optional[int]): Maximum number of workers for loading the model in parallel to avoid RAM OOM.
            disable_custom_all_reduce (bool): Disable custom all-reduce kernel and fall back to NCCL.
            max_num_batched_tokens (Optional[int]): Maximum number of tokens to be processed in a single iteration.
            max_num_seqs (int): Maximum number of sequences to be processed in a single iteration.
            max_paddings (int): Maximum number of paddings to be added to a batch.
            device (str): Device configuration, typically "cuda" or "cpu".
            max_lora_rank (Optional[int]): Maximum rank for LoRA adjustments.
            max_loras (Optional[int]): Maximum number of LoRA adjustments.
            max_cpu_loras (Optional[int]): Maximum number of LoRA adjustments stored on CPU.
            lora_dtype (Optional[torch.dtype]): Data type for LoRA parameters.
            lora_extra_vocab_size (Optional[int]): Additional vocabulary size for LoRA.
            placement_group (Optional["PlacementGroup"]): Ray placement group for distributed execution. Required for distributed execution.
            log_stats (bool): Whether to log statistics during model operation.

        Returns:
            LLMEngine: An instance of the LLMEngine class initialized with the given configurations.
        """

        vllm_model_config = VLLMModelConfig(
            model=model,
            tokenizer=tokenizer,
            tokenizer_mode=tokenizer_mode,
            trust_remote_code=trust_remote_code,
            download_dir=download_dir,
            load_format=load_format,
            dtype=dtype,
            seed=seed,
            revision=revision,
            # code_revision=code_revision,
            tokenizer_revision=tokenizer_revision,
            max_model_len=max_model_len,
            quantization=quantization,
            enforce_eager=enforce_eager,
            max_context_len_to_capture=max_context_len_to_capture,
        )

        vllm_cache_config = CacheConfig(
            block_size=block_size,
            gpu_memory_utilization=gpu_memory_utilization,
            swap_space=swap_space,
            cache_dtype=cache_dtype,
            sliding_window=sliding_window,
        )

        vllm_parallel_config = ParallelConfig(
            pipeline_parallel_size=pipeline_parallel_size,
            tensor_parallel_size=tensor_parallel_size,
            worker_use_ray=worker_use_ray,
            max_parallel_loading_workers=max_parallel_loading_workers,
            disable_custom_all_reduce=disable_custom_all_reduce,
        )

        vllm_scheduler_config = SchedulerConfig(
            max_num_batched_tokens=max_num_batched_tokens,
            max_num_seqs=max_num_seqs,
            max_model_len=max_model_len,  # type: ignore
            max_paddings=max_paddings,
        )

        vllm_device_config = DeviceConfig(device=device)

        vllm_lora_config = None
        if max_lora_rank is not None and max_loras is not None:
            vllm_lora_config = LoRAConfig(
                max_lora_rank=max_lora_rank,
                max_loras=max_loras,
                max_cpu_loras=max_cpu_loras,
                lora_dtype=lora_dtype,
                lora_extra_vocab_size=lora_extra_vocab_size,
            )

        engine: AsyncLLMEngine | LLM
        if not batched_inference:
            engine = AsyncLLMEngine(
                worker_use_ray=worker_use_ray,
                engine_use_ray=placement_group is not None,
                log_requests=True,
                start_engine_loop=True,
                model_config=vllm_model_config,
                cache_config=vllm_cache_config,
                parallel_config=vllm_parallel_config,
                scheduler_config=vllm_scheduler_config,
                device_config=vllm_device_config,
                lora_config=vllm_lora_config,
                placement_group=placement_group,
                log_stats=log_stats,
            )
        else:
            engine = LLM(
                model=model,
                tokenizer=tokenizer,
                tokenizer_mode=tokenizer_mode,
                trust_remote_code=trust_remote_code,
                download_dir=download_dir,
                load_format=load_format,
                dtype=dtype,  # type: ignore
                kv_cache_dtype=cache_dtype,
                seed=seed,
                max_model_len=max_model_len,
                pipeline_parallel_size=pipeline_parallel_size,
                tensor_parallel_size=tensor_parallel_size,
                worker_use_ray=worker_use_ray,
                max_parallel_loading_workers=max_parallel_loading_workers,
                block_size=block_size,
                gpu_memory_utilization=gpu_memory_utilization,
                swap_space=swap_space,
                max_num_batched_tokens=max_num_batched_tokens,
                max_num_seqs=max_num_seqs,
                max_paddings=max_paddings,
                revision=revision,
                # code_revision=code_revision,
                tokenizer_revision=tokenizer_revision,
                quantization=quantization,
                enforce_eager=enforce_eager,
                max_context_len_to_capture=max_context_len_to_capture,
                disable_custom_all_reduce=disable_custom_all_reduce,
                enable_lora=max_lora_rank is not None,
                max_loras=max_loras,
                max_lora_rank=max_lora_rank,
                lora_extra_vocab_size=lora_extra_vocab_size,
                max_cpu_loras=max_cpu_loras,
                device=device,
            )

        self.log.info("VLLM model loaded successfully.")
        return engine

    def load_models_llama_cpp(
        self,
        model: str,
        filename: Optional[str],
        local_dir: Optional[Union[str, os.PathLike[str]]] = None,
        n_gpu_layers: int = 0,
        split_mode: int = llama_cpp.LLAMA_SPLIT_LAYER,
        main_gpu: int = 0,
        tensor_split: Optional[List[float]] = None,
        vocab_only: bool = False,
        use_mmap: bool = True,
        use_mlock: bool = False,
        kv_overrides: Optional[Dict[str, Union[bool, int, float]]] = None,
        seed: int = llama_cpp.LLAMA_DEFAULT_SEED,
        n_ctx: int = 512,
        n_batch: int = 512,
        n_threads: Optional[int] = None,
        n_threads_batch: Optional[int] = None,
        rope_scaling_type: Optional[int] = llama_cpp.LLAMA_ROPE_SCALING_UNSPECIFIED,
        rope_freq_base: float = 0.0,
        rope_freq_scale: float = 0.0,
        yarn_ext_factor: float = -1.0,
        yarn_attn_factor: float = 1.0,
        yarn_beta_fast: float = 32.0,
        yarn_beta_slow: float = 1.0,
        yarn_orig_ctx: int = 0,
        mul_mat_q: bool = True,
        logits_all: bool = False,
        embedding: bool = False,
        offload_kqv: bool = True,
        last_n_tokens_size: int = 64,
        lora_base: Optional[str] = None,
        lora_scale: float = 1.0,
        lora_path: Optional[str] = None,
        numa: Union[bool, int] = False,
        chat_format: Optional[str] = None,
        chat_handler: Optional[llama_cpp.llama_chat_format.LlamaChatCompletionHandler] = None,
        draft_model: Optional[llama_cpp.LlamaDraftModel] = None,
        tokenizer: Optional[PreTrainedTokenizerBase] = None,
        verbose: bool = True,
        **kwargs,
    ) -> Tuple[LlamaCPP, Optional[PreTrainedTokenizerBase]]:
        """
        Initializes and loads LLaMA model with llama.cpp backend, along with an optional tokenizer.

        Args:
            model (str): Huggingface ID to the LLaMA model.
            filename: A filename or glob pattern to match the model file in the repo.
            local_dir: The local directory to save the model to.
            n_gpu_layers (int): Number of layers to offload to GPU. Default is 0.
            split_mode (int): Split mode for distributing model across GPUs.
            main_gpu (int): Main GPU index.
            tensor_split (Optional[List[float]]): Tensor split configuration.
            vocab_only (bool): Whether to load vocabulary only.
            use_mmap (bool): Use memory-mapped files for model loading.
            use_mlock (bool): Lock model data in RAM.
            kv_overrides (Optional[Dict[str, Union[bool, int, float]]]): Key-value pairs for model overrides.
            seed (int): Random seed for initialization.
            n_ctx (int): Number of context tokens.
            n_batch (int): Batch size for processing prompts.
            n_threads (Optional[int]): Number of threads for generation.
            n_threads_batch (Optional[int]): Number of threads for batch processing.
            rope_scaling_type (Optional[int]): RoPE scaling type.
            rope_freq_base (float): Base frequency for RoPE.
            rope_freq_scale (float): Frequency scaling for RoPE.
            yarn_ext_factor (float): YaRN extrapolation mix factor.
            yarn_attn_factor (float): YaRN attention factor.
            yarn_beta_fast (float): YaRN beta fast parameter.
            yarn_beta_slow (float): YaRN beta slow parameter.
            yarn_orig_ctx (int): Original context size for YaRN.
            mul_mat_q (bool): Whether to multiply matrices for queries.
            logits_all (bool): Return logits for all tokens.
            embedding (bool): Enable embedding mode only.
            offload_kqv (bool): Offload K, Q, V matrices to GPU.
            last_n_tokens_size (int): Size for the last_n_tokens buffer.
            lora_base (Optional[str]): Base model path for LoRA.
            lora_scale (float): Scale factor for LoRA adjustments.
            lora_path (Optional[str]): Path to LoRA adjustments.
            numa (Union[bool, int]): NUMA configuration.
            chat_format (Optional[str]): Chat format configuration.
            chat_handler (Optional[llama_cpp.LlamaChatCompletionHandler]): Handler for chat completions.
            draft_model (Optional[llama_cpp.LlamaDraftModel]): Draft model for speculative decoding.
            tokenizer (Optional[PreTrainedTokenizerBase]): Custom tokenizer instance.
            verbose (bool): Enable verbose logging.
            **kwargs: Additional keyword arguments.

        Returns:
            Tuple[LlamaCPP, Optional[PreTrainedTokenizerBase]]: The loaded LLaMA model and tokenizer.
        """
        self.log.info(f"Loading LLaMA model from {model} with llama.cpp backend.")

        llama_model = LlamaCPP.from_pretrained(
            repo_id=model,
            filename=filename,
            local_dir=local_dir,
            n_gpu_layers=n_gpu_layers,
            split_mode=split_mode,
            main_gpu=main_gpu,
            tensor_split=tensor_split,
            vocab_only=vocab_only,
            use_mmap=use_mmap,
            use_mlock=use_mlock,
            kv_overrides=kv_overrides,
            seed=seed,
            n_ctx=n_ctx,
            n_batch=n_batch,
            n_threads=n_threads,
            n_threads_batch=n_threads_batch,
            rope_scaling_type=rope_scaling_type,
            rope_freq_base=rope_freq_base,
            rope_freq_scale=rope_freq_scale,
            yarn_ext_factor=yarn_ext_factor,
            yarn_attn_factor=yarn_attn_factor,
            yarn_beta_fast=yarn_beta_fast,
            yarn_beta_slow=yarn_beta_slow,
            yarn_orig_ctx=yarn_orig_ctx,
            mul_mat_q=mul_mat_q,
            logits_all=logits_all,
            embedding=embedding,
            offload_kqv=offload_kqv,
            last_n_tokens_size=last_n_tokens_size,
            lora_base=lora_base,
            lora_scale=lora_scale,
            lora_path=lora_path,
            numa=numa,
            chat_format=chat_format,
            chat_handler=chat_handler,
            draft_model=draft_model,
            tokenizer=tokenizer,
            verbose=verbose,
            **kwargs,
        )

        self.log.info("LLaMA model loaded successfully.")

        return llama_model, tokenizer

    def done(self):
        if self.notification_email:
            self.output.flush()
            send_email(recipient=self.notification_email, bucket_name=self.output.bucket, prefix=self.output.s3_folder)


class TextAPI(TextBulk):
    """
    A class representing a Hugging Face API for generating text using a pre-trained language model.

    Attributes:
        model (Any): The pre-trained language model.
        tokenizer (Any): The tokenizer used to preprocess input text.
        model_name (str): The name of the pre-trained language model.
        model_revision (Optional[str]): The revision of the pre-trained language model.
        tokenizer_name (str): The name of the tokenizer used to preprocess input text.
        tokenizer_revision (Optional[str]): The revision of the tokenizer used to preprocess input text.
        model_class (str): The name of the class of the pre-trained language model.
        tokenizer_class (str): The name of the class of the tokenizer used to preprocess input text.
        use_cuda (bool): Whether to use a GPU for inference.
        quantization (int): The level of quantization to use for the pre-trained language model.
        precision (str): The precision to use for the pre-trained language model.
        device_map (str | Dict | None): The mapping of devices to use for inference.
        max_memory (Dict[int, str]): The maximum memory to use for inference.
        torchscript (bool): Whether to use a TorchScript-optimized version of the pre-trained language model.
        model_args (Any): Additional arguments to pass to the pre-trained language model.

    Methods:
        text(**kwargs: Any) -> Dict[str, Any]:
            Generates text based on the given prompt and decoding strategy.

        listen(model_name: str, model_class: str = "AutoModelForCausalLM", tokenizer_class: str = "AutoTokenizer", use_cuda: bool = False, precision: str = "float16", quantization: int = 0, device_map: str | Dict | None = "auto", max_memory={0: "24GB"}, torchscript: bool = True, endpoint: str = "*", port: int = 3000, cors_domain: str = "http://localhost:3000", username: Optional[str] = None, password: Optional[str] = None, **model_args: Any) -> None:
            Starts a CherryPy server to listen for requests to generate text.
    """

    model: Any
    tokenizer: Any

    def __init__(
        self,
        input: BatchInput,
        output: BatchOutput,
        state: State,
    ):
        """
        Initializes a new instance of the TextAPI class.

        Args:
            input (BatchInput): The input data to process.
            output (BatchOutput): The output data to process.
            state (State): The state of the API.
        """
        super().__init__(input=input, output=output, state=state)
        self.log = setup_logger(self)

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    @cherrypy.tools.allow(methods=["POST"])
    def text(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Generates text based on the given prompt and decoding strategy.

        Args:
            **kwargs (Any): Additional arguments to pass to the pre-trained language model.

        Returns:
            Dict[str, Any]: A dictionary containing the prompt, arguments, and generated text.
        """
        data = cherrypy.request.json
        prompt = data.get("prompt")
        decoding_strategy = data.get("decoding_strategy", "generate")

        max_new_tokens = data.get("max_new_tokens")
        max_length = data.get("max_length")
        temperature = data.get("temperature")
        diversity_penalty = data.get("diversity_penalty")
        num_beams = data.get("num_beams")
        length_penalty = data.get("length_penalty")
        early_stopping = data.get("early_stopping")

        others = data.__dict__

        return {
            "prompt": prompt,
            "args": others,
            "completion": self.generate(
                prompt=prompt,
                decoding_strategy=decoding_strategy,
                max_new_tokens=max_new_tokens,
                max_length=max_length,
                temperature=temperature,
                diversity_penalty=diversity_penalty,
                num_beams=num_beams,
                length_penalty=length_penalty,
                early_stopping=early_stopping,
                **others,
            ),
        }

    def validate_password(self, realm, username, password):
        """
        Validate the username and password against expected values.

        Args:
            realm (str): The authentication realm.
            username (str): The provided username.
            password (str): The provided password.

        Returns:
            bool: True if credentials are valid, False otherwise.
        """
        return username == self.username and password == self.password

    def listen(
        self,
        model_name: str,
        # Huggingface params
        model_class: str = "AutoModelForCausalLM",
        tokenizer_class: str = "AutoTokenizer",
        use_cuda: bool = False,
        precision: str = "float16",
        quantization: int = 0,
        device_map: str | Dict | None = "auto",
        max_memory={0: "24GB"},
        torchscript: bool = False,
        compile: bool = False,
        awq_enabled: bool = False,
        flash_attention: bool = False,
        concurrent_queries: bool = False,
        use_vllm: bool = False,
        use_llama_cpp: bool = False,
        # VLLM params
        vllm_tokenizer_mode: str = "auto",
        vllm_download_dir: Optional[str] = None,
        vllm_load_format: str = "auto",
        vllm_seed: int = 42,
        vllm_max_model_len: int = 1024,
        vllm_enforce_eager: bool = False,
        vllm_max_context_len_to_capture: int = 8192,
        vllm_block_size: int = 16,
        vllm_gpu_memory_utilization: float = 0.90,
        vllm_swap_space: int = 4,
        vllm_sliding_window: Optional[int] = None,
        vllm_pipeline_parallel_size: int = 1,
        vllm_tensor_parallel_size: int = 1,
        vllm_worker_use_ray: bool = False,
        vllm_max_parallel_loading_workers: Optional[int] = None,
        vllm_disable_custom_all_reduce: bool = False,
        vllm_max_num_batched_tokens: Optional[int] = None,
        vllm_max_num_seqs: int = 64,
        vllm_max_paddings: int = 512,
        vllm_max_lora_rank: Optional[int] = None,
        vllm_max_loras: Optional[int] = None,
        vllm_max_cpu_loras: Optional[int] = None,
        vllm_lora_extra_vocab_size: int = 0,
        vllm_placement_group: Optional[dict] = None,
        vllm_log_stats: bool = False,
        # llama.cpp params
        llama_cpp_filename: Optional[str] = None,
        llama_cpp_n_gpu_layers: int = 0,
        llama_cpp_split_mode: int = llama_cpp.LLAMA_SPLIT_LAYER,
        llama_cpp_tensor_split: Optional[List[float]] = None,
        llama_cpp_vocab_only: bool = False,
        llama_cpp_use_mmap: bool = True,
        llama_cpp_use_mlock: bool = False,
        llama_cpp_kv_overrides: Optional[Dict[str, Union[bool, int, float]]] = None,
        llama_cpp_seed: int = llama_cpp.LLAMA_DEFAULT_SEED,
        llama_cpp_n_ctx: int = 2048,
        llama_cpp_n_batch: int = 512,
        llama_cpp_n_threads: Optional[int] = None,
        llama_cpp_n_threads_batch: Optional[int] = None,
        llama_cpp_rope_scaling_type: Optional[int] = llama_cpp.LLAMA_ROPE_SCALING_UNSPECIFIED,
        llama_cpp_rope_freq_base: float = 0.0,
        llama_cpp_rope_freq_scale: float = 0.0,
        llama_cpp_yarn_ext_factor: float = -1.0,
        llama_cpp_yarn_attn_factor: float = 1.0,
        llama_cpp_yarn_beta_fast: float = 32.0,
        llama_cpp_yarn_beta_slow: float = 1.0,
        llama_cpp_yarn_orig_ctx: int = 0,
        llama_cpp_mul_mat_q: bool = True,
        llama_cpp_logits_all: bool = False,
        llama_cpp_embedding: bool = False,
        llama_cpp_offload_kqv: bool = True,
        llama_cpp_last_n_tokens_size: int = 64,
        llama_cpp_lora_base: Optional[str] = None,
        llama_cpp_lora_scale: float = 1.0,
        llama_cpp_lora_path: Optional[str] = None,
        llama_cpp_numa: Union[bool, int] = False,
        llama_cpp_chat_format: Optional[str] = None,
        llama_cpp_draft_model: Optional[llama_cpp.LlamaDraftModel] = None,
        # llama_cpp_tokenizer: Optional[PreTrainedTokenizerBase] = None,
        llama_cpp_verbose: bool = True,
        # Server params
        endpoint: str = "*",
        port: int = 3000,
        cors_domain: str = "http://localhost:3000",
        username: Optional[str] = None,
        password: Optional[str] = None,
        **model_args: Any,
    ) -> None:
        """
        Starts a CherryPy server to listen for requests to generate text.

        Args:
            model_name (str): Name or identifier of the pre-trained model to be used.
            model_class (str): Class name of the model to be used from the transformers library.
            tokenizer_class (str): Class name of the tokenizer to be used from the transformers library.
            use_cuda (bool): Flag to enable CUDA for GPU acceleration.
            precision (str): Specifies the precision configuration for PyTorch tensors, e.g., "float16".
            quantization (int): Level of model quantization to reduce model size and inference time.
            device_map (Union[str, Dict, None]): Maps model layers to specific devices for distributed inference.
            max_memory (Dict[int, str]): Maximum memory allocation for the model on each device.
            torchscript (bool): Enables the use of TorchScript for model optimization.
            compile (bool): Enables model compilation for further optimization.
            awq_enabled (bool): Enables Adaptive Weight Quantization (AWQ) for model optimization.
            flash_attention (bool): Utilizes Flash Attention optimizations for faster processing.
            concurrent_queries (bool): Allows the server to handle multiple requests concurrently if True.
            use_vllm (bool): Flag to use Very Large Language Models (VLLM) integration.
            use_llama_cpp (bool): Flag to use llama.cpp integration for language model inference.
            llama_cpp_filename (Optional[str]): The filename of the model file for llama.cpp.
            llama_cpp_n_gpu_layers (int): Number of layers to offload to GPU in llama.cpp configuration.
            llama_cpp_split_mode (int): Defines how the model is split across multiple GPUs in llama.cpp.
            llama_cpp_tensor_split (Optional[List[float]]): Custom tensor split configuration for llama.cpp.
            llama_cpp_vocab_only (bool): Loads only the vocabulary part of the model in llama.cpp.
            llama_cpp_use_mmap (bool): Enables memory-mapped files for model loading in llama.cpp.
            llama_cpp_use_mlock (bool): Locks the model in RAM to prevent swapping in llama.cpp.
            llama_cpp_kv_overrides (Optional[Dict[str, Union[bool, int, float]]]): Key-value pairs for overriding default llama.cpp model parameters.
            llama_cpp_seed (int): Seed for random number generation in llama.cpp.
            llama_cpp_n_ctx (int): The number of context tokens for the model in llama.cpp.
            llama_cpp_n_batch (int): Batch size for processing prompts in llama.cpp.
            llama_cpp_n_threads (Optional[int]): Number of threads for generation in llama.cpp.
            llama_cpp_n_threads_batch (Optional[int]): Number of threads for batch processing in llama.cpp.
            llama_cpp_rope_scaling_type (Optional[int]): Specifies the RoPE (Rotary Positional Embeddings) scaling type in llama.cpp.
            llama_cpp_rope_freq_base (float): Base frequency for RoPE in llama.cpp.
            llama_cpp_rope_freq_scale (float): Frequency scaling factor for RoPE in llama.cpp.
            llama_cpp_yarn_ext_factor (float): Extrapolation mix factor for YaRN in llama.cpp.
            llama_cpp_yarn_attn_factor (float): Attention factor for YaRN in llama.cpp.
            llama_cpp_yarn_beta_fast (float): Beta fast parameter for YaRN in llama.cpp.
            llama_cpp_yarn_beta_slow (float): Beta slow parameter for YaRN in llama.cpp.
            llama_cpp_yarn_orig_ctx (int): Original context size for YaRN in llama.cpp.
            llama_cpp_mul_mat_q (bool): Flag to enable matrix multiplication for queries in llama.cpp.
            llama_cpp_logits_all (bool): Returns logits for all tokens when set to True in llama.cpp.
            llama_cpp_embedding (bool): Enables embedding mode only in llama.cpp.
            llama_cpp_offload_kqv (bool): Offloads K, Q, V matrices to GPU in llama.cpp.
            llama_cpp_last_n_tokens_size (int): Size for the last_n_tokens buffer in llama.cpp.
            llama_cpp_lora_base (Optional[str]): Base model path for LoRA adjustments in llama.cpp.
            llama_cpp_lora_scale (float): Scale factor for LoRA adjustments in llama.cpp.
            llama_cpp_lora_path (Optional[str]): Path to LoRA adjustments file in llama.cpp.
            llama_cpp_numa (Union[bool, int]): NUMA configuration for llama.cpp.
            llama_cpp_chat_format (Optional[str]): Specifies the chat format for llama.cpp.
            llama_cpp_draft_model (Optional[llama_cpp.LlamaDraftModel]): Draft model for speculative decoding in llama.cpp.
            endpoint (str): Network interface to bind the server to.
            port (int): Port number to listen on for incoming requests.
            cors_domain (str): Specifies the domain to allow for Cross-Origin Resource Sharing (CORS).
            username (Optional[str]): Username for basic authentication, if required.
            password (Optional[str]): Password for basic authentication, if required.
            **model_args (Any): Additional arguments to pass to the pre-trained language model or llama.cpp configuration.
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
        self.awq_enabled = awq_enabled
        self.flash_attention = flash_attention
        self.use_vllm = use_vllm
        self.concurrent_queries = concurrent_queries

        self.model_args = model_args
        self.username = username
        self.password = password

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

        if use_vllm:
            self.model = self.load_models_vllm(
                model=model_name,
                tokenizer=tokenizer_name,
                tokenizer_mode=vllm_tokenizer_mode,
                trust_remote_code=True,
                download_dir=vllm_download_dir,
                load_format=vllm_load_format,
                dtype=self._get_torch_dtype(precision),
                seed=vllm_seed,
                revision=model_revision,
                tokenizer_revision=tokenizer_revision,
                max_model_len=vllm_max_model_len,
                quantization=(None if quantization == 0 else f"{quantization}-bit"),
                enforce_eager=vllm_enforce_eager,
                max_context_len_to_capture=vllm_max_context_len_to_capture,
                block_size=vllm_block_size,
                gpu_memory_utilization=vllm_gpu_memory_utilization,
                swap_space=vllm_swap_space,
                cache_dtype="auto",
                sliding_window=vllm_sliding_window,
                pipeline_parallel_size=vllm_pipeline_parallel_size,
                tensor_parallel_size=vllm_tensor_parallel_size,
                worker_use_ray=vllm_worker_use_ray,
                max_parallel_loading_workers=vllm_max_parallel_loading_workers,
                disable_custom_all_reduce=vllm_disable_custom_all_reduce,
                max_num_batched_tokens=vllm_max_num_batched_tokens,
                max_num_seqs=vllm_max_num_seqs,
                max_paddings=vllm_max_paddings,
                device="cuda" if use_cuda else "cpu",
                max_lora_rank=vllm_max_lora_rank,
                max_loras=vllm_max_loras,
                max_cpu_loras=vllm_max_cpu_loras,
                lora_dtype=self._get_torch_dtype(precision),
                lora_extra_vocab_size=vllm_lora_extra_vocab_size,
                placement_group=vllm_placement_group,  # type: ignore
                log_stats=vllm_log_stats,
                batched_inference=False,
            )
        elif use_llama_cpp:
            self.model, self.tokenizer = self.load_models_llama_cpp(
                model=self.model_name,
                filename=llama_cpp_filename,
                local_dir=self.output.output_folder,
                n_gpu_layers=llama_cpp_n_gpu_layers,
                split_mode=llama_cpp_split_mode,
                main_gpu=0 if self.use_cuda else -1,
                tensor_split=llama_cpp_tensor_split,
                vocab_only=llama_cpp_vocab_only,
                use_mmap=llama_cpp_use_mmap,
                use_mlock=llama_cpp_use_mlock,
                kv_overrides=llama_cpp_kv_overrides,
                seed=llama_cpp_seed,
                n_ctx=llama_cpp_n_ctx,
                n_batch=llama_cpp_n_batch,
                n_threads=llama_cpp_n_threads,
                n_threads_batch=llama_cpp_n_threads_batch,
                rope_scaling_type=llama_cpp_rope_scaling_type,
                rope_freq_base=llama_cpp_rope_freq_base,
                rope_freq_scale=llama_cpp_rope_freq_scale,
                yarn_ext_factor=llama_cpp_yarn_ext_factor,
                yarn_attn_factor=llama_cpp_yarn_attn_factor,
                yarn_beta_fast=llama_cpp_yarn_beta_fast,
                yarn_beta_slow=llama_cpp_yarn_beta_slow,
                yarn_orig_ctx=llama_cpp_yarn_orig_ctx,
                mul_mat_q=llama_cpp_mul_mat_q,
                logits_all=llama_cpp_logits_all,
                embedding=llama_cpp_embedding,
                offload_kqv=llama_cpp_offload_kqv,
                last_n_tokens_size=llama_cpp_last_n_tokens_size,
                lora_base=llama_cpp_lora_base,
                lora_scale=llama_cpp_lora_scale,
                lora_path=llama_cpp_lora_path,
                numa=llama_cpp_numa,
                chat_format=llama_cpp_chat_format,
                draft_model=llama_cpp_draft_model,
                # tokenizer=llama_cpp_tokenizer, # TODO: support custom tokenizers for llama.cpp
                verbose=llama_cpp_verbose,
                **model_args,
            )
        else:
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
                awq_enabled=self.awq_enabled,
                flash_attention=self.flash_attention,
                compile=compile,
                **self.model_args,
            )

        def sequential_locker():
            if self.concurrent_queries:
                sequential_lock.acquire()

        def sequential_unlocker():
            if self.concurrent_queries:
                sequential_lock.release()

        def CORS():
            cherrypy.response.headers["Access-Control-Allow-Origin"] = cors_domain
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
                "error_page.400": error_page,
                "error_page.401": error_page,
                "error_page.402": error_page,
                "error_page.403": error_page,
                "error_page.404": error_page,
                "error_page.405": error_page,
                "error_page.406": error_page,
                "error_page.408": error_page,
                "error_page.415": error_page,
                "error_page.429": error_page,
                "error_page.500": error_page,
                "error_page.501": error_page,
                "error_page.502": error_page,
                "error_page.503": error_page,
                "error_page.504": error_page,
                "error_page.default": error_page,
            }
        )

        if username and password:
            # Configure basic authentication
            conf = {
                "/": {
                    "tools.sequential_locker.on": True,
                    "tools.sequential_unlocker.on": True,
                    "tools.auth_basic.on": True,
                    "tools.auth_basic.realm": "geniusrise",
                    "tools.auth_basic.checkpassword": self.validate_password,
                    "tools.CORS.on": True,
                }
            }
        else:
            # Configuration without authentication
            conf = {
                "/": {
                    "tools.sequential_locker.on": True,
                    "tools.sequential_unlocker.on": True,
                    "tools.CORS.on": True,
                }
            }

        cherrypy.tools.sequential_locker = cherrypy.Tool("before_handler", sequential_locker)
        cherrypy.tools.CORS = cherrypy.Tool("before_handler", CORS)
        cherrypy.tree.mount(self, "/api/v1/", conf)
        cherrypy.tools.CORS = cherrypy.Tool("before_finalize", CORS)
        cherrypy.tools.sequential_unlocker = cherrypy.Tool("before_finalize", sequential_unlocker)
        cherrypy.engine.start()
        cherrypy.engine.block()


def error_page(status, message, traceback, version):
    response = {
        "status": status,
        "message": message,
    }
    return json.dumps(response)


def create_presigned_urls(bucket_name: str, prefix: str) -> List[str]:
    """
    Generate presigned URLs for all files in a specific S3 folder.

    :param bucket_name: Name of the S3 bucket
    :param prefix: The common prefix of all keys you want to match, effectively a folder path in S3
    :return: List of URLs
    """
    # Create a session using your AWS credentials
    s3_client = boto3.client("s3")
    presigned_urls = []

    # List objects within a given prefix
    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    for content in response.get("Contents", []):
        # Generate a presigned URL for each object
        url = s3_client.generate_presigned_url(
            "get_object", Params={"Bucket": bucket_name, "Key": content["Key"]}, ExpiresIn=86400
        )  # Link valid for 1 day
        presigned_urls.append(url)

    return presigned_urls


def send_email(
    recipient: str, bucket_name: str, prefix: str, from_email: str = "Geniusrise <mailer@geniusrise.ai>"
) -> None:
    """
    Send a nicely formatted email with the list of downloadable links.

    :param recipient: Email address to send the links to
    :param links: List of presigned URLs
    :param from_email: The email address sending this email
    """
    ses_client = boto3.client("ses")

    links = create_presigned_urls(bucket_name=bucket_name, prefix=prefix)

    # Email body
    body_html = """
    <html>
        <head></head>
        <body>
            <h1>🧠 Your Download Links from Geniusrise</h1>
            <p>We've prepared the files you requested. Below are the links to download them:</p>
            <ul>
    """
    for link in links:
        body_html += f"<li><a href='{link}'>⬇️ Download Link</a></li>"

    body_html += """
            </ul>
            <p>Please note that these links are <strong>valid for 24 hours only</strong>.</p>
            <p>Thank you for using <a href='https://geniusrise.com'>Geniusrise</a>!</p>
        </body>
    </html>
    """

    # Sending the email
    try:
        response = ses_client.send_email(
            Source=from_email,
            Destination={"ToAddresses": [recipient]},
            Message={
                "Subject": {"Data": "🧠 Your Download Links from Geniusrise"},
                "Body": {"Html": {"Data": body_html}},
            },
        )
        print(f"Email sent! Message ID: {response['MessageId']}")
    except Exception as e:
        print(f"An error occurred: {e}")


def send_fine_tuning_email(
    recipient: str, bucket_name: str, prefix: str, from_email: str = "Geniusrise <mailer@geniusrise.ai>"
) -> None:
    """
    Send a nicely formatted email with the list of downloadable links.

    :param recipient: Email address to send the links to
    :param links: List of presigned URLs
    :param from_email: The email address sending this email
    """
    ses_client = boto3.client("ses")

    links = create_presigned_urls(bucket_name=bucket_name, prefix=prefix)

    # Email body
    body_html = """
    <html>
        <head></head>
        <body>
            <h1>🧠 Your Fine-Tuned Model Download Links from Geniusrise</h1>
            <p>We've prepared the models you requested. Below are the links to download them:</p>
            <ul>
    """
    for link in links:
        body_html += f"<li><a href='{link}'>⬇️ Download Link</a></li>"

    body_html += """
            </ul>
            <p>Please note that these links are <strong>valid for 24 hours only</strong>.</p>
            <p>Thank you for using <a href='https://geniusrise.com'>Geniusrise</a>!</p>
        </body>
    </html>
    """

    # Sending the email
    try:
        response = ses_client.send_email(
            Source=from_email,
            Destination={"ToAddresses": [recipient]},
            Message={
                "Subject": {"Data": "🧠 Your Fine-Tuned Model Download Links from Geniusrise"},
                "Body": {"Html": {"Data": body_html}},
            },
        )
        print(f"Email sent! Message ID: {response['MessageId']}")
    except Exception as e:
        print(f"An error occurred: {e}")
