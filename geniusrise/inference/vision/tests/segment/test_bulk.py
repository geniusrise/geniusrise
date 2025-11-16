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
import shutil
from PIL import Image
from geniusrise import BatchInput, BatchOutput
from geniusrise.inference.vision.segment.bulk import VisionSegmentationBulk
from transformers import AutoModelForSemanticSegmentation, AutoImageProcessor


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


@pytest.fixture
def image_segmentation_bulk():
    input_dir = tempfile.mkdtemp()
    output_dir = tempfile.mkdtemp()
    state = None
    klass = VisionSegmentationBulk(
        input=BatchInput(input_dir, "geniusrise-test", "test-🤗-input"),
        output=BatchOutput(output_dir, "geniusrise-test", "test-🤗-output"),
        state=state,
    )

    return klass

# Adjust the path to your specific folder
IMAGE_FOLDER = 'test_images_segment'

@pytest.fixture
def folder_images():
    image_paths = []
    # Assuming you want to test all images in the folder
    for file_name in os.listdir(IMAGE_FOLDER):
        image_paths.append(os.path.join(IMAGE_FOLDER, file_name))

    return image_paths

@pytest.mark.parametrize("model_name, model_class, processor_class, device_map, subtask", MODELS_TO_TEST.values())
def test_segmentation_process_with_test_images(image_segmentation_bulk, folder_images, model_name, model_class, processor_class, device_map, subtask):
    # Move mock images to the input folder
    for img_path in folder_images:
        destination_path = os.path.join(image_segmentation_bulk.input.input_folder, os.path.basename(img_path))
        shutil.copy(img_path, destination_path)

    # Call the segment method with the required parameters
    image_segmentation_bulk.segment(
        model_name=model_name,
        model_class=model_class,
        processor_class=processor_class,
        device_map=device_map,
        subtask=subtask
    )

    # Verify the creation of output files
    prediction_files = os.listdir(image_segmentation_bulk.output.output_folder)
    assert len(prediction_files) > 0, f"No segmentation output files found for {model_name}."
