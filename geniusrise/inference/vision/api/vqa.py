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
import torch
import base64
from PIL import Image


class VisualQAAPI(VisionAPI):
    r"""
    VisualQAAPI extends VisionAPI to provide an interface for visual question answering (VQA) tasks. This API supports
    answering questions about an image by utilizing deep learning models specifically trained for VQA. It processes
    requests containing an image and a question about the image, performs inference using the loaded model, and returns
    the predicted answer.

    Attributes:
        Inherits all attributes from the VisionAPI class.

    Methods:
        answer_question(self): Receives an image and a question, returns the answer based on visual content.

    Example CLI Usage:

    ```bash
    genius VisualQAAPI rise \
        batch \
            --input_folder ./input \
        batch \
            --output_folder ./output \
        none \
        listen \
            --args \
                model_name="llava-hf/bakLlava-v1-hf" \
                model_class="LlavaForConditionalGeneration" \
                processor_class="AutoProcessor" \
                device_map="cuda:0" \
                use_cuda=True \
                precision="bfloat16" \
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
    ):
        """
        Initializes the VisualQAAPI with configurations for input, output, state management, and any model-specific
        parameters for visual question answering tasks.

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
    def answer_question(self):
        """
        Endpoint for receiving an image with a question and returning the answer based on the visual content of the image.
        It processes the request containing a base64-encoded image and a question string, and utilizes the loaded model
        to predict the answer to the question related to the image.

        Returns:
            Dict[str, Any]: A dictionary containing the original question and the predicted answer.

        Raises:
            ValueError: If required fields 'image_base64' and 'question' are not provided in the request.
            Exception: If an error occurs during image processing or inference.

        Example CURL Request:
        ```bash
        curl -X POST localhost:3000/api/v1/answer_question \
            -H "Content-Type: application/json" \
            -d '{"image_base64": "<base64-encoded-image>", "question": "What is the color of the sky in the image?"}'
        ```

        or

        ```bash
        (base64 -w 0 test_images_segment_finetune/image1.jpg | awk '{print "{\"image_base64\": \""$0"\", \"question\": \"how many cats are there?\"}"}' > /tmp/image_payload.json)
        curl -X POST http://localhost:3000/api/v1/answer_question \
            -H "Content-Type: application/json" \
            -u user:password \
            -d @/tmp/image_payload.json | jq
        ```
        """
        try:
            data = cherrypy.request.json
            image_base64 = data.get("image_base64", "")
            question = data.get("question", "")

            generation_params = data
            if "image_base64" in generation_params:
                del generation_params["image_base64"]
            if "question" in generation_params:
                del generation_params["question"]

            if not image_base64 or not question:
                raise ValueError("Both 'image_base64' and 'question' fields are required.")

            image_bytes = base64.b64decode(image_base64)
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

            if "uform" in self.model_name.lower():
                # Prepare inputs for the model
                inputs = self.processor(
                    texts=[question],
                    images=[image],
                    return_tensors="pt",
                    padding="max_length",
                    truncation=True,
                    max_length=512,
                )
            elif "git" in self.model_name.lower():
                pixel_values = self.processor(images=image, return_tensors="pt").pixel_values
                input_ids = self.processor(text=question, add_special_tokens=False).input_ids
                input_ids = [self.processor.tokenizer.cls_token_id] + input_ids
                input_ids = torch.tensor(input_ids).unsqueeze(0)
                inputs = {"pixel_values": pixel_values, "input_ids": input_ids}
            elif "llava" in self.model_name.lower():
                inputs = self.processor(text=question, images=image, return_tensors="pt")
            else:
                inputs = self.processor(image, question, return_tensors="pt")

            if self.use_cuda:
                inputs = {k: v.to(self.device_map) for k, v in inputs.items()}

            # Model inference
            with torch.no_grad():
                outputs = self.model.generate(**inputs, **generation_params)

            if "uform" in self.model_name.lower():
                prompt_len = inputs["input_ids"].shape[1]
                decoded_text = self.processor.batch_decode(outputs[:, prompt_len:])[0]
            else:
                decoded_text = self.processor.decode(outputs[0], skip_special_tokens=True)

            response = {"question": question, "answer": decoded_text}

            return response

        except Exception as e:
            self.log.exception(f"Error processing visual question answering task: {e}")
            raise e
