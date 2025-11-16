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

from geniusrise import BatchInput, BatchOutput, State
from geniusrise.inference.vision.base import VisionBulk
from datasets import Dataset, DatasetDict, load_dataset, load_from_disk
from typing import Dict, Optional, Union, Tuple
import torchvision.transforms as transforms
import os
import torch
import numpy as np
import json
from PIL import Image
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ImageClassificationBulk")


class ImageClassificationBulk(VisionBulk):
    """
    ImageClassificationBulk class for bulk vision classification tasks using Hugging Face models.
    Inherits from VisionBulk.
    """

    def __init__(self, input: BatchInput, output: BatchOutput, state: State, **kwargs) -> None:

        super().__init__(input, output, state, **kwargs)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def load_dataset(
        self,
        dataset_path: str,
        **kwargs,
    ) -> Union[Dataset, DatasetDict, Optional[Dataset]]:
        """
        Load a dataset for image classification from a local path or Hugging Face Datasets.

        Args:
            dataset_path (Union[str, None], optional): The local path to the dataset directory. Defaults to None.
            **kwargs: Additional arguments.

        Returns:
            Union[Dataset, DatasetDict, Optional[Dataset]]: The loaded dataset.
        """

        if self.use_huggingface_dataset:
            dataset = load_dataset(self.huggingface_dataset)
        elif os.path.isfile(os.path.join(dataset_path, "dataset_info.json")):
            dataset = load_from_disk(dataset_path)
        else:
            dataset = self._load_local_dataset(dataset_path, **kwargs)

        if hasattr(self, "map_data") and self.map_data:
            fn = eval(self.map_data)
            dataset = dataset.map(fn)
        else:
            dataset = dataset

        return dataset

    def _load_local_dataset(self, dataset_path: str, image_size: Tuple[int, int] = (224, 224)) -> Dataset:
        """
        Load a dataset for image classification from a single folder containing images of various formats.

        Args:
            dataset_path (str): The path to the dataset directory.
            image_size (Tuple[int, int]): The size to resize images to.

        Returns:
            Dataset: The loaded dataset.
        """
        # Supported image formats
        supported_formats = [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".tif"]

        # List of all image file paths in the dataset directory
        image_files = [f for f in os.listdir(dataset_path) if os.path.splitext(f)[1].lower() in supported_formats]

        # Define a transform to resize the image and convert it to a tensor
        transform = transforms.Compose(
            [
                transforms.Resize(image_size),
                transforms.ToTensor(),
            ]
        )

        # Create a dataset using lists for each field
        images = []
        paths = []
        for image_file in image_files:
            image_path = os.path.join(dataset_path, image_file)
            try:
                with Image.open(image_path).convert("RGB") as img:
                    img_tensor = transform(img)
                    images.append(img_tensor)
                paths.append(image_path)
            except Exception as e:
                self.log.exception(f"Error processing {image_file}: {e}")

        # Convert lists to PyTorch Dataset
        return Dataset.from_dict({"image": images, "path": paths})

    def sigmoid(self, _outputs):
        """
        Apply the sigmoid function to batched outputs.
        """
        return 1.0 / (1.0 + np.exp(-_outputs))

    def softmax(self, _outputs):
        """
        Apply the softmax function to batched outputs.

        Args:
            _outputs (np.ndarray): Model logits of shape (batch_size, num_classes).

        Returns:
            np.ndarray: Softmax scores of shape (batch_size, num_classes).
        """
        # Ensure that the subtraction for numerical stability and softmax computation are done across the correct axis.
        maxes = np.max(_outputs, axis=1, keepdims=True)
        shifted_exp = np.exp(_outputs - maxes)
        softmax_scores = shifted_exp / shifted_exp.sum(axis=1, keepdims=True)
        return softmax_scores

    def classify(
        self,
        model_name,
        model_class: str = "AutoModelForImageClassification",
        processor_class: str = "AutoProcessor",
        use_cuda: bool = False,
        precision: str = "float16",
        quantization: int = 0,
        device_map: str | Dict | None = "auto",
        max_memory=None,
        torchscript=False,
        compile: bool = False,
        flash_attention: bool = False,
        better_transformers: bool = False,
        batch_size=32,
        use_huggingface_dataset: bool = False,
        huggingface_dataset: str = "",
        **kwargs,
    ) -> None:
        """
        Classifies vision data using a specified Hugging Face model.

        Args:
            model_name (str): Name or path of the model.
            model_class (str): Class name of the model (default "AutoModelForImageClassification").
            processor_class (str): Class name of the processor (default "AutoProcessor").
            use_cuda (bool): Whether to use CUDA for model inference (default False).
            precision (str): Precision for model computation (default "float").
            quantization (int): Level of quantization for optimizing model size and speed (default 0).
            device_map (str | Dict | None): Specific device to use for computation (default "auto").
            max_memory (Dict): Maximum memory configuration for devices.
            torchscript (bool, optional): Whether to use a TorchScript-optimized version of the pre-trained language model. Defaults to False.
            compile (bool, optional): Whether to compile the model before fine-tuning. Defaults to True.
            flash_attention (bool): Whether to use flash attention optimization (default False).
            batch_size (int): Number of classifications to process simultaneously (default 32).
            use_huggingface_dataset (bool, optional): Whether to load a dataset from huggingface hub.
            huggingface_dataset (str, optional): The huggingface dataset to use.
            **kwargs: Arbitrary keyword arguments for model and generation configurations.
        """
        self.model_class = model_class
        self.processor_class = processor_class
        self.use_cuda = use_cuda
        self.precision = precision
        self.quantization = quantization
        self.device_map = device_map
        self.max_memory = max_memory
        self.torchscript = torchscript
        self.compile = compile
        self.flash_attention = flash_attention
        self.better_transformers = better_transformers
        self.batch_size = batch_size
        self.use_huggingface_dataset = use_huggingface_dataset
        self.huggingface_dataset = huggingface_dataset

        if ":" in model_name:
            model_revision = model_name.split(":")[1]
            processor_revision = model_name.split(":")[1]
            model_name = model_name.split(":")[0]
            processor_name = model_name
        else:
            model_revision = None
            processor_revision = None
            processor_name = model_name

        # Store model and processor details
        self.model_name = model_name
        self.model_revision = model_revision
        self.processor_name = model_name
        self.processor_revision = processor_revision

        model_args = {k.replace("model_", ""): v for k, v in kwargs.items() if "model_" in k}
        self.model_args = model_args

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
            **self.model_args,
        )

        dataset_path = self.input.input_folder
        output_path = self.output.output_folder

        # Load dataset
        dataset = self.load_dataset(self.input.input_folder)
        if dataset is None:
            self.log.error("Failed to load dataset.")
            return

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Process and classify in batches
        for batch_idx in range(0, len(dataset["image"]), batch_size):

            batch_images = dataset["image"][batch_idx : batch_idx + batch_size]
            batch_paths = dataset["path"][batch_idx : batch_idx + batch_size]
            logger.info(f"Batch Path: {batch_paths}")

            # TODO: Make this truly batch-wise processing instead of processing one by one
            batch_inputs = self.processor(
                images=[Image.open(img_path) for img_path in batch_paths], return_tensors="pt", padding=True
            )
            if self.use_cuda:
                batch_inputs = {k: v.to(self.device_map) for k, v in batch_inputs.items()}

            with torch.no_grad():
                outputs = self.model(**batch_inputs).logits

            # Apply appropriate post-processing based on the problem type
            if self.model.config.problem_type == "multi_label_classification" or self.model.config.num_labels == 1:
                scores = self.sigmoid(outputs.cpu().numpy())
            elif self.model.config.problem_type == "single_label_classification" or self.model.config.num_labels > 1:
                scores = self.softmax(outputs.cpu().numpy())
            else:
                scores = outputs.cpu().numpy()  # No function applied

            # Process each item in the batch
            for idx, img_path in enumerate(batch_paths):
                labeled_scores = [
                    {"label": self.model.config.id2label[i], "score": float(score)}
                    for i, score in enumerate(scores[idx].flatten())
                ]
                self._save_predictions(labeled_scores, img_path, self.output.output_folder, batch_idx)

    def _save_predictions(self, labeled_scores, img_path, output_path: str, batch_index) -> None:

        results = [{"image_path": img_path, "predictions": labeled_scores}]

        # Save to JSON
        file_name = os.path.join(output_path, f"predictions_batch_{batch_index}.json")
        with open(file_name, "w") as file:
            json.dump(results, file, indent=4)
