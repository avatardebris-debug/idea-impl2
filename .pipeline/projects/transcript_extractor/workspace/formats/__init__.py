"""
Format handlers for video/audio files.

Provides handlers for different video formats (mp4, avi, mov, mkv).
"""

from .video_handlers import (
    VideoHandler,
    MP4Handler,
    AVIHandler,
    MOVHandler,
    MKVHandler,
    get_handler_for_format,
)

__all__ = [
    "VideoHandler",
    "MP4Handler",
    "AVIHandler",
    "MOVHandler",
    "MKVHandler",
    "get_handler_for_format",
]
