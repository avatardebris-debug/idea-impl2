"""Core metadata generation logic for YouTube videos.

Takes a video topic/niche and produces multiple title options,
a full description, keyword tags, and hashtags.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from .config import Config
from .templates import TemplateEngine


# ── Metadata output ────────────────────────────────────────────────────

@dataclass
class Metadata:
    """Generated metadata for a YouTube video."""

    titles: List[str] = field(default_factory=list)
    description: str = ""
    tags: List[str] = field(default_factory=list)
    hashtags: List[str] = field(default_factory=list)
    category: str = ""
    topic: str = ""
    niche: str = ""
    tone: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "titles": self.titles,
            "description": self.description,
            "tags": self.tags,
            "hashtags": self.hashtags,
            "category": self.category,
            "topic": self.topic,
            "niche": self.niche,
            "tone": self.tone,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Metadata":
        return cls(
            titles=data.get("titles", []),
            description=data.get("description", ""),
            tags=data.get("tags", []),
            hashtags=data.get("hashtags", []),
            category=data.get("category", ""),
            topic=data.get("topic", ""),
            niche=data.get("niche", ""),
            tone=data.get("tone", ""),
        )


# ── Keyword helpers ────────────────────────────────────────────────────

def _extract_keywords(text: str) -> List[str]:
    """Extract meaningful keywords from text (lowercase, stripped)."""
    words = re.findall(r"[a-zA-Z\u00C0-\u024F]+", text.lower())
    stop_words = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
        "for", "of", "with", "by", "from", "is", "are", "was", "were",
        "be", "been", "being", "have", "has", "had", "do", "does", "did",
        "will", "would", "could", "should", "may", "might", "can", "shall",
        "it", "its", "this", "that", "these", "those", "i", "you", "he",
        "she", "we", "they", "me", "him", "her", "us", "them", "my", "your",
        "his", "our", "their", "not", "no", "so", "if", "as", "about",
        "up", "out", "just", "than", "then", "also", "very", "too", "get",
        "got", "like", "into", "over", "after", "before", "between", "under",
        "again", "further", "there", "when", "where", "why", "how", "all",
        "each", "few", "more", "most", "other", "some", "such", "only",
        "own", "same", "s", "t", "don", "now", "what", "who", "which",
        "who", "whom", "am", "down", "off", "here", "there", "once",
    }
    keywords = [w for w in words if len(w) > 2 and w not in stop_words]
    return keywords


def _expand_keywords(keywords: List[str], topic: str) -> List[str]:
    """Expand keywords with topic-related terms."""
    topic_words = _extract_keywords(topic)
    expanded = list(keywords)
    for w in topic_words:
        if w not in expanded:
            expanded.append(w)
    # Add common YouTube search terms
    extras = ["tutorial", "guide", "tips", "how to", "explained", "review",
              "best", "top", "beginner", "advanced", "2024", "2025", "2026"]
    for e in extras:
        if e not in expanded:
            expanded.append(e)
    return expanded


# ── Description builder ────────────────────────────────────────────────

def _build_description(
    topic: str,
    niche: str,
    tone: str,
    titles: List[str],
) -> str:
    """Build a structured description with intro, content, CTA, and links sections."""
    topic_cap = topic.capitalize() if topic else "This Topic"

    intro_templates = {
        "informative": f"Welcome to this comprehensive guide on {topic_cap}. In this video, we'll cover everything you need to know about {topic_cap}.",
        "entertaining": f"What's up everyone! Today we're diving deep into {topic_cap} — and trust me, you don't want to miss this!",
        "professional": f"In this video, we present an in-depth analysis of {topic_cap}, tailored for professionals and enthusiasts alike.",
        "casual": f"Hey guys! So today I wanted to talk about {topic_cap} — it's something I've been really into lately!",
        "educational": f"Today's lesson: {topic_cap}. Whether you're a beginner or looking to sharpen your skills, this video has something for you.",
    }
    intro = intro_templates.get(tone, intro_templates["informative"])

    content_sections = [
        f"\n\n📋 What You'll Learn:\n",
        f"• Understanding the fundamentals of {topic_cap}\n",
        f"• Practical strategies and techniques for {topic_cap}\n",
        f"• Common mistakes to avoid when working with {topic_cap}\n",
        f"• Advanced tips for experienced practitioners\n",
        f"• Real-world examples and case studies\n",
    ]

    cta_section = f"\n\n🔔 Don't forget to LIKE, SUBSCRIBE, and hit the bell icon for more content about {topic_cap}!\n\n💬 Let me know in the comments: What's your biggest challenge with {topic_cap}?"

    links_section = f"\n\n📚 Resources & Links:\n• Website: https://example.com\n• Follow us on social media\n• Join our community\n\n#YouTube #{topic_cap.replace(' ', '')}"

    return intro + "".join(content_sections) + cta_section + links_section


# ── Main generator ─────────────────────────────────────────────────────

def generate_metadata(
    topic: str,
    niche: str = "general",
    tone: str = "informative",
    config: Optional[Config] = None,
) -> Metadata:
    """Generate complete metadata for a YouTube video.

    Args:
        topic: The video topic/title subject.
        niche: The content niche/category.
        tone: The tone/style of the content.
        config: Optional configuration override.

    Returns:
        Metadata object with titles, description, tags, and hashtags.
    """
    if config is None:
        config = Config()

    max_tags = config.max_tags
    max_hashtags = config.max_hashtags

    # Generate titles using template engine
    engine = TemplateEngine()
    categories = engine.get_categories()

    # Pick relevant categories based on niche
    relevant_categories = _select_categories(niche, categories)

    all_titles: List[str] = []
    for cat in relevant_categories:
        titles = engine.generate_titles(
            topic=topic,
            categories=[cat],
        )
        all_titles.extend(titles)

    # Ensure at least 5 title variants
    if len(all_titles) < 5:
        # Add fallback titles
        fallbacks = [
            f"Complete Guide to {topic}",
            f"{topic}: Everything You Need to Know",
            f"The Truth About {topic}",
            f"{topic} Explained Simply",
            f"Why {topic} Matters More Than Ever",
        ]
        for fb in fallbacks:
            if fb not in all_titles:
                all_titles.append(fb)
            if len(all_titles) >= 5:
                break

    # Deduplicate titles while preserving order
    seen_titles: Set[str] = set()
    unique_titles: List[str] = []
    for t in all_titles:
        if t not in seen_titles:
            seen_titles.add(t)
            unique_titles.append(t)
    all_titles = unique_titles[:max(5, len(all_titles))]

    # Generate description
    description = _build_description(topic, niche, tone, all_titles)

    # Generate tags
    keywords = _extract_keywords(topic)
    all_keywords = _expand_keywords(keywords, topic)
    # Add niche-specific tags
    niche_tags = _niche_to_tags(niche)
    all_keywords.extend(niche_tags)
    # Deduplicate and limit
    seen_tags: Set[str] = set()
    unique_tags: List[str] = []
    for tag in all_keywords:
        tag_lower = tag.lower().strip()
        if tag_lower and tag_lower not in seen_tags:
            seen_tags.add(tag_lower)
            unique_tags.append(tag_lower)
    tags = unique_tags[:max_tags]

    # Generate hashtags
    hashtag_base = [tag.replace(" ", "") for tag in unique_tags[:max_hashtags]]
    # Ensure hashtags start with #
    hashtags = [f"#{h}" if not h.startswith("#") else h for h in hashtag_base]
    hashtags = hashtags[:max_hashtags]

    return Metadata(
        titles=all_titles,
        description=description,
        tags=tags,
        hashtags=hashtags,
        category=niche,
        topic=topic,
        niche=niche,
        tone=tone,
    )


def _select_categories(niche: str, all_categories: List[str]) -> List[str]:
    """Select relevant template categories based on niche."""
    niche_map = {
        "tech": ["tutorial", "review", "comparison", "howto"],
        "gaming": ["tutorial", "review", "vlog", "listicle"],
        "education": ["tutorial", "howto", "listicle", "storytelling"],
        "fitness": ["tutorial", "vlog", "listicle", "howto"],
        "cooking": ["tutorial", "review", "vlog", "howto"],
        "business": ["tutorial", "listicle", "storytelling", "announcement"],
        "music": ["tutorial", "review", "vlog", "announcement"],
        "travel": ["vlog", "listicle", "storytelling", "review"],
        "beauty": ["tutorial", "review", "vlog", "listicle"],
        "general": ["tutorial", "review", "vlog", "listicle", "howto", "comparison"],
    }
    selected = niche_map.get(niche.lower(), ["tutorial", "review", "vlog", "listicle"])
    # Return only categories that exist
    return [c for c in selected if c in all_categories]


def _niche_to_tags(niche: str) -> List[str]:
    """Convert niche to relevant tag suggestions."""
    niche_tags = {
        "tech": ["technology", "gadgets", "software", "programming", "coding", "AI", "tech review"],
        "gaming": ["gaming", "gameplay", "review", "walkthrough", "esports", "indie games"],
        "education": ["education", "learning", "tutorial", "course", "study tips", "academic"],
        "fitness": ["fitness", "workout", "health", "exercise", "gym", "nutrition"],
        "cooking": ["cooking", "recipe", "food", "kitchen", "baking", "meal prep"],
        "business": ["business", "entrepreneurship", "startup", "marketing", "finance"],
        "music": ["music", "song", "album", "concert", "musician", "production"],
        "travel": ["travel", "adventure", "destination", "culture", "tourism", "exploration"],
        "beauty": ["beauty", "makeup", "skincare", "fashion", "style", "cosmetics"],
        "general": ["youtube", "video", "content", "creator", "viral"],
    }
    return niche_tags.get(niche.lower(), ["youtube", "video", "content"])


# ── MetadataGenerator class ─────────────────────────────────────────

class MetadataGenerator:
    """Class-based wrapper around generate_metadata for CLI use."""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()

    def generate(
        self,
        topic: str,
        num_titles: int = 10,
        num_tags: int = 15,
        num_hashtags: int = 10,
        niche: str = "general",
        tone: str = "informative",
        styles: Optional[List[str]] = None,
    ) -> Metadata:
        """Generate metadata for a video topic.

        Args:
            topic: The video topic.
            num_titles: Number of title variants.
            num_tags: Number of tags.
            num_hashtags: Number of hashtags.
            niche: Content niche.
            tone: Content tone.
            styles: Optional list of title styles.

        Returns:
            Metadata object with generated content.
        """
        # Override config values if specified
        if num_tags > 0:
            self.config.max_tags = num_tags
        if num_hashtags > 0:
            self.config.max_hashtags = num_hashtags

        metadata = generate_metadata(
            topic=topic,
            niche=niche,
            tone=tone,
            config=self.config,
        )

        # Limit titles if needed
        if num_titles > 0 and len(metadata.titles) > num_titles:
            metadata.titles = metadata.titles[:num_titles]

        return metadata
