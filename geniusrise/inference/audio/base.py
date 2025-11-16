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
import multiprocessing
import os
import threading
from typing import Any, Dict, List, Optional, Tuple, Union

import boto3
import cherrypy
import torch
import transformers
from faster_whisper import WhisperModel
from geniusrise import BatchInput, BatchOutput, State
from geniusrise.logging import setup_logger
from transformers import (
    AutoConfig,
    AutoFeatureExtractor,
    AutoModelForAudioClassification,
    AutoProcessor,
)
from whispercpp import Whisper

# Define a global lock for sequential access control
sequential_lock = threading.Lock()


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


class AudioBulk:
    """
    AudioBulk is a class designed for bulk processing of audio data using various audio models from Hugging Face.
    It focuses on audio generation and transformation tasks, supporting a range of models and configurations.

    Attributes:
        model (AutoModelForAudioClassification): The audio model for generation or transformation tasks.
        processor (AutoFeatureExtractor): The processor for preparing input data for the model.

    Args:
        input (BatchInput): Configuration and data inputs for the batch process.
        output (BatchOutput): Configurations for output data handling.
        state (State): State management for the Bolt.
        **kwargs: Arbitrary keyword arguments for extended configurations.

    Methods:
        audio(**kwargs: Any) -> Dict[str, Any]:
            Provides an API endpoint for audio processing functionality.
            Accepts various parameters for customizing the audio processing tasks.

        process(audio_input: Union[str, bytes], **processing_params: Any) -> dict:
            Processes the audio input based on the provided parameters. Supports multiple processing methods.
    """

    model: AutoModelForAudioClassification
    processor: AutoFeatureExtractor | AutoProcessor

    def __init__(
        self,
        input: BatchInput,
        output: BatchOutput,
        state: State,
        **kwargs,
    ):
        """
        Initializes the AudioBulk with configurations and sets up logging.
        Prepares the environment for audio processing tasks.

        Args:
            input (BatchInput): The input data configuration for the audio processing task.
            output (BatchOutput): The output data configuration for the results of the audio processing.
            state (State): The state configuration for the Bolt, managing its operational status.
            **kwargs: Additional keyword arguments for extended functionality and model configurations.
        """
        self.input = input
        self.output = output
        self.state = state
        self.log = setup_logger(self)

    def load_models(
        self,
        model_name: str,
        processor_name: str,
        model_revision: Optional[str] = None,
        processor_revision: Optional[str] = None,
        model_class: str = "",
        processor_class: str = "AutoFeatureExtractor",
        use_cuda: bool = False,
        precision: str = "float16",
        quantization: int = 0,
        device_map: Union[str, Dict, None] = "auto",
        max_memory: Dict[int, str] = {0: "24GB"},
        torchscript: bool = False,
        compile: bool = False,
        flash_attention: bool = False,
        better_transformers: bool = False,
        use_whisper_cpp: bool = False,
        use_faster_whisper: bool = False,
        **model_args: Any,
    ) -> Tuple[AutoModelForAudioClassification, AutoFeatureExtractor]:
        """
        Loads and configures the specified audio model and processor for audio processing.

        Args:
            model_name (str): Name or path of the audio model to load.
            processor_name (str): Name or path of the processor to load.
            model_revision (Optional[str]): Specific model revision to load (e.g., commit hash).
            processor_revision (Optional[str]): Specific processor revision to load.
            model_class (str): Class of the model to be loaded.
            processor_class (str): Class of the processor to be loaded.
            use_cuda (bool): Flag to use CUDA for GPU acceleration.
            precision (str): Desired precision for computations ("float32", "float16", etc.).
            quantization (int): Bit level for model quantization (0 for none, 8 for 8-bit).
            device_map (Union[str, Dict, None]): Specific device(s) for model operations.
            max_memory (Dict[int, str]): Maximum memory allocation for the model.
            torchscript (bool): Enable TorchScript for model optimization.
            compile (bool): Enable Torch JIT compilation.
            flash_attention (bool): Flag to enable Flash Attention optimization for faster processing.
            better_transformers (bool): Flag to enable Better Transformers optimization for faster processing.
            use_whisper_cpp (bool): Whether to use whisper.cpp to load the model. Defaults to False. Note: only works for these models: https://github.com/aarnphm/whispercpp/blob/524dd6f34e9d18137085fb92a42f1c31c9c6bc29/src/whispercpp/utils.py#L32
            use_faster_whisper (bool): Whether to use faster-whisper.
            **model_args (Any): Additional arguments for model loading.

        Returns:
            Tuple[AutoModelForAudioClassification, AutoFeatureExtractor]: Loaded model and processor.
        """
        self.log.info(f"Loading audio model: {model_name}")

        if use_whisper_cpp:
            if model_name == "local":
                raise Exception("Local models or custom models are not supported yet")
            return (
                self.load_models_whisper_cpp(
                    model_name=model_name,
                    basedir=self.output.output_folder,
                ),
                None,
            )
        elif use_faster_whisper:
            if model_name == "local":
                raise Exception("Local models or custom models are not supported yet")
            return (
                self.load_models_faster_whisper(
                    model_name=model_name,
                    device_map=device_map if type(device_map) is str else "auto",
                    precision=precision,
                    cpu_threads=multiprocessing.cpu_count(),
                    num_workers=1,
                    download_root=None,
                ),
                None,
            )

        # Determine torch dtype based on precision
        torch_dtype = self._get_torch_dtype(precision)

        # Configure device map for CUDA
        if use_cuda and not device_map:
            device_map = "auto"

        # Load the model and processor
        FeatureExtractorClass = getattr(transformers, processor_class)
        config = AutoConfig.from_pretrained(processor_name, revision=processor_revision)

        if model_name == "local":
            processor = FeatureExtractorClass.from_pretrained(
                os.path.join(self.input.get(), "/model"), torch_dtype=torch_dtype
            )
        else:
            processor = FeatureExtractorClass.from_pretrained(
                processor_name, revision=processor_revision, torch_dtype=torch_dtype
            )

        ModelClass = getattr(transformers, model_class)
        if quantization == 8:
            if model_name == "local":
                model = ModelClass.from_pretrained(
                    os.path.join(self.input.get(), "/model"),
                    max_memory=max_memory,
                    load_in_8bit=True,
                    config=config,
                    **model_args,
                )
            else:
                model = ModelClass.from_pretrained(
                    model_name,
                    revision=model_revision,
                    max_memory=max_memory,
                    load_in_8bit=True,
                    config=config,
                    **model_args,
                )
        elif quantization == 4:
            if model_name == "local":
                model = ModelClass.from_pretrained(
                    os.path.join(self.input.get(), "/model"),
                    max_memory=max_memory,
                    load_in_4bit=True,
                    config=config,
                    **model_args,
                )
            else:
                model = ModelClass.from_pretrained(
                    model_name,
                    revision=model_revision,
                    max_memory=max_memory,
                    load_in_4bit=True,
                    config=config,
                    **model_args,
                )
        else:
            if model_name == "local":
                model = ModelClass.from_pretrained(
                    os.path.join(self.input.get(), "/model"),
                    torch_dtype=torch_dtype,
                    max_memory=max_memory,
                    config=config,
                    **model_args,
                )
            else:
                model = ModelClass.from_pretrained(
                    model_name,
                    revision=model_revision,
                    torch_dtype=torch_dtype,
                    max_memory=max_memory,
                    config=config,
                    **model_args,
                )

        if quantization == 0:
            model = model.to(device_map)
        if compile:
            model = torch.compile(model)

        if better_transformers:
            try:
                model = model.to_bettertransformer()
            except Exception as _:
                pass  # hf raises error for whisper cause it has eaten another lib

        # Set to evaluation mode for inference
        model.eval()

        self.log.debug("Audio model and processor loaded successfully.")
        return model, processor

    def load_models_whisper_cpp(self, model_name: str, basedir: str):
        return Whisper.from_pretrained(
            model_name=model_name,
            basedir=basedir,
        )

    def load_models_faster_whisper(
        self,
        model_name,
        device_map: str = "auto",
        precision="float16",
        quantization=0,
        cpu_threads=4,
        num_workers=1,
        download_root=None,
    ):
        return WhisperModel(
            model_size_or_path=model_name,
            device=device_map.split(":")[0] if ":" in device_map else device_map,
            device_index=int(device_map.replace("cuda:", "").replace("mps:", "")) if "cuda:" in device_map else 0,
            compute_type=precision if quantization == 0 else f"int{quantization}_{precision}",
            cpu_threads=cpu_threads,
            num_workers=num_workers,
            download_root=download_root,
            local_files_only=False,
        )

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

    def _done(self):
        """
        Finalizes the AudioBulk processing. Sends notification email if configured.

        This method should be called after all audio processing tasks are complete.
        It handles any final steps such as sending notifications or cleaning up resources.
        """
        if self.notification_email:
            self.output.flush()
            send_email(recipient=self.notification_email, bucket_name=self.output.bucket, prefix=self.output.s3_folder)


class AudioAPI(AudioBulk):
    """
    A class representing a Hugging Face API for generating text using a pre-trained language model.

    Attributes:
        model (Any): The pre-trained language model.
        processor (Any): The processor used to preprocess input text.
        model_name (str): The name of the pre-trained language model.
        model_revision (Optional[str]): The revision of the pre-trained language model.
        processor_name (str): The name of the processor used to preprocess input text.
        processor_revision (Optional[str]): The revision of the processor used to preprocess input text.
        model_class (str): The name of the class of the pre-trained language model.
        processor_class (str): The name of the class of the processor used to preprocess input text.
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

        listen(model_name: str, model_class: str = "AutoModelForCausalLM", processor_class: str = "AutoProcessor", use_cuda: bool = False, precision: str = "float16", quantization: int = 0, device_map: str | Dict | None = "auto", max_memory={0: "24GB"}, torchscript: bool = True, endpoint: str = "*", port: int = 3000, cors_domain: str = "http://localhost:3000", username: Optional[str] = None, password: Optional[str] = None, **model_args: Any) -> None:
            Starts a CherryPy server to listen for requests to generate text.
    """

    model: Any
    processor: Any

    def __init__(
        self,
        input: BatchInput,
        output: BatchOutput,
        state: State,
        **kwargs,
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

    def __validate_password(self, realm, username, password):
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
        model_class: str = "AutoModel",
        processor_class: str = "AutoProcessor",
        use_cuda: bool = False,
        precision: str = "float16",
        quantization: int = 0,
        device_map: str | Dict | None = "auto",
        max_memory={0: "24GB"},
        torchscript: bool = False,
        compile: bool = False,
        concurrent_queries: bool = False,
        use_whisper_cpp: bool = False,
        use_faster_whisper: bool = False,
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
            model_name (str): The name of the pre-trained language model.
            model_class (str, optional): The name of the class of the pre-trained language model. Defaults to "AutoModelForCausalLM".
            processor_class (str, optional): The name of the class of the processor used to preprocess input text. Defaults to "AutoProcessor".
            use_cuda (bool, optional): Whether to use a GPU for inference. Defaults to False.
            precision (str, optional): The precision to use for the pre-trained language model. Defaults to "float16".
            quantization (int, optional): The level of quantization to use for the pre-trained language model. Defaults to 0.
            device_map (str | Dict | None, optional): The mapping of devices to use for inference. Defaults to "auto".
            max_memory (Dict[int, str], optional): The maximum memory to use for inference. Defaults to {0: "24GB"}.
            torchscript (bool, optional): Whether to use a TorchScript-optimized version of the pre-trained language model. Defaults to True.
            compile (bool): Enable Torch JIT compilation.
            concurrent_queries: (bool): Whether the API supports concurrent API calls (usually false).
            use_whisper_cpp (bool): Whether to use whisper.cpp to load the model. Defaults to False. Note: only works for these models: https://github.com/aarnphm/whispercpp/blob/524dd6f34e9d18137085fb92a42f1c31c9c6bc29/src/whispercpp/utils.py#L32
            use_faster_whisper (bool): Whether to use faster-whisper.
            endpoint (str, optional): The endpoint to listen on. Defaults to "*".
            port (int, optional): The port to listen on. Defaults to 3000.
            cors_domain (str, optional): The domain to allow CORS requests from. Defaults to "http://localhost:3000".
            username (Optional[str], optional): The username to use for authentication. Defaults to None.
            password (Optional[str], optional): The password to use for authentication. Defaults to None.
            **model_args (Any): Additional arguments to pass to the pre-trained language model.
        """
        self.model_name = model_name
        self.model_class = model_class
        self.processor_class = processor_class
        self.use_cuda = use_cuda
        self.quantization = quantization
        self.precision = precision
        self.device_map = device_map
        self.max_memory = max_memory
        self.torchscript = torchscript
        self.compile = compile
        self.concurrent_queries = concurrent_queries
        self.use_whisper_cpp = use_whisper_cpp
        self.use_faster_whisper = use_faster_whisper
        self.model_args = model_args
        self.username = username
        self.password = password

        if ":" in model_name:
            model_revision = model_name.split(":")[1]
            processor_revision = model_name.split(":")[1]
            model_name = model_name.split(":")[0]
            processor_name = model_name
        else:
            model_revision = None
            processor_revision = None
        processor_name = model_name
        self.model_name = model_name
        self.model_revision = model_revision
        self.processor_name = processor_name
        self.processor_revision = processor_revision

        self.model, self.processor = self.load_models(
            model_name=self.model_name,
            processor_name=self.processor_name,
            model_revision=self.model_revision,
            processor_revision=self.processor_revision,
            model_class=self.model_class,
            processor_class=self.processor_class,
            use_cuda=self.use_cuda,
            precision=self.precision,
            quantization=self.quantization,
            device_map=self.device_map,
            max_memory=self.max_memory,
            torchscript=self.torchscript,
            compile=self.compile,
            use_whisper_cpp=use_whisper_cpp,
            use_faster_whisper=use_faster_whisper,
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
                    "tools.auth_basic.checkpassword": self.__validate_password,
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
