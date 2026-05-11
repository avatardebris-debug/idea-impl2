"""Constants for YouTube Studio module."""

# Title generation
MAX_TITLE_LENGTH = 100
MIN_TITLE_LENGTH = 10
DEFAULT_NUMBER_OF_TITLES = 5

# Keyword generation
MIN_NUMBER_OF_KEYWORDS = 5
MAX_NUMBER_OF_KEYWORDS = 500
MAX_KEYWORDS_PER_TAG = 500
DEFAULT_NUMBER_OF_KEYWORDS = 15

# Thumbnail generation
DEFAULT_THUMBNAIL_WIDTH = 1280
DEFAULT_THUMBNAIL_HEIGHT = 720
DEFAULT_THUMBNAIL_FORMAT = 'png'
DEFAULT_NUMBER_OF_THUMBNAILS = 3

# Video settings
DEFAULT_VIDEO_DURATION = 600  # 10 minutes in seconds
DEFAULT_LANGUAGE = 'en'
DEFAULT_CATEGORY = 'Education'

# Template management
TEMPLATE_EXTENSION = '.json'
TEMPLATE_DIR = 'templates'

# Video categories
VIDEO_CATEGORIES = [
    'Film & Animation',
    'Autos & Vehicles',
    'Music',
    'Pets & Animals',
    'Sports',
    'Short Movies',
    'Travel & Events',
    'Gaming',
    'Videoblogging',
    'People & Blogs',
    'Comedy',
    'Entertainment',
    'News & Politics',
    'Howto & Style',
    'Education',
    'Science & Technology',
    'Nonprofits & Activism',
    'Movies',
]

# Target audiences
TARGET_AUDIENCES = [
    'Kids',
    'Teens',
    'Young Adults',
    'Adults',
    'Seniors',
    'General',
]

# Processing time limits
MAX_PROCESSING_TIME_MS = 30000  # 30 seconds
MIN_PROCESSING_TIME_MS = 100  # 100ms

# Error codes
ERROR_CODES = {
    'TEMPLATE_NOT_FOUND': 'Template not found',
    'RENDERING_FAILED': 'Template rendering failed',
    'INVALID_INPUT': 'Invalid input data',
    'EXPORT_FAILED': 'Export operation failed',
    'VALIDATION_FAILED': 'Metadata validation failed',
}
