"""
Output formatters for transcript data.

Provides formatters for different output types: TXT, SRT, VTT, JSON.
"""

import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict


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


class TranscriptFormatter:
    """Class for formatting transcripts in various output formats."""
    
    def format_to_txt(
        self,
        result: TranscriptionResultData,
        include_timestamps: bool = False,
        include_metadata: bool = True
    ) -> str:
        """
        Format transcript as plain text.
        
        Args:
            result: Transcription result data
            include_timestamps: Whether to include timestamps
            include_metadata: Whether to include metadata header
            
        Returns:
            Formatted transcript as string
        """
        lines = []
        
        if include_metadata:
            lines.append(f"Language: {result.language}")
            lines.append(f"Duration: {result.duration:.2f} seconds")
            lines.append(f"Word count: {result.word_count}")
            lines.append("-" * 50)
            lines.append("")
        
        if include_timestamps:
            for segment in result.segments:
                start_ms = int(segment.start * 1000)
                end_ms = int(segment.end * 1000)
                start_str = self._format_timestamp(segment.start)
                end_str = self._format_timestamp(segment.end)
                lines.append(f"[{start_str}] [{end_str}] {segment.text}")
        else:
            if result.segments:
                for segment in result.segments:
                    lines.append(segment.text)
            else:
                lines.append(result.text)
        
        return "\n".join(lines)
    
    def format_to_srt(self, result: TranscriptionResultData) -> str:
        """
        Format transcript as SRT (SubRip Subtitle) file.
        
        Args:
            result: Transcription result data
            
        Returns:
            Formatted SRT content
        """
        lines = []
        
        for i, segment in enumerate(result.segments, start=1):
            start_str = self._format_timestamp(segment.start)
            end_str = self._format_timestamp(segment.end)
            
            lines.append(str(i))
            lines.append(f"{start_str} --> {end_str}")
            lines.append(segment.text)
            lines.append("")
        
        return "\n".join(lines)
    
    def format_to_vtt(self, result: TranscriptionResultData) -> str:
        """
        Format transcript as VTT (WebVTT) file.
        
        Args:
            result: Transcription result data
            
        Returns:
            Formatted VTT content
        """
        lines = []
        lines.append("WEBVTT")
        lines.append(f"Kind: captions")
        lines.append(f"Language: {result.language}")
        lines.append("")
        
        for i, segment in enumerate(result.segments, start=1):
            start_str = self._format_timestamp(segment.start)
            end_str = self._format_timestamp(segment.end)
            
            lines.append(f"{start_str} --> {end_str}")
            lines.append(segment.text)
            lines.append("")
        
        return "\n".join(lines)
    
    def format_to_json(
        self,
        result: TranscriptionResultData,
        indent: int = 2
    ) -> str:
        """
        Format transcript as JSON.
        
        Args:
            result: Transcription result data
            indent: Indentation level for JSON
            
        Returns:
            Formatted JSON string
        """
        data = {
            "metadata": {
                "language": result.language,
                "duration": result.duration,
                "word_count": result.word_count,
            },
            "text": result.text,
            "segments": [
                {
                    "index": i,
                    "text": segment.text,
                    "start": segment.start,
                    "end": segment.end,
                    "language": segment.language,
                }
                for i, segment in enumerate(result.segments, start=1)
            ]
        }
        
        return json.dumps(data, indent=indent)
    
    def _format_timestamp(self, seconds: float) -> str:
        """
        Format seconds as timestamp string (HH:MM:SS,mmm).
        
        Args:
            seconds: Time in seconds
            
        Returns:
            Formatted timestamp string
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def format_to_txt(
    result: TranscriptionResultData,
    include_timestamps: bool = False,
    include_metadata: bool = True
) -> str:
    """
    Convenience function to format transcript as TXT.
    
    Args:
        result: Transcription result data
        include_timestamps: Whether to include timestamps
        include_metadata: Whether to include metadata header
        
    Returns:
        Formatted transcript as string
    """
    formatter = TranscriptFormatter()
    return formatter.format_to_txt(result, include_timestamps, include_metadata)


def format_to_srt(result: TranscriptionResultData) -> str:
    """
    Convenience function to format transcript as SRT.
    
    Args:
        result: Transcription result data
        
    Returns:
        Formatted SRT content
    """
    formatter = TranscriptFormatter()
    return formatter.format_to_srt(result)


def format_to_vtt(result: TranscriptionResultData) -> str:
    """
    Convenience function to format transcript as VTT.
    
    Args:
        result: Transcription result data
        
    Returns:
        Formatted VTT content
    """
    formatter = TranscriptFormatter()
    return formatter.format_to_vtt(result)


def format_to_json(
    result: TranscriptionResultData,
    indent: int = 2
) -> str:
    """
    Convenience function to format transcript as JSON.
    
    Args:
        result: Transcription result data
        indent: Indentation level for JSON
        
    Returns:
        Formatted JSON string
    """
    formatter = TranscriptFormatter()
    return formatter.format_to_json(result, indent)
