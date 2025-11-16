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
import cv2
from PIL import Image
from geniusrise import BatchInput, BatchOutput, State
from geniusrise.logging import setup_logger
from geniusrise.inference.vision.base import VisionBulk
from typing import Optional, Union, List
from datasets import Dataset, DatasetDict, load_dataset, load_from_disk
from typing import Dict

# from mmocr.apis import MMOCRInferencer
import easyocr
from paddleocr import PaddleOCR
from transformers import StoppingCriteriaList
from geniusrise.inference.vision.utils.ocr import StoppingCriteriaScores
from pdf2image import convert_from_path


class ImageOCRBulk(VisionBulk):
    def __init__(
        self,
        input: BatchInput,
        output: BatchOutput,
        state: State,
        **kwargs,
    ) -> None:
        super().__init__(input, output, state, **kwargs)
        self.log = setup_logger(self.state)

    def initialize_model(
        self,
        model_name: str = None,
    ):
        if model_name == "easyocr":
            lang = self.model_args.get("lang", "en")
            self.reader = easyocr.Reader(["ch_sim", lang], quantize=self.quantization)
        # elif model_name == "mmocr":
        #     self.mmocr_infer = MMOCRInferencer(det="dbnet", rec="svtr-small", kie="SDMGR", device=self.device)
        elif model_name == "paddleocr":
            lang = self.model_args.get("lang", "en")
            self.paddleocr_model = PaddleOCR(use_angle_cls=True, lang=lang, use_gpu=self.use_cuda)

    def load_dataset(
        self,
        dataset_path: str,
        **kwargs,
    ) -> Union[Dataset, DatasetDict, Optional[Dataset]]:
        """
        Load a dataset for image OCR from a local path or Hugging Face Datasets.

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

    def _load_local_dataset(self, dataset_path: str) -> Dataset:
        """
        Load a dataset for image classification from a folder containing images and PDFs.

        Args:
            dataset_path (str): The path to the dataset directory.

        Returns:
            Tuple[List[torch.Tensor], List[str]]: A tuple containing a list of image tensors and corresponding file paths.
        """
        # Supported image formats and PDF
        supported_formats = [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".tif", ".pdf"]

        # List of all image and PDF file paths in the dataset directory
        file_paths = [f for f in os.listdir(dataset_path) if os.path.splitext(f)[1].lower() in supported_formats]

        # Create lists for images and paths
        images = []
        paths = []

        for file_path in file_paths:
            full_path = os.path.join(dataset_path, file_path)
            try:
                if full_path.lower().endswith(".pdf"):
                    # Convert each page of the PDF to an image
                    pages = convert_from_path(full_path)
                    for page in pages:
                        images.append(page.convert("RGB"))
                        paths.append(full_path)
                else:
                    with Image.open(full_path).convert("RGB") as img:
                        images.append(img)
                    paths.append(full_path)

            except Exception as e:
                self.log.exception(f"Error processing {file_path}: {e}")

        # Convert lists to PyTorch Dataset
        return Dataset.from_dict({"image": images, "path": paths})

    def ocr(
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
        use_easyocr_bbox: bool = False,
        **kwargs,
    ) -> None:
        """
        Perform OCR on images using a specified OCR engine.

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

        if model_name not in ["easyocr", "mmocr", "paddleocr"]:
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
        else:
            self.initialize_model(self.model_name)

        dataset_path = self.input.input_folder
        self.output_path = self.output.output_folder

        # Load dataset
        self.dataset = self.load_dataset(dataset_path)
        if self.dataset is None:
            self.log.error("Failed to load dataset.")
            return

        if model_name not in ["easyocr", "mmocr", "paddleocr"]:
            self.process_huggingface_models()
        else:
            self.process_other_models()

    def process_huggingface_models(self):
        for batch_idx in range(0, len(self.dataset["image"]), self.batch_size):
            batch_images = self.dataset["image"][batch_idx : batch_idx + self.batch_size]
            batch_paths = self.dataset["path"][batch_idx : batch_idx + self.batch_size]

            ocr_results = []
            if "nougat" in self.model_name.lower():
                for img_path in batch_paths:
                    image = Image.open(img_path)
                    pixel_values = self.processor(image, return_tensors="pt").pixel_values.to(self.device_map)
                    # generate transcription
                    outputs = self.model.generate(
                        pixel_values.to(self.device_map),
                        min_length=1,
                        max_length=3584,
                        bad_words_ids=[[self.processor.tokenizer.unk_token_id]],
                        return_dict_in_generate=True,
                        output_scores=True,
                        stopping_criteria=StoppingCriteriaList([StoppingCriteriaScores()]),
                    )
                    sequence = self.processor.batch_decode(outputs[0], skip_special_tokens=True)[0]
                    sequence = self.processor.post_process_generation(sequence, fix_markdown=False)
                    ocr_results.append(sequence)
            else:
                if self.use_easyocr_bbox:
                    self._process_with_easyocr_bbox(batch_paths)
                else:
                    for img_path in batch_paths:
                        image = Image.open(img_path)
                        pixel_values = self.processor(image, return_tensors="pt").pixel_values.to(self.device_map)
                        outputs = self.model.generate(pixel_values)
                        sequence = self.processor.batch_decode(outputs[0], skip_special_tokens=True)[0]
                        ocr_results.append(sequence)

        # Save OCR results
        self._save_ocr_results(ocr_results, batch_paths, self.output_path, batch_idx)

    def process_other_models(self):
        for batch_idx in range(0, len(self.dataset["image"]), self.batch_size):
            batch_images = self.dataset["image"][batch_idx : batch_idx + self.batch_size]
            batch_paths = self.dataset["path"][batch_idx : batch_idx + self.batch_size]

            ocr_texts = []
            for image_path in batch_paths:
                if self.model_name == "easyocr":
                    # OCR process
                    ocr_results = self.reader.readtext(image_path, detail=0, paragraph=True)
                    concatenated_text = " ".join(ocr_results)
                    ocr_texts.append(concatenated_text)
                # elif self.model_name == "mmocr":
                #     image = cv2.imread(image_path)
                #     if image is None or image.size == 0:
                #         continue
                #     result = self.mmocr_infer(image_path, save_vis=False)
                #     predictions = result["predictions"]

                #     # Extract texts and scores
                #     texts = [pred["rec_texts"] for pred in predictions]
                #     scores = [pred["rec_scores"] for pred in predictions]

                #     # Concatenate texts for each image
                #     concatenated_texts = [" ".join(text) for text in texts]
                #     ocr_texts.append(" ".join(concatenated_texts))
                elif self.model_name == "paddleocr":
                    result = self.paddleocr_model.ocr(image_path, cls=False)
                    # Extract texts and scores
                    texts = [line[1][0] for line in result]
                    scores = [line[1][1] for line in result]
                    # Concatenate texts for each image
                    concatenated_text = " ".join(texts)
                    ocr_texts.append(concatenated_text)
                else:
                    raise ValueError("Invalid OCR engine.")
            # Save OCR results
            self._save_ocr_results(ocr_texts, batch_paths, self.output_path, batch_idx)

    def _process_with_easyocr_bbox(self, batch_paths):
        ocr_results = []

        # Initialize EasyOCR reader
        reader = easyocr.Reader(["ch_sim", "en"], quantize=False)
        for image_path in batch_paths:
            results = reader.readtext(image_path)
            image = cv2.imread(image_path)
            image_texts = []
            # Recover text regions detected by EasyOCR
            for bbox, _, _ in results:
                # Extract coordinates from bounding box
                x_min, y_min = map(int, bbox[0])
                x_max, y_max = map(int, bbox[2])
                x_min = max(0, x_min)
                y_min = max(0, y_min)
                x_max = min(image.shape[1], x_max)
                y_max = min(image.shape[0], y_max)
                # Extract text region
                if x_max > x_min and y_max > y_min:
                    text_region = image[y_min:y_max, x_min:x_max]
                    pixel_values = self.processor(text_region, return_tensors="pt").pixel_values.to(self.device_map)
                    generated_ids = self.model.generate(pixel_values)
                    generated_text = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
                    image_texts.append(generated_text)

            full_text = " ".join(image_texts)
            ocr_results.append(full_text)

        return ocr_results

    def _save_ocr_results(self, ocr_texts: List[str], batch_paths: List[str], output_path: str, batch_index) -> None:
        """
        Save OCR results to a JSON file.

        Args:
            ocr_texts (List[str]): OCR text for each image in the batch.
            batch_paths (List[str]): Paths of the images in the batch.
            output_path (str): Directory to save the OCR results.
            batch_index (int): Index of the current batch.
        """
        # Create a list of dictionaries with image paths and their corresponding OCR texts
        results = [
            {"image_path": image_path, "ocr_text": ocr_text} for image_path, ocr_text in zip(batch_paths, ocr_texts)
        ]
        # Save to JSON
        file_name = os.path.join(self.output_path, f"ocr_results_batch_{batch_index}.json")
        with open(file_name, "w") as file:
            json.dump(results, file, indent=4)

        self.log.info(f"OCR results for batch {batch_index} saved to {file_name}")
