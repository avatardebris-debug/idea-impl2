"""Write a numpy array as a WAV file with proper RIFF header."""

import numpy as np


def write_wav(path: str, waveform: np.ndarray, sample_rate: int):
    """Write a numpy array as a WAV file.

    Args:
        path: Output file path.
        waveform: 1-D numpy array of audio samples (float32).
        sample_rate: Sample rate in Hz.
    """
    # Normalize to 16-bit PCM range
    max_val = np.max(np.abs(waveform))
    if max_val > 0:
        waveform = waveform / max_val * 32767
    pcm_data = waveform.astype(np.int16).tobytes()

    with open(path, "wb") as f:
        # WAV header
        f.write(b"RIFF")
        f.write(int.to_bytes(36 + len(pcm_data), 4, "little"))
        f.write(b"WAVE")
        f.write(b"fmt ")
        f.write(int.to_bytes(16, 4, "little"))  # PCM header size
        f.write(int.to_bytes(1, 2, "little"))   # PCM format
        f.write(int.to_bytes(1, 2, "little"))   # mono
        f.write(int.to_bytes(sample_rate, 4, "little"))
        f.write(int.to_bytes(sample_rate * 2, 4, "little"))  # byte rate
        f.write(int.to_bytes(2, 2, "little"))   # block align
        f.write(int.to_bytes(16, 2, "little"))  # bits per sample
        f.write(b"data")
        f.write(int.to_bytes(len(pcm_data), 4, "little"))
        f.write(pcm_data)
