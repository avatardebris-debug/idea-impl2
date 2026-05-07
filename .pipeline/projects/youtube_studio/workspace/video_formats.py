"""
Video Format Handler Module

This module provides the main VideoFormatHandler class for detecting,
validating, and converting video formats. It serves as the central interface
for all video format operations.
"""

import os
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum

from formats.mp4_handler import MP4Handler, MP4Metadata
from formats.avi_handler import AVIHandler, AVIMetadata
from formats.mov_handler import MOVHandler, MOVMetadata


class VideoFormat(Enum):
    """Enumeration of supported video formats"""
    MP4 = 'mp4'
    AVI = 'avi'
    MOV = 'mov'
    MKV = 'mkv'
    WEBM = 'webm'
    FLV = 'flv'
    WMV = 'wmv'
    UNKNOWN = 'unknown'


@dataclass
class VideoFormatResult:
    """Result of video format detection and validation"""
    format: VideoFormat
    is_valid: bool
    error_message: str
    metadata: Optional[Dict] = None


class FormatDetectionError(Exception):
    """Exception raised when format detection fails"""
    pass


class VideoFormatError(Exception):
    """Exception raised when video format operation fails"""
    pass


class VideoFormatHandler:
    """
    Main handler for video format operations.
    
    This class provides a unified interface for detecting, validating,
    and converting various video formats. It automatically selects the
    appropriate format handler based on the file extension.
    """
    
    # Mapping of file extensions to handler classes
    _FORMAT_HANDLERS: Dict[str, type] = {
        'mp4': MP4Handler,
        'avi': AVIHandler,
        'mov': MOVHandler,
        'm4v': MP4Handler,
        'm4a': MP4Handler,
        'qt': MOVHandler,
    }
    
    # All supported extensions
    SUPPORTED_EXTENSIONS = set(_FORMAT_HANDLERS.keys())
    
    # All supported formats
    SUPPORTED_FORMATS = [f.value for f in VideoFormat if f != VideoFormat.UNKNOWN]
    
    def __init__(self, file_path: str):
        """
        Initialize the video format handler with a file path.
        
        Args:
            file_path: Path to the video file to handle
        """
        self.file_path = file_path
        self._detected_format: Optional[VideoFormat] = None
        self._active_handler: Optional[Union[MP4Handler, AVIHandler, MOVHandler]] = None
    
    def detect_format(self) -> VideoFormat:
        """
        Detect the video format from the file extension.
        
        Returns:
            VideoFormat enum value representing the detected format
        
        Raises:
            FormatDetectionError: If format cannot be detected
        """
        if self._detected_format:
            return self._detected_format
        
        ext = os.path.splitext(self.file_path)[1].lower().lstrip('.')
        
        if not ext:
            raise FormatDetectionError("File has no extension")
        
        if ext in self.SUPPORTED_EXTENSIONS:
            self._detected_format = VideoFormat(ext)
            return self._detected_format
        
        # Check for known formats that might use different extensions
        if ext == 'm4v':
            self._detected_format = VideoFormat.MP4
            return VideoFormat.MP4
        elif ext == 'm4a':
            self._detected_format = VideoFormat.MP4
            return VideoFormat.MP4
        elif ext == 'qt':
            self._detected_format = VideoFormat.MOV
            return VideoFormat.MOV
        
        # Try to detect format from file content (basic check)
        detected = self._detect_from_content()
        if detected:
            self._detected_format = detected
            return detected
        
        self._detected_format = VideoFormat.UNKNOWN
        return VideoFormat.UNKNOWN
    
    def _detect_from_content(self) -> Optional[VideoFormat]:
        """
        Attempt to detect format from file content.
        
        This is a basic check - for more accurate detection, use ffprobe.
        
        Returns:
            Detected format or None if unable to detect
        """
        try:
            with open(self.file_path, 'rb') as f:
                # Check for MP4 (isom)
                f.seek(0)
                header = f.read(12)
                if header[:4] == b'ftyp':
                    content = f.read(100)
                    if b'isom' in content or b'mp42' in content:
                        return VideoFormat.MP4
                
                # Check for MOV
                if header[:4] == b'ftyp':
                    content = f.read(100)
                    if b'mov ' in content or b'qt ' in content:
                        return VideoFormat.MOV
                        
        except Exception:
            pass
        
        return None
    
    def get_handler(self) -> Union[MP4Handler, AVIHandler, MOVHandler]:
        """
        Get the appropriate handler for the detected format.
        
        Returns:
            Handler instance for the detected format
        
        Raises:
            VideoFormatError: If no handler is available for the format
        """
        if self._active_handler:
            return self._active_handler
        
        format_type = self.detect_format()
        
        if format_type == VideoFormat.UNKNOWN:
            raise VideoFormatError(f"No handler available for format: {format_type.value}")
        
        handler_class = self._FORMAT_HANDLERS.get(format_type.value)
        
        if not handler_class:
            raise VideoFormatError(f"No handler class found for format: {format_type.value}")
        
        self._active_handler = handler_class(self.file_path)
        return self._active_handler
    
    def validate(self) -> VideoFormatResult:
        """
        Validate the video file.
        
        Returns:
            VideoFormatResult with validation status and error message
        """
        try:
            handler = self.get_handler()
            is_valid, error_message = handler.validate_file()
            
            return VideoFormatResult(
                format=self._detected_format or VideoFormat.UNKNOWN,
                is_valid=is_valid,
                error_message=error_message
            )
            
        except Exception as e:
            return VideoFormatResult(
                format=VideoFormat.UNKNOWN,
                is_valid=False,
                error_message=str(e)
            )
    
    def get_metadata(self) -> Optional[Dict]:
        """
        Extract metadata from the video file.
        
        Returns:
            Dictionary containing video metadata, or None if extraction fails
        """
        try:
            handler = self.get_handler()
            metadata = handler.get_metadata()
            
            if metadata:
                return {
                    'format': self._detected_format.value,
                    'duration_seconds': metadata.duration_seconds,
                    'width': metadata.width,
                    'height': metadata.height,
                    'video_codec': metadata.video_codec,
                    'audio_codec': metadata.audio_codec,
                    'bitrate_kbps': metadata.bitrate_kbps,
                    'frame_rate': metadata.frame_rate,
                    'file_size_bytes': metadata.file_size_bytes
                }
            
            return None
            
        except Exception as e:
            return None
    
    def convert_to_mp4(self, output_path: str, codec: str = 'h264', audio_codec: str = 'aac') -> Tuple[bool, str]:
        """
        Convert the video file to MP4 format.
        
        Args:
            output_path: Path for the output MP4 file
            codec: Video codec to use (default: h264)
            audio_codec: Audio codec to use (default: aac)
            
        Returns:
            Tuple of (success, message)
        """
        try:
            handler = self.get_handler()
            return handler.convert_to_mp4(output_path, codec, audio_codec)
            
        except Exception as e:
            return False, f"Conversion error: {str(e)}"
    
    def is_youtube_compatible(self) -> Tuple[bool, str]:
        """
        Check if the video file is compatible with YouTube upload requirements.
        
        Returns:
            Tuple of (is_compatible, message)
        """
        try:
            handler = self.get_handler()
            return handler.is_compatible_with_youtube()
            
        except Exception as e:
            return False, f"Compatibility check error: {str(e)}"
    
    @classmethod
    def get_supported_formats(cls) -> List[str]:
        """
        Get list of supported video format extensions.
        
        Returns:
            List of supported format extensions
        """
        return cls.SUPPORTED_FORMATS.copy()
    
    def can_convert(self) -> bool:
        """
        Check if the current file can be converted to MP4.
        
        Returns:
            True if conversion is supported, False otherwise
        """
        try:
            handler = self.get_handler()
            # All handlers support conversion to MP4
            return True
        except VideoFormatError:
            return False
    
    def get_thumbnail_path(self) -> str:
        """
        Get the path for a thumbnail file associated with this video.
        
        Returns:
            Path to the thumbnail file
        """
        try:
            handler = self.get_handler()
            return handler.get_thumbnail_path()
        except VideoFormatError:
            # Fallback: just change extension to .jpg
            base_name = os.path.splitext(os.path.basename(self.file_path))[0]
            return os.path.join(
                os.path.dirname(self.file_path) or '.',
                f"{base_name}.jpg"
            )


# ==== Convenience functions and factory ====


def detect_video_format(file_path: str) -> Optional[str]:
    """
    Detect the video format from a file path.
    
    Args:
        file_path: Path to the video file
        
    Returns:
        Format string (e.g., 'mp4', 'avi', 'mov') or None if unsupported
    """
    ext = os.path.splitext(file_path)[1].lower().lstrip('.')
    if ext in VideoFormatHandler.SUPPORTED_EXTENSIONS:
        # Map aliases to canonical format names
        if ext == 'm4v' or ext == 'm4a':
            return 'mp4'
        elif ext == 'qt':
            return 'mov'
        return ext
    return None


def create_handler(file_path: str) -> Optional[Union[MP4Handler, AVIHandler, MOVHandler]]:
    """
    Factory function to create the appropriate handler for a video file.
    
    Args:
        file_path: Path to the video file
        
    Returns:
        Handler instance or None if format is unsupported
    """
    ext = os.path.splitext(file_path)[1].lower().lstrip('.')
    handler_class = VideoFormatHandler._FORMAT_HANDLERS.get(ext)
    if handler_class:
        return handler_class(file_path)
    return None


class FormatFactory:
    """
    Factory class for creating video format handlers.
    
    Provides a class-based factory interface for creating handlers
    for different video formats.
    """
    
    @staticmethod
    def create(file_path: str) -> Optional[Union[MP4Handler, AVIHandler, MOVHandler]]:
        """
        Create a handler for the given file path.
        
        Args:
            file_path: Path to the video file
            
        Returns:
            Handler instance or None if format is unsupported
        """
        return create_handler(file_path)
    
    @staticmethod
    def detect(file_path: str) -> Optional[str]:
        """
        Detect the format of a video file.
        
        Args:
            file_path: Path to the video file
            
        Returns:
            Format string or None if unsupported
        """
        return detect_video_format(file_path)
    
    @staticmethod
    def get_supported_formats() -> List[str]:
        """
        Get list of supported video format extensions.
        
        Returns:
            List of supported format extensions
        """
        return VideoFormatHandler.SUPPORTED_FORMATS.copy()
