"""
Transcript Importer Module

Import transcripts from existing files in SRT, VTT, TXT, and JSON formats.
Parses timestamps and structures content into TranscriptSection objects.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List, Optional

from transcript_builder import TranscriptBuilder, TranscriptSection, TranscriptFormat


class TranscriptImporter:
    """Import transcripts from various file formats."""

    @staticmethod
    def import_file(path: str, title: Optional[str] = None) -> TranscriptBuilder:
        """Auto-detect format and import a transcript file.

        Args:
            path: Path to the transcript file.
            title: Optional title override.

        Returns:
            TranscriptBuilder populated with the imported sections.
        """
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Transcript file not found: {path}")

        ext = p.suffix.lower()
        text = p.read_text(encoding="utf-8")
        title = title or p.stem.replace("_", " ").title()

        if ext == ".srt":
            return TranscriptImporter.from_srt(text, title)
        elif ext == ".vtt":
            return TranscriptImporter.from_vtt(text, title)
        elif ext == ".json":
            return TranscriptImporter.from_json(text, title)
        elif ext in (".txt", ".text"):
            return TranscriptImporter.from_txt(text, title)
        else:
            raise ValueError(f"Unsupported transcript format: {ext}")

    # ------------------------------------------------------------------
    # SRT
    # ------------------------------------------------------------------
    _SRT_BLOCK = re.compile(
        r"(\d+)\s*\n"
        r"(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*\n"
        r"((?:(?!\n\d+\n).)+)",
        re.DOTALL,
    )

    @staticmethod
    def from_srt(text: str, title: str = "Imported SRT") -> TranscriptBuilder:
        builder = TranscriptBuilder(title=title)
        for m in TranscriptImporter._SRT_BLOCK.finditer(text):
            seq = int(m.group(1))
            start = TranscriptImporter._parse_timestamp(m.group(2))
            end = TranscriptImporter._parse_timestamp(m.group(3))
            content = m.group(4).strip()
            builder.add_section(
                title=f"Section {seq}", content=content,
                start_time=start, end_time=end,
            )
        return builder

    # ------------------------------------------------------------------
    # VTT
    # ------------------------------------------------------------------
    _VTT_BLOCK = re.compile(
        r"(\d{2}:\d{2}:\d{2}[\.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[\.]\d{3})\s*\n"
        r"((?:(?!\n\d{2}:\d{2}).)+)",
        re.DOTALL,
    )

    @staticmethod
    def from_vtt(text: str, title: str = "Imported VTT") -> TranscriptBuilder:
        builder = TranscriptBuilder(title=title)
        idx = 1
        for m in TranscriptImporter._VTT_BLOCK.finditer(text):
            start = TranscriptImporter._parse_timestamp(m.group(1))
            end = TranscriptImporter._parse_timestamp(m.group(2))
            content = m.group(3).strip()
            builder.add_section(
                title=f"Section {idx}", content=content,
                start_time=start, end_time=end,
            )
            idx += 1
        return builder

    # ------------------------------------------------------------------
    # JSON
    # ------------------------------------------------------------------
    @staticmethod
    def from_json(text: str, title: str = "Imported JSON") -> TranscriptBuilder:
        data = json.loads(text)
        title = data.get("title", title)
        builder = TranscriptBuilder(title=title)
        for i, sec in enumerate(data.get("sections", []), 1):
            builder.add_section(
                title=sec.get("title", f"Section {i}"),
                content=sec.get("content", ""),
                start_time=sec.get("start_time", 0.0),
                end_time=sec.get("end_time"),
            )
        return builder

    # ------------------------------------------------------------------
    # Plain text (paragraphs become sections)
    # ------------------------------------------------------------------
    @staticmethod
    def from_txt(text: str, title: str = "Imported Text") -> TranscriptBuilder:
        builder = TranscriptBuilder(title=title)
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        t = 0.0
        for i, para in enumerate(paragraphs, 1):
            builder.add_section(
                title=f"Section {i}", content=para, start_time=t,
            )
            # Use the builder's estimated end_time
            t = builder.get_sections()[-1].end_time
        return builder

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------
    @staticmethod
    def search(builder: TranscriptBuilder, query: str,
               case_sensitive: bool = False) -> List[dict]:
        """Search within transcript sections.

        Returns list of dicts: {section_index, title, start_time, snippet}.
        """
        results = []
        for i, sec in enumerate(builder.get_sections()):
            content = sec.content
            q = query if case_sensitive else query.lower()
            haystack = content if case_sensitive else content.lower()
            if q in haystack:
                pos = haystack.index(q)
                start = max(0, pos - 40)
                end = min(len(content), pos + len(query) + 40)
                snippet = ("..." if start > 0 else "") + content[start:end] + ("..." if end < len(content) else "")
                results.append({
                    "section_index": i,
                    "title": sec.title,
                    "start_time": sec.start_time,
                    "snippet": snippet,
                })
        return results

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _parse_timestamp(ts: str) -> float:
        """Parse HH:MM:SS,mmm or HH:MM:SS.mmm to seconds."""
        ts = ts.replace(",", ".")
        parts = ts.split(":")
        h, m = int(parts[0]), int(parts[1])
        s = float(parts[2])
        return h * 3600 + m * 60 + s
