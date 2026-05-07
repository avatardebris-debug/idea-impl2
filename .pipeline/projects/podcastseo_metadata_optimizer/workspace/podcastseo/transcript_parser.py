"""Transcript parser for PodcastSEO.

Supports SRT, VTT, TXT, and DOCX formats with auto-detection.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict

import srt
import webvtt
from docx import Document


class TranscriptParser:
    """Auto-detects and parses transcript files (SRT, VTT, TXT, DOCX)."""

    SUPPORTED_EXTENSIONS = {".srt", ".vtt", ".txt", ".docx"}

    def detect_format(self, path: str) -> str:
        """Detect the transcript format from the file extension and content.

        Returns one of: 'srt', 'vtt', 'txt', 'docx', 'unknown'
        """
        p = Path(path)
        ext = p.suffix.lower()

        if ext == ".docx":
            return "docx"
        if ext == ".vtt":
            return "vtt"
        if ext == ".srt":
            return "srt"
        if ext == ".txt":
            return "txt"

        # Fallback: inspect file content
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read(4096)
        except (OSError, UnicodeDecodeError):
            return "unknown"

        if content.strip().startswith("WEBVTT"):
            return "vtt"
        # SRT has numeric sequence lines like "1\n00:00:01,000 --> 00:00:04,000\n"
        if re.search(r"^\d+\n\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$", content, re.MULTILINE):
            return "srt"
        return "txt"

    def _detect_format(self, path: str) -> str:
        """Detect format — public alias for detect_format."""
        fmt = self.detect_format(path)
        if fmt == "unknown":
            raise ValueError(f"Unsupported format for: {path}")
        return fmt

    def _detect_vtt(self, path: str) -> str:
        """Detect if file is VTT format."""
        p = Path(path)
        ext = p.suffix.lower()
        if ext == ".vtt":
            return "vtt"
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read(4096)
        except (OSError, UnicodeDecodeError):
            return "unknown"
        if content.strip().startswith("WEBVTT"):
            return "vtt"
        return "unknown"

    def _detect_txt(self, path: str) -> str:
        """Detect if file is TXT format."""
        p = Path(path)
        ext = p.suffix.lower()
        if ext == ".txt":
            return "txt"
        return "unknown"

    def _clean_text(self, text: str) -> str:
        """Clean text by removing speaker labels, music tags, and normalizing whitespace."""
        # Remove speaker labels
        text = re.sub(r"^(host|guest|narrator|announcer|moderator)\s*:\s*", "", text, flags=re.IGNORECASE)
        # Remove music tags
        text = re.sub(r"\[Music\]", "", text, flags=re.IGNORECASE)
        # Remove apostrophes (e.g., "It's" -> "Its")
        text = re.sub(r"'s\b", "", text)
        # Normalize whitespace
        text = re.sub(r"\n\s*\n", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _parse_srt(self, path: str) -> str:
        """Parse an SRT file and return clean text."""
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        subtitles = list(srt.parse(content))
        lines: list[str] = []
        for sub in subtitles:
            # Strip speaker labels (e.g., "Speaker 1: ")
            text = sub.content.strip()
            # Remove common speaker prefixes
            text = re.sub(r"^(speaker\s*\d+\s*:)\s*", "", text, flags=re.IGNORECASE)
            text = re.sub(r"^(host|guest|narrator|announcer|moderator)\s*:\s*", "", text, flags=re.IGNORECASE)
            if text:
                lines.append(text)
        return "\n".join(lines)

    def _parse_vtt(self, path: str) -> str:
        """Parse a VTT file and return clean text."""
        captions = webvtt.read(path)
        lines: list[str] = []
        for caption in captions:
            text = caption.text.strip()
            # Remove speaker labels
            text = re.sub(r"^(speaker\s*\d+\s*:)\s*", "", text, flags=re.IGNORECASE)
            text = re.sub(r"^(host|guest|narrator|announcer|moderator)\s*:\s*", "", text, flags=re.IGNORECASE)
            if text:
                lines.append(text)
        return "\n".join(lines)

    def _parse_txt(self, path: str) -> str:
        """Pass through TXT content, stripping only leading/trailing whitespace per line."""
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        return "\n".join(line.strip() for line in lines)

    def _parse_docx(self, path: str) -> str:
        """Parse a DOCX file and return clean text."""
        doc = Document(path)
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        return "\n".join(paragraphs)

    def parse(self, path: str) -> str:
        """Parse a transcript file and return clean text.

        Args:
            path: Path to the transcript file.

        Returns:
            Clean text with timestamps and speaker labels removed.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the format is not supported.
            RuntimeError: If parsing fails.
        """
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Transcript file not found: {path}")

        fmt = self.detect_format(path)
        if fmt == "unknown":
            raise ValueError(f"Unsupported or unrecognized format for: {path}")

        parsers = {
            "srt": self._parse_srt,
            "vtt": self._parse_vtt,
            "txt": self._parse_txt,
            "docx": self._parse_docx,
        }
        try:
            return parsers[fmt](path)
        except Exception as e:
            raise RuntimeError(f"Failed to parse {path} as {fmt}: {e}") from e

    def parse_raw(self, path: str) -> Dict[str, Any]:
        """Parse a transcript file and return text plus metadata.

        Returns:
            Dict with keys:
                - text: str (clean text)
                - format: str (detected format)
                - word_count: int
                - line_count: int
                - file_path: str
        """
        text = self.parse(path)
        fmt = self.detect_format(path)
        lines = text.split("\n")
        # Filter out empty lines for line count
        non_empty_lines = [l for l in lines if l.strip()]
        return {
            "text": text,
            "format": fmt,
            "word_count": len(text.split()),
            "line_count": len(non_empty_lines),
            "file_path": str(path),
        }
