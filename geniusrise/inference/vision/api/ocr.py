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

import base64
import io
import numpy as np
import cherrypy
import cv2
import re
import easyocr
from PIL import Image
from typing import Any

# from mmocr.apis import MMOCRInferencer
from paddleocr import PaddleOCR
from geniusrise import BatchInput, BatchOutput, State
from geniusrise.inference.vision.base import VisionAPI


class ImageOCRAPI(VisionAPI):
    r"""
    ImageOCRAPI provides Optical Character Recognition (OCR) capabilities for images, leveraging different OCR engines
    like EasyOCR, PaddleOCR, and Hugging Face models tailored for OCR tasks. This API can decode base64-encoded images,
    process them through the chosen OCR engine, and return the recognized text.

    The API supports dynamic selection of OCR engines and configurations based on the provided model name and arguments,
    offering flexibility in processing various languages and image types.

    Attributes:
        Inherits all attributes from the VisionAPI class.

    Methods:
        ocr(self): Processes an uploaded image for OCR and returns the recognized text.

    Example CLI Usage:

    EasyOCR:

    ```bash
    genius ImageOCRAPI rise \
        batch \
            --input_folder ./input \
        batch \
            --output_folder ./output \
        none \
        listen \
            --args \
                model_name="easyocr" \
                device_map="cuda:0" \
                endpoint="*" \
                port=3000 \
                cors_domain="http://localhost:3000" \
                username="user" \
                password="password"
    ```

    Paddle OCR:

    ```bash
    genius ImageOCRAPI rise \
        batch \
            --input_folder ./input \
        batch \
            --output_folder ./output \
        none \
        listen \
            --args \
                model_name="paddleocr" \
                device_map="cuda:0" \
                endpoint="*" \
                port=3000 \
                cors_domain="http://localhost:3000" \
                username="user" \
                password="password"
    ```

    Huggingface models:

    ```bash
    genius ImageOCRAPI rise \
        batch \
            --input_folder ./input \
        batch \
            --output_folder ./output \
        none \
        listen \
            --args \
                model_name="facebook/nougat-base" \
                model_class="VisionEncoderDecoderModel" \
                processor_class="NougatProcessor" \
                device_map="cuda:0" \
                use_cuda=True \
                precision="float" \
                quantization=0 \
                max_memory=None \
                torchscript=False \
                compile=False \
                flash_attention=False \
                better_transformers=False \
                endpoint="*" \
                port=3000 \
                cors_domain="http://localhost:3000" \
                username="user" \
                password="password"
    ```
    """

    def __init__(self, input: BatchInput, output: BatchOutput, state: State, **kwargs):
        """
        Initializes the ImageOCRAPI with configurations for input, output, state management, and OCR model specifics.

        Args:
            input (BatchInput): Configuration for the input data.
            output (BatchOutput): Configuration for the output data.
            state (State): State management for the API.
            **kwargs: Additional keyword arguments for extended functionality.
        """
        super().__init__(input=input, output=output, state=state)
        self.hf_model = True

    def initialize_model(self, model_name: str):
        if model_name == "easyocr":
            lang = self.model_args.get("lang", "en")
            self.reader = easyocr.Reader(["ch_sim", lang], quantize=self.quantization)
        # elif model_name == "mmocr":
        #     self.mmocr_infer = MMOCRInferencer(det="dbnet", rec="svtr-small", kie="SDMGR", device=self.device_map)
        elif model_name == "paddleocr":
            lang = self.model_args.get("lang", "en")
            self.paddleocr_model = PaddleOCR(use_angle_cls=True, lang=lang, use_gpu=self.use_cuda)

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    @cherrypy.tools.allow(methods=["POST"])
    def ocr(self):
        """
        Endpoint for performing OCR on an uploaded image. It accepts a base64-encoded image, decodes it, preprocesses
        it through the specified OCR model, and returns the recognized text.

        Args:
            None - Expects input through the POST request's JSON body including 'image_base64', 'model_name',
                   and 'use_easyocr_bbox' (optional).

        Returns:
            Dict[str, Any]: A dictionary containing the success status, recognized text ('result'), and the original
            image name ('image_name') if provided.

        Raises:
            Exception: If an error occurs during image processing or OCR.

        Example CURL Request:
        ```bash
        curl -X POST localhost:3000/api/v1/ocr \
            -H "Content-Type: application/json" \
            -d '{"image_base64": "<base64-encoded-image>", "model_name": "easyocr", "use_easyocr_bbox": true}'
        ```

        or

        ```bash
        (base64 -w 0 test_images_ocr/ReceiptSwiss.jpg | awk '{print "{\"image_base64\": \""$0"\", \"max_length\": 1024}"}' > /tmp/image_payload.json)
        curl -X POST http://localhost:3000/api/v1/ocr \
            -H "Content-Type: application/json" \
            -u user:password \
            -d @/tmp/image_payload.json | jq
        ```
        """
        if not hasattr(self, "model") or not self.model:
            self.hf_model = False
            self.initialize_model(self.model_name)

        try:
            data = cherrypy.request.json
            use_easyocr_bbox = data.get("use_easyocr_bbox", False)
            image_base64 = data.get("image_base64", "")
            image_bytes = base64.b64decode(image_base64)
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

            image_name = data.get("image_name", "Unnamed Image")
            if self.hf_model:
                result = self.process_huggingface_models(image, use_easyocr_bbox)
            else:
                result = self.process_other_models(image)

            return {"success": True, "result": result, "image_name": image_name}

        except Exception as e:
            cherrypy.log.error(f"Error processing image: {e}")
            raise e

    def process_huggingface_models(self, image: Image.Image, use_easyocr_bbox: bool):
        """
        Processes the image using a Hugging Face model specified for OCR tasks. Supports advanced configurations
        and post-processing to handle various OCR-related challenges.

        Args:
            image (Image.Image): The image to process.
            use_easyocr_bbox (bool): Whether to use EasyOCR to detect text bounding boxes before processing with
                                     Hugging Face models.

        Returns:
            str: The recognized text from the image.
        """
        # Convert PIL Image to Tensor
        pixel_values = self.processor(images=image, return_tensors="pt").pixel_values
        if self.use_cuda:
            pixel_values = pixel_values.to(self.device_map)

        if "donut" in self.model_name.lower():
            task_prompt = "<s_cord-v2>"
            decoder_input_ids = self.processor.tokenizer(
                task_prompt, add_special_tokens=False, return_tensors="pt"
            ).input_ids

            if self.use_cuda:
                decoder_input_ids = decoder_input_ids.to(self.device_map)

            # Generate transcription using Nougat
            outputs = self.model.generate(
                pixel_values,
                decoder_input_ids=decoder_input_ids,
                max_length=self.model.decoder.config.max_position_embeddings,
                bad_words_ids=[[self.processor.tokenizer.unk_token_id]],
                return_dict_in_generate=True,
                output_scores=True,
            )
            sequence = self.processor.batch_decode(outputs.sequences)[0]
            sequence = sequence.replace(self.processor.tokenizer.eos_token, "").replace(
                self.processor.tokenizer.pad_token, ""
            )
            sequence = re.sub(r"<.*?>", "", sequence, count=1).strip()  # remove first task start token
            sequence = self.processor.token2json(sequence)

        elif "nougat" in self.model_name.lower():
            # Generate transcription using Nougat
            outputs = self.model.generate(
                pixel_values,
                min_length=1,
                max_new_tokens=1024,
                bad_words_ids=[[self.processor.tokenizer.unk_token_id]],
            )
            sequence = self.processor.batch_decode(outputs, skip_special_tokens=True)[0]
            sequence = self.processor.post_process_generation(sequence, fix_markdown=True)
        else:
            if use_easyocr_bbox:
                self._process_with_easyocr_bbox(image, self.use_cuda)
            else:
                outputs = self.model.generate(pixel_values)
                sequence = self.processor.batch_decode(outputs[0], skip_special_tokens=True)[0]

        return sequence

    def process_other_models(self, image: Image.Image) -> Any:
        """
        Processes the image using non-Hugging Face OCR models like EasyOCR or PaddleOCR based on the initialization.

        Args:
            image (Image.Image): The image to process.

        Returns:
            Any: The OCR results which might include text, bounding boxes, and confidence scores depending on the model.

        Raises:
            ValueError: If an invalid or unsupported OCR model is specified.
        """
        # Convert PIL Image to OpenCV format
        open_cv_image = np.array(image)
        open_cv_image = cv2.cvtColor(open_cv_image, cv2.COLOR_RGB2BGR)

        if self.model_name == "easyocr":
            # Perform OCR using EasyOCR
            ocr_results = self.reader.readtext(open_cv_image, detail=0, paragraph=True)
            return ocr_results

        # elif self.model_name == "mmocr":
        #     concatenated_text = ""
        #     # Perform OCR using MMOCR
        #     result = self.mmocr_infer(open_cv_image, save_vis=False)
        #     predictions = result["predictions"]
        #     # Extract texts and scores
        #     texts = [pred["rec_texts"] for pred in predictions]
        #     ocr_texts = [" ".join(text) for text in texts]
        #     concatenated_texts = " ".join(ocr_texts)

        elif self.model_name == "paddleocr":
            # Perform OCR using PaddleOCR
            result = self.paddleocr_model.ocr(open_cv_image, cls=False)
            return result
        else:
            raise ValueError("Invalid OCR engine.")

    def _process_with_easyocr_bbox(
        self,
        image: Image.Image,
        use_cuda: bool,
    ):
        """
        A helper method to use EasyOCR for detecting text bounding boxes before processing the image with
        a Hugging Face OCR model.

        Args:
            image (Image.Image): The image to process.
            use_cuda (bool): Whether to use GPU acceleration for EasyOCR.

        Returns:
            str: The recognized text from the image after processing it through the specified OCR model.
        """
        # Initialize EasyOCR reader
        reader = easyocr.Reader(["ch_sim", "en"], quantize=False)

        # Convert PIL Image to OpenCV format for EasyOCR
        open_cv_image = np.array(image)
        open_cv_image = cv2.cvtColor(open_cv_image, cv2.COLOR_RGB2BGR)

        # Detect text regions using EasyOCR
        results = reader.readtext(open_cv_image, detail=1)
        image_texts = []

        # OCR using TROCR for each detected text region
        for bbox, _, _ in results:
            x_min, y_min = map(int, bbox[0])
            x_max, y_max = map(int, bbox[2])
            x_min, y_min, x_max, y_max = max(0, x_min), max(0, y_min), min(image.width, x_max), min(image.height, y_max)
            if x_max > x_min and y_max > y_min:
                # Crop the detected region from the PIL Image
                text_region = image.crop((x_min, y_min, x_max, y_max))
                # Convert cropped image to Tensor
                pixel_values = self.processor(images=text_region, return_tensors="pt").pixel_values.to(self.device_map)
                # Perform OCR using TROCR
                generated_ids = self.model.generate(pixel_values)
                generated_text = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
                image_texts.append(generated_text)
        full_text = " ".join(image_texts)
        return full_text
