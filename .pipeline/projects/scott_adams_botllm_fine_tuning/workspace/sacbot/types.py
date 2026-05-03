"""Content type definitions and specifications."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

# Type alias for content types
ContentType = Literal["blog", "tweet", "linkedin"]


@dataclass
class ContentSpec:
    """Specification for a content type."""
    target_length: int       # Target word count
    max_tokens: int          # Max tokens for LLM call
    description: str         # Human-readable description
    output_instruction: str  # Instruction for JSON output format
    platform: str            # Platform name
    max_length_chars: int    # Maximum character length


# Content type specifications
CONTENT_SPECS: dict[ContentType, ContentSpec] = {
    "blog": ContentSpec(
        target_length=300,
        max_tokens=512,
        description="a blog post",
        output_instruction='Return JSON with keys: "title", "content", "tags" (list of 3-5 tags).',
        platform="Blog",
        max_length_chars=3000,
    ),
    "tweet": ContentSpec(
        target_length=20,
        max_tokens=80,
        description="a tweet",
        output_instruction='Return JSON with key: "text" (under 280 chars).',
        platform="Twitter/X",
        max_length_chars=280,
    ),
    "linkedin": ContentSpec(
        target_length=150,
        max_tokens=256,
        description="a LinkedIn post",
        output_instruction='Return JSON with keys: "content", "hashtags" (list of 3-5 hashtags).',
        platform="LinkedIn",
        max_length_chars=3000,
    ),
}
