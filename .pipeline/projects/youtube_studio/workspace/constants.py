"""
YouTube Studio - Constants Module

This module defines all constants used throughout the YouTube Studio application.
These include limits for titles, thumbnails, keywords, and configuration for video formats.
"""

# ==================== TITLE CONSTANTS ====================

MAX_TITLE_LENGTH = 100
"""Maximum number of characters allowed in a YouTube video title"""

MIN_TITLE_LENGTH = 10
"""Minimum recommended number of characters for a video title"""

MAX_KEYWORDS_PER_TAG = 3
"""Maximum number of words per keyword tag"""

MAX_NUMBER_OF_KEYWORDS = 500
"""Maximum total character count for all keywords combined (YouTube limit)"""

MIN_NUMBER_OF_KEYWORDS = 10
"""Minimum recommended number of keyword tags"""

# ==================== THUMBNAIL CONSTANTS ====================

MAX_THUMBNAIL_SIZE_BYTES = 2 * 1024 * 1024  # 2MB
"""Maximum file size for uploaded thumbnails in bytes"""

MIN_THUMBNAIL_WIDTH = 1280
"""Minimum recommended width for YouTube thumbnails in pixels"""

MIN_THUMBNAIL_HEIGHT = 720
"""Minimum recommended height for YouTube thumbnails in pixels"""

MAX_THUMBNAIL_WIDTH = 1280
"""Maximum recommended width for YouTube thumbnails in pixels"""

MAX_THUMBNAIL_HEIGHT = 720
"""Maximum recommended height for YouTube thumbnails in pixels"""

RECOMMENDED_ASPECT_RATIO = (16, 9)
"""Recommended aspect ratio for YouTube thumbnails (width:height)"""

# ==================== VIDEO FORMAT CONSTANTS ====================

SUPPORTED_VIDEO_FORMATS = ['mp4', 'avi', 'mov', 'mkv', 'webm', 'flv', 'wmv']
"""List of supported video formats"""

PREFERRED_VIDEO_FORMAT = 'mp4'
"""Preferred video format for YouTube uploads"""

DEFAULT_VIDEO_CODEC = 'h264'
"""Default video codec for encoding"""

DEFAULT_AUDIO_CODEC = 'aac'
"""Default audio codec for encoding"""

MIN_VIDEO_DURATION = 0  # No minimum
"""Minimum video duration in seconds (0 = no minimum)"""

MAX_VIDEO_DURATION = 12 * 60 * 60  # 12 hours
"""Maximum video duration in seconds (YouTube limit)"""

# ==================== TEMPLATE CONSTANTS ====================

DEFAULT_TEMPLATE_PATH = 'templates/default_template.json'
"""Default path to the template file"""

TEMPLATE_VERSION = '1.0.0'
"""Current version of the template system"""

TEMPLATE_EXTENSION = '.json'
"""File extension for template files"""

TEMPLATE_REQUIRED_FIELDS = ['title', 'description', 'tags']
"""Required fields that every template must have"""

TEMPLATE_VARIABLE_PREFIX = '{{'
"""Prefix for template variables (e.g., {{title}})"""

TEMPLATE_VARIABLE_SUFFIX = '}}'
"""Suffix for template variables"""

# ==================== SEO CONSTANTS ====================

MIN_KEYWORD_RELEVANCE_SCORE = 0.5
"""Minimum relevance score for keywords (0.0 to 1.0)"""

DEFAULT_KEYWORD_PRIORITY = 'medium'
"""Default priority level for keywords: low, medium, high"""

SEO_KEYWORD_WEIGHT = 0.7
"""Weight given to SEO keywords in title generation"""

ENGAGEMENT_KEYWORD_WEIGHT = 0.3
"""Weight given to engagement-focused keywords in title generation"""

# ==================== EXPORT CONSTANTS ====================

EXPORT_DIR = 'exports'
"""Default directory for exported files"""

EXPORT_FILENAME_TEMPLATE = '{video_id}_{timestamp}'
"""Template for export filenames"""

EXPORT_DATE_FORMAT = '%Y%m%d_%H%M%S'
"""Date format for export filenames"""

EXPORT_JSON_PRETTY = True
"""Whether to pretty-print JSON exports"""

# ==================== API CONSTANTS ====================

API_TIMEOUT_SECONDS = 30
"""Timeout for API requests in seconds"""

API_RETRY_ATTEMPTS = 3
"""Number of retry attempts for failed API requests"""

API_RETRY_DELAY_SECONDS = 1
"""Delay between retry attempts in seconds"""

# ==================== FILE HANDLING CONSTANTS ====================

MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100MB
"""Maximum file size for processing in bytes"""

SUPPORTED_IMPORT_FORMATS = ['txt', 'srt', 'vtt', 'json', 'yaml', 'yml']
"""Supported file formats for importing content"""

DEFAULT_ENCODING = 'utf-8'
"""Default encoding for file operations"""

# ==================== OUTPUT CONSTANTS ====================

OUTPUT_PRECISION_SECONDS = 2
"""Precision for timestamp formatting in seconds"""

TIMESTAMP_FORMAT = '%H:%M:%S'
"""Format for displaying timestamps"""

TRANSCRIPT_LINE_WIDTH = 80
"""Maximum characters per line in plain text transcripts"""
