import torch
from typing import List
from torch.utils.data import Dataset
from transformers import PreTrainedTokenizerBase
from typing import Dict
import pydantic
from pydantic import validator


class FineTuningDataItem(pydantic.BaseModel):
    prompt: str
    completion: str


class FineTuningData(pydantic.BaseModel):
    data: List[FineTuningDataItem]


class FineTuningDataset(Dataset):
    def __init__(self, data: FineTuningData, tokenizer: PreTrainedTokenizerBase):
        self.data = data
        self.tokenizer = tokenizer

    def __len__(self):
        return len(self.data.data)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        item = self.data.data[idx]
        encoding = self.tokenizer(
            item.prompt, return_tensors="pt", padding="max_length", truncation=True, max_length=512
        )
        return {
            "input_ids": encoding["input_ids"].flatten(),
            "attention_mask": encoding["attention_mask"].flatten(),
            "labels": torch.tensor([item.completion], dtype=torch.long),
        }


class Model(pydantic.BaseModel):
    name: str

    @validator("name")
    def validate_model(self, v):
        valid_models = [
            # Base models
            "bert-base-uncased",
            "gpt2",
            "t5-base",
            "roberta-base",
            "distilbert-base-uncased",
            "xlnet-base-cased",
            "albert-base-v2",
            "camembert-base",
            "xlm-roberta-base",
            "longformer-base-4096",
            "flaubert/flaubert_small_cased",
            "facebook/bart-base",
            "reformer-crime-and-punishment",
            "google/bigbird-roberta-base",
            "gpt-neo-125M",
            "facebook/wav2vec2-base-960h",
            "google/vit-base-patch16-224",
            "clip-ViT-B-32",
            # Pretraining models
            "bert-base-uncased",
            "roberta-base",
            "xlnet-base-cased",
            "albert-base-v2",
            "facebook/bart-base",
            "gpt-neo-125M",
            # Causal LM
            "gpt2",
            "gpt-neo-125M",
            "transformerxl-wt103",
            "transfo-xl-wt103",
            "xlnet-base-cased",
            # Masked LM
            "bert-base-uncased",
            "roberta-base",
            "distilbert-base-uncased",
            "albert-base-v2",
            "camembert-base",
            # Seq2Seq LM
            "t5-base",
            "facebook/bart-base",
            "marian-en-de",
            "mt5-base",
            "pegasus-cnn_dailymail",
            "blenderbot-400M-distill",
            "blenderbot-1B-distill",
            "blenderbot-3B",
            "blenderbot_small-90M",
            "blenderbot_small-1B-distill",
            # Sequence Classification
            "bert-base-uncased",
            "distilbert-base-uncased",
            "albert-base-v2",
            "roberta-base",
            "xlm-roberta-base",
            "facebook/bart-base",
            "google/bigbird-roberta-base",
            "gpt-neo-125M",
            # Token Classification
            "bert-base-uncased",
            "distilbert-base-uncased",
            "albert-base-v2",
            "roberta-base",
            "xlm-roberta-base",
            "facebook/bart-base",
            "google/bigbird-roberta-base",
            "gpt-neo-125M",
            # Question Answering
            "bert-base-uncased",
            "distilbert-base-uncased",
            "albert-base-v2",
            "roberta-base",
            "xlm-roberta-base",
            "facebook/bart-base",
            "google/bigbird-roberta-base",
            "gpt-neo-125M",
            # Table Question Answering
            "google/tapas-base",
            "google/tapas-large",
            "google/tapas-base-finetuned-wtq",
            "google/tapas-large-finetuned-wtq",
            "google/tapas-base-finetuned-wikisql",
            "google/tapas-large-finetuned-wikisql",
            # Multiple Choice
            "bert-base-uncased",
            "roberta-base",
            "albert-base-v2",
            "camembert-base",
            "xlm-roberta-base",
            "facebook/bart-base",
            # Next Sentence Prediction
            "bert-base-uncased",
            # Structured Data Classification
            "google/tapas-base",
            "google/tapas-large",
            "google/tapas-base-finetuned-wtq",
            "google/tapas-large-finetuned-wtq",
            "google/tapas-base-finetuned-wikisql",
            "google/tapas-large-finetuned-wikisql",
            # Structured Data Regression
            "google/tapas-base",
            "google/tapas-large",
            "google/tapas-base-finetuned-wtq",
            "google/tapas-large-finetuned-wtq",
            "google/tapas-base-finetuned-wikisql",
            "google/tapas-large-finetuned-wikisql",
        ]
        if v not in valid_models:
            raise ValueError("Invalid model")
        return v
