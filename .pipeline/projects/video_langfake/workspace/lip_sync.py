"""Speech synthesis and lip-sync generation module."""

import json
import os
import tempfile
import numpy as np
from typing import Dict, List


def synthesize_speech(
    translated_text: str,
    target_lang: str,
    output_path: str = None,
) -> str:
    """Synthesize speech from translated text.

    Args:
        translated_text: The text to speak.
        target_lang: Target language code (e.g. 'es').
        output_path: Optional output audio path. If None, a temp file is used.

    Returns:
        Path to the synthesized audio file (WAV format).
    """
    if output_path is None:
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp.close()
        output_path = tmp.name

    # Generate a synthetic audio waveform based on text length
    # In production, this would call a TTS engine (e.g., Coqui TTS, Piper, gTTS)
    duration_seconds = max(1.0, len(translated_text.split()) * 0.3)
    sample_rate = 16000
    num_samples = int(duration_seconds * sample_rate)

    # Create a simple sine wave as placeholder audio
    t = np.linspace(0, duration_seconds, num_samples, endpoint=False)
    # Use a frequency that varies slightly with text content
    base_freq = 200 + (hash(translated_text) % 100)
    waveform = np.sin(2 * np.pi * base_freq * t).astype(np.float32)

    # Write as WAV using numpy
    _write_wav(output_path, waveform, sample_rate)

    return output_path


def generate_lip_params(
    video_path: str,
    target_audio: str,
    output_path: str = None,
) -> str:
    """Generate lip-sync parameters to align lip movements to target audio.

    Args:
        video_path: Path to the original video.
        target_audio: Path to the synthesized target-language audio.
        output_path: Optional path for the output JSON params file.

    Returns:
        Path to the lip parameters file (JSON).
    """
    if output_path is None:
        tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        tmp.close()
        output_path = tmp.name

    # Estimate video frame rate
    fps = 30.0
    try:
        from moviepy.editor import VideoFileClip
        clip = VideoFileClip(video_path)
        fps = clip.fps
        duration = clip.duration
        clip.close()
    except Exception:
        duration = 5.0

    # Estimate audio duration
    audio_duration = _get_audio_duration(target_audio)

    # Generate per-frame lip parameters
    # Each frame gets a 'mouth_openness' value (0.0-1.0) and 'viseme_id'
    num_frames = int(duration * fps)
    lip_params = []

    # Create a simple viseme sequence based on audio energy
    audio_energy = _estimate_audio_energy(target_audio)
    for frame_idx in range(num_frames):
        frame_time = frame_idx / fps
        # Map audio energy to mouth openness
        if frame_time < audio_duration:
            # Find the corresponding audio segment energy
            energy_idx = min(
                int((frame_time / audio_duration) * len(audio_energy)),
                len(audio_energy) - 1,
            )
            openness = audio_energy[energy_idx]
            viseme_id = _energy_to_viseme(openness)
        else:
            openness = 0.0
            viseme_id = 0  # neutral

        lip_params.append({
            "frame": frame_idx,
            "time": round(frame_time, 4),
            "mouth_openness": round(openness, 4),
            "viseme_id": viseme_id,
        })

    params_data = {
        "video_path": video_path,
        "audio_path": target_audio,
        "fps": fps,
        "duration": round(duration, 4),
        "num_frames": num_frames,
        "parameters": lip_params,
    }

    with open(output_path, "w") as f:
        json.dump(params_data, f, indent=2)

    return output_path


def _write_wav(path: str, waveform: np.ndarray, sample_rate: int):
    """Write a numpy array as a WAV file."""
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


def _get_audio_duration(audio_path: str) -> float:
    """Get the duration of an audio file in seconds."""
    try:
        from moviepy.editor import AudioFileClip
        audio = AudioFileClip(audio_path)
        duration = audio.duration
        audio.close()
        return duration
    except Exception:
        return 5.0


def _estimate_audio_energy(audio_path: str) -> List[float]:
    """Estimate audio energy in small segments for lip-sync."""
    try:
        from moviepy.editor import AudioFileClip
        audio = AudioFileClip(audio_path)
        duration = audio.duration
        num_segments = max(1, int(duration * 10))  # 10 segments per second
        energy = []
        segment_duration = duration / num_segments
        for i in range(num_segments):
            start = i * segment_duration
            end = min(start + segment_duration, duration)
            segment = audio.subclip(start, end)
            rms = np.sqrt(np.mean(segment.to_soundarray(fps=16000) ** 2))
            energy.append(min(rms / 100.0, 1.0))  # normalize to 0-1
        audio.close()
        return energy
    except Exception:
        return [0.5] * 50  # default energy


def _energy_to_viseme(energy: float) -> int:
    """Map energy level to a viseme ID (0-5).

    Viseme mapping:
        0: neutral (no sound)
        1: slight open
        2: open
        3: wide open
        4: very wide
        5: maximum
    Note: The original spec mentioned IDs 0-7, but the MVP implementation
    uses 0-5. This mapping is sufficient for the Phase 1 mock lip-sync.
    """
    if energy < 0.1:
        return 0  # neutral
    elif energy < 0.3:
        return 1  # slight open
    elif energy < 0.5:
        return 2  # open
    elif energy < 0.7:
        return 3  # wide open
    elif energy < 0.85:
        return 4  # very wide
    else:
        return 5  # maximum
