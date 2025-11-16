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
import tempfile
import pytest
import shutil
import json
from geniusrise import BatchInput, BatchOutput
from PIL import Image
from geniusrise.inference.vision.ocr.bulk import ImageOCRBulk
from PIL import Image, ImageDraw, ImageFont
import random
import string

def create_mock_image():
    # Create a blank image
    img = Image.new('RGB', (224, 224), color=(235, 295, 275))
    d = ImageDraw.Draw(img)

    # Generate random text
    text = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

    # Draw text on the image
    font = ImageFont.load_default()
    d.text((10,10), text, fill=(0,0,0), font=font)

    return img, text

@pytest.fixture
def mock_images(tmp_path):
    image_paths = []
    expected_texts = []
    for i in range(5):
        img, text = create_mock_image()
        img_path = tmp_path / f"mock_image_{i}.jpg"
        img.save(img_path)
        image_paths.append(img_path)
        expected_texts.append(text)
    return image_paths, expected_texts

# Adjust the path to your specific folder
IMAGE_FOLDER = 'test_images_ocr'

@pytest.fixture
def folder_images():
    image_paths = []
    # Assuming you want to test all images in the folder
    for file_name in os.listdir(IMAGE_FOLDER):
        image_paths.append(os.path.join(IMAGE_FOLDER, file_name))

    return image_paths

@pytest.fixture
def ocr_bulk(tmpdir):
    input_dir = os.path.join(tmpdir, "input")
    output_dir = os.path.join(tmpdir, "output")
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    state = None
    ocr_bulk_instance = ImageOCRBulk(
        input=BatchInput(input_dir, "geniusrise-test", "test-🤗-input"),
        output=BatchOutput(output_dir, "geniusrise-test", "test-🤗-output"),
        state=state,
        use_cuda=False,
        batch_size=2,
    )

    return ocr_bulk_instance

MODELS_TO_TEST = {
    "easyocr": {"model_name": "easyocr", "model_type": "other", "use_easyocr_bbox": False},
    "mmocr": {"model_name": "mmocr", "model_type": "other", "use_easyocr_bbox": False},
    "paddleocr": {"model_name": "paddleocr", "model_type": "other", "use_easyocr_bbox": False},
#    "hf_trocr": {"model_name": "facebook/trocr-large", "model_type": "hf", "kind": "printed", "use_easyocr_bbox": True},
}

@pytest.mark.parametrize("ocr_engine_name, ocr_engine_config", MODELS_TO_TEST.items())
def test_ocr_process(ocr_bulk, mock_images, ocr_engine_name, ocr_engine_config):
    image_paths, expected_texts = mock_images

    # Extract configuration for the current OCR engine
    model_name = ocr_engine_config['model_name']
    model_type = ocr_engine_config['model_type']
    kind = ocr_engine_config.get('kind')
    use_easyocr_bbox = ocr_engine_config['use_easyocr_bbox']

    # Update the OCR engine for the test
    ocr_bulk.initialize_model(model_name=model_name, model_type=model_type, kind=kind, use_easyocr_bbox=use_easyocr_bbox)

    # Move mock images to the input folder
    for img_path in image_paths:
        os.rename(img_path, os.path.join(ocr_bulk.input.input_folder, img_path.name))

    # Run the OCR process for each engine
    ocr_bulk.process()

    # Verify the creation of output files
    prediction_files = os.listdir(ocr_bulk.output.output_folder)
    assert len(prediction_files) > 0, f"No OCR output files found for {ocr_engine}."

@pytest.mark.parametrize("ocr_engine_name, ocr_engine_config", MODELS_TO_TEST.items())
def test_ocr_process_with_test_images(ocr_bulk, ocr_engine_name, ocr_engine_config, folder_images):
    image_paths = folder_images

    # Extract configuration for the current OCR engine
    model_name = ocr_engine_config['model_name']
    model_type = ocr_engine_config['model_type']
    kind = ocr_engine_config.get('kind')
    use_easyocr_bbox = ocr_engine_config['use_easyocr_bbox']

    # Update the OCR engine for the test
    ocr_bulk.initialize_model(model_name=model_name, model_type=model_type, kind=kind, use_easyocr_bbox=use_easyocr_bbox)

    # Move mock images to the input folder
    for img_path in image_paths:
        destination_path = os.path.join(ocr_bulk.input.input_folder, os.path.basename(img_path))
        shutil.copy(img_path, destination_path)

    # Run the OCR process for each engine
    ocr_bulk.process()

    # Verify the creation of output files
    prediction_files = os.listdir(ocr_bulk.output.output_folder)
    assert len(prediction_files) > 0, f"No OCR output files found for {ocr_engine}."
