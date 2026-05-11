"""
Export Manager Module

This module provides the ExportManager class for exporting video content
in various formats including JSON, YAML, and plain text.
"""

import os
import json
import yaml
from typing import Dict, List, Optional, Any
from datetime import datetime


class ExportManager:
    """
    Manager for exporting video content in various formats.
    
    This class handles exporting video metadata, transcripts,
    and other content to different file formats.
    """
    
    # Supported export formats
    SUPPORTED_FORMATS = ['json', 'yaml', 'txt']
    
    def __init__(self, output_dir: str = 'exports'):
        """
        Initialize the export manager.
        
        Args:
            output_dir: Directory for exported files
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def export_to_json(self, data: Dict[str, Any], filename: str, pretty: bool = True) -> str:
        """
        Export data to JSON format.
        
        Args:
            data: Data to export
            filename: Output filename (without extension)
            pretty: Whether to pretty-print the JSON
            
        Returns:
            Path to the exported file
        """
        filepath = os.path.join(self.output_dir, f"{filename}.json")
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                if pretty:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                else:
                    json.dump(data, f, ensure_ascii=False)
            
            return filepath
        except Exception as e:
            print(f"Error exporting to JSON: {e}")
            raise
    
    def export_to_yaml(self, data: Dict[str, Any], filename: str) -> str:
        """
        Export data to YAML format.
        
        Args:
            data: Data to export
            filename: Output filename (without extension)
            
        Returns:
            Path to the exported file
        """
        filepath = os.path.join(self.output_dir, f"{filename}.yaml")
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            
            return filepath
        except ImportError:
            # If PyYAML is not available, fall back to JSON
            return self.export_to_json(data, filename, pretty=False)
        except Exception as e:
            print(f"Error exporting to YAML: {e}")
            raise
    
    def export_to_text(self, data: Dict[str, Any], filename: str, line_width: int = 80) -> str:
        """
        Export data to plain text format.
        
        Args:
            data: Data to export
            filename: Output filename (without extension)
            line_width: Maximum characters per line
            
        Returns:
            Path to the exported file
        """
        filepath = os.path.join(self.output_dir, f"{filename}.txt")
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                for key, value in data.items():
                    f.write(f"{key}: {value}\n")
            
            return filepath
        except Exception as e:
            print(f"Error exporting to text: {e}")
            raise
    
    def export_to_srt(self, sections: List[Dict[str, Any]], filename: str) -> str:
        """
        Export transcript sections to SRT format.
        
        Args:
            sections: List of transcript sections
            filename: Output filename (without extension)
            
        Returns:
            Path to the exported file
        """
        filepath = os.path.join(self.output_dir, f"{filename}.srt")
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                for i, section in enumerate(sections, 1):
                    start_time = self._format_srt_time(section['start_time'])
                    end_time = self._format_srt_time(section['end_time'])
                    
                    f.write(f"{i}\n")
                    f.write(f"{start_time} --> {end_time}\n")
                    f.write(f"{section['text']}\n\n")
            
            return filepath
        except Exception as e:
            print(f"Error exporting to SRT: {e}")
            raise
    
    def export_to_vtt(self, sections: List[Dict[str, Any]], filename: str) -> str:
        """
        Export transcript sections to WebVTT format.
        
        Args:
            sections: List of transcript sections
            filename: Output filename (without extension)
            
        Returns:
            Path to the exported file
        """
        filepath = os.path.join(self.output_dir, f"{filename}.vtt")
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("WEBVTT\n\n")
                
                for i, section in enumerate(sections, 1):
                    start_time = self._format_vtt_time(section['start_time'])
                    end_time = self._format_vtt_time(section['end_time'])
                    
                    f.write(f"{i}\n")
                    f.write(f"{start_time} --> {end_time}\n")
                    f.write(f"{section['text']}\n\n")
            
            return filepath
        except Exception as e:
            print(f"Error exporting to WebVTT: {e}")
            raise
    
    def export_all(self, data: Dict[str, Any], filename: str, formats: List[str] = None) -> List[str]:
        """
        Export data in multiple formats.
        
        Args:
            data: Data to export
            filename: Base output filename
            formats: List of formats to export to
            
        Returns:
            List of paths to exported files
        """
        if formats is None:
            formats = self.SUPPORTED_FORMATS
        
        exported_files = []
        
        for fmt in formats:
            if fmt == 'json':
                filepath = self.export_to_json(data, filename)
            elif fmt == 'yaml':
                filepath = self.export_to_yaml(data, filename)
            elif fmt == 'txt':
                filepath = self.export_to_text(data, filename)
            else:
                print(f"Unsupported format: {fmt}")
                continue
            
            exported_files.append(filepath)
        
        return exported_files
    
    def _format_srt_time(self, seconds: float) -> str:
        """Format seconds to SRT timestamp format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def _format_vtt_time(self, seconds: float) -> str:
        """Format seconds to WebVTT timestamp format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"