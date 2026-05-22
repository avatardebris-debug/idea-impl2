"""
Audio extractor for extracting audio from video and audio files.

Provides the AudioExtractor class for handling audio extraction from various video and audio formats.
"""

import os
from pathlib import Path
from typing import Optional, List
import logging

from .formats.video_handlers import get_handler_for_format, VideoHandler

logger = logging.getLogger(__name__)

# Supported audio formats
SUPPORTED_AUDIO_FORMATS = ['.wav', '.mp3', '.flac', '.m4a', '.ogg', '.aac', '.wma']

# Supported video formats (handled by video_handlers)
SUPPORTED_VIDEO_FORMATS = ['.mp4', '.avi', '.mov', '.mkv', '.m4v']


class AudioExtractor:
    """Class for extracting audio from video and audio files."""
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize the AudioExtractor.
        
        Args:
            output_dir: Directory for extracted audio files. Uses current directory if None.
        """
        self.output_dir = output_dir or os.getcwd()
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
    
    def extract_audio(
        self,
        input_path: str,
        output_filename: Optional[str] = None,
        sample_rate: int = 16000
    ) -> str:
        """
        Extract audio from a video or audio file.
        
        Args:
            input_path: Path to the input file
            output_filename: Optional custom filename for output. If None, auto-generated.
            sample_rate: Sample rate for extracted audio (default: 16000 Hz)
            
        Returns:
            Path to the extracted audio file
            
        Raises:
            ValueError: If input file is not a supported format
            FileNotFoundError: If input file does not exist
            RuntimeError: If audio extraction fails
        """
        input_path = Path(input_path).resolve()
        
        # Validate input file exists
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        # Check if file is a supported format
        if not self.is_supported_format(str(input_path)):
            raise ValueError(
                f"Unsupported format: {input_path.suffix}. "
                f"Supported formats: mp4, avi, mov, mkv, wav, mp3, flac, m4a, ogg, aac, wma"
            )
        
        # Generate output filename if not provided
        if output_filename is None:
            base_name = input_path.stem
            output_filename = f"{base_name}_extracted.wav"
        
        output_path = Path(self.output_dir) / output_filename
        
        # Check if it's a video file (needs extraction) or audio-only file (just copy)
        if input_path.suffix.lower() in ['.mp4', '.avi', '.mov', '.mkv', '.m4v']:
            # Video file - extract audio
            handler = get_handler_for_format(str(input_path))
            if handler:
                try:
                    result_path = handler.extract_audio(str(input_path), str(output_path))
                    logger.info(f"Audio extracted from video successfully: {result_path}")
                    return result_path
                except RuntimeError as e:
                    logger.error(f"Audio extraction from video failed: {e}")
                    raise
        else:
            # Audio-only file - just copy with proper format conversion
            try:
                import ffmpeg
                (
                    ffmpeg
                    .input(str(input_path))
                    .output(
                        str(output_path),
                        acodec='pcm_s16le',
                        ac=1,
                        ar=str(sample_rate),
                        **{'b:a': '128k'}
                    )
                    .overwrite_output()
                    .run(capture_stdout=True, capture_stderr=True)
                )
                logger.info(f"Audio converted successfully: {output_path}")
                return str(output_path)
            except Exception as e:
                logger.error(f"Audio conversion failed: {e}")
                raise RuntimeError(f"Failed to convert audio file: {e}")
    
    def is_supported_format(self, file_path: str) -> bool:
        """
        Check if a file is a supported video or audio format.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if the file format is supported, False otherwise
        """
        ext = Path(file_path).suffix.lower()
        
        # Check audio formats
        if ext in SUPPORTED_AUDIO_FORMATS:
            return True
        
        # Check video formats
        if ext in SUPPORTED_VIDEO_FORMATS:
            return True
        
        return False
    
    def cleanup_temp_files(self, temp_dir: Optional[str] = None) -> int:
        """
        Clean up temporary audio files.
        
        Args:
            temp_dir: Directory containing temporary files. If None, uses output_dir.
            
        Returns:
            Number of files deleted
        """
        dir_to_clean = temp_dir or self.output_dir
        temp_files = Path(dir_to_clean).glob("*_extracted.wav")
        count = 0
        for file in temp_files:
            try:
                file.unlink()
                count += 1
            except OSError:
                logger.warning(f"Could not delete file: {file}")
        return count
