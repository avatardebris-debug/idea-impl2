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
        format_name: Format name
        
    Returns:
        List of feature strings
    """
    spec = get_format_spec(format_name)
    return spec['features']


def get_timestamp_formats(format_name: str) -> str:
    """
    Get timestamp format for a format.
    
    Args:
        format_name: Format name
        
    Returns:
        Timestamp format string
    """
    spec = get_format_spec(format_name)
    return spec['timestamp_format']


def get_recommended_encoding(format_name: str) -> str:
    """
    Get recommended encoding for a format.
    
    Args:
        format_name: Format name
        
    Returns:
        Encoding string
    """
    spec = get_format_spec(format_name)
    return spec['encoding']


def format_description(format_name: str) -> str:
    """
    Get human-readable description for a format.
    
    Args:
        format_name: Format name
        
    Returns:
        Description string
    """
    spec = get_format_spec(format_name)
    return spec['description']


def get_formats_by_feature(feature: str) -> List[str]:
    """
    Get formats that support a specific feature.
    
    Args:
        feature: Feature name to search for
        
    Returns:
        List of format names that support the feature
    """
    matching_formats = []
    
    for format_name, spec in FORMAT_SPECS.items():
        if feature.lower() in [f.lower() for f in spec['features']]:
            matching_formats.append(format_name)
    
    return matching_formats


def get_formats_by_name_pattern(pattern: str) -> List[str]:
    """
    Get formats matching a name pattern.
    
    Args:
        pattern: Pattern to match against format names
        
    Returns:
        List of format names matching the pattern
    """
    pattern_lower = pattern.lower()
    
    return [
        format_name for format_name in FORMAT_SPECS.keys()
        if pattern_lower in format_name.lower()
    ]


def get_format_comparison() -> Dict[str, Dict]:
    """
    Get comparison of all formats.
    
    Returns:
        Dictionary with format comparison data
    """
    comparison = {}
    
    for format_name, spec in FORMAT_SPECS.items():
        comparison[format_name] = {
            'name': spec['name'],
            'extension': spec['extension'],
            'description': spec['description'],
            'features': spec['features'],
            'timestamp_format': spec['timestamp_format'],
            'encoding': spec['encoding']
        }
    
    return comparison


def validate_format_spec(format_name: str) -> Tuple[bool, List[str]]:
    """
    Validate a format specification.
    
    Args:
        format_name: Format name to validate
        
    Returns:
        Tuple of (is_valid, list of issues)
    """
    issues = []
    
    try:
        spec = get_format_spec(format_name)
        
        # Check required fields
        required_fields = ['name', 'extension', 'description', 'timestamp_format', 'encoding', 'features']
        for field in required_fields:
            if field not in spec:
                issues.append(f"Missing required field: {field}")
        
        # Check extension format
        if not spec['extension'].isalpha():
            issues.append(f"Invalid extension format: {spec['extension']}")
        
        # Check features is a list
        if not isinstance(spec['features'], list):
            issues.append("Features must be a list")
        
        # Check encoding is valid
        valid_encodings = ['UTF-8', 'UTF-16', 'ASCII', 'ISO-8859-1']
        if spec['encoding'] not in valid_encodings:
            issues.append(f"Invalid encoding: {spec['encoding']}")
            
    except ValueError as e:
        issues.append(str(e))
    
    return (len(issues) == 0, issues)


def get_format_usage_examples(format_name: str) -> Dict[str, str]:
    """
    Get usage examples for a format.
    
    Args:
        format_name: Format name
        
    Returns:
        Dictionary with usage examples
    """
    examples = {
        'srt': """1
00:00:01,000 --> 00:00:04,000
Hello, welcome to this video!

2
00:00:05,000 --> 00:00:08,000
Today we'll learn about subtitles.""",
        
        'vtt': """WEBVTT

00:00:01.000 --> 00:00:04.000
Hello, welcome to this video!

00:00:05.000 --> 00:00:08.000
Today we'll learn about subtitles.""",
        
        'txt': """Video Transcript
================

[00:00:01 - 00:00:04]
Introduction
------------
Hello, welcome to this video!

[00:00:05 - 00:00:08]
Main Content
------------
Today we'll learn about subtitles.""",
        
        'json': """{
  "title": "Video Transcript",
  "sections": [
    {
      "start_time": 1.0,
      "end_time": 4.0,
      "content": "Hello, welcome to this video!"
    },
    {
      "start_time": 5.0,
      "end_time": 8.0,
      "content": "Today we'll learn about subtitles."
    }
  ]
}""",
        
        'yaml': """title: Video Transcript
sections:
  - start_time: 1.0
    end_time: 4.0
    content: "Hello, welcome to this video!"
  - start_time: 5.0
    end_time: 8.0
    content: "Today we'll learn about subtitles."
"""
    }
    
    return examples.get(format_name, "No examples available for this format.")


def get_format_recommendations(use_case: str) -> List[str]:
    """
    Get format recommendations for a specific use case.
    
    Args:
        use_case: Use case description
        
    Returns:
        List of recommended format names
    """
    use_case_lower = use_case.lower()
    
    recommendations = []
    
    # Web-based video
    if 'web' in use_case_lower or 'browser' in use_case_lower or 'html' in use_case_lower:
        recommendations.append('vtt')
    
    # Professional video production
    if 'professional' in use_case_lower or 'broadcast' in use_case_lower or 'tv' in use_case_lower:
        recommendations.append('srt')
    
    # Simple text processing
    if 'simple' in use_case_lower or 'text' in use_case_lower or 'readable' in use_case_lower:
        recommendations.append('txt')
    
    # Programmatic access
    if 'programmatic' in use_case_lower or 'api' in use_case_lower or 'integration' in use_case_lower:
        recommendations.append('json')
    
    # Human-readable configuration
    if 'configuration' in use_case_lower or 'config' in use_case_lower or 'human' in use_case_lower:
        recommendations.append('yaml')
    
    # Default recommendations if none matched
    if not recommendations:
        recommendations = ['srt', 'vtt', 'txt']
    
    return recommendations


def get_format_conversion_matrix() -> Dict[str, Dict[str, bool]]:
    """
    Get conversion matrix between formats.
    
    Returns:
        Dictionary showing which formats can be converted to which
    """
    # All formats can be converted to all other formats
    # This is a placeholder for future implementation
    formats = list(FORMAT_SPECS.keys())
    
    matrix = {}
    for from_format in formats:
        matrix[from_format] = {}
        for to_format in formats:
            matrix[from_format][to_format] = True  # All conversions supported
    
    return matrix


def get_format_metadata(format_name: str) -> Dict:
    """
    Get comprehensive metadata for a format.
    
    Args:
        format_name: Format name
        
    Returns:
        Dictionary with comprehensive format metadata
    """
    spec = get_format_spec(format_name)
    
    return {
        'basic_info': {
            'name': spec['name'],
            'extension': spec['extension'],
            'description': spec['description']
        },
        'technical_specs': {
            'timestamp_format': spec['timestamp_format'],
            'encoding': spec['encoding'],
            'features': spec['features']
        },
        'usage': {
            'examples': get_format_usage_examples(format_name),
            'recommendations': get_format_recommendations(format_name),
            'validation': validate_format_spec(format_name)
        },
        'related_formats': {
            'similar_formats': get_formats_by_feature(spec['features'][0]) if spec['features'] else [],
            'conversion_matrix': get_format_conversion_matrix()
        }
    }
