"""Manuscript parser — splits plain-text manuscripts into chapters/sections."""

import re
from typing import List, Dict, Any


class ManuscriptParseError(Exception):
    """Raised when manuscript parsing fails due to invalid input."""
    pass


class ManuscriptParser:
    """Reads a plain-text manuscript file and splits it into chapters/sections.

    Detects chapter boundaries by:
      - Lines starting with '# ' (Markdown-style headings)
      - Lines matching 'Chapter N' (where N is a number or word)

    Each chapter is returned as a dict with:
      - title: str
      - body: str (full text of the chapter)
      - sentences: List[str]
    """

    # Patterns for chapter headings
    HEADING_HASH = re.compile(r"^#\s+(.+)$", re.MULTILINE)
    HEADING_CHAPTER = re.compile(r"^Chapter\s+(\d+|[a-zA-Z]+)(?::\s*(.+))?$", re.MULTILINE | re.IGNORECASE)

    def __init__(self):
        pass

    def parse(self, text: str) -> List[Dict[str, Any]]:
        """Parse manuscript text into a list of chapter dicts.

        Args:
            text: Raw manuscript text.

        Returns:
            List of chapter dicts with 'title', 'body', and 'sentences'.
        """
        lines = text.splitlines()
        chapters: List[Dict[str, Any]] = []
        current_chapter: Dict[str, Any] | None = None

        for line in lines:
            # Check for '# ' heading
            hash_match = self.HEADING_HASH.match(line.strip())
            # Check for 'Chapter N' heading
            chapter_match = self.HEADING_CHAPTER.match(line.strip())

            if hash_match or chapter_match:
                # Save previous chapter if exists
                if current_chapter is not None:
                    chapters.append(current_chapter)

                if hash_match:
                    title = hash_match.group(1).strip()
                else:
                    subtitle = chapter_match.group(2)
                    if subtitle:
                        title = f"Chapter {chapter_match.group(1).strip()}: {subtitle.strip()}"
                    else:
                        title = f"Chapter {chapter_match.group(1).strip()}"
                current_chapter = {
                    "title": title,
                    "body": "",
                    "sentences": [],
                }
            else:
                if current_chapter is not None:
                    stripped = line.strip()
                    if stripped:
                        current_chapter["body"] += line + "\n"
                        # Split on sentence boundaries within a line
                        sentences = re.split(r'(?<=[.!?])\s+', stripped)
                        for sentence in sentences:
                            s = sentence.strip()
                            if s:
                                current_chapter["sentences"].append(s)
                    elif current_chapter["sentences"]:
                        # Blank line between paragraphs — keep as separator
                        pass

        # Don't forget the last chapter
        if current_chapter is not None:
            chapters.append(current_chapter)

        # If no chapters were detected, treat the whole text as one chapter
        if not chapters:
            paragraphs = re.split(r'(?<=[.!?])\s+', text.strip())
            chapters.append({
                "title": "Untitled",
                "body": text,
                "sentences": [p for p in paragraphs if p.strip()],
            })

        return chapters

    def parse_file(self, filepath: str) -> List[Dict[str, Any]]:
        """Parse a manuscript file from disk.

        Args:
            filepath: Path to the manuscript text file.

        Returns:
            List of chapter dicts.

        Raises:
            FileNotFoundError: If the file does not exist.
            PermissionError: If the file cannot be read due to permissions.
            ManuscriptParseError: If the file is empty or contains no parseable content.
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Manuscript file not found: {filepath}")
        except PermissionError:
            raise PermissionError(f"Permission denied reading file: {filepath}")

        if not text.strip():
            raise ManuscriptParseError(f"Manuscript file is empty: {filepath}")

        return self.parse(text)
