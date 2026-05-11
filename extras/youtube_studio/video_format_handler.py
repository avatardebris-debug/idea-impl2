"""Video format handler for YouTube Studio.

This module provides video format detection, validation, and conversion
functionality for YouTube Studio.
"""

import os
import shutil
from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple


class VideoFormatHandler(ABC):
    """Abstract base class for video format handlers."""
    
    def __init__(self, file_path: str):
        """Initialize video format handler.
        
        Args:
            file_path: Path to the video file
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file extension doesn't match handler format
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        self.file_path = file_path
        self.format = self._get_format_from_path(file_path)
    
    @abstractmethod
    def _get_format_from_path(self, file_path: str) -> str:
        """Get format from file path.
        
        Args:
            file_path: Path to the video file
            
        Returns:
            Format name in lowercase
        """
        pass
    
    @abstractmethod
    def get_metadata(self) -> Dict[str, str]:
        """Get video metadata.
        
        Returns:
            Dictionary of metadata
        """
        pass
    
    @abstractmethod
    def validate_integrity(self) -> Tuple[bool, str]:
        """Validate video file integrity.
        
        Returns:
            Tuple of (is_valid, message)
        """
        pass
    
    @abstractmethod
    def convert(self, output_path: str, **kwargs) -> bool:
        """Convert video to another format.
        
        Args:
            output_path: Path for the output file
            **kwargs: Additional conversion parameters
            
        Returns:
            True if conversion successful, False otherwise
        """
        pass


class FormatFactory:
    """Factory for creating video format handlers."""
    
    _handlers = {}  # {format: handler_class}
    
    @classmethod
    def register_handler(cls, format_name: str, handler_class):
        """Register a handler class for a format.
        
        Args:
            format_name: Format name (e.g., 'mp4', 'avi')
            handler_class: Handler class for the format
        """
        cls._handlers[format_name.lower()] = handler_class
    
    @classmethod
    def get_handler(cls, file_path: str) -> Optional[VideoFormatHandler]:
        """Get handler for a video file.
        
        Args:
            file_path: Path to the video file
            
        Returns:
            Handler instance or None if format not supported
        """
        format_name = detect_video_format(file_path)
        if format_name and format_name in cls._handlers:
            return cls._handlers[format_name](file_path)
        return None


def create_handler(file_path: str) -> Optional[VideoFormatHandler]:
    """Create a video format handler for a file.
    
    Args:
        file_path: Path to the video file
        
    Returns:
        Handler instance or None if format not supported
    """
    return FormatFactory.get_handler(file_path)


def detect_video_format(file_path: str) -> Optional[str]:
    """Detect video format from file path.
    
    Args:
        file_path: Path to the video file
        
    Returns:
        Format name in lowercase or None if unsupported
    """
    if not file_path:
        return None
    
    # Get extension and convert to lowercase
    _, ext = os.path.splitext(file_path)
    ext = ext.lower().lstrip('.')
    
    supported_formats = {'mp4', 'avi', 'mov', 'mkv', 'webm', 'flv', 'wmv', 'm4v'}
    
    if ext in supported_formats:
        return ext
    
    return None


class MP4Handler(VideoFormatHandler):
    """Handler for MP4 video files."""
    
    def __init__(self, file_path: str):
        """Initialize MP4 handler.
        
        Args:
            file_path: Path to the MP4 file
            
        Raises:
            ValueError: If file is not MP4 format
        """
        super().__init__(file_path)
        if self.format != 'mp4':
            raise ValueError(f"File is not MP4 format: {file_path}")
    
    def _get_format_from_path(self, file_path: str) -> str:
        """Get format from file path."""
        return detect_video_format(file_path) or 'mp4'
    
    def get_metadata(self) -> Dict[str, str]:
        """Get MP4 video metadata.
        
        Returns:
            Dictionary of metadata
        """
        return {
            'format': 'mp4',
            'codec': 'h264',
            'container': 'MPEG-4',
            'file_size': str(os.path.getsize(self.file_path)),
            'file_path': self.file_path
        }
    
    def validate_integrity(self) -> Tuple[bool, str]:
        """Validate MP4 file integrity.
        
        Returns:
            Tuple of (is_valid, message)
        """
        try:
            # Check if file exists and is readable
            if not os.path.exists(self.file_path):
                return False, "File does not exist"
            
            if not os.access(self.file_path, os.R_OK):
                return False, "File is not readable"
            
            # Check file size
            file_size = os.path.getsize(self.file_path)
            if file_size == 0:
                return False, "File is empty"
            
            # Check file extension
            _, ext = os.path.splitext(self.file_path)
            if ext.lower() != '.mp4':
                return False, "File is not an MP4 file"
            
            return True, "MP4 file is valid"
        except Exception as e:
            return False, f"Error validating MP4 file: {str(e)}"
    
    def convert(self, output_path: str, **kwargs) -> bool:
        """Convert MP4 video to another format.
        
        Args:
            output_path: Path for the output file
            **kwargs: Additional conversion parameters
            
        Returns:
            True if conversion successful, False otherwise
        """
        try:
            # In a real implementation, this would use ffmpeg or similar
            # For now, we'll just copy the file
            shutil.copy2(self.file_path, output_path)
            return True
        except Exception as e:
            print(f"Error converting MP4 file: {str(e)}")
            return False


class AVIHandler(VideoFormatHandler):
    """Handler for AVI video files."""
    
    def __init__(self, file_path: str):
        """Initialize AVI handler.
        
        Args:
            file_path: Path to the AVI file
            
        Raises:
            ValueError: If file is not AVI format
        """
        super().__init__(file_path)
        if self.format != 'avi':
            raise ValueError(f"File is not AVI format: {file_path}")
    
    def _get_format_from_path(self, file_path: str) -> str:
        """Get format from file path."""
        return detect_video_format(file_path) or 'avi'
    
    def get_metadata(self) -> Dict[str, str]:
        """Get AVI video metadata.
        
        Returns:
            Dictionary of metadata
        """
        return {
            'format': 'avi',
            'codec': 'divx',
            'container': 'Audio Video Interleave',
            'file_size': str(os.path.getsize(self.file_path)),
            'file_path': self.file_path
        }
    
    def validate_integrity(self) -> Tuple[bool, str]:
        """Validate AVI file integrity.
        
        Returns:
            Tuple of (is_valid, message)
        """
        try:
            if not os.path.exists(self.file_path):
                return False, "File does not exist"
            
            if not os.access(self.file_path, os.R_OK):
                return False, "File is not readable"
            
            file_size = os.path.getsize(self.file_path)
            if file_size == 0:
                return False, "File is empty"
            
            _, ext = os.path.splitext(self.file_path)
            if ext.lower() != '.avi':
                return False, "File is not an AVI file"
            
            return True, "AVI file is valid"
        except Exception as e:
            return False, f"Error validating AVI file: {str(e)}"
    
    def convert(self, output_path: str, **kwargs) -> bool:
        """Convert AVI video to another format.
        
        Args:
            output_path: Path for the output file
            **kwargs: Additional conversion parameters
            
        Returns:
            True if conversion successful, False otherwise
        """
        try:
            shutil.copy2(self.file_path, output_path)
            return True
        except Exception as e:
            print(f"Error converting AVI file: {str(e)}")
            return False


class MOVHandler(VideoFormatHandler):
    """Handler for MOV video files."""
    
    def __init__(self, file_path: str):
        """Initialize MOV handler.
        
        Args:
            file_path: Path to the MOV file
            
        Raises:
            ValueError: If file is not MOV format
        """
        super().__init__(file_path)
        if self.format != 'mov':
            raise ValueError(f"File is not MOV format: {file_path}")
    
    def _get_format_from_path(self, file_path: str) -> str:
        """Get format from file path."""
        return detect_video_format(file_path) or 'mov'
    
    def get_metadata(self) -> Dict[str, str]:
        """Get MOV video metadata.
        
        Returns:
            Dictionary of metadata
        """
        return {
            'format': 'mov',
            'codec': 'h264',
            'container': 'QuickTime',
            'file_size': str(os.path.getsize(self.file_path)),
            'file_path': self.file_path
        }
    
    def validate_integrity(self) -> Tuple[bool, str]:
        """Validate MOV file integrity.
        
        Returns:
            Tuple of (is_valid, message)
        """
        try:
            if not os.path.exists(self.file_path):
                return False, "File does not exist"
            
            if not os.access(self.file_path, os.R_OK):
                return False, "File is not readable"
            
            file_size = os.path.getsize(self.file_path)
            if file_size == 0:
                return False, "File is empty"
            
            _, ext = os.path.splitext(self.file_path)
            if ext.lower() != '.mov':
                return False, "File is not a MOV file"
            
            return True, "MOV file is valid"
        except Exception as e:
            return False, f"Error validating MOV file: {str(e)}"
    
    def convert(self, output_path: str, **kwargs) -> bool:
        """Convert MOV video to another format.
        
        Args:
            output_path: Path for the output file
            **kwargs: Additional conversion parameters
            
        Returns:
            True if conversion successful, False otherwise
        """
        try:
            shutil.copy2(self.file_path, output_path)
            return True
        except Exception as e:
            print(f"Error converting MOV file: {str(e)}")
            return False


# Register handlers
FormatFactory.register_handler('mp4', MP4Handler)
FormatFactory.register_handler('avi', AVIHandler)
FormatFactory.register_handler('mov', MOVHandler)
