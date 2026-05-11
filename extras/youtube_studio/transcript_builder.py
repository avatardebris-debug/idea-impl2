"""
Transcript Builder Module

This module provides the TranscriptBuilder class for creating and managing
video transcripts with timestamps, sections, and multiple output formats.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import re


class TranscriptFormat(Enum):
    """Supported transcript output formats"""
    SRT = 'srt'
    VTT = 'vtt'
    TXT = 'txt'
    JSON = 'json'
    YAML = 'yaml'


@dataclass
class TranscriptSection:
    """A section within a transcript"""
    title: str
    start_time: float  # in seconds
    end_time: float  # in seconds
    content: str
    timestamp: str = ""  # ISO format timestamp of when section was created


@dataclass
class TranscriptMetadata:
    """Metadata for a generated transcript.
    
    Attributes:
        full_transcript: Complete transcript text.
        sections: List of transcript sections.
        word_count: Total word count.
        duration_seconds: Estimated duration in seconds.
        language: Language code.
        generated_at: Generation timestamp.
    """
    full_transcript: str
    sections: List[TranscriptSection] = field(default_factory=list)
    word_count: int = 0
    duration_seconds: float = 0.0
    language: str = 'en'
    generated_at: datetime = field(default_factory=datetime.now)


class TranscriptBuilder:
    """
    Builder for creating structured video transcripts.
    
    This class provides functionality for building transcripts from text,
    adding timestamps, organizing into sections, and exporting in various formats.
    """
    
    # Default timestamp format
    DEFAULT_TIMESTAMP_FORMAT = '%H:%M:%S'
    
    # SRT timestamp format
    SRT_TIMESTAMP_FORMAT = '%H:%M:%S,%f'[:-3]  # HH:MM:SS,ms
    
    def __init__(self, title: str = "Untitled Transcript", reading_speed: int = 200):
        """
        Initialize the transcript builder.
        
        Args:
            title: Title of the transcript
        """
        self.title = title
        self._sections: List[TranscriptSection] = []
        self._created_at = datetime.now()
        self._updated_at = datetime.now()
        self._reading_speed = reading_speed  # words per minute
    
    def build_transcript(self, content: str, duration: float = 600.0,
                        language: str = 'en') -> TranscriptMetadata:
        """Build a complete transcript from content.
        
        Args:
            content: Video content description.
            duration: Video duration in seconds.
            language: Language code.
            
        Returns:
            TranscriptMetadata object with the built transcript.
        """
        # Split content into sections based on paragraphs
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        if not paragraphs:
            # If no paragraphs, split by sentences
            sentences = [s.strip() for s in re.split(r'[.!?]+', content) if s.strip()]
            paragraphs = sentences if sentences else [content]
        
        # Calculate duration per section
        total_duration = duration
        num_sections = len(paragraphs)
        duration_per_section = total_duration / num_sections if num_sections > 0 else total_duration
        
        # Build sections
        sections = []
        current_time = 0.0
        
        for i, para in enumerate(paragraphs):
            start_time = current_time
            end_time = current_time + duration_per_section
            
            section = TranscriptSection(
                title=f"Section {i + 1}",
                start_time=start_time,
                end_time=end_time,
                content=para,
                timestamp=datetime.now().isoformat()
            )
            sections.append(section)
            current_time = end_time
        
        # Combine full transcript
        full_transcript = '\n\n'.join(paragraphs)
        
        # Calculate word count
        word_count = len(full_transcript.split())
        
        return TranscriptMetadata(
            full_transcript=full_transcript,
            sections=sections,
            word_count=word_count,
            duration_seconds=total_duration,
            language=language,
        )
    
    def add_section(self, title: str, content: str, start_time: float = 0.0,
                   end_time: Optional[float] = None) -> 'TranscriptBuilder':
        """
        Add a section to the transcript.
        
        Args:
            title: Section title
            content: Section content
            start_time: Start time in seconds
            end_time: End time in seconds (calculated if not provided)
            
        Returns:
            Self for method chaining
        """
        # Calculate end time if not provided
        if end_time is None:
            end_time = start_time + self._estimate_duration(content)
        
        # Create timestamp
        timestamp = datetime.now().isoformat()
        
        section = TranscriptSection(
            title=title,
            start_time=start_time,
            end_time=end_time,
            content=content,
            timestamp=timestamp
        )
        
        self._sections.append(section)
        self._updated_at = datetime.now()
        
        return self
    
    def _estimate_duration(self, content: str) -> float:
        """
        Estimate duration of content based on word count.
        
        Args:
            content: Text content
            
        Returns:
            Estimated duration in seconds
        """
        # Average speaking rate: 150 words per minute
        words = len(content.split())
        duration = (words / 150.0) * 60.0
        
        # Add minimum 5 seconds per section
        return max(duration, 5.0)
    
    def set_section_timestamps(self, start_time: float = 0.0, 
                               end_time: Optional[float] = None) -> 'TranscriptBuilder':
        """
        Set timestamps for all sections.
        
        Args:
            start_time: Starting timestamp for first section
            end_time: End timestamp for last section (calculated if not provided)
            
        Returns:
            Self for method chaining
        """
        if not self._sections:
            return self
        
        # Set first section timestamp
        self._sections[0].start_time = start_time
        
        # Set last section end time
        if end_time:
            self._sections[-1].end_time = end_time
        
        # Calculate intermediate timestamps
        total_duration = end_time - start_time if end_time else 0
        num_sections = len(self._sections)
        
        if num_sections > 1 and total_duration > 0:
            duration_per_section = total_duration / num_sections
            for i, section in enumerate(self._sections):
                if i > 0:
                    section.start_time = start_time + (i * duration_per_section)
                if i < num_sections - 1:
                    section.end_time = start_time + ((i + 1) * duration_per_section)
                else:
                    section.end_time = end_time or start_time + duration_per_section
        
        return self
    
    def get_sections(self) -> List[TranscriptSection]:
        """
        Get all sections in the transcript.
        
        Returns:
            List of TranscriptSection objects
        """
        return self._sections.copy()
    
    def get_total_duration(self) -> float:
        """
        Get total duration of the transcript.
        
        Returns:
            Total duration in seconds
        """
        if not self._sections:
            return 0.0
        
        first_start = min(s.start_time for s in self._sections)
        last_end = max(s.end_time for s in self._sections)
        
        return last_end - first_start
    
    def get_summary(self) -> Dict:
        """
        Get a summary of the transcript.
        
        Returns:
            Dictionary containing transcript summary
        """
        total_words = sum(len(s.content.split()) for s in self._sections)
        total_chars = sum(len(s.content) for s in self._sections)
        
        return {
            'title': self.title,
            'num_sections': len(self._sections),
            'total_duration_seconds': round(self.get_total_duration(), 2),
            'total_words': total_words,
            'total_characters': total_chars,
            'created_at': self._created_at.isoformat(),
            'updated_at': self._updated_at.isoformat()
        }
    
    def export_to_srt(self) -> str:
        """
        Export transcript to SRT format.
        
        Returns:
            SRT formatted string
        """
        if not self._sections:
            return ""
        
        srt_content = ""
        for i, section in enumerate(self._sections, 1):
            # SRT format: index, timestamp, content
            srt_content += f"{i}\n"
            srt_content += f"{self._format_timestamp(section.start_time)} --> {self._format_timestamp(section.end_time)}\n"
            srt_content += f"{section.content}\n\n"
        
        return srt_content
    
    def _format_timestamp(self, seconds: float) -> str:
        """
        Format seconds to SRT timestamp format.
        
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
    
    def export_to_vtt(self) -> str:
        """
        Export transcript to VTT format.
        
        Returns:
            VTT formatted string
        """
        if not self._sections:
            return ""
        
        vtt_content = "WEBVTT\n\n"
        
        for section in self._sections:
            vtt_content += f"{self._format_vtt_timestamp(section.start_time)} --> {self._format_vtt_timestamp(section.end_time)}\n"
            vtt_content += f"{section.content}\n\n"
        
        return vtt_content
    
    def _format_vtt_timestamp(self, seconds: float) -> str:
        """
        Format seconds to VTT timestamp format.
        
        Args:
            seconds: Time in seconds
            
        Returns:
            Formatted timestamp string
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
    
    def export_to_txt(self) -> str:
        """
        Export transcript to plain text format.
        
        Returns:
            Plain text formatted string
        """
        if not self._sections:
            return ""
        
        txt_content = f"{self.title}\n"
        txt_content += "=" * len(self.title) + "\n\n"
        
        for section in self._sections:
            txt_content += f"[{self._format_timestamp(section.start_time)} - {self._format_timestamp(section.end_time)}]\n"
            txt_content += f"{section.title}\n"
            txt_content += "-" * len(section.title) + "\n"
            txt_content += f"{section.content}\n\n"
        
        return txt_content
    
    def export_to_json(self) -> str:
        """
        Export transcript to JSON format.
        
        Returns:
            JSON formatted string
        """
        import json
        
        data = {
            'title': self.title,
            'created_at': self._created_at.isoformat(),
            'updated_at': self._updated_at.isoformat(),
            'sections': [
                {
                    'title': section.title,
                    'start_time': section.start_time,
                    'end_time': section.end_time,
                    'content': section.content,
                    'timestamp': section.timestamp
                }
                for section in self._sections
            ]
        }
        
        return json.dumps(data, indent=2)
    
    def export_to_yaml(self) -> str:
        """
        Export transcript to YAML format.
        
        Returns:
            YAML formatted string
        """
        import yaml
        
        data = {
            'title': self.title,
            'created_at': self._created_at.isoformat(),
            'updated_at': self._updated_at.isoformat(),
            'sections': [
                {
                    'title': section.title,
                    'start_time': section.start_time,
                    'end_time': section.end_time,
                    'content': section.content,
                    'timestamp': section.timestamp
                }
                for section in self._sections
            ]
        }
        
        return yaml.dump(data, default_flow_style=False, sort_keys=False)
    
    def export_all_formats(self, output_dir: str = '.') -> Dict[str, str]:
        """
        Export transcript to all supported formats.
        
        Args:
            output_dir: Directory to save files
            
        Returns:
            Dictionary mapping format names to file paths
        """
        import os
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Export to each format
        formats = {
            'srt': self.export_to_srt(),
            'vtt': self.export_to_vtt(),
            'txt': self.export_to_txt(),
            'json': self.export_to_json(),
            'yaml': self.export_to_yaml()
        }
        
        # Save to files
        saved_files = {}
        for format_name, content in formats.items():
            filename = f"{self.title.lower().replace(' ', '_')}_{format_name}.{format_name}"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            saved_files[format_name] = filepath
        
        return saved_files
    
    def clear(self) -> 'TranscriptBuilder':
        """
        Clear all sections from the transcript.
        
        Returns:
            Self for method chaining
        """
        self._sections.clear()
        self._updated_at = datetime.now()
        return self
    
    def merge_sections(self, section_indices: List[int]) -> 'TranscriptBuilder':
        """
        Merge multiple sections into one.
        
        Args:
            section_indices: List of section indices to merge
            
        Returns:
            Self for method chaining
        """
        if len(section_indices) < 2:
            return self
        
        # Sort indices in reverse order to avoid shifting issues
        sorted_indices = sorted(section_indices, reverse=True)
        
        # Merge sections
        merged_content = []
        merged_start = self._sections[sorted_indices[0]].start_time
        merged_end = self._sections[sorted_indices[0]].end_time
        
        for idx in sorted_indices:
            section = self._sections[idx]
            merged_content.append(section.content)
            merged_start = min(merged_start, section.start_time)
            merged_end = max(merged_end, section.end_time)
        
        # Create merged section
        merged_section = TranscriptSection(
            title="Merged Section",
            start_time=merged_start,
            end_time=merged_end,
            content=" ".join(merged_content),
            timestamp=datetime.now().isoformat()
        )
        
        # Remove merged sections and add merged section
        for idx in sorted_indices:
            del self._sections[idx]
        
        self._sections.append(merged_section)
        self._updated_at = datetime.now()
        
        return self
    
    def get_timestamp_range(self) -> Tuple[float, float]:
        """
        Get the timestamp range of the transcript.
        
        Returns:
            Tuple of (start_time, end_time)
        """
        if not self._sections:
            return (0.0, 0.0)
        
        start_time = min(s.start_time for s in self._sections)
        end_time = max(s.end_time for s in self._sections)
        
        return (start_time, end_time)
    
    def get_section_by_time(self, time: float) -> Optional[TranscriptSection]:
        """
        Get the section that contains the given time.
        
        Args:
            time: Time in seconds
            
        Returns:
            TranscriptSection if found, None otherwise
        """
        for section in self._sections:
            if section.start_time <= time <= section.end_time:
                return section
        
        return None
