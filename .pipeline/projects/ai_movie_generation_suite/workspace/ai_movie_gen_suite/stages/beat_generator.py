"""Beat Sheet Generator — Save-the-Cat (15 beats).

This module generates a structured beat sheet from a logline and genre.
It uses a deterministic template approach for MVP (no LLM dependency required),
with an optional LLM-powered path for richer content.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from ai_movie_gen_suite.models import Beat, BeatPhase, BeatSheet, SAVE_THE_CAT_BEATS


# ── Deterministic beat descriptions (MVP fallback) ───────────────────────────

DEFAULT_BEAT_TEMPLATES: Dict[str, str] = {
    "Opening Image": "An image that sets the tone and introduces the world of the story.",
    "Theme Stated": "Someone states the theme of the story, often in passing.",
    "Setup": "We see what the protagonist's life is like before the story begins. We see their flaws and desires.",
    "Catalyst": "A major event that changes the protagonist's life forever. The 'inciting incident.'",
    "Debate": "The protagonist debates whether to take action. They resist the call to adventure.",
    "Break into Two": "The protagonist makes a decisive choice to enter the new world/situation.",
    "B Story": "A new relationship or subplot begins (often the love story).",
    "Fun and Games": "The promise of the premise. The fun parts the audience came to see.",
    "Midpoint": "A major event that raises the stakes. False victory or false defeat.",
    "Bad Guys Close In": "The antagonist's forces close in. Internal and external pressures mount.",
    "All Is Lost": "The lowest point. The hero loses everything. 'The death of the hero' (literal or metaphorical).",
    "Dark Night of the Soul": "The hero wallows in despair. But then they find inspiration.",
    "Break into Three": "The hero has an epiphany and finds the solution to the problem.",
    "Finale": "The hero confronts the antagonist and resolves the story. The theme is proven true.",
    "Final Image": "The opposite of the opening image. Shows how the protagonist has changed.",
}


class BeatGenerator:
    """Generates a Save-the-Cat beat sheet from a logline and genre."""

    def __init__(self, logline: str, genre: str, tone: str = ""):
        self.logline = logline
        self.genre = genre
        self.tone = tone

    def generate_beat_sheet(self) -> BeatSheet:
        """Generate all 15 beats using the deterministic template approach."""
        beat_sheet = BeatSheet(logline=self.logline, genre=self.genre)

        phase_map = {
            "setup": BeatPhase.SETUP,
            "confrontation": BeatPhase.CONFRONTATION,
            "resolution": BeatPhase.RESOLUTION,
        }

        # Assign phases to beats
        phase_assignments = {
            "Opening Image": "setup",
            "Theme Stated": "setup",
            "Setup": "setup",
            "Catalyst": "setup",
            "Debate": "setup",
            "Break into Two": "confrontation",
            "B Story": "confrontation",
            "Fun and Games": "confrontation",
            "Midpoint": "confrontation",
            "Bad Guys Close In": "confrontation",
            "All Is Lost": "confrontation",
            "Dark Night of the Soul": "confrontation",
            "Break into Three": "resolution",
            "Finale": "resolution",
            "Final Image": "resolution",
        }

        # Estimate page ranges (standard screenplay: ~1 page per beat)
        page_ranges = {
            "Opening Image": "1",
            "Theme Stated": "1-2",
            "Setup": "2-12",
            "Catalyst": "12-15",
            "Debate": "15-25",
            "Break into Two": "25-28",
            "B Story": "28-30",
            "Fun and Games": "30-55",
            "Midpoint": "55-60",
            "Bad Guys Close In": "60-75",
            "All Is Lost": "75-80",
            "Dark Night of the Soul": "80-85",
            "Break into Three": "85-88",
            "Finale": "88-105",
            "Final Image": "105",
        }

        for i, beat_name in enumerate(SAVE_THE_CAT_BEATS, start=1):
            beat = Beat(
                beat_name=beat_name,
                beat_number=i,
                summary=self._generate_summary(beat_name),
                description=DEFAULT_BEAT_TEMPLATES.get(beat_name, ""),
                phase=phase_map.get(phase_assignments.get(beat_name, ""), None),
                estimated_page_range=page_ranges.get(beat_name, ""),
            )
            beat_sheet.add_beat(beat)

        return beat_sheet

    def _generate_summary(self, beat_name: str) -> str:
        """Generate a summary for a beat based on the logline."""
        # For MVP, create a template summary that references the logline
        return (
            f"[{beat_name}] — In the story of '{self.logline[:60]}...', "
            f"this beat marks the {beat_name.lower()} of the narrative arc."
        )

    def generate_with_llm(self, llm_client=None, prompt_template: str = "") -> BeatSheet:
        """Generate beats using an LLM (optional, for richer content).

        Args:
            llm_client: An LLM client with a .generate() method.
            prompt_template: Jinja2 template for the beat generation prompt.

        Returns:
            BeatSheet with LLM-generated content.
        """
        if llm_client is None:
            # Fall back to deterministic generation
            return self.generate_beat_sheet()

        prompt = self._build_llm_prompt(prompt_template)
        response = llm_client.generate(prompt)
        return self._parse_llm_response(response)

    def _build_llm_prompt(self, template: str = "") -> str:
        """Build the prompt for LLM beat generation."""
        if template:
            return template.format(
                logline=self.logline,
                genre=self.genre,
                tone=self.tone,
            )

        return (
            f"Generate a Save-the-Cat beat sheet for a {self.genre} screenplay.\n\n"
            f"Logline: {self.logline}\n"
            f"Tone: {self.tone or 'Not specified'}\n\n"
            f"Include all 15 beats with detailed descriptions.\n"
            f"Format each beat as:\n"
            f"BEAT N: [Beat Name]\n"
            f"Summary: [one-line summary]\n"
            f"Description: [detailed description]\n"
            f"Phase: [setup/confrontation/resolution]\n"
            f"Page Range: [estimated pages]\n"
        )

    def _parse_llm_response(self, response: str) -> BeatSheet:
        """Parse LLM response into a BeatSheet."""
        beat_sheet = BeatSheet(logline=self.logline, genre=self.genre)

        # Simple parsing: split by beat markers
        current_beat = None
        for line in response.split("\n"):
            line = line.strip()
            if line.startswith("BEAT") and ":" in line:
                if current_beat:
                    beat_sheet.add_beat(current_beat)
                parts = line.split(":", 1)
                beat_num = int(parts[0].split()[-1])
                beat_name = parts[1].strip()
                current_beat = Beat(
                    beat_name=beat_name,
                    beat_number=beat_num,
                    summary="",
                    description="",
                )
            elif line.startswith("Summary:") and current_beat:
                current_beat.summary = line.split(":", 1)[1].strip()
            elif line.startswith("Description:") and current_beat:
                current_beat.description = line.split(":", 1)[1].strip()
            elif line.startswith("Phase:") and current_beat:
                phase_val = line.split(":", 1)[1].strip().lower()
                current_beat.phase = BeatPhase(phase_val)

        if current_beat:
            beat_sheet.add_beat(current_beat)

        return beat_sheet
