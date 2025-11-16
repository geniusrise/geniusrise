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

import glob
import json
import os
import sqlite3
import uuid
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Union

import llama_cpp
import pandas as pd
import yaml  # type: ignore
from datasets import Dataset, load_from_disk
from geniusrise import BatchInput, BatchOutput, State
from pyarrow import feather
from pyarrow import parquet as pq
from transformers.tokenization_utils_base import PreTrainedTokenizerBase
from vllm import LLM, SamplingParams

from geniusrise.inference.text.base import TextBulk


class LanguageModelBulk(TextBulk):
    r"""
    LanguageModelBulk is designed for large-scale text generation using Hugging Face language models in a bulk processing
    manner. It's particularly useful for tasks such as bulk content creation, summarization, or any other scenario where
    large datasets need to be processed with a language model.

    Attributes:
        model (Any): The loaded language model used for text generation.
        tokenizer (Any): The tokenizer corresponding to the language model, used for processing input text.

    Args:
        input (BatchInput): Configuration for the input data.
        output (BatchOutput): Configuration for the output data.
        state (State): State management for the API.
        **kwargs (Any): Arbitrary keyword arguments for extended functionality.

    CLI Usage Example:
    ```bash
    genius LanguageModelBulk rise \
        batch \
            --input_s3_bucket geniusrise-test \
            --input_s3_folder input/lm \
        batch \
            --output_s3_bucket geniusrise-test \
            --output_s3_folder output/lm \
        postgres \
            --postgres_host 127.0.0.1 \
            --postgres_port 5432 \
            --postgres_user postgres \
            --postgres_password postgres \
            --postgres_database geniusrise\
            --postgres_table state \
        --id mistralai/Mistral-7B-Instruct-v0.1-lol \
        complete \
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
                decoding_strategy="generate" \
                generation_max_new_tokens=100 \
                generation_do_sample=true
    ```

    or using VLLM:
    ```bash
    genius LanguageModelBulk rise \
        batch \
            --input_s3_bucket geniusrise-test \
            --input_s3_folder input/lm \
        batch \
            --output_s3_bucket geniusrise-test \
            --output_s3_folder output/lm \
        none \
        --id mistralai/Mistral-7B-v0.1 \
        complete_vllm \
            --args \
                model_name="mistralai/Mistral-7B-v0.1" \
                use_cuda=True \
                precision="bfloat16" \
                quantization=0 \
                device_map="auto" \
                vllm_enforce_eager=True \
                generation_temperature=0.7 \
                generation_top_p=1.0 \
                generation_n=1 \
                generation_max_tokens=50 \
                generation_stream=false \
                generation_presence_penalty=0.0 \
                generation_frequency_penalty=0.0
    ```

    or using llama.cpp:
    ```bash
    genius LanguageModelBulk rise \
        batch \
            --input_s3_bucket geniusrise-test \
            --input_s3_folder input/chat \
        batch \
            --output_s3_bucket geniusrise-test \
            --output_s3_folder output/chat \
        none \
        complete_llama_cpp \
            --args \
                model="TheBloke/Mistral-7B-v0.1-GGUF" \
                filename="mistral-7b-v0.1.Q4_K_M.gguf" \
                n_gpu_layers=35  \
                n_ctx=32768 \
                generation_temperature=0.7 \
                generation_top_p=0.95 \
                generation_top_k=40 \
                generation_max_tokens=50 \
                generation_repeat_penalty=0.1
    ```
    """

    def __init__(self, input: BatchInput, output: BatchOutput, state: State, **kwargs) -> None:
        """
        Initializes the LanguageModelBulk object with the specified configurations for input, output, and state.

        Args:
            input (BatchInput): Configuration and data inputs for the bulk process.
            output (BatchOutput): Configurations for output data handling.
            state (State): State management for the bulk process.
            **kwargs (Any): Additional keyword arguments for extended configurations.
        """
        super().__init__(input, output, state, **kwargs)

    def load_dataset(self, dataset_path: str, max_length: int = 512, **kwargs) -> Optional[Dataset]:
        r"""
        Load a completion dataset from a directory.

        Args:
            dataset_path (str): The path to the dataset directory.
            max_length (int, optional): The maximum length for tokenization. Defaults to 512.
            **kwargs: Additional keyword arguments to pass to the underlying dataset loading functions.

        Returns:
            Dataset: The loaded dataset.

        Raises:
            Exception: If there was an error loading the dataset.

        ## Supported Data Formats and Structures:

        ### Dataset files saved by Hugging Face datasets library
        The directory should contain 'dataset_info.json' and other related files.

        ### JSONL
        Each line is a JSON object representing an example.
        ```json
        {"text": "The text content"}
        ```

        ### CSV
        Should contain 'text' column.
        ```csv
        text
        "The text content"
        ```

        ### Parquet
        Should contain 'text' column.

        ### JSON
        An array of dictionaries with 'text' key.
        ```json
        [{"text": "The text content"}]
        ```

        ### XML
        Each 'record' element should contain 'text' child element.
        ```xml
        <record>
            <text>The text content</text>
        </record>
        ```

        ### YAML
        Each document should be a dictionary with 'text' key.
        ```yaml
        - text: "The text content"
        ```

        ### TSV
        Should contain 'text' column separated by tabs.

        ### Excel (.xls, .xlsx)
        Should contain 'text' column.

        ### SQLite (.db)
        Should contain a table with 'text' column.

        ### Feather
        Should contain 'text' column.
        """

        self.max_length = max_length

        if hasattr(self, "tokenizer") and self.tokenizer is not None:
            self.label_to_id = self.model.config.label2id if self.model and self.model.config.label2id else {}  # type: ignore

        try:
            self.log.info(f"Loading dataset from {dataset_path}")
            if os.path.isfile(os.path.join(dataset_path, "dataset_info.json")):
                # Load dataset saved by Hugging Face datasets library
                return load_from_disk(dataset_path)
            else:
                data = []
                for filename in glob.glob(f"{dataset_path}/**/*", recursive=True):
                    filepath = os.path.join(dataset_path, filename)
                    if filename.endswith(".jsonl"):
                        with open(filepath, "r") as f:
                            for line in f:
                                example = json.loads(line)
                                data.append(example)

                    elif filename.endswith(".csv"):
                        df = pd.read_csv(filepath)
                        data.extend(df.to_dict("records"))

                    elif filename.endswith(".parquet"):
                        df = pq.read_table(filepath).to_pandas()
                        data.extend(df.to_dict("records"))

                    elif filename.endswith(".json"):
                        with open(filepath, "r") as f:
                            json_data = json.load(f)
                            data.extend(json_data)

                    elif filename.endswith(".xml"):
                        tree = ET.parse(filepath)
                        root = tree.getroot()
                        for record in root.findall("record"):
                            text = record.find("text").text  # type: ignore
                            data.append({"text": text})

                    elif filename.endswith(".yaml") or filename.endswith(".yml"):
                        with open(filepath, "r") as f:
                            yaml_data = yaml.safe_load(f)
                            data.extend(yaml_data)

                    elif filename.endswith(".tsv"):
                        df = pd.read_csv(filepath, sep="\t")
                        data.extend(df.to_dict("records"))

                    elif filename.endswith((".xls", ".xlsx")):
                        df = pd.read_excel(filepath)
                        data.extend(df.to_dict("records"))

                    elif filename.endswith(".db"):
                        conn = sqlite3.connect(filepath)
                        query = "SELECT text FROM dataset_table;"
                        df = pd.read_sql_query(query, conn)
                        data.extend(df.to_dict("records"))

                    elif filename.endswith(".feather"):
                        df = feather.read_feather(filepath)
                        data.extend(df.to_dict("records"))

                if hasattr(self, "map_data") and self.map_data:
                    fn = eval(self.map_data)  # type: ignore
                    data = [fn(d) for d in data]
                else:
                    data = data

                return Dataset.from_pandas(pd.DataFrame(data))
        except Exception as e:
            self.log.exception(f"Error occurred when loading dataset from {dataset_path}. Error: {e}")
            raise

    def complete(
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
        awq_enabled: bool = False,
        flash_attention: bool = False,
        decoding_strategy: str = "generate",
        notification_email: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Performs text completion on the loaded dataset using the specified model and tokenizer. The method handles the
        entire process, including model loading, text generation, and saving the results.

        Args:
            model_name (str): The name of the language model to use for text completion.
            model_class (str, optional): The class of the language model. Defaults to "AutoModelForCausalLM".
            tokenizer_class (str, optional): The class of the tokenizer. Defaults to "AutoTokenizer".
            use_cuda (bool, optional): Whether to use CUDA for model inference. Defaults to False.
            precision (str, optional): Precision for model computation. Defaults to "float16".
            quantization (int, optional): Level of quantization for optimizing model size and speed. Defaults to 0.
            device_map (str | Dict | None, optional): Specific device to use for computation. Defaults to "auto".
            max_memory (Dict, optional): Maximum memory configuration for devices. Defaults to {0: "24GB"}.
            torchscript (bool, optional): Whether to use a TorchScript-optimized version of the pre-trained language model. Defaults to False.
            compile (bool, optional): Whether to compile the model before fine-tuning. Defaults to True.
            awq_enabled (bool, optional): Whether to enable AWQ optimization. Defaults to False.
            flash_attention (bool, optional): Whether to use flash attention optimization. Defaults to False.
            decoding_strategy (str, optional): Strategy for decoding the completion. Defaults to "generate".
            **kwargs: Additional keyword arguments for text generation.
        """
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
        self.tokenizer_name = tokenizer_name
        self.model_revision = model_revision
        self.tokenizer_revision = tokenizer_revision
        self.model_class = model_class
        self.tokenizer_class = tokenizer_class
        self.use_cuda = use_cuda
        self.precision = precision
        self.quantization = quantization
        self.device_map = device_map
        self.max_memory = max_memory
        self.torchscript = torchscript
        self.awq_enabled = awq_enabled
        self.flash_attention = flash_attention
        self.notification_email = notification_email
        self.compile = compile

        model_args = {k.replace("model_", ""): v for k, v in kwargs.items() if "model_" in k}
        self.model_args = model_args

        generation_args = {k.replace("generation_", ""): v for k, v in kwargs.items() if "generation_" in k}
        self.generation_args = generation_args

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
            compile=self.compile,
            **self.model_args,
        )

        dataset_path = self.input.input_folder
        output_path = self.output.output_folder

        # Load dataset
        _dataset = self.load_dataset(dataset_path)
        if _dataset is None:
            self.log.error("Failed to load dataset.")
            return
        dataset = _dataset["text"]

        prompts = []
        completions = []
        for _, prompt in enumerate(dataset):
            completion = self.generate(
                prompt=prompt,
                decoding_strategy=decoding_strategy,
                **generation_args,
            )
            completions.append(completion)
            prompts.append(prompt)

        self._save_completions(completions, prompts, output_path)
        self.done()

    def complete_vllm(
        self,
        model_name: str,
        use_cuda: bool = False,
        precision: str = "float16",
        quantization: int = 0,
        device_map: str | Dict | None = "auto",
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
        # Generate params
        notification_email: Optional[str] = None,
        batch_size: int = 32,
        **kwargs: Any,
    ) -> None:
        """
        Performs bulk text generation using the Versatile Language Learning Model (VLLM) with specified parameters
        for fine-tuning model behavior, including quantization and parallel processing settings. This method is designed
        to process large datasets efficiently by leveraging VLLM capabilities for generating high-quality text completions
        based on provided prompts.

        Args:
            model_name (str): The name or path of the VLLM model to use for text generation.
            use_cuda (bool): Flag indicating whether to use CUDA for GPU acceleration.
            precision (str): Precision of computations, can be "float16", "bfloat16", etc.
            quantization (int): Level of quantization for model weights, 0 for none.
            device_map (str | Dict | None): Specific device(s) to use for model inference.
            vllm_tokenizer_mode (str): Mode of the tokenizer ("auto", "fast", or "slow").
            vllm_download_dir (Optional[str]): Directory to download and load the model and tokenizer.
            vllm_load_format (str): Format to load the model, e.g., "auto", "pt".
            vllm_seed (int): Seed for random number generation.
            vllm_max_model_len (int): Maximum sequence length the model can handle.
            vllm_enforce_eager (bool): Enforce eager execution instead of using optimization techniques.
            vllm_max_context_len_to_capture (int): Maximum context length for CUDA graph capture.
            vllm_block_size (int): Block size for caching mechanism.
            vllm_gpu_memory_utilization (float): Fraction of GPU memory to use.
            vllm_swap_space (int): Amount of swap space to use in GiB.
            vllm_sliding_window (Optional[int]): Size of the sliding window for processing.
            vllm_pipeline_parallel_size (int): Number of pipeline parallel groups.
            vllm_tensor_parallel_size (int): Number of tensor parallel groups.
            vllm_worker_use_ray (bool): Whether to use Ray for model workers.
            vllm_max_parallel_loading_workers (Optional[int]): Maximum number of workers for parallel loading.
            vllm_disable_custom_all_reduce (bool): Disable custom all-reduce kernel and fall back to NCCL.
            vllm_max_num_batched_tokens (Optional[int]): Maximum number of tokens to be processed in a single iteration.
            vllm_max_num_seqs (int): Maximum number of sequences to be processed in a single iteration.
            vllm_max_paddings (int): Maximum number of paddings to be added to a batch.
            vllm_max_lora_rank (Optional[int]): Maximum rank for LoRA adjustments.
            vllm_max_loras (Optional[int]): Maximum number of LoRA adjustments.
            vllm_max_cpu_loras (Optional[int]): Maximum number of LoRA adjustments stored on CPU.
            vllm_lora_extra_vocab_size (int): Additional vocabulary size for LoRA.
            vllm_placement_group (Optional[dict]): Ray placement group for distributed execution.
            vllm_log_stats (bool): Whether to log statistics during model operation.
            notification_email (Optional[str]): Email to send notifications upon completion.
            batch_size (int): Number of prompts to process in each batch for efficient memory usage.
            **kwargs: Additional keyword arguments for generation settings like temperature, top_p, etc.

        This method automates the loading of large datasets, generation of text completions, and saving results,
        facilitating efficient and scalable text generation tasks.
        """
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
        self.tokenizer_name = tokenizer_name
        self.model_revision = model_revision
        self.tokenizer_revision = tokenizer_revision
        self.use_cuda = use_cuda
        self.precision = precision
        self.quantization = quantization
        self.device_map = device_map
        self.notification_email = notification_email

        self.model: LLM = self.load_models_vllm(
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
            batched_inference=True,
        )

        generation_args = {k.replace("generation_", ""): v for k, v in kwargs.items() if "generation_" in k}
        self.generation_args = generation_args

        dataset_path = self.input.input_folder
        output_path = self.output.output_folder

        # Load dataset
        _dataset = self.load_dataset(dataset_path)
        if _dataset is None:
            self.log.error("Failed to load dataset.")
            return
        dataset = _dataset["text"]

        for i in range(0, len(dataset), batch_size):
            batch = dataset[i : i + batch_size]

            outputs = self.model.generate(
                prompts=batch,
                sampling_params=SamplingParams(
                    n=generation_args.get("n", 1),
                    best_of=generation_args.get("best_of", None),
                    presence_penalty=generation_args.get("presence_penalty", 0.0),
                    frequency_penalty=generation_args.get("frequency_penalty", 0.0),
                    repetition_penalty=generation_args.get("repetition_penalty", 1.0),
                    temperature=generation_args.get("temperature", 1.0),
                    top_p=generation_args.get("top_p", 1.0),
                    top_k=generation_args.get("top_k", -1),
                    min_p=generation_args.get("min_p", 0.0),
                    use_beam_search=generation_args.get("use_beam_search", False),
                    length_penalty=generation_args.get("length_penalty", 1.0),
                    early_stopping=generation_args.get("early_stopping", False),
                    stop=generation_args.get("stop", None),
                    stop_token_ids=generation_args.get("stop_token_ids", None),
                    include_stop_str_in_output=generation_args.get("include_stop_str_in_output", False),
                    ignore_eos=generation_args.get("ignore_eos", False),
                    max_tokens=generation_args.get("max_tokens", 16),
                    logprobs=generation_args.get("logprobs", None),
                    prompt_logprobs=generation_args.get("prompt_logprobs", None),
                    skip_special_tokens=generation_args.get("skip_special_tokens", True),
                    spaces_between_special_tokens=generation_args.get("spaces_between_special_tokens", True),
                    logits_processors=generation_args.get("logits_processors", None),
                ),
            )
            completions = [" ".join(t.text for t in o.outputs) for o in outputs]
            self._save_completions(completions, batch, output_path)
        self.done()

    def complete_llama_cpp(
        self,
        model: str,
        filename: Optional[str] = None,
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
        notification_email: Optional[str] = None,
        **kwargs,
    ) -> None:
        """
        Performs bulk text generation using the LLaMA model with llama.cpp backend. This method handles the entire
        process, including model loading, prompt processing, text generation, and saving the results.

        Args:
            model: Path or identifier for the LLaMA model.
            filename: Optional filename or glob pattern to match the model file.
            local_dir: Local directory to save the model files.
            n_gpu_layers: Number of layers to offload to GPU.
            split_mode: Split mode for distributing model across GPUs.
            main_gpu: Main GPU index.
            tensor_split: Configuration for tensor splitting across GPUs.
            vocab_only: Whether to load only the vocabulary.
            use_mmap: Use memory-mapped files for model loading.
            use_mlock: Lock model data in RAM to prevent swapping.
            kv_overrides: Key-value pairs for overriding model config.
            seed: Seed for random number generation.
            n_ctx: Number of context tokens for generation.
            n_batch: Batch size for processing.
            n_threads: Number of threads for generation.
            n_threads_batch: Number of threads for batch processing.
            rope_scaling_type: Scaling type for RoPE.
            rope_freq_base: Base frequency for RoPE.
            rope_freq_scale: Frequency scaling for RoPE.
            yarn_ext_factor: YaRN extrapolation factor.
            yarn_attn_factor: YaRN attention factor.
            yarn_beta_fast: YaRN beta fast parameter.
            yarn_beta_slow: YaRN beta slow parameter.
            yarn_orig_ctx: Original context size for YaRN.
            mul_mat_q: Multiply matrices for queries.
            logits_all: Return logits for all tokens.
            embedding: Enable embedding mode.
            offload_kqv: Offload K, Q, V matrices to GPU.
            last_n_tokens_size: Size for the last_n_tokens buffer.
            lora_base: Base model path for LoRA.
            lora_scale: Scale factor for LoRA adjustments.
            lora_path: Path for LoRA adjustments.
            numa: NUMA configuration.
            chat_format: Chat format configuration.
            chat_handler: Handler for chat completions.
            draft_model: Draft model for speculative decoding.
            tokenizer: Custom tokenizer instance.
            verbose: Enable verbose logging.
            notification_email (Optional[str]): Email to send notifications upon completion.
            **kwargs: Additional arguments for model loading and text generation.
        """
        self.notification_email = notification_email

        # Loading the LLaMA model with llama.cpp
        llama_model, custom_tokenizer = self.load_models_llama_cpp(
            model=model,
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

        generation_args = {k.replace("generation_", ""): v for k, v in kwargs.items() if "generation_" in k}
        self.generation_args = generation_args

        dataset_path = self.input.input_folder
        output_path = self.output.output_folder

        # Load dataset
        _dataset = self.load_dataset(dataset_path)
        if _dataset is None:
            self.log.error("Failed to load dataset.")
            return
        dataset = _dataset["instruction"]

        for i in range(0, len(dataset), n_batch):
            batch = dataset[i : i + n_batch]
            completions = []

            for prompt in batch:
                # Generate completion for each prompt using llama_model
                completion = llama_model.create_completion(
                    prompt=prompt,
                    suffix=generation_args.get("suffix", None),
                    max_tokens=generation_args.get("max_tokens", 16),
                    temperature=generation_args.get("temperature", 0.8),
                    top_p=generation_args.get("top_p", 0.95),
                    min_p=generation_args.get("min_p", 0.05),
                    typical_p=generation_args.get("typical_p", 1.0),
                    logprobs=generation_args.get("logprobs", None),
                    echo=generation_args.get("echo", False),
                    stop=generation_args.get("stop", []),
                    frequency_penalty=generation_args.get("frequency_penalty", 0.0),
                    presence_penalty=generation_args.get("presence_penalty", 0.0),
                    repeat_penalty=generation_args.get("repeat_penalty", 1.1),
                    top_k=generation_args.get("top_k", 40),
                    seed=generation_args.get("seed", None),
                    tfs_z=generation_args.get("tfs_z", 1.0),
                    mirostat_mode=generation_args.get("mirostat_mode", 0),
                    mirostat_tau=generation_args.get("mirostat_tau", 5.0),
                    mirostat_eta=generation_args.get("mirostat_eta", 0.1),
                    model=generation_args.get("model", None),
                    stopping_criteria=generation_args.get("stopping_criteria", None),
                    logits_processor=generation_args.get("logits_processor", None),
                    grammar=generation_args.get("grammar", None),
                    logit_bias=generation_args.get("logit_bias", None),
                )
                completions.append(completion)

            self._save_completions([c["choices"][0]["text"] for c in completions], batch, output_path)  # type: ignore
        self.done()

    def _save_completions(self, completions: List[str], prompts: List[str], output_path: str) -> None:
        """
        Saves the generated completions to the specified output path.

        Args:
            completions (List[str]): The list of generated text completions.
            prompts (List[str]): The list of prompts corresponding to the completions.
            output_path (str): The path to save the completion results.

        This method is called internally by the complete method to persist the completion results.
        """
        data_to_save = [
            {"prompt": prompt, "completion": completion} for prompt, completion in zip(prompts, completions)
        ]
        with open(os.path.join(output_path, f"completions-{str(uuid.uuid4())}.json"), "w") as f:
            json.dump(data_to_save, f)
