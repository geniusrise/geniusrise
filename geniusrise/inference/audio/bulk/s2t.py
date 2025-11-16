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
import multiprocessing
import os
import uuid
from typing import Any, Dict, List, Optional

from geniusrise import BatchInput, BatchOutput, State
from transformers import AutoModelForCTC, AutoProcessor

from geniusrise.inference.audio.utils.s2t_inference import SpeechToTextInference
from geniusrise.inference.audio.utils.s2t import decode_audio


class SpeechToTextBulk(SpeechToTextInference):
    r"""
    SpeechToTextBulk is designed for bulk processing of speech-to-text tasks. It efficiently processes large datasets of audio files,
    converting speech to text using Hugging Face's Wav2Vec2 models.

    Attributes:
        model (AutoModelForCTC): The speech-to-text model.
        processor (AutoProcessor): The processor to prepare input audio data for the model.

    Methods:
        transcribe_batch(audio_files: List[str], **kwargs: Any) -> List[str]:
            Transcribes a batch of audio files to text.

    Example CLI Usage:

    ```bash
    genius SpeechToTextBulk rise \
        batch \
            --input_folder ./input \
        batch \
            --output_folder ./output \
        none \
        --id facebook/bart-large-cnn-lol \
        transcribe \
            --args \
                model_name="facebook/bart-large-cnn" \
                model_class="AutoModelForSeq2SeqLM" \
                processor_class="AutoTokenizer" \
                use_cuda=True \
                precision="float" \
                quantization=0 \
                device_map="cuda:0" \
                max_memory=None \
                torchscript=False \
                generation_bos_token_id=0 \
                generation_decoder_start_token_id=2 \
                generation_early_stopping=true \
                generation_eos_token_id=2 \
                generation_forced_bos_token_id=0 \
                generation_forced_eos_token_id=2 \
                generation_length_penalty=2.0 \
                generation_max_length=142 \
                generation_min_length=56 \
                generation_no_repeat_ngram_size=3 \
                generation_num_beams=4 \
                generation_pad_token_id=1 \
                generation_do_sample=false
    ```

    or using whisper.cpp:

    ```bash
    genius SpeechToTextBulk rise \
        batch \
            --input_folder ./input \
        batch \
            --output_folder ./output \
        none \
        --id facebook/bart-large-cnn-lol \
        transcribe \
            --args \
                model_name="facebook/bart-large-cnn" \
                use_whisper_cpp=True
    ```
    """

    model: AutoModelForCTC
    processor: AutoProcessor

    def __init__(
        self,
        input: BatchInput,
        output: BatchOutput,
        state: State,
        **kwargs,
    ):
        """
        Initializes the SpeechToTextBulk with configurations for speech-to-text processing.

        Args:
            input (BatchInput): The input data configuration.
            output (BatchOutput): The output data configuration.
            state (State): The state configuration.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(input=input, output=output, state=state, **kwargs)

    def transcribe(
        self,
        model_name: str,
        model_class: str = "AutoModel",
        processor_class: str = "AutoProcessor",
        use_cuda: bool = False,
        precision: str = "float16",
        quantization: int = 0,
        device_map: str | Dict | None = "auto",
        max_memory={0: "24GB"},
        torchscript: bool = False,
        compile: bool = False,
        batch_size: int = 8,
        use_whisper_cpp: bool = False,
        use_faster_whisper: bool = False,
        notification_email: Optional[str] = None,
        model_sampling_rate: int = 16_000,
        chunk_size: int = 0,
        overlap_size: int = 0,
        **kwargs: Any,
    ):
        """
        Transcribes a batch of audio files to text using the speech-to-text model.

        Args:
            model_name (str): Name or path of the model.
            model_class (str): Class name of the model (default "AutoModelForSequenceClassification").
            processor_class (str): Class name of the processor (default "AutoProcessor").
            use_cuda (bool): Whether to use CUDA for model inference (default False).
            precision (str): Precision for model computation (default "float").
            quantization (int): Level of quantization for optimizing model size and speed (default 0).
            device_map (str | Dict | None): Specific device to use for computation (default "auto").
            max_memory (Dict): Maximum memory configuration for devices.
            torchscript (bool, optional): Whether to use a TorchScript-optimized version of the pre-trained language model. Defaults to False.
            compile (bool, optional): Whether to compile the model before fine-tuning. Defaults to True.
            batch_size (int): Number of classifications to process simultaneously (default 8).
            use_whisper_cpp (bool): Whether to use whisper.cpp to load the model. Defaults to False. Note: only works for these models: https://github.com/aarnphm/whispercpp/blob/524dd6f34e9d18137085fb92a42f1c31c9c6bc29/src/whispercpp/utils.py#L32
            use_faster_whisper (bool): Whether to use faster-whisper.
            model_sampling_rate (int): Rate of sampling supported by the model, usually 16000 Hz.
            chunk_size (int): size of chunks to divide the audio file into to decode, 16000 = 1 second, 30s is a decent value, does not apply for longform models like whisper.
            overlap_size (int): how much of the chunks to overlap, usually around 50% of chunk size.
            **kwargs: Arbitrary keyword arguments for model and generation configurations.
        """
        self.model_class = model_class
        self.processor_class = processor_class
        self.use_cuda = use_cuda
        self.precision = precision
        self.quantization = quantization
        self.device_map = device_map
        self.max_memory = max_memory
        self.torchscript = torchscript
        self.compile = compile
        self.batch_size = batch_size
        self.use_whisper_cpp = use_whisper_cpp
        self.use_faster_whisper = use_faster_whisper
        self.notification_email = notification_email
        self.model_sampling_rate = model_sampling_rate
        self.chunk_size = chunk_size
        self.overlap_size = overlap_size

        if ":" in model_name:
            model_revision = model_name.split(":")[1]
            processor_revision = model_name.split(":")[1]
            model_name = model_name.split(":")[0]
            processor_name = model_name
        else:
            model_revision = None
            processor_revision = None
        processor_name = model_name
        self.model_name = model_name
        self.model_revision = model_revision
        self.processor_name = processor_name
        self.processor_revision = processor_revision

        model_args = {k.replace("model_", ""): v for k, v in kwargs.items() if "model_" in k}
        self.model_args = model_args

        generation_args = {k.replace("generation_", ""): v for k, v in kwargs.items() if "generation_" in k}
        self.generation_args = generation_args

        processor_args = {k.replace("processor_", ""): v for k, v in kwargs.items() if "processor_" in k}
        self.processor_args = processor_args

        dataset_path = self.input.input_folder
        output_path = self.output.output_folder

        self.model, self.processor = self.load_models(
            model_name=self.model_name,
            processor_name=self.processor_name,
            model_revision=self.model_revision,
            processor_revision=self.processor_revision,
            model_class=self.model_class,
            processor_class=self.processor_class,
            use_cuda=self.use_cuda,
            precision=self.precision,
            quantization=self.quantization,
            device_map=self.device_map,
            max_memory=self.max_memory,
            torchscript=self.torchscript,
            compile=self.compile,
            use_whisper_cpp=use_whisper_cpp,
            use_faster_whisper=use_faster_whisper,
            **self.model_args,
        )

        # Load dataset
        audio_files = []
        for filename in glob.glob(f"{dataset_path}/**/*", recursive=True):
            extension = os.path.splitext(filename)[1]
            if extension.lower() not in [".wav", ".mp3", ".flac", ".ogg"]:
                continue
            if dataset_path not in filename:
                filepath = os.path.join(dataset_path, filename)
                audio_files.append(filepath)
            else:
                audio_files.append(filename)

        # process batchwise
        for i in range(0, len(audio_files), self.batch_size):
            batch = audio_files[i : i + self.batch_size]

            results = []
            for audio_file in batch:
                # Load and preprocess audio
                if not self.use_faster_whisper:
                    audio_input, sampling_rate = decode_audio(
                        audio_bytes=open(audio_file, "rb").read(),
                        model_type=self.model.config.model_type,
                        model_sampling_rate=model_sampling_rate,
                    )

                if self.use_whisper_cpp:
                    transcription = self.model.transcribe(audio_input, num_proc=multiprocessing.cpu_count())
                elif self.use_faster_whisper:
                    transcription = self.process_faster_whisper(
                        open(audio_file, "rb").read(), model_sampling_rate, chunk_size, generation_args
                    )
                elif self.model.config.model_type == "whisper":
                    transcriptions = self.process_whisper(
                        audio_input,
                        model_sampling_rate,
                        processor_args,
                        chunk_size,
                        overlap_size,
                        generation_args,
                    )
                    results.append(transcriptions)
                elif self.model.config.model_type == "seamless_m4t_v2":
                    transcriptions = self.process_seamless(
                        audio_input,
                        model_sampling_rate,
                        processor_args,
                        chunk_size,
                        overlap_size,
                        generation_args,
                    )
                    results.append(transcriptions)
                elif self.model.config.model_type == "wav2vec2":
                    transcriptions = self.process_wav2vec2(
                        audio_input,
                        model_sampling_rate,
                        processor_args,
                        chunk_size,
                        overlap_size,
                    )
                    results.append(transcriptions)

            self._save_transcriptions(transcriptions=results, filenames=batch, chunk_idx=i, output_path=output_path)
        self._done()

    def _save_transcriptions(self, filenames: List[str], transcriptions: List[str], chunk_idx: int, output_path: str):
        """
        Saves the transcriptions to the specified output folder.

        Args:
            filenames (List[str]): List of filenames of the transcribed audio files.
            transcriptions (List[str]): List of transcribed texts.
            chunk_idx (int): Index of the current batch (for naming files).
            output_path (str): Path to the output folder.
        """
        data_to_save = [
            {"input": filename, "prediction": transcription}
            for filename, transcription in zip(filenames, transcriptions)
        ]

        with open(
            os.path.join(output_path, f"predictions-{chunk_idx}-{str(uuid.uuid4())}.json"),
            "w",
        ) as f:
            json.dump(data_to_save, f)
