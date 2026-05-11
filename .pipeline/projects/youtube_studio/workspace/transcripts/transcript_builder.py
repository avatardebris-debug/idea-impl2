"""
Transcript Builder Module

This module provides the TranscriptBuilder class for creating and managing
video transcripts with timestamps, sections, and multiple output formats.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
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
    
    def __init__(self, title: str = "Untitled Transcript"):
        """
        Initialize the transcript builder.
        
        Args:
            title: Title of the transcript
        """
        self.title = title
        self._sections: List[TranscriptSection] = []
        self._created_at = datetime.now()
        self._updated_at = datetime.now()
    
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
            'total_chars': total_chars,
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
            # SRT format: index, start --> end, content
            start_time = self._format_srt_timestamp(section.start_time)
            end_time = self._format_srt_timestamp(section.end_time)
            
            srt_content += f"{i}\n"
            srt_content += f"{start_time} --> {end_time}\n"
            srt_content += f"{section.title}\n"
            srt_content += f"{section.content}\n"
            srt_content += "\n"
        
        return srt_content
    
    def export_to_vtt(self) -> str:
        """
        Export transcript to VTT format.
        
        Returns:
            VTT formatted string
        """
        if not self._sections:
            return ""
        
        vtt_content = "WEBVTT\n\n"
        
        for i, section in enumerate(self._sections, 1):
            start_time = self._format_vtt_timestamp(section.start_time)
            end_time = self._format_vtt_timestamp(section.end_time)
            
            vtt_content += f"{start_time}\n"
            vtt_content += f"{end_time}\n"
            vtt_content += f"{section.title}\n"
            vtt_content += f"{section.content}\n"
            vtt_content += "\n"
        
        return vtt_content
    
    def export_to_txt(self) -> str:
        """
        Export transcript to plain text format.
        
        Returns:
            Plain text string
        """
        txt_content = f"{self.title}\n"
        txt_content += "=" * len(self.title) + "\n\n"
        
        for section in self._sections:
            txt_content += f"[{self._format_timestamp(section.start_time)}] {section.title}\n"
            txt_content += f"[{self._format_timestamp(section.end_time)}]\n\n"
            txt_content += f"{section.content}\n\n"
            txt_content += "-" * 50 + "\n\n"
        
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
            'total_duration_seconds': round(self.get_total_duration(), 2),
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
            'total_duration_seconds': round(self.get_total_duration(), 2),
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
        
        return yaml.dump(data, default_flow_style=False)
    
    def export(self, format: TranscriptFormat) -> str:
        """
        Export transcript in the specified format.
        
        Args:
            format: Output format
            
        Returns:
            Formatted string
        """
        exporters = {
            TranscriptFormat.SRT: self.export_to_srt,
            TranscriptFormat.VTT: self.export_to_vtt,
            TranscriptFormat.TXT: self.export_to_txt,
            TranscriptFormat.JSON: self.export_to_json,
            TranscriptFormat.YAML: self.export_to_yaml,
        }
        
        exporter = exporters.get(format)
        if not exporter:
            raise ValueError(f"Unsupported format: {format}")
        
        return exporter()
    
    def _format_srt_timestamp(self, seconds: float) -> str:
        """
        Format seconds to SRT timestamp.
        
        Args:
            seconds: Time in seconds
            
        Returns:
            SRT formatted timestamp
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def _format_vtt_timestamp(self, seconds: float) -> str:
        """
        Format seconds to VTT timestamp.
        
        Args:
            seconds: Time in seconds
            
        Returns:
            VTT formatted timestamp
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
    
    def _format_timestamp(self, seconds: float) -> str:
        """
        Format seconds to human-readable timestamp.
        
        Args:
            seconds: Time in seconds
            
        Returns:
            Human-readable timestamp
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
    
    def add_timestamps_from_text(self, text: str, 
                                 timestamp_pattern: str = r'\[(\d+):(\d+)\]') -> 'TranscriptBuilder':
        """
        Add timestamps to sections from text with timestamp patterns.
        
        Args:
            text: Text with timestamp patterns
            timestamp_pattern: Regex pattern for timestamps
            
        Returns:
            Self for method chaining
        """
        matches = re.finditer(timestamp_pattern, text)
        
        for match in matches:
            minutes = int(match.group(1))
            seconds = int(match.group(2))
            start_time = minutes * 60 + seconds
            
            # Find the content after this timestamp
            start_pos = match.end()
            end_pos = len(text)
            
            # Find next timestamp or end of text
            next_match = re.search(timestamp_pattern, text[start_pos:])
            if next_match:
                end_pos = start_pos + next_match.start()
            
            content = text[start_pos:end_pos].strip()
            
            if content:
                self.add_section(
                    title=f"Section at {minutes}:{seconds:02d}",
                    content=content,
                    start_time=start_time
                )
        
        return self
    
    def split_by_sentences(self, content: str, 
                          chunk_size: int = 100) -> 'TranscriptBuilder':
        """
        Split content into sections by sentences.
        
        Args:
            content: Content to split
            chunk_size: Approximate number of sentences per section
            
        Returns:
            Self for method chaining
        """
        # Split by sentences
        sentences = re.split(r'(?<=[.!?])\s+', content)
        
        # Group sentences into chunks
        for i in range(0, len(sentences), chunk_size):
            chunk = sentences[i:i + chunk_size]
            if chunk:
                section_content = ' '.join(chunk)
                start_time = i * 5  # Assume 5 seconds per sentence
                end_time = (i + len(chunk)) * 5
                
                self.add_section(
                    title=f"Section {i // chunk_size + 1}",
                    content=section_content,
                    start_time=start_time,
                    end_time=end_time
                )
        
        return self
    
    def merge_sections(self, start_index: int, end_index: int) -> 'TranscriptBuilder':
        """
        Merge sections from start_index to end_index.
        
        Args:
            start_index: Start index (inclusive)
            end_index: End index (inclusive)
            
        Returns:
            Self for method chaining
        """
        if start_index < 0 or end_index >= len(self._sections):
            return self
        
        merged_content = ' '.join(
            section.content for section in self._sections[start_index:end_index + 1]
        )
        
        merged_title = f"Merged {start_index + 1}-{end_index + 1}"
        
        # Remove merged sections
        del self._sections[start_index:end_index + 1]
        
        # Add merged section
        self._sections.insert(start_index, TranscriptSection(
            title=merged_title,
            start_time=self._sections[start_index].start_time if self._sections else 0,
            end_time=self._sections[end_index].end_time if end_index < len(self._sections) else 0,
            content=merged_content
        ))
        
        return self
    
    def clear(self):
        """Clear all sections"""
        self._sections.clear()
        self._updated_at = datetime.now()
    
    def get_keyword_density(self) -> Dict[str, int]:
        """
        Get keyword density for the transcript.
        
        Returns:
            Dictionary with word frequencies
        """
        word_freq = {}
        
        for section in self._sections:
            words = section.content.lower().split()
            for word in words:
                # Clean word
                word = re.sub(r'[^\w\s]', '', word)
                if word:
                    word_freq[word] = word_freq.get(word, 0) + 1
        
        return word_freq
    
    def get_top_keywords(self, num_keywords: int = 10) -> List[Tuple[str, int]]:
        """
        Get top keywords by frequency.
        
        Args:
            num_keywords: Number of top keywords to return
            
        Returns:
            List of (keyword, count) tuples
        """
        word_freq = self.get_keyword_density()
        
        # Sort by frequency descending
        sorted_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        return sorted_keywords[:num_keywords]
