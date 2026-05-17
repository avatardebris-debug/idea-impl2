"""Tests for droppain.content_generator module."""

import pytest

from droppain.content_generator import ContentGenerator, GeneratedContent
from droppain.planner import ContentBrief


class TestGeneratedContent:
    """Tests for GeneratedContent."""

    def test_generated_content_creation(self):
        """Test basic content creation."""
        content = GeneratedContent(
            platform="facebook",
            body="Test body",
            hashtags=["#test"],
        )
        assert content.platform == "facebook"
        assert content.body == "Test body"
        assert content.hashtags == ["#test"]

    def test_generated_content_str(self):
        """Test string representation."""
        content = GeneratedContent(
            platform="facebook",
            body="Test body",
            hashtags=["#test"],
        )
        assert "facebook" in str(content)
        assert "Test body" in str(content)


class TestContentGenerator:
    """Tests for ContentGenerator."""

    def test_default_hashtags(self):
        """Test default hashtags."""
        generator = ContentGenerator()
        assert len(generator.default_hashtags) > 0

    def test_generate_facebook(self):
        """Test Facebook content generation."""
        generator = ContentGenerator()
        brief = ContentBrief(
            title="Test",
            copy="Check out Test! Great product.",
            target_audience="General audience",
            platform="facebook",
        )
        content = generator.generate(brief)
        assert content.platform == "facebook"
        assert "Test" in content.body
        assert len(content.hashtags) > 0

    def test_generate_instagram(self):
        """Test Instagram content generation."""
        generator = ContentGenerator()
        brief = ContentBrief(
            title="Test",
            copy="Check out Test! Great product.",
            target_audience="General audience",
            platform="instagram",
        )
        content = generator.generate(brief)
        assert content.platform == "instagram"
        assert "Test" in content.body
        assert len(content.hashtags) > 0

    def test_generate_email(self):
        """Test email content generation."""
        generator = ContentGenerator()
        brief = ContentBrief(
            title="Test",
            copy="Check out Test! Great product.",
            target_audience="General audience",
            platform="email",
        )
        content = generator.generate(brief)
        assert content.platform == "email"
        assert content.subject is not None
        assert "Test" in content.body

    def test_generate_email_no_subject(self):
        """Test email content without subject."""
        generator = ContentGenerator()
        brief = ContentBrief(
            title="Test",
            copy="Check out Test! Great product.",
            target_audience="General audience",
            platform="email",
        )
        content = generator.generate(brief)
        assert content.subject is not None
        assert len(content.subject) > 0

    def test_generate_google(self):
        """Test Google Ads content generation."""
        generator = ContentGenerator()
        brief = ContentBrief(
            title="Test",
            copy="Check out Test! Great product.",
            target_audience="General audience",
            platform="google",
        )
        content = generator.generate(brief)
        assert content.platform == "google"
        assert "Test" in content.body
        assert len(content.hashtags) == 0

    def test_generate_tiktok(self):
        """Test TikTok content generation."""
        generator = ContentGenerator()
        brief = ContentBrief(
            title="Test",
            copy="Check out Test! Great product.",
            target_audience="General audience",
            platform="tiktok",
        )
        content = generator.generate(brief)
        assert content.platform == "tiktok"
        assert "NEED" in content.body
        assert len(content.hashtags) > 0

    def test_generate_unknown_platform(self):
        """Test content generation for unknown platform."""
        generator = ContentGenerator()
        brief = ContentBrief(
            title="Test",
            copy="Test body",
            target_audience="General audience",
            platform="twitter",
        )
        content = generator.generate(brief)
        assert content.platform == "twitter"
        assert content.body == "Test body"

    def test_generate_batch(self):
        """Test batch content generation."""
        generator = ContentGenerator()
        briefs = [
            ContentBrief(title="Test 1", copy="Body 1", target_audience="General", platform="facebook"),
            ContentBrief(title="Test 2", copy="Body 2", target_audience="General", platform="instagram"),
        ]
        contents = generator.generate_batch(briefs)
        assert len(contents) == 2
        assert contents[0].platform == "facebook"
        assert contents[1].platform == "instagram"

    def test_clean_copy(self):
        """Test copy cleaning."""
        generator = ContentGenerator()
        result = generator._clean_copy("  Test   body  ")
        assert result == "Test body"

    def test_clean_copy_removes_html(self):
        """Test HTML tag removal."""
        generator = ContentGenerator()
        result = generator._clean_copy("<b>Test</b> body")
        assert result == "Test body"
