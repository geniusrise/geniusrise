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

import pytest
import cherrypy
import base64
import io
import torch
import random
import string
from unittest.mock import patch, MagicMock
from PIL import Image
from PIL import Image, ImageDraw, ImageFont
from geniusrise import BatchInput, BatchOutput, InMemoryState, State
from geniusrise.inference.vision.imgclass.api import ImageClassificationAPI
from transformers import AutoModelForImageClassification, AutoProcessor


# Fixtures
@pytest.fixture
def base64_test_image():
    # Create an image with random text
    img = Image.new("RGB", (384, 384), color="white")
    draw = ImageDraw.Draw(img)
    text = "".join(random.choices(string.ascii_letters + string.digits, k=10))
    draw.text((10, 10), text, fill="black")

    # Convert the image to a Base64 string
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="JPEG")
    img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode()
    return img_base64


@pytest.fixture
def api_instance():
    input = MagicMock(spec=BatchInput)
    output = MagicMock(spec=BatchOutput)
    state = MagicMock(spec=InMemoryState)

    api = ImageClassificationAPI("microsoft/resnet-50", input, output, state)

    return api


# Test for correct classification output
def test_classification_output(api_instance, base64_test_image):
    # Mock CherryPy request
    cherrypy.request = MagicMock()
    cherrypy.request.json = {"image_base64": base64_test_image}

    # Call classify_image
    response = api_instance.classify_image()

    # Check if there is a 'label_scores' key in the response
    assert "predictions" in response, "No label_scores in the response"

    # Check if the label_scores dictionary is not empty
    assert response["predictions"], "The label_scores dictionary is empty"


# Test to check for invalid image output
def test_invalid_image_input(api_instance):
    # Create an invalid image input
    invalid_image = b"notanimage"

    # Mock CherryPy request
    cherrypy.request = MagicMock()
    cherrypy.request.json = {"image_base64": io.BytesIO(invalid_image)}

    # Call classify_image
    response = api_instance.classify_image()

    # Check if the response indicates an error
    assert "error" in response, "No error indicated for invalid image input"


def test_response_structure(api_instance, base64_test_image):
    # Mock CherryPy request
    cherrypy.request = MagicMock()
    cherrypy.request.json = {"image_base64": base64_test_image}

    # Call classify_image
    response = api_instance.classify_image()

    # Check response structure
    assert isinstance(response, dict), "Response is not a dictionary"
    assert "original_image" in response, "No original_image in the response"
    assert "predictions" in response, "No label_scores in the response"


def test_large_image_input(api_instance):
    # Create a large image for testing
    large_img = Image.new("RGB", (4000, 4000), color="blue")
    img_byte_arr = io.BytesIO()
    large_img.save(img_byte_arr, format="JPEG")
    img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode()

    # Mock CherryPy request
    cherrypy.request = MagicMock()
    cherrypy.request.json = {"image_base64": img_base64}

    # Call classify_image
    response = api_instance.classify_image()

    # Check if the API can handle large images
    assert isinstance(response, dict), "Response is not a dictionary"
    assert "original_image" in response, "No original_image in the response"
    assert "predictions" in response, "API failed to handle large image"
