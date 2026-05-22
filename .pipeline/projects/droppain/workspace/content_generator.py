"""Content generator for droppain.

Produces marketing copy (social media posts, email drafts, ad copy)
based on campaign briefs.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from droppain.planner import ContentBrief


@dataclass
class GeneratedContent:
    """Output from the content generator."""

    platform: str
    subject: Optional[str] = None
    body: str = ""
    hashtags: List[str] = field(default_factory=list)
    ad_headline: Optional[str] = None
    ad_description: Optional[str] = None

    def __str__(self) -> str:
        parts = []
        parts.append(f"Platform: {self.platform}")
        if self.subject:
            parts.append(f"Subject: {self.subject}")
        if self.ad_headline:
            parts.append(f"Headline: {self.ad_headline}")
        parts.append(f"Body:\n{self.body}")
        if self.hashtags:
            parts.append(f"\nHashtags: {' '.join(self.hashtags)}")
        return "\n".join(parts)


class ContentGenerator:
    """Generates marketing content from content briefs.

    Uses template-based generation with deterministic output.
    Can be extended with LLM integration later.
    """

    def __init__(self, default_hashtags: Optional[List[str]] = None):
        self.default_hashtags = default_hashtags or [
            "#dropshipping", "#ecommerce", "#onlineshopping", "#shopnow", "#deals"
        ]

    def generate(self, brief: ContentBrief) -> GeneratedContent:
        """Generate content from a content brief.

        Args:
            brief: ContentBrief with title, copy, target audience, and platform.

        Returns:
            GeneratedContent with formatted output for the platform.
        """
        platform = brief.platform.lower()

        if platform == "facebook":
            return self._generate_facebook(brief)
        elif platform == "instagram":
            return self._generate_instagram(brief)
        elif platform == "email":
            return self._generate_email(brief)
        elif platform == "google":
            return self._generate_google(brief)
        elif platform == "tiktok":
            return self._generate_tiktok(brief)
        else:
            return self._generate_generic(brief)

    def _generate_facebook(self, brief: ContentBrief) -> GeneratedContent:
        """Generate Facebook post content."""
        body = self._clean_copy(brief.copy)
        hashtags = brief.hashtags or self.default_hashtags[:3]

        return GeneratedContent(
            platform="facebook",
            body=body,
            hashtags=hashtags,
        )

    def _generate_instagram(self, brief: ContentBrief) -> GeneratedContent:
        """Generate Instagram post content."""
        body = self._clean_copy(brief.copy)
        hashtags = brief.hashtags or self.default_hashtags[:5]

        return GeneratedContent(
            platform="instagram",
            body=body,
            hashtags=hashtags,
        )

    def _generate_email(self, brief: ContentBrief) -> GeneratedContent:
        """Generate email content."""
        # Extract subject line if present
        subject = None
        body = brief.copy
        if "Subject:" in body:
            match = re.search(r"Subject:\s*(.+)", body)
            if match:
                subject = match.group(1).strip()
                body = re.sub(r"Subject:\s*.+", "", body).strip()

        return GeneratedContent(
            platform="email",
            subject=subject or "Special Offer Inside!",
            body=body,
        )

    def _generate_google(self, brief: ContentBrief) -> GeneratedContent:
        """Generate Google Ads content."""
        # Split headline and description
        parts = brief.copy.split(" | ")
        headline = parts[0].strip() if parts else brief.title
        description = " | ".join(parts[1:]).strip() if len(parts) > 1 else brief.copy

        return GeneratedContent(
            platform="google",
            ad_headline=headline,
            ad_description=description,
            body=brief.title,
        )

    def _generate_tiktok(self, brief: ContentBrief) -> GeneratedContent:
        """Generate TikTok video content."""
        body = self._clean_copy(brief.copy)
        # TikTok content needs a call to action
        if "NEED" not in body:
            body = f"NEED this! {body}"
        hashtags = brief.hashtags or self.default_hashtags[:4]

        return GeneratedContent(
            platform="tiktok",
            body=body,
            hashtags=hashtags,
        )

    def _generate_generic(self, brief: ContentBrief) -> GeneratedContent:
        """Generate generic content for unknown platforms."""
        return GeneratedContent(
            platform=brief.platform,
            body=brief.copy,
            hashtags=self.default_hashtags,
        )

    def _clean_copy(self, copy: str) -> str:
        """Clean and normalize copy text."""
        # Remove excessive whitespace
        copy = re.sub(r"\s+", " ", copy).strip()
        # Remove HTML tags if present
        copy = re.sub(r"<[^>]+>", "", copy)
        return copy

    def generate_batch(self, briefs: List[ContentBrief]) -> List[GeneratedContent]:
        """Generate content for multiple briefs.

        Args:
            briefs: List of ContentBrief objects.

        Returns:
            List of GeneratedContent objects.
        """
        return [self.generate(brief) for brief in briefs]
