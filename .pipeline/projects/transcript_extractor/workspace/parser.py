"""
Parser module for transcript data.

Provides the TranscriptParser class for parsing and formatting transcripts.
"""

from .formatters.output_formats import (
    TranscriptFormatter,
    TranscriptionSegment,
    TranscriptionResultData,
    format_to_txt,
    format_to_srt,
    format_to_vtt,
    format_to_json,
)

__all__ = [
    "TranscriptParser",
    "TranscriptionSegment",
    "TranscriptionResultData",
    "format_to_txt",
    "format_to_srt",
    "format_to_vtt",
    "format_to_json",
]


class TranscriptParser:
    """Class for parsing and validating transcript data."""
    
    @staticmethod
    def parse_text(text: str, language: str = "en", duration: float = 0.0) -> TranscriptionResultData:
        """
        Parse plain text into a structured transcription result.
        
        Args:
            text: Plain text content
            language: Language code
            duration: Duration in seconds
            
        Returns:
            TranscriptionResultData with parsed content
        """
        # Count words properly
        words = text.split()
        return TranscriptionResultData(
            text=text,
            segments=[],
            language=language,
            duration=duration,
            word_count=len(words),
        )
    
    @staticmethod
    def parse_segments(
        segments_data: list,
        language: str = "en",
        duration: float = 0.0,
    ) -> TranscriptionResultData:
        """
        Parse segment data into a structured transcription result.
        
        Args:
            segments_data: List of segment dictionaries with 'text', 'start', 'end'
            language: Language code
            duration: Total duration in seconds
            
        Returns:
            TranscriptionResultData with parsed segments
        """
        transcription_segments = []
        full_text_parts = []
        
        for segment_data in segments_data:
            segment = TranscriptionSegment(
                text=segment_data.get('text', ''),
                start=segment_data.get('start', 0.0),
                end=segment_data.get('end', 0.0),
                language=segment_data.get('language', language),
            )
            transcription_segments.append(segment)
            full_text_parts.append(segment.text)
        
        full_text = " ".join(full_text_parts)
        word_count = len(full_text.split())
        
        return TranscriptionResultData(
            text=full_text,
            segments=transcription_segments,
            language=language,
            duration=duration,
            word_count=word_count,
        )
    
    @staticmethod
    def validate_result(result: TranscriptionResultData) -> bool:
        """
        Validate a transcription result.
        
        Args:
            result: TranscriptionResultData to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not result.text or len(result.text.strip()) == 0:
            return False
        if result.word_count < 0:
            return False
        if result.duration < 0:
            return False
        return True
