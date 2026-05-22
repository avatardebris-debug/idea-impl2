"""Data models for SEO analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ImageInfo:
    """Information about an image found on the page."""
    src: str = ""
    alt: Optional[str] = None


@dataclass
class LinkInfo:
    """Information about a link found on the page."""
    href: str = ""
    text: str = ""
    is_internal: bool = False


@dataclass
class MetaTag:
    """A single meta tag."""
    name: str = ""
    content: Optional[str] = None


@dataclass
class OpenGraphTag:
    """A single Open Graph tag."""
    property: str = ""
    content: Optional[str] = None


@dataclass
class SEOReport:
    """Complete SEO analysis report for a single URL.

    All fields default to safe empty/None values so the report
    can be constructed partially and still be valid.
    """
    url: Optional[str] = None
    title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None
    headings: list[tuple[int, str]] = field(default_factory=list)
    images: list[ImageInfo] = field(default_factory=list)
    canonical_link: Optional[str] = None
    og_tags: list[OpenGraphTag] = field(default_factory=list)
    meta_tags: list[MetaTag] = field(default_factory=list)
    word_count: int = 0
    link_count: int = 0
    internal_links: list[LinkInfo] = field(default_factory=list)
    external_links: list[LinkInfo] = field(default_factory=list)
    http_status: Optional[int] = None
    fetch_error: Optional[str] = None
