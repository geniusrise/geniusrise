import logging
import os
from abc import abstractmethod

import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from transformers import AdamW, EvalPrediction, Trainer, TrainingArguments, get_linear_schedule_with_warmup

from geniusrise.core import BatchInputConfig, BatchOutputConfig, Bolt, StateManager


class HuggingFaceBatchFineTuner(Bolt):
    """
    A bolt for fine-tuning Hugging Face models.

    This bolt uses the Hugging Face Transformers library to fine-tune a pre-trained model.
    It uses the `Trainer` class from the Transformers library to handle the training.
    """

    def __init__(
        self,
        model,
        tokenizer,
        input_config: BatchInputConfig,
        output_config: BatchOutputConfig,
        state_manager: StateManager,
        eval: bool = False,
        **kwargs,
    ) -> None:
        """
        Initialize the bolt.

        Args:
            model: The pre-trained model to fine-tune.
            tokenizer: The tokenizer associated with the model.
            input_config (BatchInputConfig): The batch input configuration.
            output_config (OutputConfig): The output configuration.
            state_manager (StateManager): The state manager.
        """
        super().__init__(
            input_config=input_config,
            output_config=output_config,
            state_manager=state_manager,
        )
        self.model = model
        self.tokenizer = tokenizer
        self.input_config = input_config
        self.output_config = output_config
        self.state_manager = state_manager
        self.eval = eval
        self.log = logging.getLogger(self.__class__.__name__)

        # Copy the datasets from S3 to the local input folder
        self.input_config.copy_from_remote()

        # Load the datasets from the local input folder
        train_dataset_path = os.path.join(self.input_config.get(), "train")
        eval_dataset_path = os.path.join(self.input_config.get(), "eval")
        self.train_dataset = self.load_dataset(train_dataset_path)
        if self.eval:
            self.eval_dataset = self.load_dataset(eval_dataset_path)

    @abstractmethod
    def load_dataset(self, dataset_path, **kwargs):
        """
        Load a dataset from a file.

        Args:
            dataset_path (str): The path to the dataset file.
            **kwargs: Additional keyword arguments to pass to the `load_dataset` method.

        Returns:
            Dataset: The loaded dataset.
        """
        # Implement your custom dataset loading logic here
        pass

    def compute_metrics(self, eval_pred: EvalPrediction):
        """
        Compute metrics for evaluation.

        Args:
            eval_pred (EvalPrediction): The evaluation predictions.

        Returns:
            dict: The computed metrics.
        """
        predictions, labels = eval_pred
        predictions = np.argmax(predictions, axis=1)

        return {
            "accuracy": accuracy_score(labels, predictions),
            "precision": precision_recall_fscore_support(labels, predictions, average="binary")[0],
            "recall": precision_recall_fscore_support(labels, predictions, average="binary")[1],
            "f1": precision_recall_fscore_support(labels, predictions, average="binary")[2],
        }

    def create_optimizer_and_scheduler(self, num_training_steps: int):
        """
        Customize the optimizer and the learning rate scheduler.

        Args:
            num_training_steps (int): The total number of training steps.

        Returns:
            tuple: The optimizer and the learning rate scheduler.
        """
        optimizer = AdamW(self.model.parameters(), lr=5e-5)
        scheduler = get_linear_schedule_with_warmup(
            optimizer, num_warmup_steps=0, num_training_steps=num_training_steps
        )

        return optimizer, scheduler

    def fine_tune(
        self,
        output_dir: str,
        num_train_epochs: int,
        per_device_train_batch_size: int,
        learning_rate: float = 5e-5,
        weight_decay: float = 0.01,
        logging_steps: int = 100,
        use_ipex: bool = False,
        bf16: bool = False,
        fp16: bool = False,
        fp16_opt_level: str = "O1",
        half_precision_backend: str = "auto",
        bf16_full_eval: bool = False,
        fp16_full_eval: bool = False,
        tf32: bool = False,
        save_safetensors: bool = False,
        save_on_each_node: bool = False,
        adam_beta1: float = 0.9,
        adam_beta2: float = 0.999,
        adam_epsilon: float = 1e-8,
        max_grad_norm: float = 1.0,
    ):
        """
        Fine-tune the model.

        Args:
            output_dir (str): The output directory where the model predictions and checkpoints will be written.
            num_train_epochs (int): Total number of training epochs to perform.
            per_device_train_batch_size (int): Batch size per device during training.
            learning_rate (float): The learning rate for the optimizer.
            weight_decay (float): The weight decay for the optimizer.
            logging_steps (int): Log metrics every this many steps.
            use_ipex (bool): Use Intel extension for PyTorch when it is available.
            bf16 (bool): Whether to use bf16 16-bit (mixed) precision training instead of 32-bit training.
            fp16 (bool): Whether to use fp16 16-bit (mixed) precision training instead of 32-bit training.
            fp16_opt_level (str): For `fp16` training, Apex AMP optimization level selected in ['O0', 'O1', 'O2', and 'O3'].
            half_precision_backend (str): The backend to use for mixed precision training.
            bf16_full_eval (bool): Whether to use full bfloat16 evaluation instead of 32-bit.
            fp16_full_eval (bool): Whether to use full float16 evaluation instead of 32-bit.
            tf32 (bool): Whether to enable the TF32 mode, available in Ampere and newer GPU architectures.
            save_safetensors (bool): Use safetensors saving and loading for state dicts instead of default `torch.load` and `torch.save`.
            save_on_each_node (bool): When doing multi-node distributed training, whether to save models and checkpoints on each node, or only on the main one.
            adam_beta1 (float): The beta1 hyperparameter for the AdamW optimizer.
            adam_beta2 (float): The beta2 hyperparameter for the AdamW optimizer.
            adam_epsilon (float): The epsilon hyperparameter for the AdamW optimizer.
            max_grad_norm (float): Maximum gradient norm (for gradient clipping).
        """
        # Define the training arguments
        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=num_train_epochs,
            per_device_train_batch_size=per_device_train_batch_size,
            learning_rate=learning_rate,
            weight_decay=weight_decay,
            logging_steps=logging_steps,
            use_ipex=use_ipex,
            bf16=bf16,
            fp16=fp16,
            fp16_opt_level=fp16_opt_level,
            half_precision_backend=half_precision_backend,
            bf16_full_eval=bf16_full_eval,
            fp16_full_eval=fp16_full_eval,
            tf32=tf32,
            save_safetensors=save_safetensors,
            save_on_each_node=save_on_each_node,
            adam_beta1=adam_beta1,
            adam_beta2=adam_beta2,
            adam_epsilon=adam_epsilon,
            max_grad_norm=max_grad_norm,
        )

        # Initialize the trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=self.train_dataset,
            eval_dataset=self.eval_dataset if self.eval else None,
            tokenizer=self.tokenizer,
            compute_metrics=self.compute_metrics,
            data_collator=getattr(self, "data_collator") if hasattr(self, "data_collator") else None,
        )

        # Train the model
        trainer.train()

        # Save the model
        trainer.save_model()

        # Evaluate the model
        if self.eval:
            eval_result = trainer.evaluate()

            # Log the evaluation results
            self.log.info(f"Evaluation results: {eval_result}")
