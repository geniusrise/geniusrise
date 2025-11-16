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

from typing import Any, Dict, Optional, Tuple
import os
import json
import threading
import torch
import transformers
import cherrypy
from geniusrise import BatchInput, BatchOutput, Bolt, State
from geniusrise.logging import setup_logger
from transformers import AutoModel, AutoProcessor
from geniusrise.inference.vision.utils.communication import send_email
from uform.gen_model import VLMForCausalLM, VLMProcessor
from optimum.bettertransformer import BetterTransformer


# Define a global lock for sequential access control
sequential_lock = threading.Lock()


class VisionBulk(Bolt):
    """
    A class representing the VisionBulk operations that inherits from Bolt.

    This class encapsulates methods for loading and utilizing models for image-related bulk operations.
    It must be subclassed with an implementation for the 'generate' method which is specific to the inheriting class.

    Attributes:
        model (Any): The machine learning model used for processing.
        processor (Any): The processor used for preparing data for the model.

    Args:
        input (BatchInput): A data structure containing input data batches.
        output (BatchOutput): A data structure to store the output data from the model.
        state (State): An object representing the state of the processing operation.
    """

    model: Any
    processor: Any

    def __init__(
        self,
        input: BatchInput,
        output: BatchOutput,
        state: State,
    ):
        """
        Initializes the VisionBulk instance with input data, output data holder, and state.

        Args:
            input (BatchInput): The input data for the bulk operation.
            output (BatchOutput): The holder for the output results of the bulk operation.
            state (State): The state of the bulk operation, containing any required metadata or context.
        """
        super().__init__(input=input, output=output, state=state)
        self.log = setup_logger(self)

    def generate(*args, **kwargs):
        """
        Generates results based on the loaded models and input data.

        This method is a placeholder and must be implemented by subclasses.
        """
        raise NotImplementedError("Has to be implemented by every inheriting class")

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
        processor_name: str,
        model_revision: Optional[str] = None,
        processor_revision: Optional[str] = None,
        model_class: str = "AutoModel",
        processor_class: str = "AutoProcessor",
        use_cuda: bool = False,
        precision: str = "float16",
        quantization: int = 0,
        device_map: str | Dict | None = "auto",
        max_memory={0: "24GB"},
        torchscript: bool = False,
        compile: bool = False,
        flash_attention: bool = False,
        better_transformers: bool = False,
        **model_args: Any,
    ) -> Tuple[AutoModel, AutoProcessor]:
        """
        Loads the model and processor necessary for image processing tasks.

        Args:
            model_name (str): The name of the model to be loaded from Hugging Face's model repository.
            processor_name (str): The name of the processor to be used for preprocessing the data.
            model_revision (Optional[str]): The specific revision of the model to be loaded.
            processor_revision (Optional[str]): The specific revision of the processor to be loaded.
            model_class (str): The class name of the model to be loaded from the transformers package.
            processor_class (str): The class name of the processor to be loaded.
            use_cuda (bool): Flag to utilize CUDA for GPU acceleration.
            precision (str): The floating-point precision to be used by the model. Options are 'float32', 'float16', 'bfloat16'.
            quantization (int): The bit level for model quantization (0 for none, 8 for 8-bit quantization).
            device_map (Union[str, Dict, None]): The device mapping for model parallelism. 'auto' or specific mapping dict.
            max_memory (Dict[int, str]): The maximum memory configuration for the model per device.
            torchscript (bool): Flag to enable TorchScript for model optimization.
            compile (bool): Flag to enable JIT compilation of the model.
            flash_attention (bool): Flag to enable Flash Attention optimization for faster processing.
            better_transformers (bool): Flag to enable Better Transformers optimization for faster processing.
            **model_args (Any): Additional arguments to be passed to the model's 'from_pretrained' method.

        Returns:
            Tuple[AutoModelForCausalLM, AutoProcessor]: A tuple containing the loaded model and processor.
        """
        self.log.info(f"Loading Hugging Face model: {model_name}")

        torch_dtype = self._get_torch_dtype(precision)

        if use_cuda and not device_map:
            device_map = "auto"

        # Note: exception for Uform models
        if "uform" in model_name.lower():
            model = VLMForCausalLM.from_pretrained(model_name)
            processor = VLMProcessor.from_pretrained(processor_name)
            if use_cuda:
                model = model.to(device_map)

            return model, processor

        ModelClass = getattr(transformers, model_class)
        processorClass = getattr(transformers, processor_class)

        # Load the model and processor
        if model_name == "local":
            processor = processorClass.from_pretrained(
                os.path.join(self.input.get(), "/model"), torch_dtype=torch_dtype
            )
        else:
            processor = processorClass.from_pretrained(
                processor_name, revision=processor_revision, torch_dtype=torch_dtype
            )

        self.log.info(f"Loading model from {model_name} {model_revision} with {model_args}")

        if flash_attention:
            model_args = {**model_args, **{"attn_implementation": "flash_attention_2"}}

        if quantization == 8:
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

        self.log.debug("Hugging Face model and processor loaded successfully.")
        return model, processor

    def done(self):
        if self.notification_email:
            self.output.flush()
            send_email(recipient=self.notification_email, bucket_name=self.output.bucket, prefix=self.output.s3_folder)


class VisionAPI(VisionBulk):
    """
    The VisionAPI class inherits from VisionBulk and is designed to facilitate
    the handling of vision-based tasks using a pre-trained machine learning model.
    It sets up a server to process image-related requests using a specified model.
    """

    model: Any
    processor: Any

    def __init__(
        self,
        input: BatchInput,
        output: BatchOutput,
        state: State,
    ):
        """
        Initializes the VisionAPI object with batch input, output, and state.

        Args:
            input (BatchInput): Object to handle batch input operations.
            output (BatchOutput): Object to handle batch output operations.
            state (State): Object to maintain the state of the API.
        """
        super().__init__(input=input, output=output, state=state)
        self.log = setup_logger(self)

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
        model_class: str = "AutoModel",
        processor_class: str = "AutoProcessor",
        device_map: str | Dict | None = "auto",
        max_memory={0: "24GB"},
        use_cuda: bool = False,
        precision: str = "float16",
        quantization: int = 0,
        torchscript: bool = False,
        compile: bool = False,
        flash_attention: bool = False,
        better_transformers: bool = False,
        concurrent_queries: bool = False,
        endpoint: str = "*",
        port: int = 3000,
        cors_domain: str = "http://localhost:3000",
        username: Optional[str] = None,
        password: Optional[str] = None,
        **model_args: Any,
    ) -> None:
        """
        Configures and starts a CherryPy server to listen for image processing requests.

        Args:
            model_name (str): The name of the pre-trained vision model.
            model_class (str, optional): The class of the pre-trained vision model. Defaults to "AutoModel".
            processor_class (str, optional): The class of the processor for input image preprocessing. Defaults to "AutoProcessor".
            device_map (str | Dict | None, optional): Device mapping for model inference. Defaults to "auto".
            max_memory (Dict[int, str], optional): Maximum memory allocation for model inference. Defaults to {0: "24GB"}.
            precision (str): The floating-point precision to be used by the model. Options are 'float32', 'float16', 'bfloat16'.
            quantization (int): The bit level for model quantization (0 for none, 8 for 8-bit quantization).
            torchscript (bool, optional): Whether to use TorchScript for model optimization. Defaults to True.
            compile (bool, optional): Whether to compile the model before fine-tuning. Defaults to False.
            flash_attention (bool): Whether to use flash attention 2. Default is False.
            better_transformers (bool): Flag to enable Better Transformers optimization for faster processing.
            concurrent_queries: (bool): Whether the API supports concurrent API calls (usually false).
            endpoint (str, optional): The network endpoint for the server. Defaults to "*".
            port (int, optional): The network port for the server. Defaults to 3000.
            cors_domain (str, optional): The domain to allow for CORS requests. Defaults to "http://localhost:3000".
            username (Optional[str], optional): Username for server authentication. Defaults to None.
            password (Optional[str], optional): Password for server authentication. Defaults to None.
            **model_args (Any): Additional arguments for the vision model.
        """
        self.model_name = model_name
        self.model_class = model_class
        self.processor_class = processor_class
        self.device_map = device_map
        self.max_memory = max_memory
        self.use_cuda = use_cuda
        self.precision = precision
        self.quantization = quantization
        self.torchscript = torchscript
        self.compile = compile
        self.flash_attention = flash_attention
        self.better_transformers = better_transformers
        self.concurrent_queries = concurrent_queries
        self.model_args = model_args
        self.username = username
        self.password = password

        # Extract model revision details if specified in model_name
        if ":" in model_name:
            model_revision = model_name.split(":")[1]
            processor_revision = model_name.split(":")[1]
            model_name = model_name.split(":")[0]
            processor_name = model_name
        else:
            model_revision = None
            processor_revision = None

        # Store model and processor details
        self.model_name = model_name
        self.model_revision = model_revision
        self.processor_name = model_name
        self.processor_revision = processor_revision

        if model_name not in ["easyocr", "mmocr", "paddleocr"]:
            # Load the specified models with the given configurations
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
                flash_attention=self.flash_attention,
                better_transformers=self.better_transformers,
                # **self.model_args,
            )

        def sequential_locker():
            if self.concurrent_queries:
                sequential_lock.acquire()

        def sequential_unlocker():
            if self.concurrent_queries:
                sequential_lock.release()

        def CORS():
            """
            Configures Cross-Origin Resource Sharing (CORS) for the server.
            This allows the server to accept requests from the specified domain.
            """
            # Setting up CORS headers
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
