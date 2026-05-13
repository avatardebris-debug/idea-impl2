"""Speech synthesis and lip-sync generation module."""

import json
import os
import tempfile
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional

from video_langfake.exceptions import SynthesisError, LipSyncError, AudioError

try:
    from moviepy.editor import VideoFileClip, AudioFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False


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

    Raises:
        SynthesisError: If synthesis fails.
    """
    if not translated_text or not translated_text.strip():
        raise SynthesisError(translated_text, "Empty text provided")

    if not target_lang:
        raise SynthesisError(translated_text, "Target language cannot be empty")

    if output_path is None:
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp.close()
        output_path = tmp.name

    try:
        # Generate a synthetic audio waveform based on text length
        # In production, this would call a TTS engine (e.g., Coqui TTS, Piper, gTTS)
        duration_seconds = max(1.0, len(translated_text.split()) * 0.3)
        sample_rate = 16000
        num_samples = int(duration_seconds * sample_rate)

        # Create a simple sine wave as placeholder audio
        t = np.linspace(0, duration_seconds, num_samples, endpoint=False)
        # Use a frequency that varies slightly with text content (deterministic)
        base_freq = 200 + (sum(ord(c) for c in translated_text) % 100)
        waveform = np.sin(2 * np.pi * base_freq * t).astype(np.float32)

        # Write as WAV using numpy
        _write_wav(output_path, waveform, sample_rate)
    except Exception as e:
        raise SynthesisError(translated_text, f"Failed to synthesize speech: {e}")

    if not os.path.exists(output_path):
        raise SynthesisError(translated_text, f"Output audio file was not created: {output_path}")

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

    Raises:
        LipSyncError: If lip-sync parameter generation fails.
    """
    if not os.path.exists(video_path):
        raise LipSyncError("generate", f"Video file not found: {video_path}")

    if not os.path.exists(target_audio):
        raise LipSyncError("generate", f"Audio file not found: {target_audio}")

    if output_path is None:
        tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        tmp.close()
        output_path = tmp.name

    try:
        # Estimate video frame rate
        fps = 30.0
        duration = 5.0
        if MOVIEPY_AVAILABLE:
            try:
                clip = VideoFileClip(video_path)
                fps = clip.fps or 30.0
                duration = clip.duration or 5.0
                clip.close()
            except Exception:
                pass

        # Generate lip-sync parameters
        # In production, this would use a model like Wav2Lip or SadTalker
        num_frames = int(duration * fps)
        params = []
        for i in range(num_frames):
            # Deterministic lip params based on frame index
            params.append({
                "frame": i,
                "mouth_open": 0.1 + 0.4 * ((i * 7 + 3) % 10) / 9.0,
                "mouth_width": 0.05 + 0.25 * ((i * 11 + 5) % 10) / 9.0,
            })

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump({
                "fps": fps,
                "duration": duration,
                "num_frames": num_frames,
                "params": params,
            }, f, indent=2)
    except Exception as e:
        raise LipSyncError("generate", f"Failed to generate lip parameters: {e}")

    return output_path


def apply_lip_sync(
    video_path: str,
    target_audio: str,
    lip_params_path: str,
    output_path: str = None,
) -> str:
    """Apply lip-sync to the video using generated parameters.

    Args:
        video_path: Path to the original video.
        target_audio: Path to the synthesized target-language audio.
        lip_params_path: Path to the lip parameters JSON file.
        output_path: Optional output video path.

    Returns:
        Path to the lip-synced video file.

    Raises:
        LipSyncError: If lip-sync application fails.
    """
    if not os.path.exists(video_path):
        raise LipSyncError("apply", f"Video file not found: {video_path}")

    if not os.path.exists(target_audio):
        raise LipSyncError("apply", f"Audio file not found: {target_audio}")

    if not os.path.exists(lip_params_path):
        raise LipSyncError("apply", f"Lip params file not found: {lip_params_path}")

    if output_path is None:
        tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        tmp.close()
        output_path = tmp.name

    try:
        # Load lip parameters
        with open(lip_params_path, "r", encoding="utf-8") as f:
            lip_data = json.load(f)

        # In production, this would apply the lip-sync model
        # For MVP, we just replace the audio track
        if MOVIEPY_AVAILABLE:
            video_clip = VideoFileClip(video_path)
            audio_clip = AudioFileClip(target_audio)

            # Trim audio to match video duration
            if audio_clip.duration > video_clip.duration:
                audio_clip = audio_clip.subclip(0, video_clip.duration)

            # Set the new audio track
            final_clip = video_clip.set_audio(audio_clip)
            final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
            final_clip.close()
            video_clip.close()
            audio_clip.close()
        else:
            # Fallback: just copy the video and note that audio replacement is needed
            import shutil
            shutil.copy2(video_path, output_path)
    except Exception as e:
        raise LipSyncError("apply", f"Failed to apply lip-sync: {e}")

    return output_path


def _write_wav(output_path: str, waveform: np.ndarray, sample_rate: int) -> None:
    """Write a numpy array as a WAV file.

    Args:
        output_path: Output file path.
        waveform: Audio waveform array.
        sample_rate: Sample rate in Hz.
    """
    import struct

    with open(output_path, "wb") as f:
        # WAV header
        num_channels = 1
        bits_per_sample = 16
        byte_rate = sample_rate * num_channels * bits_per_sample // 8
        block_align = num_channels * bits_per_sample // 8
        data_size = len(waveform) * bits_per_sample // 8

        f.write(b"RIFF")
        f.write(struct.pack("<I", 36 + data_size))
        f.write(b"WAVE")
        f.write(b"fmt ")
        f.write(struct.pack("<I", 16))
        f.write(struct.pack("<H", 1))  # PCM
        f.write(struct.pack("<H", num_channels))
        f.write(struct.pack("<I", sample_rate))
        f.write(struct.pack("<I", byte_rate))
        f.write(struct.pack("<H", block_align))
        f.write(struct.pack("<H", bits_per_sample))
        f.write(b"data")
        f.write(struct.pack("<I", data_size))

        # Write samples
        for sample in waveform:
            val = int(np.clip(sample * 32767, -32768, 32767))
            f.write(struct.pack("<h", val))
