"""Show notes generator for PodcastSEO.

Provides ShowNotesGenerator, TimestampAnchorBuilder, and ConfigLoader
classes to generate structured show notes from keyword data and transcripts.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from jinja2 import Environment, FileSystemLoader, BaseLoader

from podcastseo.transcript_parser import TranscriptParser
from podcastseo.keyword_extractor import KeywordExtractor


# ── Default config ──────────────────────────────────────────────────────────

DEFAULT_CONFIG: Dict[str, Any] = {
    "tone": "professional",
    "summary_length": "medium",
    "section_order": [
        "summary",
        "takeaways",
        "anchors",
        "tags",
        "cta",
    ],
    "cta_text": "Subscribe and rate this podcast on your favorite platform!",
    "max_takeaways": 5,
    "max_anchors": 10,
    "max_tags": 10,
}


# ── ConfigLoader ────────────────────────────────────────────────────────────

class ConfigLoader:
    """Loads and merges configuration for show notes generation."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize with optional config file path.

        Args:
            config_path: Path to a YAML config file. If None, uses defaults.
        """
        self.defaults = dict(DEFAULT_CONFIG)
        self.config = dict(DEFAULT_CONFIG)
        if config_path:
            self._load(config_path)

    def _load(self, config_path: str) -> None:
        """Load config from a YAML file and merge with defaults."""
        path = Path(config_path)
        if not path.exists():
            return
        with open(path, "r", encoding="utf-8") as f:
            user_config = yaml.safe_load(f) or {}
        # Deep merge: user values override defaults
        for key, value in user_config.items():
            if key in self.config and isinstance(self.config[key], dict) and isinstance(value, dict):
                self.config[key].update(value)
            else:
                self.config[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get a config value, falling back to default."""
        return self.config.get(key, default)

    def merge(self, overrides: Dict[str, Any]) -> Dict[str, Any]:
        """Merge override dict into config and return the result."""
        merged = dict(self.config)
        merged.update(overrides)
        return merged


# ── TimestampAnchorBuilder ─────────────────────────────────────────────────

class TimestampAnchorBuilder:
    """Maps keywords to their first occurrence in a transcript."""

    def __init__(self):
        self.parser = TranscriptParser()

    def build(self, keyword: str, transcript_path: str) -> Optional[str]:
        """Find the first timestamp/line reference for a keyword in a transcript.

        Args:
            keyword: The keyword to search for.
            transcript_path: Path to the transcript file.

        Returns:
            A string like "00:01:23" for SRT/VTT or "Line 42" for TXT/DOCX,
            or None if the keyword is not found.
        """
        if not keyword or not keyword.strip():
            return None

        p = Path(transcript_path)
        if not p.exists():
            return None

        fmt = self.parser.detect_format(transcript_path)
        keyword_lower = keyword.strip().lower()

        if fmt == "srt":
            return self._find_srt_anchor(transcript_path, keyword_lower)
        elif fmt == "vtt":
            return self._find_vtt_anchor(transcript_path, keyword_lower)
        elif fmt == "txt":
            return self._find_txt_anchor(transcript_path, keyword_lower)
        elif fmt == "docx":
            return self._find_docx_anchor(transcript_path, keyword_lower)
        return None

    def _find_srt_anchor(self, path: str, keyword_lower: str) -> Optional[str]:
        """Find keyword in SRT and return timestamp string."""
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        subtitles = list(srt_parse(content))
        for sub in subtitles:
            if keyword_lower in sub.content.lower():
                return format_timestamp(sub.start)
        return None

    def _find_vtt_anchor(self, path: str, keyword_lower: str) -> Optional[str]:
        """Find keyword in VTT and return timestamp string."""
        try:
            import webvtt
            captions = webvtt.read(path)
            for caption in captions:
                if keyword_lower in caption.text.lower():
                    return format_timestamp(caption.start)
        except Exception:
            # Fallback: raw text search
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            lines = content.split("\n")
            for line in lines:
                if keyword_lower in line.lower():
                    ts_match = re.search(r"(\d{2}:\d{2}:\d{2}\.\d{3})", line)
                    if ts_match:
                        return ts_match.group(1)
        return None

    def _find_txt_anchor(self, path: str, keyword_lower: str) -> Optional[str]:
        """Find keyword in TXT and return line number."""
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for i, line in enumerate(lines, start=1):
            if keyword_lower in line.lower():
                return f"Line {i}"
        return None

    def _find_docx_anchor(self, path: str, keyword_lower: str) -> Optional[str]:
        """Find keyword in DOCX and return paragraph number."""
        try:
            from docx import Document
            doc = Document(path)
            for i, para in enumerate(doc.paragraphs, start=1):
                if keyword_lower in para.text.lower():
                    return f"Paragraph {i}"
        except Exception:
            return None
        return None


# ── Minimal SRT parsing helpers (no external dependency needed) ──────────────

def srt_parse(content: str):
    """Minimal SRT parser returning objects with start, end, content."""
    import datetime
    blocks = re.split(r"\n\s*\n", content.strip())
    results = []
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 3:
            continue
        ts_line = lines[1]
        ts_match = re.match(
            r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})",
            ts_line,
        )
        if not ts_match:
            continue
        start = datetime.timedelta(
            hours=int(ts_match.group(1)),
            minutes=int(ts_match.group(2)),
            seconds=int(ts_match.group(3)),
            milliseconds=int(ts_match.group(4)),
        )
        end = datetime.timedelta(
            hours=int(ts_match.group(5)),
            minutes=int(ts_match.group(6)),
            seconds=int(ts_match.group(7)),
            milliseconds=int(ts_match.group(8)),
        )
        text = "\n".join(lines[2:])
        results.append(_SRTBlock(start, end, text))
    return results


class _SRTBlock:
    """Internal SRT subtitle block."""
    def __init__(self, start, end, content):
        self.start = start
        self.end = end
        self.content = content


def format_timestamp(td) -> str:
    """Format a timedelta as HH:MM:SS."""
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


# ── ShowNotesGenerator ─────────────────────────────────────────────────────

class ShowNotesGenerator:
    """Generates structured show notes from keyword data and transcript text."""

    def __init__(
        self,
        config_path: Optional[str] = None,
        template_dir: Optional[str] = None,
    ):
        """Initialize the generator.

        Args:
            config_path: Optional path to config.yaml.
            template_dir: Optional path to templates directory. Defaults to
                          ``podcastseo/templates/`` relative to this file.
        """
        self.config = ConfigLoader(config_path)
        if template_dir is None:
            template_dir = str(Path(__file__).parent / "templates")
        self.template_dir = template_dir
        self.anchor_builder = TimestampAnchorBuilder()

    def _load_template(self, name: str) -> str:
        """Load a Jinja2 template by name from the template directory."""
        env = Environment(
            loader=FileSystemLoader(self.template_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        return env.get_template(name).render

    def _build_context(
        self,
        keywords: List[Dict[str, Any]],
        transcript_text: str,
        episode_title: str = "",
        episode_description: str = "",
        transcript_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Build the context dict for template rendering."""
        tone = self.config.get("tone", "professional")
        summary_length = self.config.get("summary_length", "medium")
        max_takeaways = self.config.get("max_takeaways", 5)
        max_anchors = self.config.get("max_anchors", 10)
        max_tags = self.config.get("max_tags", 10)
        cta_text = self.config.get("cta_text", DEFAULT_CONFIG["cta_text"])

        # Episode summary
        if not episode_title:
            episode_title = "Podcast Episode"
        if not episode_description:
            episode_description = ""

        summary = self._generate_summary(keywords, transcript_text, summary_length)

        # Key takeaways
        key_takeaways = [
            f"- {kw['keyword']}: {kw['score']:.2f} ({kw['category']})"
            for kw in keywords[:max_takeaways]
        ]

        # Timestamped anchors
        timestamped_anchors = []
        if transcript_path:
            for kw in keywords[:max_anchors]:
                ts = self.anchor_builder.build(kw["keyword"], transcript_path)
                if ts:
                    timestamped_anchors.append({
                        "keyword": kw["keyword"],
                        "timestamp": ts,
                    })
        else:
            for kw in keywords[:max_anchors]:
                timestamped_anchors.append({
                    "keyword": kw["keyword"],
                    "timestamp": "N/A",
                })

        # Related tags
        categories = set()
        for kw in keywords[:max_tags]:
            categories.add(kw["category"])
        related_tags = sorted(categories)

        return {
            "episode_title": episode_title,
            "episode_description": episode_description,
            "episode_summary": summary,
            "key_takeaways": key_takeaways,
            "timestamped_anchors": timestamped_anchors,
            "related_tags": related_tags,
            "cta_text": cta_text,
            "tone": tone,
            "summary_length": summary_length,
        }

    def _generate_summary(
        self,
        keywords: List[Dict[str, Any]],
        transcript_text: str,
        length: str = "medium",
    ) -> str:
        """Generate an episode summary from keywords and transcript text."""
        if not keywords:
            return "No keywords extracted from this episode."

        # Build a concise summary from top keywords
        top_keywords = [kw["keyword"] for kw in keywords[:5]]
        word_count = {"short": 30, "medium": 60, "long": 100}.get(length, 60)

        # Use transcript context around first keyword occurrence
        first_kw = top_keywords[0] if top_keywords else ""
        if first_kw and transcript_text:
            idx = transcript_text.lower().find(first_kw.lower())
            if idx >= 0:
                start = max(0, idx - 50)
                end = min(len(transcript_text), idx + word_count)
                context = transcript_text[start:end].strip()
                # Clean up context
                context = re.sub(r"\s+", " ", context)
                if len(context) > word_count:
                    context = context[:word_count - 3] + "..."
                return f"This episode covers {first_kw} and related topics. {context}"

        # Fallback: keyword list summary
        kw_str = ", ".join(top_keywords)
        return f"This episode discusses {kw_str} and related subjects."

    def generate(
        self,
        keywords: List[Dict[str, Any]],
        transcript_text: str,
        episode_title: str = "",
        episode_description: str = "",
        transcript_path: Optional[str] = None,
        output_format: str = "markdown",
    ) -> str:
        """Generate show notes in the specified format.

        Args:
            keywords: List of keyword dicts from KeywordExtractor.
            transcript_text: Raw transcript text.
            episode_title: Optional episode title.
            episode_description: Optional episode description.
            transcript_path: Optional path to the original transcript file
                             (for timestamp resolution).
            output_format: One of 'markdown', 'html', 'txt'.

        Returns:
            The rendered show notes as a string.
        """
        template_map = {
            "markdown": "show_notes.md.j2",
            "html": "show_notes.html.j2",
            "txt": "show_notes.txt.j2",
        }
        if output_format not in template_map:
            raise ValueError(
                f"Unsupported format: {output_format}. "
                f"Choose from {list(template_map.keys())}"
            )

        template_name = template_map[output_format]
        render = self._load_template(template_name)
        context = self._build_context(
            keywords=keywords,
            transcript_text=transcript_text,
            episode_title=episode_title,
            episode_description=episode_description,
            transcript_path=transcript_path,
        )
        return render(**context)

    def generate_all_formats(
        self,
        keywords: List[Dict[str, Any]],
        transcript_text: str,
        episode_title: str = "",
        episode_description: str = "",
        transcript_path: Optional[str] = None,
    ) -> Dict[str, str]:
        """Generate show notes in all supported formats.

        Returns:
            Dict mapping format name to rendered string.
        """
        return {
            "markdown": self.generate(keywords, transcript_text, episode_title,
                                      episode_description, transcript_path, "markdown"),
            "html": self.generate(keywords, transcript_text, episode_title,
                                  episode_description, transcript_path, "html"),
            "txt": self.generate(keywords, transcript_text, episode_title,
                                 episode_description, transcript_path, "txt"),
        }
