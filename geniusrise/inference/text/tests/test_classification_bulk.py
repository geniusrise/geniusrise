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

import glob
import json
import os
import sqlite3
import tempfile
import xml.etree.ElementTree as ET

import pandas as pd
import pytest
import yaml  # type: ignore
from datasets import Dataset
from geniusrise.core import BatchInput, BatchOutput
from pyarrow import feather
from pyarrow import parquet as pq

from geniusrise.inference.text.bulk.classification import TextClassificationBulk

MODELS_TO_TEST = {
    # fmt: off
    "cardiffnlp/twitter-roberta-base-hate-multiclass-latest": ["sexism", "racism", "disability", "sexual_orientation", "religion", "other", "not_hate"],
    "cardiffnlp/twitter-roberta-base-hate-latest": ["NOT-HATE", "HATE"],
    "cardiffnlp/twitter-roberta-base-offensive": ["non-offensive", "offensive"],
    "cardiffnlp/twitter-xlm-roberta-base-sentiment": ["positive", "neutral", "negative"],
    "cardiffnlp/twitter-roberta-base-emotion": ["joy", "optimism", "anger", "sadness"],
    "cardiffnlp/twitter-roberta-base-irony": ["non_irony", "irony"],
    "cardiffnlp/twitter-xlm-roberta-base-sentiment-multilingual": ["positive", "neutral", "negative"],
    "tomh/toxigen_roberta": ["LABEL_0", "LABEL_1"],
    "cointegrated/rubert-tiny-toxicity": ["non-toxic", "insult", "obscenity", "threat", "dangerous"],
    "michellejieli/NSFW_text_classifier": ["SFW", "NSFW"],
    "bvanaken/clinical-assertion-negation-bert": ["ABSENT", "PRESENT", "POSSIBLE"],
    "bucketresearch/politicalBiasBERT": ["LEFT", "CENTER", "RIGHT"],
    "soleimanian/financial-roberta-large-sentiment": ["neutral", "negative", "positive"],
    "jpwahle/longformer-base-plagiarism-detection": ["ORIGINAL", "PLAGIARISM"],
    "mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis": ["negative", "neutral", "positive"],
    "lxyuan/distilbert-base-multilingual-cased-sentiments-student": ["negative", "neutral", "positive"],
    "Sigma/financial-sentiment-analysis": ["LABEL_0", "LABEL_1", "LABEL_2"],
    "SamLowe/roberta-base-go_emotions": ["disappointment", "sadness", "annoyance", "neutral", "disapproval", "realization",
                                         "nervousness", "approval", "joy", "anger", "embarrassment", "caring", "remorse",
                                         "disgust", "grief", "confusion", "relief", "desire", "admiration", "optimism",
                                         "fear", "love", "excitement", "curiosity", "amusement", "surprise", "gratitude", "pride"],
    "cardiffnlp/tweet-topic-21-multi": ["sports", "news_&_social_concern", "fitness_&_health", "youth_&_student_life", "learning_&_educational",
                                        "science_&_technology", "celebrity_&_pop_culture", "travel_&_adventure", "diaries_&_daily_life",
                                        "food_&_dining", "gaming", "business_&_entrepreneurs", "family", "relationships", "fashion_&_style",
                                        "music", "film_tv_&_video", "other_hobbies", "arts_&_culture"],
    "padmajabfrl/Gender-Classification": ["Female", "Male"],
    "ProsusAI/finbert": ["positive", "neutral", "negative"],
    "yiyanghkust/finbert-tone": ["Positive", "Neutral", "Negative"],
    "wajidlinux99/gibberish-text-detector": ["clean", "mild gibberish", "word salad", "noise"],
    "cnut1648/biolinkbert-large-mnli-snli": ["entailment", "neutral", "contradiction"],
    # fmt: on
}


# Helper function to create synthetic data in different formats
def create_dataset_in_format(directory, ext):
    os.makedirs(directory, exist_ok=True)
    data = [{"text": f"text_{i}"} for i in range(10)]
    df = pd.DataFrame(data)

    if ext == "huggingface":
        dataset = Dataset.from_pandas(df)
        dataset.save_to_disk(directory)
    elif ext == "csv":
        df.to_csv(os.path.join(directory, "data.csv"), index=False)
    elif ext == "jsonl":
        with open(os.path.join(directory, "data.jsonl"), "w") as f:
            for item in data:
                f.write(json.dumps(item) + "\n")
    elif ext == "parquet":
        pq.write_table(feather.Table.from_pandas(df), os.path.join(directory, "data.parquet"))
    elif ext == "json":
        with open(os.path.join(directory, "data.json"), "w") as f:
            json.dump(data, f)
    elif ext == "xml":
        root = ET.Element("root")
        for item in data:
            record = ET.SubElement(root, "record")
            ET.SubElement(record, "text").text = item["text"]
        tree = ET.ElementTree(root)
        tree.write(os.path.join(directory, "data.xml"))
    elif ext == "yaml":
        with open(os.path.join(directory, "data.yaml"), "w") as f:
            yaml.dump(data, f)
    elif ext == "tsv":
        df.to_csv(os.path.join(directory, "data.tsv"), index=False, sep="\t")
    elif ext == "xlsx":
        df.to_excel(os.path.join(directory, "data.xlsx"), index=False)
    elif ext == "db":
        conn = sqlite3.connect(os.path.join(directory, "data.db"))
        df.to_sql("dataset_table", conn, if_exists="replace", index=False)
        conn.close()
    elif ext == "feather":
        feather.write_feather(df, os.path.join(directory, "data.feather"))


# Fixture for models
@pytest.fixture(params=MODELS_TO_TEST.items())
def model(request):
    return request.param


# Fixtures for each file type
@pytest.fixture(
    params=[
        "huggingface",
        "csv",
        "jsonl",
        "parquet",
        "json",
        "xml",
        "yaml",
        "tsv",
        "xlsx",
        "db",
        "feather",
    ]
)
def dataset_file(request, tmpdir):
    ext = request.param
    create_dataset_in_format(tmpdir, ext)
    return tmpdir, ext


@pytest.fixture
def classification_bolt():
    input_dir = tempfile.mkdtemp()
    output_dir = tempfile.mkdtemp()
    input = BatchInput(input_dir, "geniusrise-test", "test-🤗-input")
    output = BatchOutput(output_dir, "geniusrise-test", "test-🤗-output")
    state = None
    klass = TextClassificationBulk(
        input=input,
        output=output,
        state=state,
    )

    return klass


def test_classify(classification_bolt, dataset_file, model):
    tmpdir, ext = dataset_file
    classification_bolt.input.input_folder = tmpdir

    model_name, labels = model
    tokenizer_name = model_name
    model_class = "AutoModelForSequenceClassification"
    tokenizer_class = "AutoTokenizer"

    # Classify
    classification_bolt.classify(
        model_name=model_name,
        tokenizer_name=tokenizer_name,
        model_class=model_class,
        tokenizer_class=tokenizer_class,
        device_map="cuda:0",
        num_train_epochs=2,
        per_device_batch_size=2,
        precision="float16",
    )
    # Check output
    files = glob.glob(f"{classification_bolt.output.output_folder}/predictions-*.json")
    assert len(files) > 0

    # Check one of the output files to ensure it contains the predictions and input data
    with open(files[0], "r") as f:
        results = json.load(f)
    assert len(results) > 0
    for result in results:
        assert "input" in result
        assert "prediction" in result
        assert result["prediction"] in MODELS_TO_TEST[model_name]
