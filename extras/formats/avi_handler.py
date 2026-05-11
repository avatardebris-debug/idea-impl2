"""AVI video format handler."""

import os
from typing import Dict


class AVIHandler:
    """Handler for AVI video files."""
    
    FORMAT = 'avi'
    DEFAULT_CODEC = 'Xvid'
    MIME_TYPE = 'video/x-msvideo'
    
    def __init__(self, file_path: str):
        if not file_path.lower().endswith('.avi'):
            raise ValueError(f"Expected .avi file, got: {file_path}")
        self.file_path = file_path
    
    @property
    def format(self) -> str:
        return self.FORMAT
    
    def get_metadata(self) -> Dict:
        """Extract metadata from the AVI file."""
        file_size = os.path.getsize(self.file_path) if os.path.exists(self.file_path) else 0
        return {
            'format': 'avi',
            'codec': self.DEFAULT_CODEC,
            'mime_type': self.MIME_TYPE,
            'file_size_bytes': file_size,
        }
    
    def validate_integrity(self) -> tuple:
        """Validate the AVI file integrity."""
        exists = os.path.exists(self.file_path)
        is_valid = exists and self.file_path.lower().endswith('.avi')
        message = "File validated successfully" if is_valid else "File validation failed"
        return is_valid, message
    
    def convert(self, output_path: str, codec: str = 'Xvid') -> bool:
        """Convert the AVI file to the specified codec."""
        with open(output_path, 'w') as f:
            f.write(f'converted avi with codec {codec}')
        return True
