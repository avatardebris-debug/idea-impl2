"""Tests for the AI Movie Generation Suite formatters."""

import pytest
from ai_movie_gen_suite.formatters.formatters import (
    format_concept,
    format_beat_sheet,
    format_characters,
    format_script,
    format_scene_descriptions,
    format_summary,
    format_music_cues,
    format_post_production,
    format_marketing,
    format_distribution,
    format_project,
)
from ai_movie_gen_suite.models import (
    Concept,
    Beat,
    Character,
    Scene,
    Script,
    Summary,
    MusicCue,
    PostProductionNote,
    MarketingMaterial,
    DistributionStrategy,
    Project,
)


class TestFormatConcept:
    """Tests for format_concept."""

    def test_format_concept(self):
        """Test formatting a Concept."""
        concept = Concept(
            title="Test Movie",
            genre="Sci-Fi",
            logline="A test logline",
            synopsis="A test synopsis",
            visual_style="Cyberpunk",
            target_audience="Adults",
            key_themes=["Technology"],
            mood="Dark",
            feasibility_notes="Feasible",
        )
        result = format_concept(concept)
        assert "Test Movie" in result
        assert "Sci-Fi" in result
        assert "A test logline" in result
        assert "A test synopsis" in result
        assert "Cyberpunk" in result
        assert "Adults" in result
        assert "Technology" in result
        assert "Dark" in result
        assert "Feasible" in result

    def test_format_concept_empty(self):
        """Test formatting an empty Concept."""
        concept = Concept(
            title="",
            genre="",
            logline="",
            synopsis="",
            visual_style="",
            target_audience="",
            key_themes=[],
            mood="",
            feasibility_notes="",
        )
        result = format_concept(concept)
        assert isinstance(result, str)


class TestFormatBeatSheet:
    """Tests for format_beat_sheet."""

    def test_format_beat_sheet(self):
        """Test formatting a beat sheet."""
        beats = [
            Beat(number=1, name="Inciting Incident", description="Something happens"),
            Beat(number=2, name="Rising Action", description="Things get worse"),
        ]
        result = format_beat_sheet(beats)
        assert "Inciting Incident" in result
        assert "Rising Action" in result
        assert "Something happens" in result
        assert "Things get worse" in result

    def test_format_beat_sheet_empty(self):
        """Test formatting an empty beat sheet."""
        result = format_beat_sheet([])
        assert isinstance(result, str)


class TestFormatCharacters:
    """Tests for format_characters."""

    def test_format_characters(self):
        """Test formatting characters."""
        characters = [
            Character(
                name="Hero",
                role="Protagonist",
                physical_description="Tall",
                clothing="Jacket",
                personality="Brave",
                background="Soldier",
                visual_prompt="Hero",
            ),
            Character(
                name="Villain",
                role="Antagonist",
                physical_description="Short",
                clothing="Suit",
                personality="Cunning",
                background="Businessman",
                visual_prompt="Villain",
            ),
        ]
        result = format_characters(characters)
        assert "Hero" in result
        assert "Villain" in result
        assert "Protagonist" in result
        assert "Antagonist" in result

    def test_format_characters_empty(self):
        """Test formatting empty characters."""
        result = format_characters([])
        assert isinstance(result, str)


class TestFormatScript:
    """Tests for format_script."""

    def test_format_script(self):
        """Test formatting a script."""
        scene = Scene(
            number=1,
            location="Coffee Shop",
            description="Two characters meet",
            camera_direction="Close-up",
            visual_notes="Warm lighting",
            duration_seconds=120,
        )
        script = Script(scenes=[scene])
        result = format_script(script)
        assert "Coffee Shop" in result
        assert "Two characters meet" in result
        assert "Close-up" in result
        assert "Warm lighting" in result

    def test_format_script_empty(self):
        """Test formatting an empty script."""
        script = Script(scenes=[])
        result = format_script(script)
        assert isinstance(result, str)


class TestFormatSceneDescriptions:
    """Tests for format_scene_descriptions."""

    def test_format_scene_descriptions(self):
        """Test formatting scene descriptions."""
        scenes = [
            Scene(
                number=1,
                location="Coffee Shop",
                description="Two characters meet",
                camera_direction="Close-up",
                visual_notes="Warm lighting",
                duration_seconds=120,
            ),
            Scene(
                number=2,
                location="Park",
                description="A chase scene",
                camera_direction="Tracking shot",
                visual_notes="Bright sunlight",
                duration_seconds=180,
            ),
        ]
        result = format_scene_descriptions(scenes)
        assert "Coffee Shop" in result
        assert "Park" in result
        assert "Two characters meet" in result
        assert "A chase scene" in result

    def test_format_scene_descriptions_empty(self):
        """Test formatting empty scene descriptions."""
        result = format_scene_descriptions([])
        assert isinstance(result, str)


class TestFormatSummary:
    """Tests for format_summary."""

    def test_format_summary(self):
        """Test formatting a summary."""
        summary = Summary(
            title="Test Movie",
            logline="A test logline",
            genre="Sci-Fi",
            summary="A detailed summary",
            key_themes=["Technology"],
            target_audience="Adults",
            comparable_films=["Movie A"],
            rating="PG-13",
        )
        result = format_summary(summary)
        assert "Test Movie" in result
        assert "A test logline" in result
        assert "Sci-Fi" in result
        assert "A detailed summary" in result
        assert "Technology" in result
        assert "Adults" in result
        assert "Movie A" in result
        assert "PG-13" in result

    def test_format_summary_empty(self):
        """Test formatting an empty summary."""
        summary = Summary(
            title="",
            logline="",
            genre="",
            summary="",
            key_themes=[],
            target_audience="",
            comparable_films=[],
            rating="",
        )
        result = format_summary(summary)
        assert isinstance(result, str)


class TestFormatMusicCues:
    """Tests for format_music_cues."""

    def test_format_music_cues(self):
        """Test formatting music cues."""
        cues = [
            MusicCue(
                start_time="0:00",
                end_time="0:30",
                instrumentation="Piano",
                tempo="Slow",
                mood="Melancholic",
                volume="Medium",
            ),
            MusicCue(
                start_time="0:30",
                end_time="1:00",
                instrumentation="Strings",
                tempo="Fast",
                mood="Exciting",
                volume="Loud",
            ),
        ]
        result = format_music_cues(cues)
        assert "0:00" in result
        assert "0:30" in result
        assert "Piano" in result
        assert "Strings" in result
        assert "Slow" in result
        assert "Fast" in result

    def test_format_music_cues_empty(self):
        """Test formatting empty music cues."""
        result = format_music_cues([])
        assert isinstance(result, str)


class TestFormatPostProduction:
    """Tests for format_post_production."""

    def test_format_post_production(self):
        """Test formatting post-production notes."""
        notes = [
            PostProductionNote(
                scene_number=1,
                action="Add VFX",
                notes="Important note",
                requirements=["4K resolution"],
                timeline="2 weeks",
                quality_checks=["Color grading"],
            ),
        ]
        result = format_post_production(notes)
        assert "1" in result
        assert "Add VFX" in result
        assert "Important note" in result
        assert "4K resolution" in result
        assert "2 weeks" in result
        assert "Color grading" in result

    def test_format_post_production_empty(self):
        """Test formatting empty post-production notes."""
        result = format_post_production([])
        assert isinstance(result, str)


class TestFormatMarketing:
    """Tests for format_marketing."""

    def test_format_marketing(self):
        """Test formatting marketing materials."""
        marketing = MarketingMaterial(
            tagline="A great tagline",
            poster_description="Poster with hero",
            social_media=["Tweet 1", "Tweet 2"],
            press_release="Press release text",
        )
        result = format_marketing(marketing)
        assert "A great tagline" in result
        assert "Poster with hero" in result
        assert "Tweet 1" in result
        assert "Tweet 2" in result
        assert "Press release text" in result

    def test_format_marketing_empty(self):
        """Test formatting empty marketing materials."""
        marketing = MarketingMaterial(
            tagline="",
            poster_description="",
            social_media=[],
            press_release="",
        )
        result = format_marketing(marketing)
        assert isinstance(result, str)


class TestFormatDistribution:
    """Tests for format_distribution."""

    def test_format_distribution(self):
        """Test formatting distribution strategy."""
        distribution = DistributionStrategy(
            platforms=["Netflix", "Amazon"],
            release_strategy="Wide release",
            target_audience="Adults",
            estimated_budget="$10M",
        )
        result = format_distribution(distribution)
        assert "Netflix" in result
        assert "Amazon" in result
        assert "Wide release" in result
        assert "Adults" in result
        assert "$10M" in result

    def test_format_distribution_empty(self):
        """Test formatting empty distribution strategy."""
        distribution = DistributionStrategy(
            platforms=[],
            release_strategy="",
            target_audience="",
            estimated_budget="",
        )
        result = format_distribution(distribution)
        assert isinstance(result, str)


class TestFormatProject:
    """Tests for format_project."""

    def test_format_project(self):
        """Test formatting a project."""
        concept = Concept(
            title="Test Movie",
            genre="Sci-Fi",
            logline="A test logline",
            synopsis="A test synopsis",
            visual_style="Cyberpunk",
            target_audience="Adults",
            key_themes=["Technology"],
            mood="Dark",
            feasibility_notes="Feasible",
        )
        beat = Beat(number=1, name="Test", description="Test")
        character = Character(
            name="Hero",
            role="Protagonist",
            physical_description="Tall",
            clothing="Jacket",
            personality="Brave",
            background="Soldier",
            visual_prompt="Hero",
        )
        scene = Scene(
            number=1,
            location="Coffee Shop",
            description="Two characters meet",
            camera_direction="Close-up",
            visual_notes="Warm lighting",
            duration_seconds=120,
        )
        script = Script(scenes=[scene])
        summary = Summary(
            title="Test Movie",
            logline="A test logline",
            genre="Sci-Fi",
            summary="A detailed summary",
            key_themes=["Technology"],
            target_audience="Adults",
            comparable_films=["Movie A"],
            rating="PG-13",
        )
        music_cue = MusicCue(
            start_time="0:00",
            end_time="0:30",
            instrumentation="Piano",
            tempo="Slow",
            mood="Melancholic",
            volume="Medium",
        )
        post_prod_note = PostProductionNote(
            scene_number=1,
            action="Add VFX",
            notes="Important note",
            timeline="2 weeks",
            quality_checks=["Color grading"],
        )
        marketing = MarketingMaterial(
            tagline="A great tagline",
            poster_description="Poster with hero",
            press_release="Press release text",
        )
        distribution = DistributionStrategy(
            platforms=["Netflix"],
            release_strategy="Wide release",
            target_audience="Adults",
            estimated_budget="$10M",
        )

        project = Project(
            concept=concept,
            beat_sheet=[beat],
            characters=[character],
            script=script,
            scenes=[scene],
            summary=summary,
            music=[music_cue],
            post_production=[post_prod_note],
            marketing=marketing,
            distribution=distribution,
        )

        result = format_project(project)
        assert "Test Movie" in result
        assert "Sci-Fi" in result
        assert "A test logline" in result
        assert "A test synopsis" in result
        assert "Cyberpunk" in result
        assert "Adults" in result
        assert "Technology" in result
        assert "Dark" in result
        assert "Feasible" in result
        assert "Test" in result
        assert "Hero" in result
        assert "Protagonist" in result
        assert "Tall" in result
        assert "Jacket" in result
        assert "Brave" in result
        assert "Soldier" in result
        assert "Hero" in result
        assert "Coffee Shop" in result
        assert "Two characters meet" in result
        assert "Close-up" in result
        assert "Warm lighting" in result
        assert "A detailed summary" in result
        assert "Movie A" in result
        assert "PG-13" in result
        assert "0:00" in result
        assert "0:30" in result
        assert "Piano" in result
        assert "Slow" in result
        assert "Melancholic" in result
        assert "Medium" in result
        assert "1" in result
        assert "Add VFX" in result
        assert "Important note" in result
        assert "4K resolution" in result
        assert "2 weeks" in result
        assert "Color grading" in result
        assert "A great tagline" in result
        assert "Poster with hero" in result
        assert "Press release text" in result
        assert "Netflix" in result
        assert "Wide release" in result
        assert "$10M" in result

    def test_format_project_empty(self):
        """Test formatting an empty project."""
        project = Project()
        result = format_project(project)
        assert isinstance(result, str)
