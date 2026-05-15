"""
Transcription pipeline for end-to-end transcript extraction.

Provides the TranscriptionPipeline class for processing video/audio files.
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict

from .config import Config
from .constants import (
    DEFAULT_MODEL,
    DEFAULT_LANGUAGE,
    DEFAULT_SUMMARY_LENGTH,
    DEFAULT_OUTPUT_FORMAT,
    SAMPLE_RATE,
)
from .audio_extractor import AudioExtractor
from .transcriber import WhisperTranscriber
from .parser import TranscriptFormatter, TranscriptionResultData
from .summarizer import SummaryGenerator

logger = logging.getLogger(__name__)


@dataclass
class TranscriptionOutput:
    """Structured output from transcription pipeline."""
    input_file: str
    transcript: str
    transcript_format: str
    summary: str
    summary_length: str
    language: str
    duration: float
    word_count: int
    segments_count: int
    success: bool
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        import json
        return json.dumps(self.to_dict(), indent=2)


class TranscriptionPipeline:
    """
    Main transcription pipeline that orchestrates all components.
    
    This class provides a unified API for processing video/audio files
    and generating transcripts with summaries.
    """
    
    def __init__(
        self,
        config: Optional[Config] = None,
        model_size: str = DEFAULT_MODEL,
        language: str = DEFAULT_LANGUAGE,
        output_format: str = DEFAULT_OUTPUT_FORMAT,
        summary_length: str = DEFAULT_SUMMARY_LENGTH,
        summary_strategy: str = "extractive",
        audio_extractor=None,
        transcriber=None,
        summarizer=None,
        formatter=None,
    ):
        """
        Initialize the transcription pipeline.
        
        Args:
            config: Configuration object. If None, creates default.
            model_size: Whisper model size (tiny, small, medium, large)
            language: Language code for transcription
            output_format: Output format (txt, srt, vtt, json)
            summary_length: Summary length (short, medium, long)
            summary_strategy: Summarization strategy (extractive, abstractive, simple)
        """
        self.config = config or Config()
        self.model_size = model_size
        self.language = language
        self.output_format = output_format
        self.summary_length = summary_length
        self.summary_strategy = summary_strategy
        
        # Initialize components
        self.audio_extractor = audio_extractor or AudioExtractor(output_dir=self.config.temp_dir)
        self.transcriber = transcriber or WhisperTranscriber(
            model_size=model_size,
            model_path=self.config.model_path,
        )
        self.summarizer = summarizer or SummaryGenerator(
            length=summary_length,
            strategy=summary_strategy,
        )
        self.formatter = formatter or TranscriptFormatter()
        
        logger.info(f"Pipeline initialized with model: {model_size}, language: {language}")
    
    def process(
        self,
        input_path: str,
        output_dir: Optional[str] = None,
        language: Optional[str] = None,
        include_timestamps: bool = True,
    ) -> TranscriptionOutput:
        """
        Process a video/audio file end-to-end.
        
        Args:
            input_path: Path to input file
            output_dir: Directory for output files
            language: Override language for transcription
            include_timestamps: Whether to include timestamps
            
        Returns:
            TranscriptionOutput with results
        """
        try:
            # Validate input
            input_path = Path(input_path).resolve()
            if not input_path.exists():
                raise FileNotFoundError(f"Input file not found: {input_path}")
            
            # Check supported format
            if not self.audio_extractor.is_supported_format(str(input_path)):
                raise ValueError(
                    f"Unsupported format: {input_path.suffix}. "
                    f"Supported formats: mp4, avi, mov, mkv"
                )
            
            logger.info(f"Processing file: {input_path}")
            
            # Extract audio
            audio_path = self.audio_extractor.extract_audio(
                str(input_path),
                sample_rate=SAMPLE_RATE,
            )
            logger.info(f"Audio extracted: {audio_path}")
            
            # Transcribe
            language_to_use = language or self.language
            transcription_result = self.transcriber.transcribe(
                audio_path,
                language=language_to_use,
                include_timestamps=include_timestamps,
            )
            logger.info(f"Transcription complete: {transcription_result.word_count} words")
            
            # Generate summary
            summary_result = self.summarizer.generate(
                transcription_result.text,
                language=transcription_result.language,
            )
            
            # Format transcript
            transcript_text = self.formatter.format_to_txt(
                transcription_result,
                include_timestamps=include_timestamps,
                include_metadata=True,
            )
            
            # Prepare output
            output = TranscriptionOutput(
                input_file=str(input_path),
                transcript=transcript_text,
                transcript_format=self.output_format,
                summary=summary_result["summary"],
                summary_length=self.summary_length,
                language=transcription_result.language,
                duration=transcription_result.duration,
                word_count=transcription_result.word_count,
                segments_count=len(transcription_result.segments),
                success=True,
            )
            
            # Save output if directory specified
            if output_dir:
                output_path = self._save_output(output, output_dir)
                output.input_file = output_path  # Update with output path
            
            logger.info(f"Pipeline completed successfully")
            return output
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            return TranscriptionOutput(
                input_file=str(input_path) if 'input_path' in locals() else "",
                transcript="",
                transcript_format=self.output_format,
                summary="",
                summary_length=self.summary_length,
                language="",
                duration=0,
                word_count=0,
                segments_count=0,
                success=False,
                error_message=str(e),
            )
    
    def _save_output(
        self,
        output: TranscriptionOutput,
        output_dir: str,
    ) -> str:
        """Save output to file."""
        output_dir_path = Path(output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        base_name = Path(output.input_file).stem
        filename = f"{base_name}.{self.output_format}"
        output_path = output_dir_path / filename
        
        # Write content
        content = output.transcript
        if self.output_format == "json":
            content = output.to_json()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Output saved: {output_path}")
        return str(output_path)
    
    def process_batch(
        self,
        input_paths: List[str],
        output_dir: Optional[str] = None,
    ) -> List[TranscriptionOutput]:
        """
        Process multiple files.
        
        Args:
            input_paths: List of input file paths
            output_dir: Directory for output files
            
        Returns:
            List of TranscriptionOutput results
        """
        results = []
        for path in input_paths:
            output = self.process(path, output_dir=output_dir)
            results.append(output)
        return results

    def process_file(
        self,
        input_path: str,
        language: Optional[str] = None,
        include_timestamps: bool = True,
        summary_strategy: Optional[str] = None,
        output_format: Optional[str] = None,
        progress_callback=None,
        cleanup: bool = False,
    ) -> Dict[str, Any]:
        """Backward compatibility for tests expecting process_file."""
        if summary_strategy:
            self.summarizer.strategy = summary_strategy
        if output_format:
            self.output_format = output_format

        output = self.process(
            input_path,
            language=language,
            include_timestamps=include_timestamps,
        )
        if not output.success:
            if isinstance(output.error_message, str) and "not found" in output.error_message.lower():
                raise FileNotFoundError(output.error_message)
            raise Exception(output.error_message)

        if cleanup and hasattr(self.audio_extractor, "cleanup_temp_files"):
            self.audio_extractor.cleanup_temp_files()

        return {
            "transcript": output.transcript,
            "summary": {"summary": output.summary, "key_points": [], "method": self.summarizer.strategy},
            "formatted": {"text": output.transcript, "summary": output.summary}
        }
