"""Video frame and transcript extractor."""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import numpy as np


class ExtractionError(Exception):
    """Raised when video extraction fails."""
    pass


def _detect_motion(video_path: str) -> np.ndarray:
    """Detect motion timestamps in a video using ffmpeg.

    Uses ffmpeg's scene change detection to find timestamps where
    significant visual changes occur.

    Args:
        video_path: Path to the video file.

    Returns:
        Numpy array of timestamps (in seconds) where motion was detected.
    """
    try:
        result = subprocess.run(
            [
                "ffmpeg",
                "-i", video_path,
                "-vf", "select='gt(scene,0.3)'",
                "-vsync", "vfr",
                os.path.join(tempfile.gettempdir(), "motion_%06d.png"),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        # Parse the output to get timestamps
        timestamps = []
        for line in result.stderr.split("\n"):
            if "pts_time" in line:
                try:
                    ts = float(line.split("pts_time:")[1].split(" ")[0])
                    timestamps.append(ts)
                except (IndexError, ValueError):
                    pass
        return np.array(timestamps) if timestamps else np.array([])
    except Exception:
        return np.array([])


def _extract_adaptive_frames(
    video_path: str,
    output_dir: Path,
    duration: float = 10.0,
    base_interval: float = 2.0,
) -> list[dict[str, Any]]:
    """Extract frames from a video using adaptive motion detection.

    Args:
        video_path: Path to the video file.
        output_dir: Directory to save extracted frames.
        duration: Total video duration in seconds.
        base_interval: Base interval between frames.

    Returns:
        List of frame dicts with 'path' and 'timestamp' keys.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    frames: list[dict[str, Any]] = []

    try:
        motion = _detect_motion(video_path)
        if len(motion) > 0:
            # Use motion-detected timestamps
            for ts in motion:
                if ts <= duration:
                    frame_path = output_dir / f"frame_{int(ts * 1000):06d}.png"
                    subprocess.run(
                        [
                            "ffmpeg",
                            "-i", video_path,
                            "-ss", str(ts),
                            "-vframes", "1",
                            "-q:v", "2",
                            str(frame_path),
                        ],
                        capture_output=True,
                        timeout=30,
                    )
                    if frame_path.exists():
                        frames.append({"path": str(frame_path), "timestamp": float(ts)})
        else:
            # Fallback to uniform extraction
            interval = base_interval
            ts = 0.0
            while ts <= duration:
                frame_path = output_dir / f"frame_{int(ts * 1000):06d}.png"
                subprocess.run(
                    [
                        "ffmpeg",
                        "-i", video_path,
                        "-ss", str(ts),
                        "-vframes", "1",
                        "-q:v", "2",
                        str(frame_path),
                    ],
                    capture_output=True,
                    timeout=30,
                )
                if frame_path.exists():
                    frames.append({"path": str(frame_path), "timestamp": float(ts)})
                ts += interval
    except Exception:
        pass

    return frames


def _normalize_video_format(video_path: str, output_dir: Path) -> str:
    """Normalize a video to MP4 format with H.264 codec.

    Args:
        video_path: Path to the input video.
        output_dir: Directory to save the normalized video.

    Returns:
        Path to the normalized video file.

    Raises:
        ExtractionError: If the format is unsupported or normalization fails.
    """
    ext = Path(video_path).suffix.lower()
    if ext not in (".mp4", ".mov", ".avi", ".mkv", ".webm"):
        raise ExtractionError(f"Unsupported video format: {ext}")

    output_path = output_dir / "normalized.mp4"

    if ext == ".mp4":
        # Check if already H.264
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=codec_name", "-of", "csv=p=0", video_path],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.stdout.strip() == "h264":
            return str(Path(video_path).resolve())

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i", video_path,
            "-c:v", "libx264",
            "-c:a", "aac",
            str(output_path),
        ],
        capture_output=True,
        timeout=60,
    )

    if not output_path.exists():
        raise ExtractionError("Video normalization failed.")

    return str(output_path.resolve())


def extract_frames_and_transcript(
    video_path: str,
    output_dir: Path,
    duration: float = 10.0,
) -> tuple[list[dict[str, Any]], str]:
    """Extract frames and transcript from a video.

    Args:
        video_path: Path to the video file.
        output_dir: Directory to save extracted frames.
        duration: Duration of video to process in seconds.

    Returns:
        Tuple of (frames list, transcript string).

    Raises:
        ExtractionError: If extraction fails.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Normalize video format
    normalized_path = _normalize_video_format(video_path, output_dir)

    # Extract frames
    frames = _extract_adaptive_frames(normalized_path, output_dir, duration)

    # Extract transcript using whisper
    transcript = _extract_transcript(normalized_path)

    return frames, transcript


def _extract_transcript(video_path: str) -> str:
    """Extract audio transcript from a video using whisper.

    Args:
        video_path: Path to the video file.

    Returns:
        Transcript string.
    """
    try:
        import whisper
        model = whisper.load_model("base")
        result = model.transcribe(video_path, language="en")
        return result.get("text", "")
    except Exception:
        # Fallback: return empty transcript
        return ""
