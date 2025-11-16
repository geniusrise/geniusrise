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


import os
import torch
import json
import numpy as np
from PIL import Image
from datasets import load_dataset
from geniusrise import BatchInput, BatchOutput, State
from geniusrise.inference.vision.base import VisionBulk
from datasets import Dataset, DatasetDict
from typing import Dict, Optional, Union, List, Tuple


class VisionSegmentationBulk(VisionBulk):
    def __init__(self, input: BatchInput, output: BatchOutput, state: State, **kwargs) -> None:

        super().__init__(input, output, state, **kwargs)

    def load_dataset(
        self,
        dataset_path: Union[str, None] = None,
        hf_dataset: Union[str, None] = None,
        **kwargs,
    ) -> Union[Dataset, DatasetDict, Optional[Dataset]]:
        if dataset_path:
            return self._load_local_dataset(dataset_path, **kwargs)
        elif hf_dataset:
            return load_dataset(hf_dataset, **kwargs)
        else:
            raise ValueError("Either 'dataset_path' or 'hf_dataset' must be provided")

    def _load_local_dataset(self, dataset_path: str, image_size: Tuple[int, int] = (224, 224)) -> Dataset:
        # Supported image formats
        supported_formats = [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".tif"]

        # List of all image file paths in the dataset directory
        image_files = [f for f in os.listdir(dataset_path) if os.path.splitext(f)[1].lower() in supported_formats]

        # Create a dataset using lists for each field
        images = []
        paths = []
        for image_file in image_files:
            image_path = os.path.join(dataset_path, image_file)
            try:
                with Image.open(image_path).convert("RGB") as img:
                    images.append(img)
                paths.append(image_path)
            except Exception as e:
                print(f"Error processing {image_file}: {e}")

        # Convert lists to PyTorch Dataset
        return Dataset.from_dict({"image": images, "path": paths})

    def segment(
        self,
        model_name,
        model_class: str = "AutoModelForSemanticSegmentation",
        processor_class: str = "AutoImageProcessor",
        device_map: str | Dict | None = "auto",
        max_memory=None,
        torchscript=False,
        batch_size=32,
        subtask: str = "semantic",
        threshold=0.5,
        mask_threshold=0.3,
        overlap_mask_area_threshold=0.2,
        **kwargs,
    ) -> None:
        """
        Segments vision data using a specified Hugging Face model.

        :param model_name: Name of the model to use.
        :param dataset_path: Path to the dataset.
        :param output_path: Path to save predictions.
        :param model_class: The class of the model.
        :param device_map: Device map for model parallelism.
        :param max_memory: Maximum memory for model parallelism.
        :param torchscript: Whether to use TorchScript.
        :param batch_size: Size of the batch for processing.
        :param kwargs: Additional keyword arguments.
        """
        if ":" in model_name:
            model_revision = model_name.split(":")[1]
            processor_revision = model_name.split(":")[1]
            model_name = model_name.split(":")[0]
            processor_name = model_name
        else:
            model_revision = None
            processor_revision = None
            processor_name = model_name

        # Load model
        self.model_name = model_name
        self.processor_name = processor_name
        self.model_revision = model_revision
        self.processor_revision = processor_revision
        self.model_class = model_class
        self.processor_class = processor_class
        self.device_map = device_map
        self.max_memory = max_memory
        self.torchscript = torchscript
        self.batch_size = batch_size
        self.subtask = subtask

        model_args = {k.replace("model_", ""): v for k, v in kwargs.items() if "model_" in k}
        self.model_args = model_args

        self.model, self.processor = self.load_models(
            model_name=self.model_name,
            processor_name=self.processor_name,
            model_revision=self.model_revision,
            processor_revision=self.processor_revision,
            model_class=self.model_class,
            processor_class=self.processor_class,
            device_map=self.device_map,
            max_memory=self.max_memory,
            torchscript=self.torchscript,
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

            for image, image_path in zip(batch_images, batch_paths):
                target_size = [(image.height, image.width)]
                if self.model.config.__class__.__name__ == "OneFormerConfig":
                    if subtask is None:
                        kwargs = {}
                    else:
                        kwargs = {"task_inputs": [subtask]}
                        inputs = self.processor(images=[image], return_tensors="pt", **kwargs)
                        inputs["task_inputs"] = self.tokenizer(
                            inputs["task_inputs"],
                            padding="max_length",
                            max_length=self.model.config.task_seq_len,
                            return_tensors=self.framework,
                        )["input_ids"]
                else:
                    inputs = self.processor(images=[image], return_tensors="pt")
                inputs["target_size"] = target_size

                with torch.no_grad():
                    target_size = inputs.pop("target_size")
                    model_outputs = self.model(**inputs)
                    model_outputs["target_size"] = target_size

                    fn = None
                    if self.subtask in {"panoptic", None} and hasattr(
                        self.processor, "post_process_panoptic_segmentation"
                    ):
                        fn = self.processor.post_process_panoptic_segmentation
                    elif self.subtask in {"instance", None} and hasattr(
                        self.processor, "post_process_instance_segmentation"
                    ):
                        fn = self.processor.post_process_instance_segmentation

                    if fn is not None:
                        outputs = fn(
                            model_outputs,
                            threshold=threshold,
                            mask_threshold=mask_threshold,
                            overlap_mask_area_threshold=overlap_mask_area_threshold,
                            target_sizes=model_outputs["target_size"],
                        )[0]

                        annotation = []
                        segmentation = outputs["segmentation"]

                        for segment in outputs["segments_info"]:
                            mask = segmentation == segment["id"]
                            mask_indices = np.argwhere(mask.cpu().numpy())

                            # Transpose the mask_indices to separate x and y coordinates
                            y_coordinates, x_coordinates = mask_indices.T
                            # Pair the x and y coordinates
                            paired_coordinates = zip(x_coordinates, y_coordinates)
                            # Format each pair of coordinates as a string and join them
                            mask_value = ", ".join([f"({x},{y})" for x, y in paired_coordinates])

                            mask = (segmentation == segment["id"]) * 255
                            mask_img = Image.fromarray(mask.numpy().astype(np.uint8), mode="L")
                            label = self.model.config.id2label[segment["label_id"]]
                            score = segment["score"]
                            annotation.append(
                                {"score": score, "label": label, "mask_value": mask_value, "mask_img": mask_img}
                            )

                    elif subtask in {"semantic", None} and hasattr(
                        self.processor, "post_process_semantic_segmentation"
                    ):
                        outputs = self.processor.post_process_semantic_segmentation(
                            model_outputs, target_sizes=model_outputs["target_size"]
                        )[0]

                        annotation = []
                        segmentation = outputs.numpy()
                        labels = np.unique(segmentation)

                        for label in labels:
                            mask = segmentation == label
                            mask_value = np.argwhere(mask)
                            # Format each pair of coordinates as a string and join them
                            mask_value = ", ".join([f"({x},{y})" for x, y in mask_value])
                            mask = (segmentation == label) * 255
                            mask_img = Image.fromarray(mask.astype(np.uint8), mode="L")
                            label = self.model.config.id2label[label]
                            annotation.append(
                                {"score": None, "label": label, "mask_value": mask_value, "mask_img": mask_img}
                            )
                    else:
                        raise ValueError(f"Subtask {subtask} is not supported for model {type(self.model)}")

                    self._save_annotations(annotation, image_path, self.output.output_folder)

    def _save_annotations(
        self,
        annotations: List[Dict[str, any]],
        image_path: str,
        output_path: str,
    ) -> None:
        """
        Saves the segmentation annotations as images and a JSON file.

        :param annotations: List of annotations for the batch.
        :param batch_paths: List of batch items (e.g., image paths).
        :param output_path: Directory to save the output files.
        :param batch_index: Index of the batch.
        """

        # Directory to save masks for this image
        image_dir = os.path.join(output_path, os.path.basename(image_path).split(".")[0])
        os.makedirs(image_dir, exist_ok=True)

        # Prepare data structure for JSON
        annotation_data = []

        for i, annotation in enumerate(annotations):
            # Save mask as an image
            mask_img = annotation["mask_img"]
            mask_img.save(os.path.join(image_dir, f"mask_{i}.png"))

            # Append annotation data
            annotation_data.append(
                {"score": annotation["score"], "label": annotation["label"], "mask_value": annotation["mask_value"]}
            )

        # Save annotation data as JSON
        json_path = os.path.join(image_dir, "annotations.json")
        with open(json_path, "w") as json_file:
            json.dump(annotation_data, json_file, indent=4)
