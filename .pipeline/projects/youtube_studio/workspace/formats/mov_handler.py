"""
MOV Video Format Handler

This module provides specific handling for MOV video files, including
format validation, metadata extraction, and conversion capabilities.
"""

import os
import subprocess
from typing import Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class MOVMetadata:
    """Metadata extracted from MOV files"""
    duration_seconds: float
    width: int
    height: int
    video_codec: str
    audio_codec: str
    bitrate_kbps: int
    frame_rate: float
    file_size_bytes: int


class MOVHandler:
    """
    Handler for MOV video format operations.
    
    This class provides methods for validating MOV files, extracting metadata,
    and performing format-specific operations.
    """
    
    # Supported MOV container formats
    SUPPORTED_CONTAINERS = ['mov', 'qt']
    
    # Common video codecs in MOV
    SUPPORTED_VIDEO_CODECS = ['h264', 'h265', 'hevc', 'prores', 'dnxhd', 'vp9']
    
    # Common audio codecs in MOV
    SUPPORTED_AUDIO_CODECS = ['aac', 'mp3', 'pcm', 'alac', 'mp3']
    
    # Minimum valid file size for MOV
    MIN_FILE_SIZE = 1024  # 1KB
    
    def __init__(self, file_path: str):
        """
        Initialize the MOV handler with a file path.
        
        Args:
            file_path: Path to the MOV file to handle
        """
        self.file_path = file_path
        self._metadata: Optional[MOVMetadata] = None
    
    @classmethod
    def is_valid_extension(cls, file_path: str) -> bool:
        """
        Check if the file has a valid MOV extension.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file has a valid MOV extension
        """
        ext = os.path.splitext(file_path)[1].lower().lstrip('.')
        return ext in cls.SUPPORTED_CONTAINERS
    
    def validate_file(self) -> Tuple[bool, str]:
        """
        Validate the MOV file integrity.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if file exists
        if not os.path.exists(self.file_path):
            return False, f"File not found: {self.file_path}"
        
        # Check file size
        file_size = os.path.getsize(self.file_path)
        if file_size < self.MIN_FILE_SIZE:
            return False, f"File too small: {file_size} bytes (minimum: {self.MIN_FILE_SIZE})"
        
        # Check file extension
        if not self.is_valid_extension(self.file_path):
            return False, f"Invalid MOV file extension: {os.path.splitext(self.file_path)[1]}"
        
        return True, "File is valid"
    
    def get_metadata(self) -> Optional[MOVMetadata]:
        """
        Extract metadata from the MOV file.
        
        Returns:
            MOVMetadata object with file information, or None if extraction fails
        """
        if self._metadata:
            return self._metadata
        
        try:
            # Use ffprobe if available
            result = subprocess.run(
                ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', self.file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return None
            
            import json
            probe_data = json.loads(result.stdout)
            
            # Extract format information
            format_info = probe_data.get('format', {})
            streams = probe_data.get('streams', [])
            
            # Find video and audio streams
            video_stream = next((s for s in streams if s.get('codec_type') == 'video'), None)
            audio_stream = next((s for s in streams if s.get('codec_type') == 'audio'), None)
            
            # Build metadata
            self._metadata = MOVMetadata(
                duration_seconds=float(format_info.get('duration', 0)),
                width=int(video_stream.get('width', 0)) if video_stream else 0,
                height=int(video_stream.get('height', 0)) if video_stream else 0,
                video_codec=video_stream.get('codec_name', 'unknown') if video_stream else 'unknown',
                audio_codec=audio_stream.get('codec_name', 'unknown') if audio_stream else 'unknown',
                bitrate_kbps=int(float(format_info.get('bit_rate', 0)) / 1000) if format_info.get('bit_rate') else 0,
                frame_rate=float(video_stream.get('r_frame_rate', '0/1').split('/')[1]) if video_stream and video_stream.get('r_frame_rate') else 0,
                file_size_bytes=int(format_info.get('size', 0)) if format_info.get('size') else os.path.getsize(self.file_path)
            )
            
            return self._metadata
            
        except Exception as e:
            # Fall back to basic metadata extraction
            return self._get_basic_metadata()
    
    def _get_basic_metadata(self) -> Optional[MOVMetadata]:
        """
        Get basic metadata without external tools.
        
        Returns:
            Basic MOVMetadata object
        """
        file_size = os.path.getsize(self.file_path)
        
        return MOVMetadata(
            duration_seconds=0,  # Cannot determine without ffprobe
            width=0,
            height=0,
            video_codec='unknown',
            audio_codec='unknown',
            bitrate_kbps=0,
            frame_rate=0,
            file_size_bytes=file_size
        )
    
    def convert_to_mp4(self, output_path: str, codec: str = 'h264', audio_codec: str = 'aac') -> Tuple[bool, str]:
        """
        Convert the MOV file to MP4 format.
        
        Args:
            output_path: Path for the output MP4 file
            codec: Video codec to use (default: h264)
            audio_codec: Audio codec to use (default: aac)
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Check if ffmpeg is available
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return False, "FFmpeg not available for conversion"
            
            # Build conversion command
            cmd = [
                'ffmpeg', '-y',  # Overwrite output
                '-i', self.file_path,
                '-c:v', codec,
                '-c:a', audio_codec,
                output_path
            ]
            
            # Run conversion
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout for conversion
            )
            
            if result.returncode == 0:
                return True, f"Successfully converted to MP4: {output_path}"
            else:
                return False, f"Conversion failed: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return False, "Conversion timed out"
        except FileNotFoundError:
            return False, "FFmpeg not found"
        except Exception as e:
            return False, f"Conversion error: {str(e)}"
    
    def is_compatible_with_youtube(self) -> Tuple[bool, str]:
        """
        Check if the MOV file is compatible with YouTube upload requirements.
        
        Note: MOV is not a preferred format for YouTube. It should be converted to MP4.
        
        Returns:
            Tuple of (is_compatible, message)
        """
        # MOV is not directly supported by YouTube regardless of metadata
        return False, "MOV format is not directly supported by YouTube. Please convert to MP4 first."
    
    def get_thumbnail_path(self) -> str:
        """
        Get the path for a thumbnail file associated with this MOV.
        
        Returns:
            Path to the thumbnail file (filename.mov.jpg)
        """
        base_name = os.path.splitext(os.path.basename(self.file_path))[0]
        return os.path.join(
            os.path.dirname(self.file_path) or '.',
            f"{base_name}.jpg"
        )
