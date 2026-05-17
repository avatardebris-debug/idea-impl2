"""Video input handler — accepts local file paths or YouTube URLs."""

import os
import subprocess
import tempfile
import urllib.parse
from pathlib import Path


class VideoInputError(Exception):
    """Raised when video input is invalid or cannot be processed."""
    pass


def _is_youtube_url(url: str) -> bool:
    """Check if a string is a YouTube URL."""
    youtube_domains = [
        "youtube.com", "www.youtube.com", "youtu.be",
        "www.youtu.be", "youtube-nocookie.com",
    ]
    parsed = urllib.parse.urlparse(url)
    return parsed.netloc in youtube_domains


def _is_video_file(path: str) -> bool:
    """Check if a path points to a video file by extension."""
    supported_formats = {
        ".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv",
        ".webm", ".m4v", ".mpg", ".mpeg", ".3gp", ".mts", ".m2ts",
    }
    return Path(path).suffix.lower() in supported_formats


def handle_input(input_str: str) -> str:
    """Handle video input — local file or YouTube URL.

    Args:
        input_str: Local file path or YouTube URL.

    Returns:
        Absolute path to the video file.

    Raises:
        VideoInputError: If input is invalid.
    """
    # Check if it's a YouTube URL
    if _is_youtube_url(input_str):
        return _download_youtube_video(input_str)

    # Check if it's a local file
    if not os.path.exists(input_str):
        raise VideoInputError(f"Input file does not exist: {input_str}")

    if not _is_video_file(input_str):
        raise VideoInputError(f"Input file does not appear to be a video: {input_str}")

    return str(Path(input_str).resolve())


def _download_youtube_video(url: str) -> str:
    """Download a YouTube video using yt-dlp.

    Args:
        url: YouTube video URL.

    Returns:
        Path to the downloaded video file.

    Raises:
        VideoInputError: If yt-dlp is not installed or download fails.
    """
    try:
        import yt_dlp
    except ImportError:
        raise VideoInputError(
            "yt-dlp is required for YouTube URLs. Install it with: pip install yt-dlp"
        )

    with tempfile.TemporaryDirectory() as tmpdir:
        ydl_opts = {
            "outtmpl": os.path.join(tmpdir, "video.%(ext)s"),
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "merge_output_format": "mp4",
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            # Find the downloaded file
            for ext in ["mp4", "mkv", "webm"]:
                candidate = os.path.join(tmpdir, f"video.{ext}")
                if os.path.exists(candidate):
                    return candidate
            # Fallback: list files in tmpdir
            for f in os.listdir(tmpdir):
                if f.endswith((".mp4", ".mkv", ".webm")):
                    return os.path.join(tmpdir, f)

        raise VideoInputError("Failed to download YouTube video.")
