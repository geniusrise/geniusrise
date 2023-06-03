from transformers import TrainingArguments, Trainer, AutoModelForSequenceClassification, AutoTokenizer
from geniusrise_cli.llm.base import LLM
from geniusrise_cli.llm.types import FineTuningData, FineTuningDataset, Model
import pandas as pd
from typing import List, Optional


class CustomTrainingArguments(TrainingArguments):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.learning_rate = kwargs.pop("learning_rate", 5e-5)
        self.weight_decay = kwargs.pop("weight_decay", 0.01)
        self.adam_epsilon = kwargs.pop("adam_epsilon", 1e-8)
        self.max_grad_norm = kwargs.pop("max_grad_norm", 1.0)
        self.num_train_epochs = kwargs.pop("num_train_epochs", 3)
        self.max_steps = kwargs.pop("max_steps", -1)
        self.warmup_steps = kwargs.pop("warmup_steps", 0)
        self.logging_dir = kwargs.pop("logging_dir", "./logs")
        self.logging_first_step = kwargs.pop("logging_first_step", False)
        self.logging_steps = kwargs.pop("logging_steps", 500)
        self.save_steps = kwargs.pop("save_steps", 500)
        self.save_total_limit = kwargs.pop("save_total_limit", None)
        self.no_cuda = kwargs.pop("no_cuda", False)
        self.seed = kwargs.pop("seed", 42)
        self.fp16 = kwargs.pop("fp16", False)
        self.fp16_opt_level = kwargs.pop("fp16_opt_level", "O1")
        self.local_rank = kwargs.pop("local_rank", -1)
        self.tpu_num_cores = kwargs.pop("tpu_num_cores", None)
        self.tpu_metrics_debug = kwargs.pop("tpu_metrics_debug", False)
        self.debug = kwargs.pop("debug", False)
        self.dataloader_drop_last = kwargs.pop("dataloader_drop_last", False)
        self.eval_steps = kwargs.pop("eval_steps", 500)
        self.dataloader_num_workers = kwargs.pop("dataloader_num_workers", 0)
        self.past_index = kwargs.pop("past_index", -1)
        self.run_name = kwargs.pop("run_name", None)
        self.disable_tqdm = kwargs.pop("disable_tqdm", False)
        self.remove_unused_columns = kwargs.pop("remove_unused_columns", True)
        self.label_names = kwargs.pop("label_names", None)
        self.load_best_model_at_end = kwargs.pop("load_best_model_at_end", False)
        self.metric_for_best_model = kwargs.pop("metric_for_best_model", None)
        self.greater_is_better = kwargs.pop("greater_is_better", None)
        self.ignore_data_skip = kwargs.pop("ignore_data_skip", False)
        self.sharded_ddp = kwargs.pop("sharded_ddp", False)
        self.deepspeed = kwargs.pop("deepspeed", None)
        self.label_smoothing_factor = kwargs.pop("label_smoothing_factor", 0.0)
        self.adafactor = kwargs.pop("adafactor", False)
        self.group_by_length = kwargs.pop("group_by_length", False)
        self.length_column_name = kwargs.pop("length_column_name", "length")
        self.report_to = kwargs.pop("report_to", [])
        self.ddp_find_unused_parameters = kwargs.pop("ddp_find_unused_parameters", None)
        self.dataloader_pin_memory = kwargs.pop("dataloader_pin_memory", True)
        self.skip_memory_metrics = kwargs.pop("skip_memory_metrics", False)
        self.use_legacy_prediction_loop = kwargs.pop("use_legacy_prediction_loop", False)
        self.push_to_hub = kwargs.pop("push_to_hub", False)
        self.resume_from_checkpoint = kwargs.pop("resume_from_checkpoint", None)
        self.log_on_each_node = kwargs.pop("log_on_each_node", True)
        self.mp_parameters = kwargs.pop("mp_parameters", "")
        self.sortish_sampler = kwargs.pop("sortish_sampler", False)
        self.predict_with_generate = kwargs.pop("predict_with_generate", False)


class HuggingFaceLLM(LLM):
    def __init__(
        self,
        api_type: Optional[str] = None,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        api_version: Optional[str] = None,
    ) -> None:
        super().__init__(api_type, api_key, api_base, api_version)
        self.model = None
        self.tokenizer = None

    def preprocess_for_fine_tuning(self, data: FineTuningData) -> pd.DataFrame:
        return FineTuningDataset(data, self.tokenizer)

    def generate_prompts(self, data: List[str], model: str, what: str) -> pd.DataFrame:
        # Implement your prompt generation logic here
        pass

    def fine_tune(self, model_name: str, training_data, validation_data, *args, **kwargs):  # type: ignore
        model = Model(name=model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model.name)
        self.tokenizer = AutoTokenizer.from_pretrained(model.name)

        training_args = CustomTrainingArguments(
            output_dir="./results",  # output directory
            num_train_epochs=3,  # total number of training epochs
            per_device_train_batch_size=16,  # batch size per device during training
            per_device_eval_batch_size=64,  # batch size for evaluation
            warmup_steps=500,  # number of warmup steps for learning rate scheduler
            weight_decay=0.01,  # strength of weight decay
            logging_dir="./logs",  # directory for storing logs
            logging_steps=10,
            **kwargs  # Override defaults with supplied arguments
        )

        trainer = Trainer(
            model=self.model,  # the instantiated 🤗 Transformers model to be trained
            args=training_args,  # training arguments, defined above
            train_dataset=training_data,  # training dataset
            eval_dataset=validation_data,  # evaluation dataset
        )

        trainer.train()

    def get_fine_tuning_job(self, job_id: str):
        pass

    def wait_for_fine_tuning(self, job_id: str, check_interval: int = 60):
        pass

    def delete_fine_tuned_model(self, model_id: str):
        pass
