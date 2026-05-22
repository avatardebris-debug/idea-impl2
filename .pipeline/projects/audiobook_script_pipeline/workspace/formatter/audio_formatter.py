"""Audio script formatter — adds pacing markers to parsed chapter data."""

import re
from typing import List, Dict, Any


class AudioScriptFormatter:
    """Takes parsed chapter data and produces an audio script format.

    Adds pacing markers:
      - [PAUSE: Ns] for natural breaks (sentence/paragraph boundaries)
      - [EMPHASIS] for key terms (detected via capitalization patterns,
        or words in ALL CAPS, or first mention of proper nouns)
      - [SLOW] / [FAST] for tempo changes at section transitions

    Output is a structured dict ready for TTS consumption.
    """

    # Sentence-ending punctuation
    SENTENCE_END = re.compile(r'([.!?])\s+')

    # Words in ALL CAPS (at least 2 chars) — likely emphasis
    ALL_CAPS = re.compile(r'\b([A-Z]{2,})\b')

    # First word of a sentence — candidate for emphasis
    FIRST_WORD = re.compile(r'(?:^|[.!?]\s+)([A-Z][a-z]+)(?=\s|$)')

    def __init__(self, default_pause: float = 1.0):
        """
        Args:
            default_pause: Default pause duration in seconds between paragraphs.
        """
        self.default_pause = default_pause
        self.emphasis_markers = True  # Whether to apply emphasis detection

    def format_chapters(self, chapters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Format all chapters into an audio script.

        Args:
            chapters: List of chapter dicts from ManuscriptParser.

        Returns:
            Dict with 'title', 'chapters' (list of formatted chapter dicts).

        Raises:
            ValueError: If chapters list is empty.
        """
        if not chapters:
            raise ValueError("Cannot format audio script: chapters list is empty")

        formatted_chapters = []
        for chapter in chapters:
            formatted_chapters.append(self._format_chapter(chapter))

        # Use the first chapter's title as the document title (document title = first chapter title)
        doc_title = chapters[0]["title"] if chapters else "Untitled"
        return {
            "title": doc_title,
            "chapters": formatted_chapters,
        }

    def _format_chapter(self, chapter: Dict[str, Any]) -> Dict[str, Any]:
        """Format a single chapter into audio script entries."""
        entries = []
        sentences = chapter.get("sentences", [])

        # Add [SLOW] at chapter start
        entries.append({
            "text": f"[SLOW] {chapter['title']}",
            "markers": ["SLOW"],
        })

        for i, sentence in enumerate(sentences):
            # Add [PAUSE] before each sentence (except the first)
            if i > 0:
                entries.append({
                    "text": f"[PAUSE: {self.default_pause}s]",
                    "markers": ["PAUSE"],
                })

            # Process the sentence text for emphasis
            processed_text = self._add_emphasis(sentence)

            entries.append({
                "text": processed_text,
                "markers": [],
            })

            # Add [PAUSE] after each sentence (including the last)
            entries.append({
                "text": f"[PAUSE: {self.default_pause}s]",
                "markers": ["PAUSE"],
            })

        # Add [FAST] at chapter end to signal transition
        entries.append({
            "text": "[FAST]",
            "markers": ["FAST"],
        })

        return {
            "title": chapter["title"],
            "entries": entries,
        }

    def _add_emphasis(self, text: str) -> str:
        """Add [EMPHASIS] markers to key terms in the text.

        Detects:
          - Words in ALL CAPS (at least 2 chars) that are not already wrapped
          - First word of each sentence (if it's a proper noun pattern)
        """
        result = text

        # Skip if already wrapped
        if "[EMPHASIS]" in result:
            return result

        # Mark ALL CAPS words (not already wrapped)
        def caps_replacer(m):
            word = m.group(1)
            # Skip common acronyms and words that are already part of emphasis markers
            skip_words = {
                "EMPHASIS", "PAUSE", "SLOW", "FAST", "API", "HTML", "XML",
                "JSON", "URL", "HTTP", "HTTPS", "FTP", "SMTP", "POP", "IMAP",
                "TCP", "UDP", "IP", "CPU", "GPU", "RAM", "ROM", "BIOS", "USB",
                "PCI", "LED", "LCD", "DVD", "CD", "AI", "ML", "DL", "OS", "DB",
                "SQL", "CLI", "GUI", "SDK", "IDE", "DNS", "DHCP", "NAT", "VPN",
                "WAN", "LAN", "WLAN", "IoT",
            }
            if word in skip_words:
                return word
            return f"[EMPHASIS]{word}[/EMPHASIS]"

        result = self.ALL_CAPS.sub(caps_replacer, result)

        # Mark first word of sentences that look like proper nouns
        def proper_noun_replacer(m):
            word = m.group(1)
            # Exclude common words that are not proper nouns
            stop_words = {
                "The", "With", "As", "When", "This", "That", "These", "Those",
                "It", "Is", "Are", "Was", "Were", "Have", "Has", "Had",
                "Will", "Would", "Could", "Should", "May", "Might", "Must",
                "Can", "Not", "And", "But", "Or", "For", "So", "Yet",
                "At", "By", "In", "Of", "On", "To", "An", "If", "Then",
                "From", "He", "She", "We", "They", "You", "I", "Me",
                "My", "Our", "Your", "His", "Her", "Its", "Their",
                "What", "Which", "Who", "How", "Where", "Why",
                "All", "Any", "Each", "Every", "Some", "Only",
                "Just", "Also", "Very", "Too", "Much", "Many",
                "First", "Last", "Next", "Now", "Here", "There",
                "Even", "Still", "Never", "Often", "Sometimes",
                "However", "Therefore", "Thus", "Hence",
                "Although", "Though", "While", "Unless",
                "Until", "Before", "After", "During", "Since",
                "Through", "Across", "Above", "Over", "Under",
                "Within", "Without", "Upon", "Into", "About", "Like",
            }
            if word in stop_words:
                return m.group(0)
            if len(word) > 1 and word[0].isupper():
                return f"[EMPHASIS]{word}[/EMPHASIS]"
            return m.group(0)

        result = self.FIRST_WORD.sub(proper_noun_replacer, result)

        return result

    def format_to_string(self, audio_script: Dict[str, Any]) -> str:
        """Convert the formatted audio script dict to a readable string.

        Args:
            audio_script: Output from format_chapters().

        Returns:
            Formatted string with all pacing markers visible.
        """
        lines = []
        lines.append(f"=== {audio_script['title']} ===")
        lines.append("")

        for chapter in audio_script["chapters"]:
            lines.append(f"--- {chapter['title']} ---")
            for entry in chapter["entries"]:
                lines.append(entry["text"])
            lines.append("")

        return "\n".join(lines)
