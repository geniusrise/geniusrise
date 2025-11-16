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
from geniusrise.inference.vision.base import VisionAPI
import io
import cherrypy
import numpy as np
import torch
import base64
from PIL import Image
from typing import Dict, Any, List


class ImageClassificationAPI(VisionAPI):
    r"""
    ImageClassificationAPI extends the VisionAPI for image classification tasks. This API provides functionalities
    to classify images into various categories based on the trained model it uses. It supports both single-label
    and multi-label classification problems.

    Attributes:
        Inherits all attributes from the VisionAPI class.

    Methods:
        classify_image(self): Endpoint to classify an uploaded image and return the classification scores.
        sigmoid(self, _outputs): Applies the sigmoid function to the model's outputs.
        softmax(self, _outputs): Applies the softmax function to the model's outputs.

    Example CLI Usage:

    ```bash
    genius ImageClassificationAPI rise \
        batch \
            --input_folder ./input \
        batch \
            --output_folder ./output \
        none \
        listen \
            --args \
                model_name="Kaludi/food-category-classification-v2.0" \
                model_class="AutoModelForImageClassification" \
                processor_class="AutoImageProcessor" \
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

    def __init__(
        self,
        input: BatchInput,
        output: BatchOutput,
        state: State,
        **kwargs,
    ) -> None:
        """
        Initializes the ImageClassificationAPI with the necessary configurations for input, output, and state management,
        along with model-specific parameters.

        Args:
            input (BatchInput): Configuration for the input data.
            output (BatchOutput): Configuration for the output data.
            state (State): State management for the API.
            **kwargs: Additional keyword arguments for extended functionality, such as model configuration.
        """
        super().__init__(input=input, output=output, state=state)

    def sigmoid(self, _outputs: np.ndarray) -> np.ndarray:
        """
        Applies the sigmoid function to the model's outputs for binary classification or multi-label classification tasks.

        Args:
            _outputs (np.ndarray): The raw outputs from the model.

        Returns:
            np.ndarray: The outputs after applying the sigmoid function.
        """
        return 1.0 / (1.0 + np.exp(-_outputs))

    def softmax(self, _outputs: np.ndarray) -> np.ndarray:
        """
        Applies the softmax function to the model's outputs for single-label classification tasks, ensuring the output
        scores sum to 1 across classes.

        Args:
            _outputs (np.ndarray): The raw outputs from the model.

        Returns:
            np.ndarray: The outputs after applying the softmax function.
        """
        maxes = np.max(_outputs, axis=-1, keepdims=True)
        shifted_exp = np.exp(_outputs - maxes)
        return shifted_exp / shifted_exp.sum(axis=-1, keepdims=True)

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    @cherrypy.tools.allow(methods=["POST"])
    def classify_image(self) -> Dict[str, Any]:
        """
        Endpoint for classifying an image. It accepts a base64-encoded image, decodes it, preprocesses it, and
        runs it through the classification model. It supports both single-label and multi-label classification
        by applying the appropriate post-processing function to the model outputs.

        Returns:
            Dict[str, Any]: A dictionary containing the predictions with the highest scores and all prediction scores.
            Each prediction includes the label and its corresponding score.

        Raises:
            Exception: If an error occurs during image processing or classification.

        Example CURL Request:
        ```bash
        curl -X POST localhost:3000/api/v1/classify_image \
            -H "Content-Type: application/json" \
            -d '{"image_base64": "<base64-encoded-image>"}'
        ```

        or to feed an image:
        ```bash
        (base64 -w 0 cat.jpg | awk '{print "{\"image_base64\": \""$0"\"}"}' > /tmp/image_payload.json)
        curl -X POST http://localhost:3000/api/v1/classify_image \
            -H "Content-Type: application/json" \
            -u user:password \
            -d @/tmp/image_payload.json | jq
        ```
        """
        try:
            data = cherrypy.request.json
            image_base64 = data.get("image_base64", "")
            image_bytes = base64.b64decode(image_base64)
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

            generation_params = data
            if "image_base64" in generation_params:
                del generation_params["image_base64"]

            # Preprocess the image
            inputs = self.processor(images=image, return_tensors="pt")

            if self.use_cuda:
                inputs = {k: v.to(self.device_map) for k, v in inputs.items()}

            # Perform inference
            with torch.no_grad():
                outputs = self.model(**inputs, **generation_params).logits
                outputs = outputs.cpu().numpy()

            if self.model.config.problem_type == "multi_label_classification" or self.model.config.num_labels == 1:
                scores = self.sigmoid(outputs)
            elif self.model.config.problem_type == "single_label_classification" or self.model.config.num_labels > 1:
                scores = self.softmax(outputs)
            else:
                scores = outputs  # No function applied

            # Prepare scores and labels for the response
            labeled_scores: List[Dict[str, Any]] = [
                {"label": self.model.config.id2label[i], "score": float(score)}
                for i, score in enumerate(scores.flatten())
            ]

            max_score = max([x["score"] for x in labeled_scores])
            max_scorers = [x for x in labeled_scores if x["score"] == max_score]
            response = {"predictions": max_scorers, "all_predictions": labeled_scores}

            return response

        except Exception as e:
            self.log.error(f"Error processing image: {e}")
            raise e
