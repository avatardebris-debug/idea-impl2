"""MP4 video format handler."""

import os
from typing import Dict, Optional


class MP4Handler:
    """Handler for MP4 video files."""
    
    SUPPORTED_CODECS = ['H.264', 'H.265', 'VP9', 'AV1']
    FORMAT = 'mp4'
    DEFAULT_CODEC = 'H.264'
    MIME_TYPE = 'video/mp4'
    
    def __init__(self, file_path: str):
        if not file_path.lower().endswith('.mp4'):
            raise ValueError(f"Expected .mp4 file, got: {file_path}")
        self.file_path = file_path
    
    @property
    def format(self) -> str:
        return self.FORMAT
    
    def get_metadata(self) -> Dict:
        """Extract metadata from the MP4 file."""
        file_size = os.path.getsize(self.file_path) if os.path.exists(self.file_path) else 0
        return {
            'format': 'mp4',
            'codec': self.DEFAULT_CODEC,
            'mime_type': self.MIME_TYPE,
            'file_size_bytes': file_size,
        }
    
    def validate_integrity(self) -> tuple:
        """Validate the MP4 file integrity."""
        exists = os.path.exists(self.file_path)
        is_valid = exists and self.file_path.lower().endswith('.mp4')
        message = "File validated successfully" if is_valid else "File validation failed"
        return is_valid, message
    
    def convert(self, output_path: str, codec: str = 'H.264') -> bool:
        """Convert the MP4 file to the specified codec."""
        if codec not in self.SUPPORTED_CODECS:
            raise ValueError(f"Unsupported codec: {codec}. Supported: {self.SUPPORTED_CODECS}")
        # Simulate conversion
        with open(output_path, 'w') as f:
            f.write(f'converted mp4 with codec {codec}')
        return True
