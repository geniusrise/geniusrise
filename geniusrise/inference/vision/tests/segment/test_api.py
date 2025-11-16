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
import io
import base64
import tempfile
import pytest
import shutil
import json
import cherrypy
from geniusrise import BatchInput, BatchOutput, InMemoryState
from geniusrise.inference.vision.segment.api import VisionSegmentationAPI
from PIL import Image, ImageDraw, ImageFont
from unittest.mock import MagicMock
import random
import string

MODELS_TO_TEST = {
    "beit": ("microsoft/beit-base-finetuned-ade-640-640", "AutoModelForSemanticSegmentation", "AutoImageProcessor", "cpu", "semantic"),
    "data2vec": ("facebook/data2vec-vision-base","AutoModelForSemanticSegmentation", "AutoImageProcessor", "cpu", "semantic"),
    "dpt": ("Intel/dpt-large-ade","AutoModelForSemanticSegmentation", "AutoImageProcessor", "cpu", "semantic"),
    "mobilenetv2": ("google/deeplabv3_mobilenet_v2_1.0_513", "AutoModelForSemanticSegmentation", "AutoImageProcessor", "cpu", "semantic"),
    "mobilevit": ("apple/deeplabv3-mobilevit-small", "AutoModelForSemanticSegmentation", "AutoImageProcessor", "cpu", "semantic"),
    "mobilevit2": ("apple/mobilevitv2-1.0-imagenet1k-256", "AutoModelForSemanticSegmentation", "AutoImageProcessor", "cpu", "semantic"),
    "segformer": ("nvidia/segformer-b0-finetuned-ade-512-512",  "AutoModelForSemanticSegmentation", "AutoImageProcessor", "cpu", "semantic"),
    "mask2formersemantic": ("facebook/mask2former-swin-small-ade-semantic", "Mask2FormerForUniversalSegmentation", "AutoImageProcessor", "cpu", "semantic"),
    "mask2formerpanoptic": ("facebook/mask2former-swin-small-cityscapes-panoptic", "Mask2FormerForUniversalSegmentation", "AutoImageProcessor", "cpu", "panoptic"),
    "mask2formerinstance": ("facebook/mask2former-swin-small-coco-instance", "Mask2FormerForUniversalSegmentation", "AutoImageProcessor", "cpu", "instance"),
    "maskformersemantic": ("facebook/maskformer-swin-base-ade", "MaskFormerForInstanceSegmentation", "AutoImageProcessor", "cpu", "semantic"),
    "maskformerpanoptic": ("facebook/maskformer-swin-base-coco", "MaskFormerForInstanceSegmentation", "AutoImageProcessor", "cpu", "panoptic"),
    "maskformerinstance": ("facebook/maskformer-swin-base-coco", "MaskFormerForInstanceSegmentation", "AutoImageProcessor", "cpu", "instance"),
}

@pytest.fixture(params=MODELS_TO_TEST.values())
def model(request):
    model_name, model_class, processor_class, device_map, subtask = request.param
    return model_name, model_class, processor_class, device_map, subtask

# Adjust the path to your specific folder
IMAGE_FOLDER = 'test_images_segment'

@pytest.fixture
def folder_images():
    image_paths = []
    # Assuming you want to test all images in the folder
    for file_name in os.listdir(IMAGE_FOLDER):
        image_paths.append(os.path.join(IMAGE_FOLDER, file_name))

    return image_paths

@pytest.fixture
def base64_test_image(folder_images):
    # Choose a random image from the folder
    img_path = random.choice(folder_images)
    with Image.open(img_path) as img:
        # Convert the image to a compatible mode if necessary
        if img.mode == 'P' or img.mode == 'RGBA':
            img = img.convert('RGB')
        # Convert the image to a Base64 string
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG')
        img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode()
        return img_base64

@pytest.fixture(params=MODELS_TO_TEST.values())
def segment_api_instance(tmpdir, request):
    input_dir = os.path.join(tmpdir, "input")
    output_dir = os.path.join(tmpdir, "output")
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    state = InMemoryState()

    model_name, _, _, _, subtask = request.param

    api_instance = VisionSegmentationAPI(
        model_name=model_name,
        subtask=subtask,
        input=BatchInput(input_dir, "geniusrise-test", "test-🤗-input"),
        output=BatchOutput(output_dir, "geniusrise-test", "test-🤗-output"),
        state=state,
    )

    return api_instance

def test_segment_engines(segment_api_instance, base64_test_image):
    # Mock CherryPy request
    cherrypy.request = MagicMock()
    cherrypy.request.json = {"image_base64": base64_test_image}

    # Call the segmentation method for the current instance
    response = segment_api_instance.segment_image()

    # Assertions
    assert isinstance(response, list)
    for segment in response:
        assert 'score' in segment
        assert 'label' in segment
        assert 'mask' in segment
