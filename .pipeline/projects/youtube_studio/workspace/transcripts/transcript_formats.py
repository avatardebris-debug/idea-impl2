"""
Transcript Formats Module

This module provides transcript format definitions and conversion utilities
for various output formats.
"""

from typing import Dict, List, Optional, Tuple
from enum import Enum


class TranscriptFormats(Enum):
    """Supported transcript formats"""
    SRT = 'srt'
    VTT = 'vtt'
    TXT = 'txt'
    JSON = 'json'
    YAML = 'yaml'


# Format specifications
FORMAT_SPECS: Dict[str, Dict] = {
    'srt': {
        'name': 'SubRip Subtitle',
        'extension': 'srt',
        'description': 'Standard subtitle format used by most video players',
        'timestamp_format': 'HH:MM:SS,mmm --> HH:MM:SS,mmm',
        'encoding': 'UTF-8',
        'features': ['timestamps', 'sequence_numbers', 'multi-line support']
    },
    'vtt': {
        'name': 'WebVTT',
        'extension': 'vtt',
        'description': 'Web Video Text Tracks format for web-based video players',
        'timestamp_format': 'HH:MM:SS.mmm --> HH:MM:SS.mmm',
        'encoding': 'UTF-8',
        'features': ['timestamps', 'cue settings', 'HTML support', 'metadata']
    },
    'txt': {
        'name': 'Plain Text',
        'extension': 'txt',
        'description': 'Simple text format with timestamps and sections',
        'timestamp_format': '[HH:MM:SS - HH:MM:SS]',
        'encoding': 'UTF-8',
        'features': ['timestamps', 'section headers', 'readable format']
    },
    'json': {
        'name': 'JSON',
        'extension': 'json',
        'description': 'Structured data format for programmatic access',
        'timestamp_format': 'ISO 8601 or float seconds',
        'encoding': 'UTF-8',
        'features': ['structured data', 'metadata', 'easy parsing', 'validation']
    },
    'yaml': {
        'name': 'YAML',
        'extension': 'yaml',
        'description': 'Human-readable data serialization format',
        'timestamp_format': 'ISO 8601 or float seconds',
        'encoding': 'UTF-8',
        'features': ['human-readable', 'structured', 'validation', 'comments']
    }
}


def format_to_extension(format_name: str) -> str:
    """
    Convert format name to file extension.
    
    Args:
        format_name: Format name or enum value
        
    Returns:
        File extension string
    """
    if isinstance(format_name, TranscriptFormats):
        format_name = format_name.value
    
    format_name = format_name.lower()
    
    if format_name in FORMAT_SPECS:
        return FORMAT_SPECS[format_name]['extension']
    
    # Try to match by extension
    for spec in FORMAT_SPECS.values():
        if spec['extension'] == format_name:
            return spec['extension']
    
    raise ValueError(f"Unknown format: {format_name}")


def get_format_spec(format_name: str) -> Dict:
    """
    Get specifications for a format.
    
    Args:
        format_name: Format name or enum value
        
    Returns:
        Dictionary containing format specifications
    """
    if isinstance(format_name, TranscriptFormats):
        format_name = format_name.value
    
    format_name = format_name.lower()
    
    if format_name in FORMAT_SPECS:
        return FORMAT_SPECS[format_name]
    
    raise ValueError(f"Unknown format: {format_name}")


def is_valid_format(format_name: str) -> bool:
    """
    Check if a format name is valid.
    
    Args:
        format_name: Format name to check
        
    Returns:
        True if format is valid, False otherwise
    """
    try:
        get_format_spec(format_name)
        return True
    except ValueError:
        return False


def get_all_formats() -> List[Dict]:
    """
    Get all supported transcript formats.
    
    Returns:
        List of format specifications
    """
    return [
        {
            'name': spec['name'],
            'extension': spec['extension'],
            'description': spec['description'],
            'features': spec['features']
        }
        for spec in FORMAT_SPECS.values()
    ]


def get_format_by_extension(extension: str) -> Optional[str]:
    """
    Get format name by file extension.
    
    Args:
        extension: File extension to match
        
    Returns:
        Format name or None if not found
    """
    extension = extension.lower().lstrip('.')
    
    for format_name, spec in FORMAT_SPECS.items():
        if spec['extension'] == extension:
            return format_name
    
    return None


def get_supported_features(format_name: str) -> List[str]:
    """
    Get supported features for a format.
    
    Args:
        format_name: Format name or enum value
        
    Returns:
        List of supported features
    """
    spec = get_format_spec(format_name)
    return spec['features']


def get_timestamp_format(format_name: str) -> str:
    """
    Get timestamp format string for a format.
    
    Args:
        format_name: Format name or enum value
        
    Returns:
        Timestamp format string
    """
    spec = get_format_spec(format_name)
    return spec['timestamp_format']


def convert_timestamp_format(timestamp: str, 
                            from_format: str, 
                            to_format: str) -> str:
    """
    Convert timestamp between formats.
    
    Args:
        timestamp: Timestamp string to convert
        from_format: Source format name
        to_format: Target format name
        
    Returns:
        Converted timestamp string
    """
    # Parse the timestamp based on source format
    if from_format.lower() == 'srt':
        # SRT format: HH:MM:SS,mmm
        parts = timestamp.split(',')
        time_part = parts[0]
        millis = int(parts[1]) if len(parts) > 1 else 0
        
        hours, minutes, seconds = time_part.split(':')
        total_seconds = int(hours) * 3600 + int(minutes) * 60 + int(seconds) + millis / 1000.0
        
    elif from_format.lower() == 'vtt':
        # VTT format: HH:MM:SS.mmm
        parts = timestamp.split('.')
        time_part = parts[0]
        millis = int(parts[1]) if len(parts) > 1 else 0
        
        hours, minutes, seconds = time_part.split(':')
        total_seconds = int(hours) * 3600 + int(minutes) * 60 + int(seconds) + millis / 1000.0
        
    elif from_format.lower() == 'txt':
        # TXT format: [HH:MM:SS - HH:MM:SS]
        # Extract start time
        start_part = timestamp.split(' - ')[0].strip('[]')
        hours, minutes, seconds = start_part.split(':')
        total_seconds = int(hours) * 3600 + int(minutes) * 60 + int(seconds)
        
    elif from_format.lower() in ['json', 'yaml']:
        # JSON/YAML format: ISO 8601 or float seconds
        try:
            total_seconds = float(timestamp)
        except ValueError:
            # Try ISO 8601 parsing
            from datetime import datetime
            dt = datetime.fromisoformat(timestamp)
            total_seconds = dt.timestamp()
    else:
        raise ValueError(f"Unsupported source format: {from_format}")
    
    # Convert to target format
    if to_format.lower() == 'srt':
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        millis = int((total_seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"
        
    elif to_format.lower() == 'vtt':
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        millis = int((total_seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{millis:03d}"
        
    elif to_format.lower() == 'txt':
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        
        return f"[{hours:02d}:{minutes:02d}:{seconds:02d}]"
        
    elif to_format.lower() in ['json', 'yaml']:
        return str(total_seconds)
        
    else:
        raise ValueError(f"Unsupported target format: {to_format}")


def validate_timestamp(timestamp: str, format_name: str) -> bool:
    """
    Validate a timestamp for a specific format.
    
    Args:
        timestamp: Timestamp string to validate
        format_name: Format name or enum value
        
    Returns:
        True if timestamp is valid, False otherwise
    """
    import re
    
    if format_name.lower() == 'srt':
        # SRT format: HH:MM:SS,mmm
        pattern = r'^\d{2}:\d{2}:\d{2},\d{3}$'
        return bool(re.match(pattern, timestamp))
        
    elif format_name.lower() == 'vtt':
        # VTT format: HH:MM:SS.mmm
        pattern = r'^\d{2}:\d{2}:\d{2}\.\d{3}$'
        return bool(re.match(pattern, timestamp))
        
    elif format_name.lower() == 'txt':
        # TXT format: [HH:MM:SS - HH:MM:SS]
        pattern = r'^\[\d{2}:\d{2}:\d{2} - \d{2}:\d{2}:\d{2}\]$'
        return bool(re.match(pattern, timestamp))
        
    elif format_name.lower() in ['json', 'yaml']:
        # JSON/YAML format: ISO 8601 or float seconds
        try:
            float(timestamp)
            return True
        except ValueError:
            try:
                from datetime import datetime
                datetime.fromisoformat(timestamp)
                return True
            except ValueError:
                return False
    else:
        return False


def get_format_capabilities(format_name: str) -> Dict[str, bool]:
    """
    Get capabilities for a format.
    
    Args:
        format_name: Format name or enum value
        
    Returns:
        Dictionary of capabilities
    """
    capabilities = {
        'timestamps': True,
        'sections': True,
        'metadata': False,
        'html_support': False,
        'validation': True,
        'encoding': 'UTF-8'
    }
    
    if format_name.lower() == 'vtt':
        capabilities['html_support'] = True
        capabilities['metadata'] = True
        
    elif format_name.lower() in ['json', 'yaml']:
        capabilities['metadata'] = True
        capabilities['validation'] = True
        
    return capabilities


def create_format_template(format_name: str) -> str:
    """
    Create a template for a specific format.
    
    Args:
        format_name: Format name or enum value
        
    Returns:
        Template string
    """
    if format_name.lower() == 'srt':
        return """1
00:00:00,000 --> 00:00:05,000
Section Title

Content goes here

2
00:00:05,000 --> 00:00:10,000
Next Section

More content here
"""
    elif format_name.lower() == 'vtt':
        return """WEBVTT

00:00:00.000
00:00:05.000
Section Title

Content goes here

00:00:05.000
00:00:10.000
Next Section

More content here
"""
    elif format_name.lower() == 'txt':
        return """[00:00:00 - 00:00:05] Section Title
[00:00:05 - 00:00:10] Next Section

Content goes here

More content here
"""
    elif format_name.lower() == 'json':
        return """{
  "title": "Transcript Title",
  "created_at": "2024-01-01T00:00:00",
  "sections": [
    {
      "title": "Section Title",
      "start_time": 0.0,
      "end_time": 5.0,
      "content": "Content goes here"
    }
  ]
}
"""
    elif format_name.lower() == 'yaml':
        return """title: Transcript Title
created_at: '2024-01-01T00:00:00'
sections:
  - title: Section Title
    start_time: 0.0
    end_time: 5.0
    content: Content goes here
"""
    else:
        raise ValueError(f"Unsupported format: {format_name}")
