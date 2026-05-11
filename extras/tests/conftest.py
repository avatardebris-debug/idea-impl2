"""Pytest configuration and fixtures for ai_movie_gen_suite tests."""

import pytest


@pytest.fixture
def sample_project():
    """Create a sample Project for testing."""
    from ai_movie_gen_suite.models import Project

    return Project(
        title="Test Movie",
        logline="A test logline",
        genre="drama",
        tone="dark",
        project_id="test-id",
    )


@pytest.fixture
def sample_beat_sheet():
    """Create a sample BeatSheet for testing."""
    from ai_movie_gen_suite.models import Beat, BeatSheet

    return BeatSheet(
        beats=[
            Beat(id="1", act=1, description="Act 1 beat"),
            Beat(id="2", act=2, description="Act 2 beat"),
        ]
    )


@pytest.fixture
def sample_character_registry():
    """Create a sample CharacterRegistry for testing."""
    from ai_movie_gen_suite.models import Character, CharacterRegistry

    return CharacterRegistry(
        characters=[
            Character(id="char1", name="Hero", description="Protagonist"),
            Character(id="char2", name="Villain", description="Antagonist"),
        ]
    )


@pytest.fixture
def sample_script():
    """Create a sample Script for testing."""
    from ai_movie_gen_suite.models import DialogueLine, Scene, Script

    return Script(
        logline="A test logline",
        scenes=[
            Scene(
                scene_id="1",
                scene_heading="INT. ROOM - DAY",
                action="Action.",
                characters_present=["Hero"],
                dialogue_lines=[
                    DialogueLine(
                        character_id="char1",
                        character_name="Hero",
                        text="Hello!",
                        parenthetical="smiling",
                    )
                ],
            )
        ],
    )


@pytest.fixture
def sample_project_with_data(sample_project, sample_beat_sheet, sample_character_registry, sample_script):
    """Create a sample Project with all data populated."""
    sample_project.beats = sample_beat_sheet
    sample_project.characters = sample_character_registry
    sample_project.script = sample_script
    return sample_project
