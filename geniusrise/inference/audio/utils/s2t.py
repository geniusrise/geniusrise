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
from typing import Tuple

import librosa
import torch
import torchaudio
from pydub import AudioSegment

# https://gist.github.com/hollance/42e32852f24243b748ae6bc1f985b13a
# fmt: off
whisper_alignment_heads = {
    "whisper-tiny.en": [[1, 0], [2, 0], [2, 5], [3, 0], [3, 1], [3, 2], [3, 3], [3, 4]],
    "whisper-tiny": [[2, 2], [3, 0], [3, 2], [3, 3], [3, 4], [3, 5]],
    "whisper-base.en": [[3, 3], [4, 7], [5, 1], [5, 5], [5, 7]],
    "whisper-base": [[3, 1], [4, 2], [4, 3], [4, 7], [5, 1], [5, 2], [5, 4], [5, 6]],
    "whisper-small.en": [[6, 6], [7, 0], [7, 3], [7, 8], [8, 2], [8, 5], [8, 7], [9, 0], [9, 4], [9, 8], [9, 10], [10, 0], [10, 1], [10, 2], [10, 3], [10, 6], [10, 11], [11, 2], [11, 4]],
    "whisper-small": [[5, 3], [5, 9], [8, 0], [8, 4], [8, 7], [8, 8], [9, 0], [9, 7], [9, 9], [10, 5]],
    "whisper-medium.en": [[11, 4], [14, 1], [14, 12], [14, 14], [15, 4], [16, 0], [16, 4], [16, 9], [17, 12], [17, 14], [18, 7], [18, 10], [18, 15], [20, 0], [20, 3], [20, 9], [20, 14], [21, 12]],
    "whisper-medium": [[13, 15], [15, 4], [15, 15], [16, 1], [20, 0], [23, 4]],
    "whisper-large-v1": [[9, 19], [11, 2], [11, 4], [11, 17], [22, 7], [22, 11], [22, 17], [23, 2], [23, 15]],
    "whisper-large-v2": [[10, 12], [13, 17], [16, 11], [16, 12], [16, 13], [17, 15], [17, 16], [18, 4], [18, 11], [18, 19], [19, 11], [21, 2], [21, 3], [22, 3], [22, 9], [22, 12], [23, 5], [23, 7], [23, 13], [25, 5], [26, 1], [26, 12], [27, 15]],
    "whisper-large": [[10, 12], [13, 17], [16, 11], [16, 12], [16, 13], [17, 15], [17, 16], [18, 4], [18, 11], [18, 19], [19, 11], [21, 2], [21, 3], [22, 3], [22, 9], [22, 12], [23, 5], [23, 7], [23, 13], [25, 5], [26, 1], [26, 12], [27, 15]],
}
# fmt: on


def decode_audio(audio_bytes: bytes, model_type: str, model_sampling_rate: int) -> Tuple[torch.Tensor, int]:
    """
    Decodes the base64 encoded audio data to bytes, determines its sampling rate,
    and converts it to a uniform format based on the model type.

    Args:
        audio_data (str): Base64 encoded audio data.
        model_type (str): The type of model to be used for transcription.

    Returns:
        torch.Tensor: Decoded and converted audio data as a tensor.
        int: The sampling rate of the audio file.
    """
    audio_stream = io.BytesIO(audio_bytes)

    if model_type == "wav2vec":
        # Using Librosa for Wave2Vec
        _waveform, original_sampling_rate = librosa.load(audio_stream, sr=model_sampling_rate, mono=True)
        waveform = torch.from_numpy(_waveform).unsqueeze(0)
        return waveform, int(original_sampling_rate)

    elif model_type == "wav2vec2":
        # Using torchaudio for Wave2Vec2
        _waveform, original_sampling_rate = torchaudio.load(audio_stream)
        if _waveform.shape[0] > 1:
            _waveform = torch.mean(_waveform, dim=0, keepdim=True)  # type: ignore

        # Resample to 16kHz if needed
        if original_sampling_rate != model_sampling_rate:
            _waveform = torchaudio.functional.resample(
                _waveform, orig_freq=original_sampling_rate, new_freq=model_sampling_rate
            )

        return _waveform, original_sampling_rate  # type: ignore

    else:
        # For whisper, seamlessm4t
        # Using PyDub for other models
        audio = AudioSegment.from_file(audio_stream)

        # Get the sampling rate of the audio file
        original_sampling_rate = audio.frame_rate

        # Convert to mono (if not already)
        if audio.channels > 1:
            audio = audio.set_channels(1)

        # Export to a uniform format (e.g., WAV) keeping original sampling rate
        audio_stream = io.BytesIO()
        audio.export(audio_stream, format="wav")
        audio_stream.seek(0)

        # Load the audio into a tensor
        waveform, _ = torchaudio.load(audio_stream, backend="ffmpeg")

        waveform = torchaudio.functional.resample(
            waveform, orig_freq=original_sampling_rate, new_freq=model_sampling_rate
        )
        return waveform, int(original_sampling_rate)


def chunk_audio(audio_input, chunk_size, stride_left, stride_right):
    """
    Splits the audio input into overlapping chunks with specified left and right strides.

    Args:
        audio_input (torch.Tensor): The input audio tensor.
        chunk_size (int): The size of each audio chunk.
        stride_left (int): The size of the left stride for overlap.
        stride_right (int): The size of the right stride for overlap.

    Returns:
        List[torch.Tensor]: List of chunked audio tensors with overlap.
    """
    chunks = []

    for block_start in range(0, len(audio_input), chunk_size):
        chunk_end_idx = min(block_start + chunk_size + stride_right, len(audio_input))
        chunk_start_idx = max(0, block_start - stride_left)

        chunk = audio_input[chunk_start_idx:chunk_end_idx]
        chunks.append(chunk)

    return chunks


def chunk_audio_batched(audio_input, chunk_size, stride_left, stride_right):
    """
    Splits the audio input into overlapping chunks with specified left and right strides.

    Args:
        audio_input (torch.Tensor): The input audio tensor.
        chunk_size (int): The size of each audio chunk.
        stride_left (int): The size of the left stride for overlap.
        stride_right (int): The size of the right stride for overlap.

    Returns:
        List[torch.Tensor]: List of chunked audio tensors with overlap.
    """
    chunks = []
    sequence_length = audio_input.shape[-1]

    for block_start in range(0, sequence_length, chunk_size):
        chunk_end_idx = min(block_start + chunk_size + stride_right, sequence_length)
        chunk_start_idx = max(0, block_start - stride_left)

        chunk = audio_input[:, chunk_start_idx:chunk_end_idx]
        chunks.append(chunk)

    return chunks
