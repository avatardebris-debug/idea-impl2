"""
Transcriber module for transcript extraction.

Provides the WhisperTranscriber class for transcribing audio files using Whisper.
"""

from .models.whisper_wrapper import WhisperWrapper, TranscriptionSegment, TranscriptionResultData


class WhisperTranscriber:
    """Main transcriber class for transcript extraction using Whisper."""
    
    def __init__(
        self,
        model_size: str = "small",
        model_path: str = None,
        device: str = "auto",
        compute_type: str = "float32",
    ):
        """
        Initialize the Whisper transcriber.
        
        Args:
            model_size: Size of the Whisper model (tiny, small, medium, large)
            model_path: Path to model files. If None, will download automatically.
            device: Device to use for inference ('cpu', 'cuda', 'auto')
            compute_type: Compute type for inference ('float32', 'float16', 'int8')
        """
        self.wrapper = WhisperWrapper(
            model_size=model_size,
            model_path=model_path,
            device=device,
            compute_type=compute_type,
        )
        self.model_size = model_size
        self.model_path = model_path
    
    def transcribe(
        self,
        audio_path: str,
        language: str = "en",
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
        language: str = "en",
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
        if progress_callback:
            progress_callback(0.0)
        result = self.transcribe(audio_path, language=language)
        if progress_callback:
            progress_callback(100.0)
        return result
