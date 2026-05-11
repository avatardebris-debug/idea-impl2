"""Tests for YouTube Studio package."""

import pytest
from youtube_studio import (
    YouTubeStudio,
    VideoMetadata,
    TitleGenerator,
    TitleGenerationResult,
    ThumbnailGenerator,
    ThumbnailMetadata,
    ThumbnailStyle,
    KeywordGenerator,
    KeywordResult,
    KeywordPriority,
    TranscriptBuilder,
    TranscriptMetadata,
    TranscriptSection,
    DescriptionBuilder,
    DescriptionResult,
    DescriptionSection,
    get_config,
)


class TestYouTubeStudio:
    """Tests for YouTubeStudio class."""
    
    def test_init(self):
        """Test initialization."""
        studio = YouTubeStudio()
        assert studio is not None
    
    def test_generate_metadata(self):
        """Test generating complete metadata."""
        studio = YouTubeStudio()
        content = "This is a tutorial about Python programming for beginners"
        metadata = studio.generate_metadata(
            content=content,
            topic="Python Programming",
            duration=600,
        )
        
        assert isinstance(metadata, VideoMetadata)
        assert metadata.title
        assert len(metadata.titles) > 0
        assert metadata.description
        assert len(metadata.keywords) > 0
        assert len(metadata.thumbnail_suggestions) > 0
        assert metadata.transcript
    
    def test_generate_titles(self):
        """Test generating titles."""
        studio = YouTubeStudio()
        content = "This is a tutorial about Python programming for beginners"
        titles = studio.generate_titles(content, num_titles=3)
        
        assert len(titles) == 3
        for title in titles:
            assert isinstance(title, TitleGenerationResult)
            assert title.title
            assert 0.0 <= title.confidence <= 1.0
    
    def test_generate_description(self):
        """Test generating description."""
        studio = YouTubeStudio()
        description = studio.generate_description(
            topic="Python Programming",
            chapters=["Introduction", "Basics", "Advanced"],
            links=["https://example.com"],
            hashtags=["#python", "#tutorial"],
        )
        
        assert isinstance(description, DescriptionResult)
        assert description.full_description
        assert len(description.sections) > 0
    
    def test_generate_keywords(self):
        """Test generating keywords."""
        studio = YouTubeStudio()
        content = "This is a tutorial about Python programming for beginners"
        keywords = studio.generate_keywords(content, num_keywords=5)
        
        assert len(keywords) == 5
        for keyword in keywords:
            assert isinstance(keyword, KeywordResult)
            assert keyword.keyword
            assert keyword.priority in [KeywordPriority.HIGH, KeywordPriority.MEDIUM, KeywordPriority.LOW]
    
    def test_generate_thumbnail_suggestions(self):
        """Test generating thumbnail suggestions."""
        studio = YouTubeStudio()
        content = "This is a tutorial about Python programming for beginners"
        suggestions = studio.generate_thumbnail_suggestions(
            content=content,
            topic="Python Programming",
            num_suggestions=3,
        )
        
        assert len(suggestions) == 3
        for suggestion in suggestions:
            assert isinstance(suggestion, ThumbnailMetadata)
            assert suggestion.style in ThumbnailStyle
            assert 0.0 <= suggestion.confidence <= 1.0
    
    def test_generate_transcript(self):
        """Test generating transcript."""
        studio = YouTubeStudio()
        content = "This is a tutorial about Python programming for beginners"
        transcript = studio.generate_transcript(
            content=content,
            duration=600,
        )
        
        assert isinstance(transcript, TranscriptMetadata)
        assert transcript.word_count > 0
        assert transcript.reading_time > 0
        assert len(transcript.sections) > 0


class TestTitleGenerator:
    """Tests for TitleGenerator class."""
    
    def test_init(self):
        """Test initialization."""
        generator = TitleGenerator()
        assert generator is not None
    
    def test_generate_titles(self):
        """Test generating titles."""
        generator = TitleGenerator()
        content = "This is a tutorial about Python programming for beginners"
        titles = generator.generate_titles(content, num_titles=5)
        
        assert len(titles) == 5
        for title in titles:
            assert title.title
            assert 0.0 <= title.confidence <= 1.0
            assert title.style in TitleStyle


class TestThumbnailGenerator:
    """Tests for ThumbnailGenerator class."""
    
    def test_init(self):
        """Test initialization."""
        generator = ThumbnailGenerator()
        assert generator is not None
    
    def test_generate_suggestions(self):
        """Test generating suggestions."""
        generator = ThumbnailGenerator()
        suggestions = generator.generate_suggestions(
            content="Python tutorial",
            topic="Python",
            num_suggestions=3,
        )
        
        assert len(suggestions) == 3
        for suggestion in suggestions:
            assert suggestion.style in ThumbnailStyle
            assert 0.0 <= suggestion.confidence <= 1.0


class TestKeywordGenerator:
    """Tests for KeywordGenerator class."""
    
    def test_init(self):
        """Test initialization."""
        generator = KeywordGenerator()
        assert generator is not None
    
    def test_generate_keywords(self):
        """Test generating keywords."""
        generator = KeywordGenerator()
        content = "This is a tutorial about Python programming for beginners"
        keywords = generator.generate_keywords(content, num_keywords=5)
        
        assert len(keywords) == 5
        for keyword in keywords:
            assert keyword.keyword
            assert keyword.priority in [KeywordPriority.HIGH, KeywordPriority.MEDIUM, KeywordPriority.LOW]


class TestTranscriptBuilder:
    """Tests for TranscriptBuilder class."""
    
    def test_init(self):
        """Test initialization."""
        builder = TranscriptBuilder()
        assert builder is not None
    
    def test_build_transcript(self):
        """Test building transcript."""
        builder = TranscriptBuilder()
        content = "This is a tutorial about Python programming for beginners"
        transcript = builder.build_transcript(
            content=content,
            duration=600,
        )
        
        assert isinstance(transcript, TranscriptMetadata)
        assert transcript.word_count > 0
        assert transcript.reading_time > 0
        assert len(transcript.sections) > 0


class TestDescriptionBuilder:
    """Tests for DescriptionBuilder class."""
    
    def test_init(self):
        """Test initialization."""
        builder = DescriptionBuilder()
        assert builder is not None
    
    def test_build_description(self):
        """Test building description."""
        builder = DescriptionBuilder()
        description = builder.build_description(
            topic="Python Programming",
            chapters=["Introduction", "Basics"],
            links=["https://example.com"],
            hashtags=["#python", "#tutorial"],
        )
        
        assert isinstance(description, DescriptionResult)
        assert description.full_description
        assert len(description.sections) > 0


class TestConfig:
    """Tests for config module."""
    
    def test_get_config(self):
        """Test getting config."""
        config = get_config()
        assert isinstance(config, dict)
        assert 'max_title_length' in config
        assert 'thumbnail_width' in config


class TestConstants:
    """Tests for constants module."""
    
    def test_constants(self):
        """Test constants are defined."""
        from youtube_studio.constants import (
            DEFAULT_VIDEO_DURATION,
            DEFAULT_LANGUAGE,
            DEFAULT_CATEGORY,
            DEFAULT_THUMBNAIL_WIDTH,
            DEFAULT_THUMBNAIL_HEIGHT,
            DEFAULT_THUMBNAIL_FORMAT,
            MIN_NUMBER_OF_KEYWORDS,
            MAX_NUMBER_OF_KEYWORDS,
            DEFAULT_NUMBER_OF_TITLES,
            DEFAULT_NUMBER_OF_KEYWORDS,
            DEFAULT_NUMBER_OF_THUMBNAILS,
        )
        
        assert DEFAULT_VIDEO_DURATION > 0
        assert DEFAULT_LANGUAGE
        assert DEFAULT_CATEGORY
        assert DEFAULT_THUMBNAIL_WIDTH > 0
        assert DEFAULT_THUMBNAIL_HEIGHT > 0
        assert DEFAULT_THUMBNAIL_FORMAT
        assert MIN_NUMBER_OF_KEYWORDS > 0
        assert MAX_NUMBER_OF_KEYWORDS > MIN_NUMBER_OF_KEYWORDS
        assert DEFAULT_NUMBER_OF_TITLES > 0
        assert DEFAULT_NUMBER_OF_KEYWORDS > 0
        assert DEFAULT_NUMBER_OF_THUMBNAILS > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
