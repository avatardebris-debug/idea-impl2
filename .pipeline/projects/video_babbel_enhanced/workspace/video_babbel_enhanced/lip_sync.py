"""
lip_sync.py — Lip sync generation for video clips.

Uses ffmpeg to overlay a talking-head animation onto video clips.
In production, this would integrate with a lip-sync model (e.g., Wav2Lip,
SadTalker, or a similar service). For now, it generates a placeholder
video with the original audio and a visual indicator.

Public API:
    generate_lipsync(clip_id: str, source_video: str, audio_path: str,
                     output_path: str) -> dict
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import uuid
from typing import Any


def generate_lipsync(
    clip_id: str,
    source_video: str,
    audio_path: str,
    output_path: str,
) -> dict[str, Any]:
    """Generate a lip-synced version of a video clip.

    Args:
        clip_id: Unique clip identifier.
        source_video: Path to the original source video.
        audio_path: Path to the extracted audio for the clip.
        output_path: Path where the lip-synced video will be saved.

    Returns:
        Dict with 'status' (bool) and 'output_path' (str) on success,
        or 'status' (False) and 'error' (str) on failure.
    """
    try:
        source_path = pathlib.Path(source_video)
        audio_p = pathlib.Path(audio_path)
        out_path = pathlib.Path(output_path)

        # Validate inputs
        if not source_path.exists():
            return {"status": False, "error": f"Source video not found: {source_video}"}
        if not audio_p.exists():
            return {"status": False, "error": f"Audio file not found: {audio_path}"}

        # Ensure output directory exists
        out_path.parent.mkdir(parents=True, exist_ok=True)

        # Extract audio duration for the clip
        audio_duration = _get_audio_duration(audio_p)

        # Generate lip-synced video using ffmpeg
        # In production, replace this with a real lip-sync model call.
        # For now, we create a video with the original video content
        # and overlay a subtle animation indicator.
        _generate_placeholder_lipsync(source_path, audio_p, out_path, clip_id)

        return {"status": True, "output_path": str(out_path)}

    except Exception as e:
        return {"status": False, "error": str(e)}


def _get_audio_duration(audio_path: pathlib.Path) -> float:
    """Get the duration of an audio file in seconds using ffprobe."""
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "json",
                str(audio_path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        data = json.loads(result.stdout)
        return float(data["format"]["duration"])
    except (KeyError, ValueError, FileNotFoundError):
        return 10.0  # default fallback


def _generate_placeholder_lipsync(
    source: pathlib.Path,
    audio: pathlib.Path,
    output: pathlib.Path,
    clip_id: str,
) -> None:
    """Generate a lip-synced video.

    In production, this would:
    1. Run the audio through a lip-sync model (e.g., Wav2Lip).
    2. Generate a face animation video.
    3. Overlay the animation onto the source video.

    For now, we create a simple video with the original content
    and a text overlay indicating lip-sync generation.
    """
    # Use ffmpeg to create a video with the original content
    # and add a text overlay for lip-sync status
    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(source),
        "-i", str(audio),
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "libx264",
        "-preset", "fast",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        "-vf", f"drawtext=text='Lip Sync: {clip_id}':fontsize=24:fontcolor=white:x=(w-text_w)/2:y=h-th-10",
        str(output),
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=120,
    )

    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {result.stderr}")
