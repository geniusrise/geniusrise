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
import numpy as np
import cherrypy
import torch
import base64
from PIL import Image
from typing import List, Dict, Any


class VisionSegmentationAPI(VisionAPI):
    r"""
    VisionSegmentationAPI extends VisionAPI to provide image segmentation functionalities, including panoptic,
    instance, and semantic segmentation. This API supports different segmentation tasks based on the model's
    capabilities and the specified subtask in the request.

    Attributes:
        Inherits all attributes from the VisionAPI class.

    Methods:
        segment_image(self): Processes an image for segmentation and returns the segmentation masks along with labels.

    Example CLI Usage:

    ```bash
    genius VisionSegmentationAPI rise \
        batch \
            --input_folder ./input \
        batch \
            --output_folder ./output \
        none \
        listen \
            --args \
                model_name="facebook/mask2former-swin-large-mapillary-vistas-semantic" \
                model_class="Mask2FormerForUniversalSegmentation" \
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

    def __init__(self, input: BatchInput, output: BatchOutput, state: State, **kwargs):
        """
        Initializes the VisionSegmentationAPI with configurations for input, output, and state management, along
        with any model-specific parameters for segmentation tasks.

        Args:
            input (BatchInput): Configuration for the input data.
            output (BatchOutput): Configuration for the output data.
            state (State): State management for the API.
            **kwargs: Additional keyword arguments for extended functionality.
        """
        super().__init__(input=input, output=output, state=state)

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    @cherrypy.tools.allow(methods=["POST"])
    def segment_image(self) -> List[Dict[str, Any]]:
        """
        Endpoint for segmenting an image according to the specified subtask (panoptic, instance, or semantic segmentation).
        It decodes the base64-encoded image, processes it through the model, and returns the segmentation masks along with
        labels and scores (if applicable) in base64 format.

        The method supports dynamic task inputs for models requiring specific task descriptions and applies different
        post-processing techniques based on the subtask.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries where each dictionary contains a 'label', a 'score' (if applicable),
            and a 'mask' (base64-encoded image of the segmentation mask).

        Raises:
            Exception: If an error occurs during image processing or segmentation.

        Example CURL Request:
        ```bash
        curl -X POST localhost:3000/api/v1/segment_image \
            -H "Content-Type: application/json" \
            -d '{"image_base64": "<base64-encoded-image>", "subtask": "panoptic"}'
        ```

        or to save all masks:

        ```bash
        (base64 -w 0 guy.jpg | awk '{print "{\"image_base64\": \""$0"\", \"subtask\": \"semantic\"}"}' > /tmp/image_payload.json)
        curl -X POST http://localhost:3000/api/v1/segment_image \
            -H "Content-Type: application/json" \
            -u user:password \
            -d @/tmp/image_payload.json | jq -r '.[] | .mask + " " + .label' | while read mask label; do echo $mask | base64 --decode > "${label}.jpg"; done
        ```
        """
        try:
            data = cherrypy.request.json
            image_base64 = data.get("image_base64", "")
            subtask = data.get("subtask", "")

            kwargs = data
            if "image_base64" in kwargs:
                del kwargs["image_base64"]
            if "subtask" in kwargs:
                del kwargs["subtask"]

            image_bytes = base64.b64decode(image_base64)
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

            if self.model.config.__class__.__name__ == "OneFormerConfig" and subtask:
                inputs = self.processor(images=[image], return_tensors="pt", task_inputs=[subtask])
            else:
                inputs = self.processor(images=[image], return_tensors="pt")

            target_size = [(image.height, image.width)]

            if self.use_cuda:
                inputs = inputs.to(self.device_map)

            with torch.no_grad():
                model_outputs = self.model(**inputs, **kwargs)

                if subtask == "panoptic":
                    outputs = self.processor.post_process_panoptic_segmentation(
                        model_outputs, target_sizes=target_size
                    )[0]
                elif subtask == "instance":
                    outputs = self.processor.post_process_instance_segmentation(
                        model_outputs, target_sizes=target_size
                    )[0]
                elif subtask == "semantic":
                    outputs = self.processor.post_process_semantic_segmentation(
                        model_outputs, target_sizes=target_size
                    )[0]
                else:
                    raise ValueError(f"Subtask {subtask} is not supported for model {type(self.model)}")

                annotation = self._prepare_annotation(outputs, subtask)

            return annotation

        except Exception as e:
            self.log.exception(f"Error processing image: {e}")
            raise e

    def _prepare_annotation(self, outputs: Dict[str, Any], subtask: str) -> List[Dict[str, Any]]:
        """
        Prepares the annotation response based on the segmentation outputs and subtask. This method is responsible for
        formatting the segmentation masks, labels, and scores into a list of dictionaries suitable for the API response.

        Args:
            outputs (Dict[str, Any]): The outputs from the model's segmentation processing.
            subtask (str): The specified segmentation subtask (panoptic, instance, or semantic).

        Returns:
            List[Dict[str, Any]]: A list of annotation dictionaries with 'label', 'score' (if applicable), and 'mask'
            (base64-encoded segmentation mask).
        """
        annotation = []

        if subtask in ["panoptic", "instance"]:
            segmentation = outputs["segmentation"]
            for segment in outputs["segments_info"]:
                mask = (segmentation == segment["id"]) * 255
                mask = Image.fromarray(mask.cpu().numpy().astype(np.uint8), mode="L")
                label = self.model.config.id2label[segment["label_id"]]
                score = segment.get("score", None)

                buffered = io.BytesIO()
                mask.save(buffered, format="JPEG")
                image_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

                annotation.append({"score": score, "label": label, "mask": image_base64})
        elif subtask == "semantic":
            segmentation = outputs.cpu().numpy()  # type: ignore
            labels = np.unique(segmentation)

            for label in labels:
                mask = (segmentation == label) * 255
                mask = Image.fromarray(mask.astype(np.uint8), mode="L")
                label_name = self.model.config.id2label[label]

                buffered = io.BytesIO()
                mask.save(buffered, format="JPEG")
                image_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

                annotation.append({"score": None, "label": label_name, "mask": image_base64})

        return annotation
