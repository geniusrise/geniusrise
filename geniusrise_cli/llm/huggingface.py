from transformers import Trainer, AutoModelForCausalLM, AutoTokenizer, default_data_collator
from geniusrise_cli.llm.base import LLM
from geniusrise_cli.llm.types import FineTuningData, FineTuningDataset, Model
from geniusrise_cli.llm.utils import CustomTrainingArguments

# from geniusrise_cli.preprocessing.huggingface import HuggingFacePreprocessor
import pandas as pd
from typing import List, Optional, Any


class HuggingFaceLLM(LLM):
    """
    HuggingFaceLLM is a subclass of LLM and uses the Hugging Face library for language model fine-tuning.
    """

    def __init__(
        self,
        api_type: Optional[str] = None,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        api_version: Optional[str] = None,
        model_name: str = None,
    ) -> None:
        super().__init__(api_type, api_key, api_base, api_version)
        self.model = None
        self.tokenizer = None
        self.model_name = model_name

        model = Model(name=self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model.name)
        self.tokenizer = AutoTokenizer.from_pretrained(model.name)

    def preprocess_for_fine_tuning(self, data: FineTuningData) -> pd.DataFrame:
        """
        Preprocesses the data for fine-tuning.

        Args:
            data (FineTuningData): The data to be preprocessed.

        Returns:
            FineTuningDataset: The preprocessed data.
        """
        # HuggingFacePreprocessor.preprocess_for_fine_tuning(data)
        return FineTuningDataset(data, self.tokenizer)

    def generate_prompts(self, data: List[str], model: str, what: str) -> pd.DataFrame:
        """
        Generates prompts.

        Args:
            data (List[str]): The data to generate prompts from.
            model (str): The model to use for prompt generation.
            what (str): Additional information to guide prompt generation.

        Returns:
            pd.DataFrame: The generated prompts.
        """
        # Implement your prompt generation logic here
        pass

    def fine_tune(
        self,
        training_data: FineTuningDataset,
        validation_data: FineTuningDataset,
        num_train_epochs=3,
        per_device_train_batch_size: int = 16,
        per_device_eval_batch_size: int = 64,
        warmup_steps: int = 500,
        weight_decay: int = 0,
        logging_steps: int = 10,
        **kwargs: Any
    ) -> None:
        """
        Fine-tunes the model.

        Args:
            training_data (FineTuningDataset): The training data.
            validation_data (FineTuningDataset): The validation data.
            kwargs (Any): Additional keyword arguments passed to training arguments.
            num_train_epochs (int): The number of training epochs.
            per_device_train_batch_size (int): The batch size per device during training.
            per_device_eval_batch_size (int): The batch size for evaluation.
            warmup_steps (int): The number of warmup steps for learning rate scheduler.
            weight_decay (int): The strength of weight decay.
            logging_steps (int): The number of steps to log training metrics.

        Returns:
            Dict[str, float]: The evaluation results.
        """
        training_args = CustomTrainingArguments(
            output_dir="./results",  # output directory
            num_train_epochs=num_train_epochs,  # total number of training epochs
            per_device_train_batch_size=per_device_train_batch_size,  # batch size per device during training
            per_device_eval_batch_size=per_device_eval_batch_size,  # batch size for evaluation
            warmup_steps=warmup_steps,  # number of warmup steps for learning rate scheduler
            weight_decay=weight_decay,  # strength of weight decay
            logging_dir="./logs",  # directory for storing logs
            logging_steps=logging_steps,
            **kwargs  # Override defaults with supplied arguments
        )

        trainer = Trainer(
            model=self.model,  # the instantiated 🤗 Transformers model to be trained
            args=training_args,  # training arguments, defined above
            train_dataset=training_data,  # training dataset
            eval_dataset=validation_data,  # evaluation dataset
            data_collator=default_data_collator,  # Add this
            prediction_loss_only=True,  # Add this
        )

        # Training
        trainer.train()

        # Evaluation
        eval_results = trainer.evaluate()

        # Save the model
        trainer.save_model()

        return eval_results  # Return evaluation results

    def get_fine_tuning_job(self, job_id: str):
        pass

    def wait_for_fine_tuning(self, job_id: str, check_interval: int = 60):
        pass

    def delete_fine_tuned_model(self, model_id: str):
        pass
