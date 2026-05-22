"""
Constants for Transcript Extractor.

Defines supported formats, model sizes, output formats, and other constants.
"""

# Supported video/audio input formats
SUPPORTED_FORMATS = ["mp4", "avi", "mov", "mkv", "mp3", "wav", "flac", "aac", "m4a"]

# Supported output formats for transcripts
OUTPUT_FORMATS = ["txt", "srt", "vtt", "json"]

# Whisper model sizes
MODEL_SIZES = ["tiny", "small", "medium", "large", "large-v2", "large-v3"]

# Default settings
DEFAULT_MODEL = "small"
DEFAULT_LANGUAGE = "en"
DEFAULT_SUMMARY_LENGTH = "medium"  # short, medium, long
DEFAULT_OUTPUT_FORMAT = "txt"

# Audio processing settings
SAMPLE_RATE = 16000  # Sample rate for extracted audio in Hz
AUDIO_BITRATE = "128k"

# Transcript settings
MAX_TRANSCRIPT_LENGTH = 1000000  # Maximum characters in a transcript
MAX_SUMMARY_LENGTH = 500  # Maximum characters in a summary
MIN_WORD_COUNT_FOR_SUMMARY = 50  # Minimum words required to generate summary

# File size limits (in bytes)
MAX_INPUT_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2 GB

# Timestamp precision
TIMESTAMP_PRECISION = "milliseconds"

# Summarization settings
KEY_POINTS_COUNT = 5  # Number of key points to extract

# Error handling
RETRY_COUNT = 3
RETRY_DELAY = 1.0  # seconds

# Progress reporting
PROGRESS_INTERVAL = 10  # Report progress every 10%
