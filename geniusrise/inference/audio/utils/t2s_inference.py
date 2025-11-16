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

from typing import Dict, List

import numpy as np
import torch
from datasets import load_dataset
from geniusrise import BatchInput, BatchOutput, State
from transformers import AutoModelForSeq2SeqLM, AutoProcessor, AutoTokenizer, SpeechT5HifiGan

from geniusrise.inference.audio.base import AudioBulk


class _TextToSpeechInference:
    """
    _TextToSpeechInference is a base class that provides common functionality for text-to-speech inference.
    It contains methods for processing text input using various models and frameworks.

    Attributes:
        model (AutoModelForSeq2SeqLM): The text-to-speech model.
        tokenizer (AutoTokenizer): The tokenizer for preparing text input for the model.
        processor (AutoProcessor): The processor for post-processing the generated speech.
        vocoder (Any): The vocoder for converting generated features to waveforms.
        embeddings_dataset (Any): The dataset containing speaker embeddings for voice customization.
        use_cuda (bool): Flag indicating whether to use CUDA for GPU acceleration.
        device_map (str | Dict | None): Device mapping for model execution.
    """

    model: AutoModelForSeq2SeqLM
    tokenizer: AutoTokenizer
    processor: AutoProcessor
    vocoder = None
    embeddings_dataset = None
    use_cuda: bool
    device_map: str | Dict | None

    def process_mms(self, text_input: str, generate_args: dict) -> np.ndarray:
        """
        Processes text input with the MMS model.

        Args:
            text_input (str): The input text for speech synthesis.
            generate_args (Dict[str, Any]): Additional arguments for speech synthesis.

        Returns:
            np.ndarray: The synthesized speech waveform.
        """
        inputs = self.processor(text_input, return_tensors="pt")

        if self.use_cuda:
            inputs = inputs.to(self.device_map)

        with torch.no_grad():
            outputs = self.model(**inputs, **generate_args)

        waveform = outputs.waveform[0].cpu().numpy().squeeze()
        return waveform

    def process_bark(self, text_input: str, voice_preset: str, generate_args: dict) -> np.ndarray:
        """
        Processes text input with the BARK model.

        Args:
            text_input (str): The input text for speech synthesis.
            voice_preset (str): The voice preset to use for synthesis.
            generate_args (Dict[str, Any]): Additional arguments for speech synthesis.

        Returns:
            np.ndarray: The synthesized speech waveform.
        """
        # Process the input text with the selected voice preset
        # Presets here: https://suno-ai.notion.site/8b8e8749ed514b0cbf3f699013548683?v=bc67cff786b04b50b3ceb756fd05f68c
        chunks = text_input.split(".")
        audio_arrays: List[np.ndarray] = []
        for chunk in chunks:
            inputs = self.processor(chunk, voice_preset=voice_preset, return_tensors="pt", return_attention_mask=True)

            if self.use_cuda:
                inputs = inputs.to(self.device_map)

            # Generate the audio waveform
            with torch.no_grad():
                audio_array = self.model.generate(**inputs, **generate_args, min_eos_p=0.05)
                audio_array = audio_array.cpu().numpy().squeeze()
                audio_arrays.append(audio_array)

        return np.concatenate(audio_arrays)

    def process_speecht5_tts(self, text_input: str, voice_preset: str, generate_args: dict) -> np.ndarray:
        """
        Processes text input with the SpeechT5-TTS model.

        Args:
            text_input (str): The input text for speech synthesis.
            voice_preset (str): The voice preset to use for synthesis.
            generate_args (Dict[str, Any]): Additional arguments for speech synthesis.

        Returns:
            np.ndarray: The synthesized speech waveform.
        """
        if not self.vocoder:
            self.vocoder = SpeechT5HifiGan.from_pretrained("microsoft/speecht5_hifigan")
            if self.use_cuda:
                self.vocoder = self.vocoder.to(self.device_map)  # type: ignore
        if not self.embeddings_dataset:
            # use the CMU arctic dataset for voice presets
            self.embeddings_dataset = load_dataset(
                "Matthijs/cmu-arctic-xvectors", split="validation", revision="01090996e2ec93b238f194db1ff9c184ed741b07"
            )

        chunks = text_input.split(".")
        audio_arrays: List[np.ndarray] = []
        for chunk in chunks:
            inputs = self.processor(text=chunk, return_tensors="pt")
            speaker_embeddings = torch.tensor(self.embeddings_dataset[int(voice_preset)]["xvector"]).unsqueeze(0)  # type: ignore

            if self.use_cuda:
                inputs = inputs.to(self.device_map)
                speaker_embeddings = speaker_embeddings.to(self.device_map)  # type: ignore

            with torch.no_grad():
                # Generate speech tensor
                speech = self.model.generate_speech(inputs["input_ids"], speaker_embeddings, vocoder=self.vocoder)
                audio_output = speech.cpu().numpy().squeeze()
                audio_arrays.append(audio_output)

        return np.concatenate(audio_arrays)

    def process_seamless(self, text_input: str, voice_preset: str, generate_args: dict) -> np.ndarray:
        """
        Processes text input with the Seamless model.

        Args:
            text_input (str): The input text for speech synthesis.
            voice_preset (str): The voice preset to use for synthesis.
            generate_args (Dict[str, Any]): Additional arguments for speech synthesis.

        Returns:
            np.ndarray: The synthesized speech waveform.
        """
        # Splitting the input text into chunks based on full stops to manage long text inputs
        chunks = text_input.split(".")
        audio_arrays: List[np.ndarray] = []

        for chunk in chunks:
            inputs = self.processor(
                text=chunk,
                return_tensors="pt",
                src_lang="eng" if "src_lang" not in generate_args else generate_args["src_lang"],
            )

            if "src_lang" in generate_args:
                del generate_args["src_lang"]

            if self.use_cuda:
                inputs = inputs.to(self.device_map)

            # Generate the audio waveform
            with torch.no_grad():
                # Seamless M4T v2 specific generation code
                outputs = self.model.generate(inputs.input_ids, speaker_id=int(voice_preset), **generate_args)[0]

            audio_array = outputs.cpu().numpy().squeeze()
            audio_arrays.append(audio_array)

        return np.concatenate(audio_arrays)


class TextToSpeechInference(AudioBulk, _TextToSpeechInference):
    def __init__(
        self,
        input: BatchInput,
        output: BatchOutput,
        state: State,
        **kwargs,
    ):
        """
        TextToSpeechInference is a class for performing text-to-speech inference using bulk processing.

        Args:
            input (BatchInput): The input data configuration.
            output (BatchOutput): The output data configuration.
            state (State): The state configuration.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(input=input, output=output, state=state, **kwargs)
