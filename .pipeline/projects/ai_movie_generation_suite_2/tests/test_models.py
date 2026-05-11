"""Tests for the AI Movie Generation Suite models."""

import pytest
from ai_movie_gen_suite.models import (
    Project,
    Concept,
    Beat,
    Character,
    Scene,
    Script,
    SceneDescription,
    Summary,
    MusicCue,
    PostProductionNote,
    MarketingMaterial,
    DistributionStrategy,
)


class TestProject:
    """Tests for the Project model."""

    def test_create_project(self):
        """Test creating a project."""
        project = Project(
            title="Test Movie",
            status="initialized",
        )
        assert project.title == "Test Movie"
        assert project.status == "initialized"
        assert project.concept is None
        assert project.beat_sheet is None
        assert project.characters == []
        assert project.script is None
        assert project.scenes == []
        assert project.summary is None
        assert project.music == []
        assert project.post_production == []
        assert project.marketing is None
        assert project.distribution is None

    def test_project_to_dict(self):
        """Test project serialization."""
        project = Project(
            title="Test Movie",
            status="initialized",
        )
        data = project.to_dict()
        assert data["title"] == "Test Movie"
        assert data["status"] == "initialized"
        assert "concept" in data
        assert "beat_sheet" in data
        assert "characters" in data
        assert "script" in data
        assert "scenes" in data
        assert "summary" in data
        assert "music" in data
        assert "post_production" in data
        assert "marketing" in data
        assert "distribution" in data

    def test_project_from_dict(self):
        """Test project deserialization."""
        data = {
            "title": "Test Movie",
            "status": "initialized",
            "concept": {
                "title": "Test Concept",
                "genre": "Drama",
                "logline": "A test logline",
                "synopsis": "A test synopsis",
                "visual_style": "Realistic",
                "target_audience": "Adults",
                "key_themes": ["test"],
                "mood": "Serious",
                "feasibility_notes": "Feasible",
            },
            "beat_sheet": {
                "beats": [
                    {
                        "number": 1,
                        "name": "Opening Image",
                        "description": "Test beat",
                        "scene_numbers": [1],
                    }
                ]
            },
            "characters": [
                {
                    "name": "Test Character",
                    "role": "Protagonist",
                    "physical_description": "Tall",
                    "clothing": "Casual",
                    "personality": "Brave",
                    "background": "Test background",
                    "visual_prompt": "Test prompt",
                    "reference_images": [],
                }
            ],
            "script": {
                "scenes": [
                    {
                        "number": 1,
                        "location": "Test Location",
                        "description": "Test description",
                        "dialogue": [],
                        "characters_present": ["Test Character"],
                        "camera_direction": "Static",
                        "visual_notes": "Test notes",
                        "duration_seconds": 30,
                    }
                ]
            },
            "scenes": [
                {
                    "scene_number": 1,
                    "location": "Test Location",
                    "visual_description": "Test visual",
                    "camera_directions": "Static",
                    "lighting": "Bright",
                    "color_palette": "Warm",
                    "mood": "Happy",
                    "props_and_set_design": "Test props",
                }
            ],
            "summary": {
                "title": "Test Movie",
                "logline": "Test logline",
                "genre": "Drama",
                "summary": "Test summary",
                "key_themes": ["test"],
                "target_audience": "Adults",
                "comparable_films": ["Test Film"],
                "rating": "PG-13",
            },
            "music": [
                {
                    "scene_number": 1,
                    "music_cues": [
                        {
                            "start_time": "0:00",
                            "end_time": "0:30",
                            "instrumentation": "Piano",
                            "tempo": "Slow",
                            "mood": "Sad",
                            "volume": "Medium",
                        }
                    ],
                    "sound_effects": [],
                    "audio_direction": "Test direction",
                }
            ],
            "post_production": [
                {
                    "scene_number": 1,
                    "action": "Color grading",
                    "notes": "Test notes",
                    "requirements": ["Test requirement"],
                    "timeline": "1 week",
                    "quality_checks": ["Test check"],
                }
            ],
            "marketing": {
                "tagline": "Test tagline",
                "poster_description": "Test poster",
                "social_media": [],
                "press_release": "Test press release",
            },
            "distribution": {
                "platforms": ["Netflix"],
                "release_strategy": "Test strategy",
                "target_audience": "Adults",
                "estimated_budget": "Test budget",
            },
        }
        project = Project.from_dict(data)
        assert project.title == "Test Movie"
        assert project.status == "initialized"
        assert project.concept is not None
        assert project.concept.title == "Test Concept"
        assert len(project.characters) == 1
        assert project.characters[0].name == "Test Character"
        assert project.script is not None
        assert len(project.script.scenes) == 1
        assert project.summary is not None
        assert project.summary.title == "Test Movie"


class TestConcept:
    """Tests for the Concept model."""

    def test_create_concept(self):
        """Test creating a concept."""
        concept = Concept(
            title="Test Movie",
            genre="Drama",
            logline="A test logline",
            synopsis="A test synopsis",
            visual_style="Realistic",
            target_audience="Adults",
            key_themes=["test"],
            mood="Serious",
            feasibility_notes="Feasible",
        )
        assert concept.title == "Test Movie"
        assert concept.genre == "Drama"
        assert concept.logline == "A test logline"
        assert concept.synopsis == "A test synopsis"
        assert concept.visual_style == "Realistic"
        assert concept.target_audience == "Adults"
        assert concept.key_themes == ["test"]
        assert concept.mood == "Serious"
        assert concept.feasibility_notes == "Feasible"

    def test_concept_to_dict(self):
        """Test concept serialization."""
        concept = Concept(
            title="Test Movie",
            genre="Drama",
            logline="A test logline",
            synopsis="A test synopsis",
            visual_style="Realistic",
            target_audience="Adults",
            key_themes=["test"],
            mood="Serious",
            feasibility_notes="Feasible",
        )
        data = concept.to_dict()
        assert data["title"] == "Test Movie"
        assert data["genre"] == "Drama"
        assert data["logline"] == "A test logline"
        assert data["synopsis"] == "A test synopsis"
        assert data["visual_style"] == "Realistic"
        assert data["target_audience"] == "Adults"
        assert data["key_themes"] == ["test"]
        assert data["mood"] == "Serious"
        assert data["feasibility_notes"] == "Feasible"


class TestBeat:
    """Tests for the Beat model."""

    def test_create_beat(self):
        """Test creating a beat."""
        beat = Beat(
            number=1,
            name="Opening Image",
            description="Test beat",
            scene_numbers=[1],
        )
        assert beat.number == 1
        assert beat.name == "Opening Image"
        assert beat.description == "Test beat"
        assert beat.scene_numbers == [1]

    def test_beat_to_dict(self):
        """Test beat serialization."""
        beat = Beat(
            number=1,
            name="Opening Image",
            description="Test beat",
            scene_numbers=[1],
        )
        data = beat.to_dict()
        assert data["number"] == 1
        assert data["name"] == "Opening Image"
        assert data["description"] == "Test beat"
        assert data["scene_numbers"] == [1]


class TestCharacter:
    """Tests for the Character model."""

    def test_create_character(self):
        """Test creating a character."""
        character = Character(
            name="Test Character",
            role="Protagonist",
            physical_description="Tall",
            clothing="Casual",
            personality="Brave",
            background="Test background",
            visual_prompt="Test prompt",
            reference_images=[],
        )
        assert character.name == "Test Character"
        assert character.role == "Protagonist"
        assert character.physical_description == "Tall"
        assert character.clothing == "Casual"
        assert character.personality == "Brave"
        assert character.background == "Test background"
        assert character.visual_prompt == "Test prompt"
        assert character.reference_images == []

    def test_character_to_dict(self):
        """Test character serialization."""
        character = Character(
            name="Test Character",
            role="Protagonist",
            physical_description="Tall",
            clothing="Casual",
            personality="Brave",
            background="Test background",
            visual_prompt="Test prompt",
            reference_images=[],
        )
        data = character.to_dict()
        assert data["name"] == "Test Character"
        assert data["role"] == "Protagonist"
        assert data["physical_description"] == "Tall"
        assert data["clothing"] == "Casual"
        assert data["personality"] == "Brave"
        assert data["background"] == "Test background"
        assert data["visual_prompt"] == "Test prompt"
        assert data["reference_images"] == []


class TestScene:
    """Tests for the Scene model."""

    def test_create_scene(self):
        """Test creating a scene."""
        scene = Scene(
            number=1,
            location="Test Location",
            description="Test description",
            dialogue=[],
            characters_present=["Test Character"],
            camera_direction="Static",
            visual_notes="Test notes",
            duration_seconds=30,
        )
        assert scene.number == 1
        assert scene.location == "Test Location"
        assert scene.description == "Test description"
        assert scene.dialogue == []
        assert scene.characters_present == ["Test Character"]
        assert scene.camera_direction == "Static"
        assert scene.visual_notes == "Test notes"
        assert scene.duration_seconds == 30

    def test_scene_to_dict(self):
        """Test scene serialization."""
        scene = Scene(
            number=1,
            location="Test Location",
            description="Test description",
            dialogue=[],
            characters_present=["Test Character"],
            camera_direction="Static",
            visual_notes="Test notes",
            duration_seconds=30,
        )
        data = scene.to_dict()
        assert data["number"] == 1
        assert data["location"] == "Test Location"
        assert data["description"] == "Test description"
        assert data["dialogue"] == []
        assert data["characters_present"] == ["Test Character"]
        assert data["camera_direction"] == "Static"
        assert data["visual_notes"] == "Test notes"
        assert data["duration_seconds"] == 30


class TestScript:
    """Tests for the Script model."""

    def test_create_script(self):
        """Test creating a script."""
        script = Script(
            scenes=[
                Scene(
                    number=1,
                    location="Test Location",
                    description="Test description",
                    dialogue=[],
                    characters_present=["Test Character"],
                    camera_direction="Static",
                    visual_notes="Test notes",
                    duration_seconds=30,
                )
            ]
        )
        assert len(script.scenes) == 1
        assert script.scenes[0].number == 1

    def test_script_to_dict(self):
        """Test script serialization."""
        script = Script(
            scenes=[
                Scene(
                    number=1,
                    location="Test Location",
                    description="Test description",
                    dialogue=[],
                    characters_present=["Test Character"],
                    camera_direction="Static",
                    visual_notes="Test notes",
                    duration_seconds=30,
                )
            ]
        )
        data = script.to_dict()
        assert len(data["scenes"]) == 1
        assert data["scenes"][0]["number"] == 1


class TestSceneDescription:
    """Tests for the SceneDescription model."""

    def test_create_scene_description(self):
        """Test creating a scene description."""
        description = SceneDescription(
            scene_number=1,
            location="Test Location",
            visual_description="Test visual",
            camera_directions="Static",
            lighting="Bright",
            color_palette="Warm",
            mood="Happy",
            props_and_set_design="Test props",
        )
        assert description.scene_number == 1
        assert description.location == "Test Location"
        assert description.visual_description == "Test visual"
        assert description.camera_directions == "Static"
        assert description.lighting == "Bright"
        assert description.color_palette == "Warm"
        assert description.mood == "Happy"
        assert description.props_and_set_design == "Test props"

    def test_scene_description_to_dict(self):
        """Test scene description serialization."""
        description = SceneDescription(
            scene_number=1,
            location="Test Location",
            visual_description="Test visual",
            camera_directions="Static",
            lighting="Bright",
            color_palette="Warm",
            mood="Happy",
            props_and_set_design="Test props",
        )
        data = description.to_dict()
        assert data["scene_number"] == 1
        assert data["location"] == "Test Location"
        assert data["visual_description"] == "Test visual"
        assert data["camera_directions"] == "Static"
        assert data["lighting"] == "Bright"
        assert data["color_palette"] == "Warm"
        assert data["mood"] == "Happy"
        assert data["props_and_set_design"] == "Test props"


class TestSummary:
    """Tests for the Summary model."""

    def test_create_summary(self):
        """Test creating a summary."""
        summary = Summary(
            title="Test Movie",
            logline="Test logline",
            genre="Drama",
            summary="Test summary",
            key_themes=["test"],
            target_audience="Adults",
            comparable_films=["Test Film"],
            rating="PG-13",
        )
        assert summary.title == "Test Movie"
        assert summary.logline == "Test logline"
        assert summary.genre == "Drama"
        assert summary.summary == "Test summary"
        assert summary.key_themes == ["test"]
        assert summary.target_audience == "Adults"
        assert summary.comparable_films == ["Test Film"]
        assert summary.rating == "PG-13"

    def test_summary_to_dict(self):
        """Test summary serialization."""
        summary = Summary(
            title="Test Movie",
            logline="Test logline",
            genre="Drama",
            summary="Test summary",
            key_themes=["test"],
            target_audience="Adults",
            comparable_films=["Test Film"],
            rating="PG-13",
        )
        data = summary.to_dict()
        assert data["title"] == "Test Movie"
        assert data["logline"] == "Test logline"
        assert data["genre"] == "Drama"
        assert data["summary"] == "Test summary"
        assert data["key_themes"] == ["test"]
        assert data["target_audience"] == "Adults"
        assert data["comparable_films"] == ["Test Film"]
        assert data["rating"] == "PG-13"


class TestMusicCue:
    """Tests for the MusicCue model."""

    def test_create_music_cue(self):
        """Test creating a music cue."""
        cue = MusicCue(
            start_time="0:00",
            end_time="0:30",
            instrumentation="Piano",
            tempo="Slow",
            mood="Sad",
            volume="Medium",
        )
        assert cue.start_time == "0:00"
        assert cue.end_time == "0:30"
        assert cue.instrumentation == "Piano"
        assert cue.tempo == "Slow"
        assert cue.mood == "Sad"
        assert cue.volume == "Medium"

    def test_music_cue_to_dict(self):
        """Test music cue serialization."""
        cue = MusicCue(
            start_time="0:00",
            end_time="0:30",
            instrumentation="Piano",
            tempo="Slow",
            mood="Sad",
            volume="Medium",
        )
        data = cue.to_dict()
        assert data["start_time"] == "0:00"
        assert data["end_time"] == "0:30"
        assert data["instrumentation"] == "Piano"
        assert data["tempo"] == "Slow"
        assert data["mood"] == "Sad"
        assert data["volume"] == "Medium"


class TestPostProductionNote:
    """Tests for the PostProductionNote model."""

    def test_create_post_production_note(self):
        """Test creating a post-production note."""
        note = PostProductionNote(
            scene_number=1,
            action="Color grading",
            notes="Test notes",
            requirements=["Test requirement"],
            timeline="1 week",
            quality_checks=["Test check"],
        )
        assert note.scene_number == 1
        assert note.action == "Color grading"
        assert note.notes == "Test notes"
        assert note.requirements == ["Test requirement"]
        assert note.timeline == "1 week"
        assert note.quality_checks == ["Test check"]

    def test_post_production_note_to_dict(self):
        """Test post-production note serialization."""
        note = PostProductionNote(
            scene_number=1,
            action="Color grading",
            notes="Test notes",
            requirements=["Test requirement"],
            timeline="1 week",
            quality_checks=["Test check"],
        )
        data = note.to_dict()
        assert data["scene_number"] == 1
        assert data["action"] == "Color grading"
        assert data["notes"] == "Test notes"
        assert data["requirements"] == ["Test requirement"]
        assert data["timeline"] == "1 week"
        assert data["quality_checks"] == ["Test check"]


class TestMarketingMaterial:
    """Tests for the MarketingMaterial model."""

    def test_create_marketing_material(self):
        """Test creating a marketing material."""
        material = MarketingMaterial(
            tagline="Test tagline",
            poster_description="Test poster",
            social_media=[],
            press_release="Test press release",
        )
        assert material.tagline == "Test tagline"
        assert material.poster_description == "Test poster"
        assert material.social_media == []
        assert material.press_release == "Test press release"

    def test_marketing_material_to_dict(self):
        """Test marketing material serialization."""
        material = MarketingMaterial(
            tagline="Test tagline",
            poster_description="Test poster",
            social_media=[],
            press_release="Test press release",
        )
        data = material.to_dict()
        assert data["tagline"] == "Test tagline"
        assert data["poster_description"] == "Test poster"
        assert data["social_media"] == []
        assert data["press_release"] == "Test press release"


class TestDistributionStrategy:
    """Tests for the DistributionStrategy model."""

    def test_create_distribution_strategy(self):
        """Test creating a distribution strategy."""
        strategy = DistributionStrategy(
            platforms=["Netflix"],
            release_strategy="Test strategy",
            target_audience="Adults",
            estimated_budget="Test budget",
        )
        assert strategy.platforms == ["Netflix"]
        assert strategy.release_strategy == "Test strategy"
        assert strategy.target_audience == "Adults"
        assert strategy.estimated_budget == "Test budget"

    def test_distribution_strategy_to_dict(self):
        """Test distribution strategy serialization."""
        strategy = DistributionStrategy(
            platforms=["Netflix"],
            release_strategy="Test strategy",
            target_audience="Adults",
            estimated_budget="Test budget",
        )
        data = strategy.to_dict()
        assert data["platforms"] == ["Netflix"]
        assert data["release_strategy"] == "Test strategy"
        assert data["target_audience"] == "Adults"
        assert data["estimated_budget"] == "Test budget"
