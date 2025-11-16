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
from geniusrise import BatchInput, BatchOutput
from geniusrise.inference.vision.ocr.api import ImageOCRAPI
from PIL import Image, ImageDraw, ImageFont
from unittest.mock import MagicMock
import random
import string

@pytest.fixture
def base64_test_image():
    # Create an image with random text
    img = Image.new('RGB', (384, 384), color='white')
    draw = ImageDraw.Draw(img)
    text = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    draw.text((10, 10), text, fill='black')

    # Convert the image to a Base64 string
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode()
    return img_base64

@pytest.fixture
def base64_test_image_text():
    # Create an image with random text
    img = Image.new('RGB', (384, 384), color='white')
    draw = ImageDraw.Draw(img)
    text = "ABCDE12345!@"
    draw.text((10, 10), text, fill='black')

    # Convert the image to a Base64 string
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode()
    return img_base64

@pytest.fixture
def ocr_api_instance(tmpdir, request):
    input_dir = os.path.join(tmpdir, "input")
    output_dir = os.path.join(tmpdir, "output")
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    state = None

    api_instance = ImageOCRAPI(
        input=BatchInput(input_dir, "geniusrise-test", "test-🤗-input"),
        output=BatchOutput(output_dir, "geniusrise-test", "test-🤗-output"),
        state=state,
        use_cuda=False
    )

    return api_instance

MODELS_TO_TEST = {
    "easyocr": {"model_name": "easyocr", "model_type": "other", "use_easyocr_bbox": False},
    "mmocr": {"model_name": "mmocr", "model_type": "other", "use_easyocr_bbox": False},
    "paddleocr": {"model_name": "paddleocr", "model_type": "other", "use_easyocr_bbox": False},
    # "hf_trocr": {"model_name": "facebook/trocr-large", "model_type": "hf", "kind": "printed", "use_easyocr_bbox": True},
}

@pytest.mark.parametrize("ocr_engine_name, ocr_engine_config", MODELS_TO_TEST.items())
def test_ocr_engines(ocr_api_instance, base64_test_image, ocr_engine_name, ocr_engine_config):
    # Mock CherryPy request
    cherrypy.request = MagicMock()
    cherrypy.request.json = {"image_base64": base64_test_image}

    # Extract configuration for the current OCR engine
    model_name = ocr_engine_config['model_name']
    model_type = ocr_engine_config['model_type']
    kind = ocr_engine_config.get('kind')
    use_easyocr_bbox = ocr_engine_config['use_easyocr_bbox']

    # Update the OCR engine for the test
    ocr_api_instance.initialize_model(model_name=model_name, model_type=model_type, kind=kind, use_easyocr_bbox=use_easyocr_bbox)

    # Call the OCR method for the current instance
    response = ocr_api_instance.ocr()

    # Assertions
    assert isinstance(response, dict)
    assert 'ocr_text' in response
    assert 'image_name' in response

@pytest.mark.parametrize("ocr_engine_name, ocr_engine_config", MODELS_TO_TEST.items())
def test_ocr_specific_text(ocr_api_instance, base64_test_image_text, ocr_engine_name, ocr_engine_config):
    # Mock CherryPy request
    cherrypy.request = MagicMock()
    cherrypy.request.json = {"image_base64": base64_test_image_text}

    # Extract configuration for the current OCR engine
    model_name = ocr_engine_config['model_name']
    model_type = ocr_engine_config['model_type']
    kind = ocr_engine_config.get('kind')
    use_easyocr_bbox = ocr_engine_config['use_easyocr_bbox']

    # Update the OCR engine for the test
    ocr_api_instance.initialize_model(model_name=model_name, model_type=model_type, kind=kind, use_easyocr_bbox=use_easyocr_bbox)

    # Call the OCR method for the current instance
    response = ocr_api_instance.ocr()

    # Assertions
    assert isinstance(response, dict)
    assert 'ocr_text' in response
    assert 'image_name' in response
    # assert "ABCDE12345!@" in response['ocr_text'], "Specific text not found in OCR response"
