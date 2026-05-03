"""Tests for sacbot.types module."""

import pytest
from sacbot.types import ContentType, ContentSpec, CONTENT_SPECS


class TestContentType:
    """Tests for ContentType type alias."""

    def test_content_type_values(self):
        """ContentType should accept blog, tweet, linkedin."""
        assert ContentType  # type alias exists
        # Verify the literal values
        valid_types: list[ContentType] = ["blog", "tweet", "linkedin"]
        assert len(valid_types) == 3


class TestContentSpec:
    """Tests for ContentSpec dataclass."""

    def test_blog_spec(self):
        """Blog spec should have correct values."""
        spec = CONTENT_SPECS["blog"]
        assert isinstance(spec, ContentSpec)
        assert spec.target_length == 300
        assert spec.max_tokens == 512
        assert spec.platform == "Blog"
        assert spec.max_length_chars == 3000

    def test_tweet_spec(self):
        """Tweet spec should have correct values."""
        spec = CONTENT_SPECS["tweet"]
        assert isinstance(spec, ContentSpec)
        assert spec.target_length == 20
        assert spec.max_tokens == 80
        assert spec.platform == "Twitter/X"
        assert spec.max_length_chars == 280

    def test_linkedin_spec(self):
        """LinkedIn spec should have correct values."""
        spec = CONTENT_SPECS["linkedin"]
        assert isinstance(spec, ContentSpec)
        assert spec.target_length == 150
        assert spec.max_tokens == 256
        assert spec.platform == "LinkedIn"
        assert spec.max_length_chars == 3000


class TestContentSpecs:
    """Tests for CONTENT_SPECS dictionary."""

    def test_all_types_present(self):
        """All three content types should be in CONTENT_SPECS."""
        assert "blog" in CONTENT_SPECS
        assert "tweet" in CONTENT_SPECS
        assert "linkedin" in CONTENT_SPECS

    def test_no_extra_types(self):
        """Only three content types should be in CONTENT_SPECS."""
        assert len(CONTENT_SPECS) == 3

    def test_all_specs_have_required_fields(self):
        """All specs should have required fields."""
        required_fields = ["target_length", "max_tokens", "description",
                          "output_instruction", "platform", "max_length_chars"]
        for content_type, spec in CONTENT_SPECS.items():
            for field in required_fields:
                assert hasattr(spec, field), f"Missing field {field} in {content_type}"
