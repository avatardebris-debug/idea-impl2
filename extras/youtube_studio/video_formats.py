"""Video format handler base class and factory."""

from abc import ABC, abstractmethod
from typing import Dict, Optional, List
from formats.mp4_handler import MP4Handler
from formats.avi_handler import AVIHandler
from formats.mov_handler import MOVHandler


class VideoFormatHandler(ABC):
    """Abstract base class for video format handlers."""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
    
    @property
    @abstractmethod
    def format(self) -> str:
        pass
    
    @abstractmethod
    def get_metadata(self) -> Dict:
        pass
    
    @abstractmethod
    def validate_integrity(self) -> tuple:
        pass
    
    @abstractmethod
    def convert(self, output_path: str, **kwargs) -> bool:
        pass


class FormatFactory:
    """Factory for creating video format handlers."""
    
    _handlers = {
        'mp4': MP4Handler,
        'avi': AVIHandler,
        'mov': MOVHandler,
    }
    
    @classmethod
    def get_handler(cls, format_name: str) -> Optional[type]:
        """Get handler class for a format name."""
        return cls._handlers.get(format_name.lower())


def create_handler(file_path: str) -> Optional[VideoFormatHandler]:
    """Create a handler for the given file path."""
    format_name = detect_video_format(file_path)
    if format_name is None:
        return None
    handler_class = FormatFactory.get_handler(format_name)
    if handler_class is None:
        return None
    return handler_class(file_path)


def detect_video_format(file_path: str) -> Optional[str]:
    """Detect video format from file path."""
    ext = file_path.rsplit('.', 1)[-1].lower() if '.' in file_path else None
    supported = {'mp4', 'avi', 'mov'}
    if ext and ext in supported:
        return ext
    return None
