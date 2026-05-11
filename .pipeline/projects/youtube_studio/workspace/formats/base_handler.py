"""
Base video format handler and factory for YouTube Studio.

This module provides the abstract base class for all video format handlers
and a factory for creating the appropriate handler based on file extension.
"""

import os
from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple


class VideoFormatHandler(ABC):
    """
    Abstract base class for all video format handlers.
    
    All concrete handlers (MP4, AVI, MOV, etc.) must inherit from this class
    and implement the required abstract methods.
    """
    
    # Format name (e.g., 'mp4', 'avi', 'mov')
    FORMAT_NAME: str = None
    
    # Supported file extensions
    SUPPORTED_EXTENSIONS: list = []
    
    # MIME type for this format
    MIME_TYPE: str = None
    
    # Default codec for this format
    DEFAULT_CODEC: str = None
    
    # Minimum valid file size in bytes
    MIN_FILE_SIZE: int = 1024
    
    def __init__(self, file_path: str):
        """
        Initialize the handler with a file path.
        
        Args:
            file_path: Path to the video file to handle
            
        Raises:
            ValueError: If the file extension doesn't match this format
        """
        self.file_path = file_path
        self._validate_extension(file_path)
    
    @property
    def format(self) -> str:
        """Return the format name."""
        return self.FORMAT_NAME
    
    @property
    def mime_type(self) -> str:
        """Return the MIME type for this format."""
        return self.MIME_TYPE
    
    @property
    def default_codec(self) -> str:
        """Return the default codec for this format."""
        return self.DEFAULT_CODEC
    
    @classmethod
    def is_valid_extension(cls, file_path: str) -> bool:
        """
        Check if the file has a valid extension for this format.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file has a valid extension
        """
        ext = os.path.splitext(file_path)[1].lower().lstrip('.')
        return ext in [e.lower() for e in cls.SUPPORTED_EXTENSIONS]
    
    def _validate_extension(self, file_path: str) -> None:
        """
        Validate that the file extension matches this handler's format.
        
        Args:
            file_path: Path to validate
            
        Raises:
            ValueError: If the extension doesn't match
        """
        if not self.is_valid_extension(file_path):
            ext = os.path.splitext(file_path)[1].lower().lstrip('.')
            valid = ', '.join(self.SUPPORTED_EXTENSIONS)
            raise ValueError(
                f"Invalid extension '.{ext}' for {self.FORMAT_NAME.upper()} handler. "
                f"Valid extensions: {valid}"
            )
    
    @abstractmethod
    def validate_integrity(self) -> Tuple[bool, str]:
        """
        Validate the video file integrity.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        pass
    
    @abstractmethod
    def get_metadata(self) -> Dict:
        """
        Extract metadata from the video file.
        
        Returns:
            Dictionary with metadata fields
        """
        pass
    
    def convert(self, output_path: str, codec: str = None) -> Tuple[bool, str]:
        """
        Convert the video file to the handler's format.
        
        Args:
            output_path: Path for the output file
            codec: Video codec to use (defaults to format's default)
            
        Returns:
            Tuple of (success, message)
        """
        raise NotImplementedError("Subclasses must implement convert()")
    
    def is_compatible_with_youtube(self) -> Tuple[bool, str]:
        """
        Check if the file is compatible with YouTube upload requirements.
        
        Returns:
            Tuple of (is_compatible, message)
        """
        metadata = self.get_metadata()
        
        if not metadata:
            return False, "Unable to extract metadata"
        
        # Check file size (YouTube limit: 256GB)
        file_size = metadata.get('file_size_bytes', 0)
        if file_size > 256 * 1024 * 1024 * 1024:
            return False, f"File size ({file_size} bytes) exceeds YouTube limit (256GB)"
        
        # Check duration (YouTube limit: 12 hours)
        duration = metadata.get('duration_seconds', 0)
        if duration > 12 * 60 * 60:
            return False, f"Video duration ({duration}s) exceeds YouTube limit (12 hours)"
        
        return True, "File is compatible with YouTube"


class FormatFactory:
    """
    Factory class for creating video format handlers.
    
    This class provides a centralized way to create the appropriate handler
    for a given video file based on its extension.
    """
    
    # Registry of format names to handler classes
    _handlers: Dict[str, type] = {}
    
    @classmethod
    def register_handler(cls, format_name: str, handler_class: type) -> None:
        """
        Register a handler class for a specific format.
        
        Args:
            format_name: Format name (e.g., 'mp4', 'avi')
            handler_class: Handler class to register
        """
        cls._handlers[format_name.lower()] = handler_class
    
    @classmethod
    def get_handler(cls, file_path: str) -> Optional[VideoFormatHandler]:
        """
        Get the appropriate handler for a video file.
        
        Args:
            file_path: Path to the video file
            
        Returns:
            Handler instance or None if format is not supported
        """
        format_name = detect_video_format(file_path)
        if format_name is None:
            return None
        
        handler_class = cls._handlers.get(format_name)
        if handler_class is None:
            return None
        
        return handler_class(file_path)
    
    @classmethod
    def get_supported_formats(cls) -> list:
        """
        Get list of supported format names.
        
        Returns:
            List of supported format names
        """
        return list(cls._handlers.keys())


def detect_video_format(file_path: str) -> Optional[str]:
    """
    Detect the video format from the file extension.
    
    Args:
        file_path: Path to the video file
        
    Returns:
        Format name (e.g., 'mp4', 'avi', 'mov') or None if unsupported
    """
    ext = os.path.splitext(file_path)[1].lower().lstrip('.')
    
    # Map of supported formats
    format_map = {
        'mp4': 'mp4',
        'm4a': 'mp4',
        'm4v': 'mp4',
        'avi': 'avi',
        'mov': 'mov',
        'qt': 'mov',
    }
    
    return format_map.get(ext)


def create_handler(file_path: str) -> Optional[VideoFormatHandler]:
    """
    Create the appropriate handler for a video file.
    
    This is a convenience function that uses the FormatFactory.
    
    Args:
        file_path: Path to the video file
        
    Returns:
        Handler instance or None if format is not supported
    """
    return FormatFactory.get_handler(file_path)


# Register default handlers
from .mp4_handler import MP4Handler
from .avi_handler import AVIHandler
from .mov_handler import MOVHandler

FormatFactory.register_handler('mp4', MP4Handler)
FormatFactory.register_handler('avi', AVIHandler)
FormatFactory.register_handler('mov', MOVHandler)
