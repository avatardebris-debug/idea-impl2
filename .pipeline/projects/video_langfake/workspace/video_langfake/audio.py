"""Audio extraction and speech-to-text module."""

import os
import tempfile
import json
from pathlib import Path
from typing import Optional

import numpy as np

from video_langfake.exceptions import AudioError, TranscriptionError

try:
    from moviepy.editor import VideoFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False


def extract_audio(video_path: str, output_path: str = None) -> str:
    """Extract the audio track from a video file.

    Args:
        video_path: Path to the input video file.
        output_path: Optional path for the output audio file.
            If None, a temp file is created and returned.

    Returns:
        Path to the extracted audio file (WAV format).

    Raises:
        AudioError: If extraction fails or dependencies are missing.
    """
    if not os.path.exists(video_path):
        raise AudioError("extract", f"Video file not found: {video_path}")

    if not MOVIEPY_AVAILABLE:
        raise AudioError(
            "extract",
            "moviepy is required for audio extraction. "
            "Install it with: pip install moviepy",
        )

    if output_path is None:
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp.close()
        output_path = tmp.name

    try:
        clip = VideoFileClip(video_path)
        clip.audio.write_audiofile(output_path, codec="pcm_s16le")
        clip.close()
    except Exception as e:
        raise AudioError("extract", f"Failed to extract audio: {e}")

    if not os.path.exists(output_path):
        raise AudioError("extract", f"Output audio file was not created: {output_path}")

    return output_path


def transcribe_audio(
    audio_path: str, language: str = None
) -> dict:
    """Transcribe audio using Whisper (or fall back to a mock implementation).

    Args:
        audio_path: Path to the audio file (WAV/MP3).
        language: Language code for transcription (e.g. 'en', 'es').
            If None, Whisper auto-detects.

    Returns:
        A dict with keys:
            - 'text': Full transcribed text string.
            - 'segments': List of dicts with 'start', 'end', 'text' per segment.
            - 'words': List of dicts with 'word', 'start', 'end' per word.

    Raises:
        TranscriptionError: If transcription fails.
    """
    if not os.path.exists(audio_path):
        raise TranscriptionError(f"Audio file not found: {audio_path}")

    try:
        if WHISPER_AVAILABLE:
            return _transcribe_with_whisper(audio_path, language)
        else:
            return _transcribe_mock(audio_path, language)
    except Exception as e:
        raise TranscriptionError(f"Transcription failed: {e}")


def _transcribe_with_whisper(audio_path: str, language: str = None) -> dict:
    """Use openai-whisper for transcription."""
    model = whisper.load_model("base")
    result = model.transcribe(
        audio_path,
        language=language,
        word_timestamps=True,
    )

    segments = []
    words = []
    full_text = ""

    for seg in result.get("segments", []):
        seg_info = {
            "start": seg.get("start", 0.0),
            "end": seg.get("end", 0.0),
            "text": seg.get("text", "").strip(),
        }
        segments.append(seg_info)
        full_text += seg_info["text"] + " "

        for w in seg.get("words", []):
            words.append({
                "word": w.get("word", "").strip(),
                "start": w.get("start", 0.0),
                "end": w.get("end", 0.0),
            })

    return {
        "text": full_text.strip(),
        "segments": segments,
        "words": words,
    }


def _transcribe_mock(audio_path: str, language: str = None) -> dict:
    """Mock transcription for testing without Whisper."""
    # Simulate a simple transcription result
    return {
        "text": "This is a mock transcription for testing purposes.",
        "segments": [
            {
                "start": 0.0,
                "end": 3.0,
                "text": "This is a mock transcription",
            },
            {
                "start": 3.0,
                "end": 6.0,
                "text": "for testing purposes.",
            },
        ],
        "words": [
            {"word": "This", "start": 0.0, "end": 0.5},
            {"word": "is", "start": 0.5, "end": 1.0},
            {"word": "a", "start": 1.0, "end": 1.5},
            {"word": "mock", "start": 1.5, "end": 2.0},
            {"word": "transcription", "start": 2.0, "end": 2.5},
            {"word": "for", "start": 2.5, "end": 3.0},
            {"word": "testing", "start": 3.0, "end": 3.5},
            {"word": "purposes.", "start": 3.5, "end": 4.0},
        ],
    }


def save_transcription(transcription: dict, output_path: str) -> str:
    """Save transcription results to a JSON file.

    Args:
        transcription: Dict from transcribe_audio().
        output_path: Path to save the JSON file.

    Returns:
        The output path.

    Raises:
        TranscriptionError: If saving fails.
    """
    try:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(transcription, f, indent=2, ensure_ascii=False)
        return output_path
    except Exception as e:
        raise TranscriptionError(f"Failed to save transcription: {e}")


def load_transcription(input_path: str) -> dict:
    """Load transcription results from a JSON file.

    Args:
        input_path: Path to the JSON file.

    Returns:
        The transcription dict.

    Raises:
        TranscriptionError: If loading fails.
    """
    if not os.path.exists(input_path):
        raise TranscriptionError(f"Transcription file not found: {input_path}")

    try:
        with open(input_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise TranscriptionError(f"Invalid JSON in transcription file: {e}")
    except Exception as e:
        raise TranscriptionError(f"Failed to load transcription: {e}")
