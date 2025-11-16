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

import io

import numpy as np
import pydub
import soundfile as sf
import torch


def convert_waveform_to_audio_file(
    waveform: torch.Tensor | np.ndarray, format: str = "wav", sample_rate: int = 16_000
) -> bytes:
    """
    Convert an audio waveform tensor to a sound file in various formats.

    Args:
        waveform (torch.Tensor): The waveform tensor output by the TTS model.
        format (str): Desired audio file format. Supported formats include 'wav', 'mp3', 'flac', 'ogg', 'aac', 'wma', 'm4a', 'opus', and 'ac3'.
        sample_rate (int): The sample rate of the audio.

    Returns:
        bytes: The audio file in the specified format as a byte string.
    """
    supported_formats = ["wav", "mp3", "flac", "ogg", "aac", "wma", "m4a", "opus", "ac3"]
    if format not in supported_formats:
        raise ValueError(f"Unsupported audio format: {format}. Supported formats are {supported_formats}.")

    # Convert the tensor to numpy array
    if type(waveform) is torch.Tensor:
        audio_numpy = waveform.cpu().numpy()
    else:
        audio_numpy = waveform

    # Write waveform to buffer as WAV
    with io.BytesIO() as buffer:
        sf.write(buffer, audio_numpy, sample_rate, format="wav")
        buffer.seek(0)
        audio = buffer.read()

    # Convert WAV to the specified format using PyDub
    audio_segment = pydub.AudioSegment.from_file(io.BytesIO(audio), format="wav")

    # Write the audio segment to buffer in the specified format
    with io.BytesIO() as buffer:
        audio_segment.export(buffer, format=format)
        buffer.seek(0)
        converted_audio = buffer.read()

    return converted_audio
