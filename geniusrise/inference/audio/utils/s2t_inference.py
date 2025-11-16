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

from io import BytesIO
from typing import Any, Dict

import torch
from geniusrise import BatchInput, BatchOutput, State
from transformers import AutoModelForCTC, AutoProcessor

from geniusrise.inference.audio.base import AudioBulk
from geniusrise.inference.audio.utils.s2t import chunk_audio, whisper_alignment_heads


class _SpeechToTextInference:
    """
    _SpeechToTextInference is a base class that provides common functionality for speech-to-text inference.
    It contains methods for processing audio input using various models and frameworks.

    Attributes:
        model (AutoModelForCTC): The speech-to-text model.
        processor (AutoProcessor): The processor for preparing audio input for the model.
        use_cuda (bool): Flag indicating whether to use CUDA for GPU acceleration.
        device_map (str | Dict | None): Device mapping for model execution.
    """

    model: AutoModelForCTC
    processor: AutoProcessor

    def process_faster_whisper(
        self,
        audio_input: bytes,
        model_sampling_rate: int,
        chunk_size: int,
        generate_args: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Processes audio input with the faster-whisper model.

        Args:
            audio_input (bytes): The audio input for transcription.
            model_sampling_rate (int): The sampling rate of the model.
            chunk_size (int): The size of audio chunks to process.
            generate_args (Dict[str, Any]): Additional arguments for transcription.

        Returns:
            Dict[str, Any]: A dictionary containing the transcription results.
        """
        transcribed_segments, transcription_info = self.model.transcribe(
            audio=BytesIO(audio_input),
            beam_size=generate_args.get("beam_size", 5),
            best_of=generate_args.get("best_of", 5),
            patience=generate_args.get("patience", 1.0),
            length_penalty=generate_args.get("length_penalty", 1.0),
            repetition_penalty=generate_args.get("repetition_penalty", 1.0),
            no_repeat_ngram_size=generate_args.get("no_repeat_ngram_size", 0),
            temperature=generate_args.get("temperature", [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]),
            compression_ratio_threshold=generate_args.get("compression_ratio_threshold", 2.4),
            log_prob_threshold=generate_args.get("log_prob_threshold", -1.0),
            no_speech_threshold=generate_args.get("no_speech_threshold", 0.6),
            condition_on_previous_text=generate_args.get("condition_on_previous_text", True),
            prompt_reset_on_temperature=generate_args.get("prompt_reset_on_temperature", 0.5),
            initial_prompt=generate_args.get("initial_prompt", None),
            prefix=generate_args.get("prefix", None),
            suppress_blank=generate_args.get("suppress_blank", True),
            suppress_tokens=generate_args.get("suppress_tokens", [-1]),
            without_timestamps=generate_args.get("without_timestamps", False),
            max_initial_timestamp=generate_args.get("max_initial_timestamp", 1.0),
            word_timestamps=generate_args.get("word_timestamps", False),
            prepend_punctuations=generate_args.get("prepend_punctuations", "\"'“¿([{-"),
            append_punctuations=generate_args.get(
                "append_punctuations",
                "\"'.。,，!！?？:：”)]}、",
            ),
            vad_filter=generate_args.get("vad_filter", False),
            vad_parameters=generate_args.get("vad_parameters", None),
            max_new_tokens=generate_args.get("max_new_tokens", None),
            chunk_length=chunk_size / model_sampling_rate if chunk_size else None,
            clip_timestamps=generate_args.get("clip_timestamps", "0"),
            hallucination_silence_threshold=generate_args.get("hallucination_silence_threshold", None),
        )

        # Format the results
        transcriptions = [segment.text for segment in transcribed_segments]
        return {"transcriptions": transcriptions, "transcription_info": transcription_info._asdict()}

    def process_whisper(
        self, audio_input, model_sampling_rate, processor_args, chunk_size, overlap_size, generate_args
    ):
        """
        Processes audio input with the Whisper model.

        Args:
            audio_input (Any): The audio input for transcription.
            model_sampling_rate (int): The sampling rate of the model.
            processor_args (Dict[str, Any]): Arguments for the audio processor.
            chunk_size (int): The size of audio chunks to process.
            overlap_size (int): The size of overlap between audio chunks.
            generate_args (Dict[str, Any]): Additional arguments for transcription.

        Returns:
            Dict[str, Any]: A dictionary containing the transcription results.
        """
        alignment_heads = [v for k, v in whisper_alignment_heads.items() if k in self.model_name][0]
        self.model.generation_config.alignment_heads = alignment_heads

        # Preprocess and transcribe
        input_values = self.processor(
            audio_input.squeeze(0),
            return_tensors="pt",
            sampling_rate=model_sampling_rate,
            truncation=False,
            padding="longest",
            return_attention_mask=True,
            do_normalize=True,
            **processor_args,
        )

        if self.use_cuda:
            input_values = input_values.to(self.device_map)

        # TODO: make generate generic
        logits = self.model.generate(
            **input_values,
            **generate_args,  # , return_timestamps=True, return_token_timestamps=True, return_segments=True
        )

        # Decode the model output
        if type(logits) is torch.Tensor:
            transcription = self.processor.batch_decode(logits[0], skip_special_tokens=True)
            return {"transcription": "".join(transcription), "segments": []}
        else:
            transcription = self.processor.batch_decode(logits["sequences"], skip_special_tokens=True)
            segments = self.processor.batch_decode(
                [x["tokens"] for x in logits["segments"][0]], skip_special_tokens=True
            )
            timestamps = [
                {
                    "tokens": t,
                    "start": l["start"].cpu().numpy().tolist(),
                    "end": l["end"].cpu().numpy().tolist(),
                }
                for t, l in zip(segments, logits["segments"][0])
            ]
            return {"transcription": transcription, "segments": timestamps}

    def process_seamless(
        self, audio_input, model_sampling_rate, processor_args, chunk_size, overlap_size, generate_args
    ):
        """
        Processes audio input with the Seamless model.

        Args:
            audio_input (Any): The audio input for transcription.
            model_sampling_rate (int): The sampling rate of the model.
            processor_args (Dict[str, Any]): Arguments for the audio processor.
            chunk_size (int): The size of audio chunks to process.
            overlap_size (int): The size of overlap between audio chunks.
            generate_args (Dict[str, Any]): Additional arguments for transcription.

        Returns:
            Dict[str, Any]: A dictionary containing the transcription results.
        """
        audio_input = audio_input.squeeze(0)

        # Split audio input into chunks with overlap
        chunks = chunk_audio(audio_input, chunk_size, overlap_size, overlap_size) if chunk_size > 0 else [audio_input]

        segments = []
        for chunk_id, chunk in enumerate(chunks):
            # Preprocess and transcribe
            input_values = self.processor(
                audios=chunk,
                return_tensors="pt",
                sampling_rate=model_sampling_rate,
                do_normalize=True,
                **processor_args,
            )

            if self.use_cuda:
                input_values = input_values.to(self.device_map)

            # TODO: make generate generic
            logits = self.model.generate(**input_values, **generate_args)[0]

            # Decode the model output
            _transcription = self.processor.batch_decode(logits, skip_special_tokens=True)
            segments.append(
                {
                    "tokens": " ".join([x.strip() for x in _transcription]).strip(),
                    "start": chunk_id * overlap_size,
                    "end": (chunk_id + 1) * overlap_size,
                }
            )

        transcription = " ".join([s["tokens"].strip() for s in segments])
        return {"transcription": transcription, "segments": segments}

    def process_wav2vec2(self, audio_input, model_sampling_rate, processor_args, chunk_size, overlap_size):
        """
        Processes audio input with the Wav2Vec2 model.

        Args:
            audio_input (Any): The audio input for transcription.
            model_sampling_rate (int): The sampling rate of the model.
            processor_args (Dict[str, Any]): Arguments for the audio processor.
            chunk_size (int): The size of audio chunks to process.
            overlap_size (int): The size of overlap between audio chunks.

        Returns:
            Dict[str, Any]: A dictionary containing the transcription results.
        """
        # TensorFloat32 tensor cores for float32 matrix multiplication availabl
        torch.set_float32_matmul_precision("high")
        audio_input = audio_input.squeeze(0)

        # Split audio input into chunks with overlap
        chunks = chunk_audio(audio_input, chunk_size, overlap_size, overlap_size) if chunk_size > 0 else [audio_input]

        segments = []
        for chunk_id, chunk in enumerate(chunks):
            processed = self.processor(
                chunk,
                return_tensors="pt",
                sampling_rate=model_sampling_rate,
                truncation=False,
                padding="longest",
                do_normalize=True,
                **processor_args,
            )

            if self.use_cuda:
                input_values = processed.input_values.to(self.device_map)
                if hasattr(processed, "attention_mask"):
                    attention_mask = processed.attention_mask.to(self.device_map)
            else:
                input_values = processed.input_values
                if hasattr(processed, "attention_mask"):
                    attention_mask = processed.attention_mask

            if self.model.config.feat_extract_norm == "layer":
                logits = self.model(input_values, attention_mask=attention_mask).logits
            else:
                logits = self.model(input_values).logits

            predicted_ids = torch.argmax(logits, dim=-1)

            # Decode each chunk
            chunk_transcription = self.processor.batch_decode(predicted_ids, skip_special_tokens=True)
            segments.append(
                {
                    "tokens": chunk_transcription[0],
                    "start": chunk_id * overlap_size,
                    "end": (chunk_id + 1) * overlap_size,
                }
            )

        transcription = " ".join([s["tokens"].strip() for s in segments])
        return {"transcription": transcription, "segments": segments}


class SpeechToTextInference(AudioBulk, _SpeechToTextInference):
    def __init__(
        self,
        input: BatchInput,
        output: BatchOutput,
        state: State,
        **kwargs,
    ):
        """
        SpeechToTextInference is a class for performing speech-to-text inference using bulk processing.

        Args:
            input (BatchInput): The input data configuration.
            output (BatchOutput): The output data configuration.
            state (State): The state configuration.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(input=input, output=output, state=state, **kwargs)
