"""
Whisper wrapper for transcript extraction.

Provides the WhisperTranscriber class for transcribing audio files using Faster-Whisper.
"""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import logging

from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)


@dataclass
class TranscriptionSegment:
    """Represents a segment of transcribed audio."""
    text: str
    start: float
    end: float
    language: str


@dataclass
class TranscriptionResultData:
    """Complete transcription result."""
    text: str
    segments: List[TranscriptionSegment]
    language: str
    duration: float
    word_count: int


class WhisperWrapper:
    """Wrapper class for Faster-Whisper model."""
    
    SUPPORTED_MODELS = ["tiny", "small", "medium", "large-v2", "large-v3"]
    
    def __init__(
        self,
        model_size: str = "small",
        model_path: Optional[str] = None,
        device: str = "auto",
        compute_type: str = "float32",
    ):
        """
        Initialize the Whisper wrapper.
        
        Args:
            model_size: Size of the Whisper model to use (tiny, small, medium, large)
            model_path: Path to model files. If None, will download automatically.
            device: Device to use for inference ('cpu', 'cuda', 'auto')
            compute_type: Compute type for inference ('float32', 'float16', 'int8')
        """
        if model_size not in self.SUPPORTED_MODELS:
            raise ValueError(
                f"Invalid model size: {model_size}. "
                f"Supported sizes: {', '.join(self.SUPPORTED_MODELS)}"
            )
        
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        
        # Determine model path
        self.model_path = model_path or self._get_model_cache_path(model_size)
        
        # Load the model
        try:
            logger.info(f"Loading Whisper model: {model_size} from {self.model_path}")
            self.model = WhisperModel(
                self.model_path,
                device=device,
                compute_type=compute_type,
            )
            logger.info(f"Model loaded successfully: {self.model_size}")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise RuntimeError(f"Failed to load Whisper model: {e}")
    
    def _get_model_cache_path(self, model_size: str) -> str:
        """Get the cache path for Whisper models."""
        cache_dir = os.environ.get("WHISPER_CACHE_DIR", "")
        if cache_dir:
            return os.path.join(cache_dir, model_size)
        # Use huggingface cache
        return model_size
    
    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        word_timestamps: bool = False,
        vad_filter: bool = True,
        vad_parameters: Optional[Dict[str, Any]] = None,
    ) -> TranscriptionResultData:
        """
        Transcribe an audio file.
        
        Args:
            audio_path: Path to the audio file
            language: Language code (e.g., 'en', 'es', 'fr'). If None, auto-detect.
            word_timestamps: Whether to include word-level timestamps
            vad_filter: Whether to use voice activity detection filtering
            vad_parameters: Parameters for VAD filtering
            
        Returns:
            TranscriptionResultData with complete transcription information
            
        Raises:
            FileNotFoundError: If audio file does not exist
            RuntimeError: If transcription fails
        """
        audio_path = Path(audio_path)
        
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        try:
            segments, info = self.model.transcribe(
                str(audio_path),
                language=language,
                word_timestamps=word_timestamps,
                vad_filter=vad_filter,
                vad_parameters=vad_parameters,
            )
            
            # Convert segments to our format
            transcription_segments = []
            full_text = []
            
            for segment in segments:
                transcription_segments.append(TranscriptionSegment(
                    text=segment.text,
                    start=segment.start,
                    end=segment.end,
                    language=info.language,
                ))
                full_text.append(segment.text)
            
            # Calculate duration
            duration = info.duration if hasattr(info, 'duration') else 0.0
            
            # Count words
            word_count = len(" ".join(full_text).split())
            
            return TranscriptionResultData(
                text=" ".join(full_text),
                segments=transcription_segments,
                language=info.language,
                duration=duration,
                word_count=word_count,
            )
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise RuntimeError(f"Transcription failed: {e}")


class WhisperTranscriber:
    """Main transcriber class for transcript extraction."""
    
    def __init__(
        self,
        model_size: str = "small",
        model_path: Optional[str] = None,
        device: str = "auto",
        compute_type: str = "float32",
    ):
        """
        Initialize the Whisper transcriber.
        
        Args:
            model_size: Size of the Whisper model
            model_path: Path to model files
            device: Device to use for inference
            compute_type: Compute type for inference
        """
        self.wrapper = WhisperWrapper(
            model_size=model_size,
            model_path=model_path,
            device=device,
            compute_type=compute_type,
        )
    
    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        include_timestamps: bool = True,
    ) -> TranscriptionResultData:
        """
        Transcribe an audio file.
        
        Args:
            audio_path: Path to the audio file
            language: Language code. If None, auto-detect.
            include_timestamps: Whether to include timestamps in output
            
        Returns:
            TranscriptionResultData with transcription information
        """
        return self.wrapper.transcribe(
            audio_path=audio_path,
            language=language,
            word_timestamps=include_timestamps,
        )
    
    def transcribe_with_progress(
        self,
        audio_path: str,
        language: Optional[str] = None,
        progress_callback=None,
    ) -> TranscriptionResultData:
        """
        Transcribe an audio file with progress reporting.
        
        Args:
            audio_path: Path to the audio file
            language: Language code. If None, auto-detect.
            progress_callback: Optional callback function(progress_percentage: float)
            
        Returns:
            TranscriptionResultData with transcription information
        """
        return self.transcribe(audio_path, language=language)
