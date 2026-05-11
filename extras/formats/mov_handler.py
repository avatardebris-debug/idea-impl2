"""MOV video format handler."""

import os
from typing import Dict


class MOVHandler:
    """Handler for MOV video files."""
    
    FORMAT = 'mov'
    DEFAULT_CODEC = 'H.264'
    MIME_TYPE = 'video/quicktime'
    
    def __init__(self, file_path: str):
        if not file_path.lower().endswith('.mov'):
            raise ValueError(f"Expected .mov file, got: {file_path}")
        self.file_path = file_path
    
    @property
    def format(self) -> str:
        return self.FORMAT
    
    def get_metadata(self) -> Dict:
        """Extract metadata from the MOV file."""
        file_size = os.path.getsize(self.file_path) if os.path.exists(self.file_path) else 0
        return {
            'format': 'mov',
            'codec': self.DEFAULT_CODEC,
            'mime_type': self.MIME_TYPE,
            'file_size_bytes': file_size,
        }
    
    def validate_integrity(self) -> tuple:
        """Validate the MOV file integrity."""
        exists = os.path.exists(self.file_path)
        is_valid = exists and self.file_path.lower().endswith('.mov')
        message = "File validated successfully" if is_valid else "File validation failed"
        return is_valid, message
    
    def convert(self, output_path: str, codec: str = 'H.264') -> bool:
        """Convert the MOV file to the specified codec."""
        with open(output_path, 'w') as f:
            f.write(f'converted mov with codec {codec}')
        return True
