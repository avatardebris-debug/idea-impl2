"""BeatSheetService — bridges movie ideas to Save-the-Cat beat sheets."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from ai_movie_gen_suite.formatters.json_formatter import JSONFormatter
from ai_movie_gen_suite.models import BeatPhase, BeatSheet
from ai_movie_gen_suite.stages.beat_generator import BeatGenerator, DEFAULT_BEAT_TEMPLATES


class BeatSheetService:
    """Orchestrates beat sheet generation from movie ideas.

    Accepts input as:
      - Raw strings (title, genre, logline, optional characters)
      - A dict from movie_idea_generator output
      - A path to a JSON file containing a movie idea

    Generates a Save-the-Cat 15-beat sheet using the ai_movie_gen_suite pipeline.
    """

    def __init__(
        self,
        title: str = "Untitled",
        genre: str = "",
        logline: str = "",
        characters: Optional[List[Dict[str, Any]]] = None,
        tone: str = "",
    ):
        self.title = title
        self.genre = genre
        self.logline = logline
        self.characters = characters or []
        self.tone = tone
        self._beat_sheet: Optional[BeatSheet] = None
        self._output_path: Optional[str] = None

    @classmethod
    def from_idea_dict(cls, idea: Dict[str, Any]) -> "BeatSheetService":
        """Create a BeatSheetService from a movie_idea_generator output dict.

        Args:
            idea: Dict with keys 'title', 'genre', 'logline', 'characters'.

        Returns:
            A configured BeatSheetService instance.
        """
        return cls(
            title=idea.get("title", "Untitled"),
            genre=idea.get("genre", ""),
            logline=idea.get("logline", ""),
            characters=idea.get("characters", []),
        )

    @classmethod
    def from_json_file(cls, filepath: str) -> "BeatSheetService":
        """Create a BeatSheetService from a JSON file containing a movie idea.

        Args:
            filepath: Path to a JSON file with keys 'title', 'genre', 'logline', 'characters'.

        Returns:
            A configured BeatSheetService instance.
        """
        with open(filepath, "r", encoding="utf-8") as f:
            idea = json.load(f)
        return cls.from_idea_dict(idea)

    def generate(self) -> Dict[str, Any]:
        """Generate a complete Save-the-Cat beat sheet.

        Returns:
            Dict with keys:
                - beat_sheet: BeatSheet pydantic model
                - beat_sheet_json: JSON string
                - beat_sheet_dict: serializable dict
                - output_path: str | None
                - title: str
                - genre: str
                - num_beats: int
        """
        if not self.logline:
            raise ValueError("Logline is required to generate a beat sheet.")
        if not self.genre:
            raise ValueError("Genre is required to generate a beat sheet.")

        generator = BeatGenerator(
            logline=self.logline,
            genre=self.genre,
            tone=self.tone,
        )
        self._beat_sheet = generator.generate_beat_sheet()

        # Enrich beats with character info if available
        if self.characters:
            self._enrich_beats_with_characters()

        # Serialize
        beat_sheet_dict = self._beat_sheet.model_dump()
        beat_sheet_json = json.dumps(beat_sheet_dict, indent=2, ensure_ascii=False)

        return {
            "beat_sheet": self._beat_sheet,
            "beat_sheet_json": beat_sheet_json,
            "beat_sheet_dict": beat_sheet_dict,
            "output_path": self._output_path,
            "title": self.title,
            "genre": self.genre,
            "num_beats": len(self._beat_sheet.beats),
        }

    def save_to_file(self, filepath: str) -> str:
        """Save the beat sheet to a JSON file.

        Args:
            filepath: Output file path.

        Returns:
            The absolute path of the saved file.
        """
        if self._beat_sheet is None:
            raise RuntimeError("No beat sheet generated yet. Call generate() first.")

        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)

        formatter = JSONFormatter(beat_sheet=self._beat_sheet)
        formatter.save(filepath)
        self._output_path = os.path.abspath(filepath)
        return self._output_path

    def get_beat_sheet(self) -> Optional[BeatSheet]:
        """Return the current BeatSheet model, if generated."""
        return self._beat_sheet

    def _enrich_beats_with_characters(self) -> None:
        """Add character involvement to each beat based on character roles."""
        if not self.characters:
            return

        # Map character names to roles
        char_roles: Dict[str, str] = {}
        for char in self.characters:
            name = char.get("name", "")
            role = char.get("role", "supporting")
            if name:
                char_roles[name] = role

        # Assign characters to beats based on narrative logic
        protagonist_names = [n for n, r in char_roles.items() if r == "protagonist"]
        antagonist_names = [n for n, r in char_roles.items() if r == "antagonist"]
        mentor_names = [n for n, r in char_roles.items() if r == "mentor"]
        ally_names = [n for n, r in char_roles.items() if r == "ally"]

        for beat in self._beat_sheet.beats:
            involved: List[str] = list(beat.characters_involved or [])

            # Opening image: protagonist
            if beat.beat_number == 1 and protagonist_names:
                involved.extend(protagonist_names[:1])

            # Theme stated: protagonist + mentor
            if beat.beat_number == 2:
                involved.extend(protagonist_names[:1])
                involved.extend(mentor_names[:1])

            # Setup: protagonist + ally
            if beat.beat_number == 3:
                involved.extend(protagonist_names[:1])
                involved.extend(ally_names[:1])

            # Catalyst: protagonist
            if beat.beat_number == 4 and protagonist_names:
                involved.extend(protagonist_names[:1])

            # Debate: protagonist
            if beat.beat_number == 5 and protagonist_names:
                involved.extend(protagonist_names[:1])

            # Break into two: protagonist
            if beat.beat_number == 6 and protagonist_names:
                involved.extend(protagonist_names[:1])

            # B story: protagonist + B-story character
            if beat.beat_number == 7:
                involved.extend(protagonist_names[:1])
                # Use ally or mentor as B-story character
                b_char = ally_names[:1] or mentor_names[:1]
                involved.extend(b_char)

            # Fun and games: protagonist + antagonist
            if beat.beat_number in (8, 9):
                involved.extend(protagonist_names[:1])
                involved.extend(antagonist_names[:1])

            # Midpoint: protagonist + antagonist
            if beat.beat_number == 10:
                involved.extend(protagonist_names[:1])
                involved.extend(antagonist_names[:1])

            # Bad guys close in: protagonist + antagonist + ally
            if beat.beat_number in (11, 12):
                involved.extend(protagonist_names[:1])
                involved.extend(antagonist_names[:1])
                involved.extend(ally_names[:1])

            # All is lost: protagonist
            if beat.beat_number == 13 and protagonist_names:
                involved.extend(protagonist_names[:1])

            # Dark night: protagonist
            if beat.beat_number == 14 and protagonist_names:
                involved.extend(protagonist_names[:1])

            # Finale: protagonist + antagonist + ally
            if beat.beat_number == 15:
                involved.extend(protagonist_names[:1])
                involved.extend(antagonist_names[:1])
                involved.extend(ally_names[:1])

            beat.characters_involved = list(set(involved))

    def __repr__(self) -> str:
        return (
            f"BeatSheetService(title={self.title!r}, genre={self.genre!r}, "
            f"logline={self.logline!r}, num_beats={len(self._beat_sheet.beats) if self._beat_sheet else 0})"
        )
