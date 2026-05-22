"""
Video handlers for extracting audio from different video formats.

Supports mp4, avi, mov, mkv formats using ffmpeg-python.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Type
from abc import ABC, abstractmethod

import ffmpeg

from ..constants import SAMPLE_RATE, AUDIO_BITRATE


class VideoHandler(ABC):
    """Abstract base class for video format handlers."""
    
    @property
    @abstractmethod
    def supported_extensions(self) -> list:
        """List of supported file extensions for this handler."""
        pass
    
    @abstractmethod
    def extract_audio(self, input_path: str, output_path: str) -> str:
        """
        Extract audio from video file.
        
        Args:
            input_path: Path to input video file
            output_path: Path where extracted audio will be saved
            
        Returns:
            Path to extracted audio file
            
        Raises:
            ValueError: If input file is not supported
            RuntimeError: If audio extraction fails
        """
        pass
    
    def is_supported(self, file_path: str) -> bool:
        """Check if file format is supported by this handler."""
        ext = Path(file_path).suffix.lower().lstrip('.')
        return ext in self.supported_extensions


class MP4Handler(VideoHandler):
    """Handler for MP4 video format."""
    
    @property
    def supported_extensions(self) -> list:
        return ['mp4', 'm4v']
    
    def extract_audio(self, input_path: str, output_path: str) -> str:
        """Extract audio from MP4 file."""
        try:
            (
                ffmpeg
                .input(input_path)
                .output(
                    output_path,
                    acodec='pcm_s16le',
                    ac=1,
                    ar=str(SAMPLE_RATE),
                    **{'b:a': AUDIO_BITRATE}
                )
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            return output_path
        except ffmpeg.Error as e:
            raise RuntimeError(f"Failed to extract audio from MP4: {e.stderr.decode()}")


class AVIHandler(VideoHandler):
    """Handler for AVI video format."""
    
    @property
    def supported_extensions(self) -> list:
        return ['avi']
    
    def extract_audio(self, input_path: str, output_path: str) -> str:
        """Extract audio from AVI file."""
        try:
            (
                ffmpeg
                .input(input_path)
                .output(
                    output_path,
                    acodec='pcm_s16le',
                    ac=1,
                    ar=str(SAMPLE_RATE),
                    **{'b:a': AUDIO_BITRATE}
                )
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            return output_path
        except ffmpeg.Error as e:
            raise RuntimeError(f"Failed to extract audio from AVI: {e.stderr.decode()}")


class MOVHandler(VideoHandler):
    """Handler for MOV video format."""
    
    @property
    def supported_extensions(self) -> list:
        return ['mov', 'm4a']
    
    def extract_audio(self, input_path: str, output_path: str) -> str:
        """Extract audio from MOV file."""
        try:
            (
                ffmpeg
                .input(input_path)
                .output(
                    output_path,
                    acodec='pcm_s16le',
                    ac=1,
                    ar=str(SAMPLE_RATE),
                    **{'b:a': AUDIO_BITRATE}
                )
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            return output_path
        except ffmpeg.Error as e:
            raise RuntimeError(f"Failed to extract audio from MOV: {e.stderr.decode()}")


class MKVHandler(VideoHandler):
    """Handler for MKV video format."""
    
    @property
    def supported_extensions(self) -> list:
        return ['mkv']
    
    def extract_audio(self, input_path: str, output_path: str) -> str:
        """Extract audio from MKV file."""
        try:
            (
                ffmpeg
                .input(input_path)
                .output(
                    output_path,
                    acodec='pcm_s16le',
                    ac=1,
                    ar=str(SAMPLE_RATE),
                    **{'b:a': AUDIO_BITRATE}
                )
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            return output_path
        except ffmpeg.Error as e:
            raise RuntimeError(f"Failed to extract audio from MKV: {e.stderr.decode()}")


# Registry of all video handlers
HANDLERS: Dict[str, Type[VideoHandler]] = {
    'mp4': MP4Handler,
    'm4v': MP4Handler,
    'avi': AVIHandler,
    'mov': MOVHandler,
    'm4a': MOVHandler,
    'mkv': MKVHandler,
}


def get_handler_for_format(file_path: str) -> Optional[VideoHandler]:
    """
    Get the appropriate video handler for a given file.
    
    Args:
        file_path: Path to the video file
        
    Returns:
        Appropriate VideoHandler instance or None if no handler found
    """
    ext = Path(file_path).suffix.lower().lstrip('.')
    handler_class = HANDLERS.get(ext)
    if handler_class:
        return handler_class()
    return None
