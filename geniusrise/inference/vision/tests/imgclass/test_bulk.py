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
import os
import glob
import tempfile
import json
from PIL import Image
from geniusrise import BatchInput, BatchOutput, InMemoryState
from geniusrise.inference.vision.imgclass.bulk import ImageClassificationBulk
from transformers import AutoModelForImageClassification, AutoProcessor

IMAGE_FORMATS = ["jpg", "png", "bmp"]
IMAGE_SIZE = (224, 224)
NUM_TEST_IMAGES = 10


def create_test_images(directory, image_format):
    os.makedirs(directory, exist_ok=True)
    for i in range(NUM_TEST_IMAGES):
        image = Image.new("RGB", IMAGE_SIZE, color="blue")
        image_path = os.path.join(directory, f"test_image_{i}.{image_format}")
        image.save(image_path)


@pytest.fixture
def image_classification_bulk(tmpdir):
    input_dir = os.path.join(tmpdir, "input")
    output_dir = os.path.join(tmpdir, "output")
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    state = InMemoryState()
    klass = ImageClassificationBulk(
        input=BatchInput(input_dir, "geniusrise-test", "test-🤗-input"),
        output=BatchOutput(output_dir, "geniusrise-test", "test-🤗-output"),
        state=state,
    )

    return klass


@pytest.fixture(params=IMAGE_FORMATS)
def image_dataset(request, tmpdir):
    ext = request.param
    # Create images directly in the input directory
    dataset_path = os.path.join(tmpdir, "input")
    create_test_images(dataset_path, ext)
    return dataset_path, ext


def test_load_dataset(image_classification_bulk, image_dataset):
    dataset_path, _ = image_dataset
    dataset = image_classification_bulk.load_dataset(dataset_path)
    assert len(dataset) == NUM_TEST_IMAGES


def test_prediction_file_creation_and_content(image_classification_bulk, image_dataset):
    dataset_path, ext = image_dataset
    image_classification_bulk.load_dataset(dataset_path)

    model_name = "microsoft/resnet-50"
    image_classification_bulk.classify(
        model_name=model_name,
        model_class="AutoModelForImageClassification",
        processor_class="AutoProcessor",
        device_map="cpu",
    )

    prediction_files = glob.glob(os.path.join(image_classification_bulk.output.output_folder, "*.json"))
    assert len(prediction_files) > 0, "No prediction files found in the output directory."

    with open(prediction_files[0], "r") as file:
        predictions = json.load(file)
        assert isinstance(predictions, list), "Predictions file should contain a list."
        assert len(predictions) > 0, "Prediction list is empty."
