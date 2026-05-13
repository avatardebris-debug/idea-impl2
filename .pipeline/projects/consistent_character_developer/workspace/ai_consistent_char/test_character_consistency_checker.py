"""Tests for ai_consistent_char package.

These tests validate the consistent character reference sheet pipeline:
- CharacterVisualProfile and SceneCharacterRender data models
- SceneCharacterRenderCollection container
- ReferenceSheetGenerator
- SceneCharacterRenderer
- CharacterConsistencyChecker
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


@pytest.fixture
def mock_provider():
    """Return a mock CharacterImageProvider."""
    provider = MagicMock()
    provider.generate_reference_image.return_value = "/tmp/ref.png"
    provider.render_character.return_value = "/tmp/render.png"
    return provider


# ---------------------------------------------------------------------------
# Tests: CharacterVisualProfile (models.py)
# ---------------------------------------------------------------------------


def test_character_visual_profile_serialization(temp_dir):
    """CharacterVisualProfile.model_dump() returns a dict, not a string."""
    from ai_consistent_char.models import CharacterVisualProfile

    profile = CharacterVisualProfile(
        character_id="char_001",
        visual_anchor_text="tall man with red hair",
        status="generated",
        seed=42,
    )
    dump = profile.model_dump()
    assert isinstance(dump, dict)
    assert dump["character_id"] == "char_001"
    assert dump["visual_anchor_text"] == "tall man with red hair"
    assert dump["status"] == "generated"
    assert dump["seed"] == 42


def test_character_visual_profile_default_status(temp_dir):
    """Default status should be 'pending'."""
    from ai_consistent_char.models import CharacterVisualProfile

    profile = CharacterVisualProfile(character_id="char_002")
    assert profile.status == "pending"


def test_character_visual_profile_with_seed(temp_dir):
    """Seed field should be optional and stored correctly."""
    from ai_consistent_char.models import CharacterVisualProfile

    profile = CharacterVisualProfile(
        character_id="char_003",
        seed=12345,
    )
    assert profile.seed == 12345


# ---------------------------------------------------------------------------
# Tests: SceneCharacterRender (models.py)
# ---------------------------------------------------------------------------


def test_scene_character_render_model_dump(temp_dir):
    """SceneCharacterRender.model_dump() returns a dict."""
    from ai_consistent_char.models import SceneCharacterRender

    render = SceneCharacterRender(
        scene_id="scene_001",
        character_id="char_001",
        render_path="/tmp/render.png",
        scene_context="INT. COFFEE SHOP - DAY",
    )
    dump = render.model_dump()
    assert isinstance(dump, dict)
    assert dump["scene_id"] == "scene_001"
    assert dump["character_id"] == "char_001"
    assert dump["render_path"] == "/tmp/render.png"
    assert dump["scene_context"] == "INT. COFFEE SHOP - DAY"


# ---------------------------------------------------------------------------
# Tests: SceneCharacterRenderCollection (models.py)
# ---------------------------------------------------------------------------


def test_scene_character_render_collection_add_render(temp_dir):
    """add_render() takes a SceneCharacterRender object."""
    from ai_consistent_char.models import SceneCharacterRender, SceneCharacterRenderCollection

    collection = SceneCharacterRenderCollection()
    render = SceneCharacterRender(
        scene_id="scene_001",
        character_id="char_001",
        render_path="/tmp/render.png",
        scene_context="INT. COFFEE SHOP - DAY",
    )
    collection.add_render(render)
    assert len(collection) == 1


def test_scene_character_render_collection_get_renders_for_scene(temp_dir):
    """get_renders_for_scene() returns a list of renders for a given scene."""
    from ai_consistent_char.models import SceneCharacterRender, SceneCharacterRenderCollection

    collection = SceneCharacterRenderCollection()
    render1 = SceneCharacterRender(
        scene_id="scene_001",
        character_id="char_001",
        render_path="/tmp/render1.png",
        scene_context="INT. COFFEE SHOP - DAY",
    )
    render2 = SceneCharacterRender(
        scene_id="scene_001",
        character_id="char_002",
        render_path="/tmp/render2.png",
        scene_context="INT. COFFEE SHOP - DAY",
    )
    render3 = SceneCharacterRender(
        scene_id="scene_002",
        character_id="char_001",
        render_path="/tmp/render3.png",
        scene_context="EXT. PARK - NIGHT",
    )
    collection.add_render(render1)
    collection.add_render(render2)
    collection.add_render(render3)

    scene_001_renders = collection.get_renders_for_scene("scene_001")
    assert len(scene_001_renders) == 2
    assert all(r.scene_id == "scene_001" for r in scene_001_renders)


def test_scene_character_render_collection_to_dict(temp_dir):
    """to_dict() returns a dict with a 'renders' key containing a list."""
    from ai_consistent_char.models import SceneCharacterRender, SceneCharacterRenderCollection

    collection = SceneCharacterRenderCollection()
    render = SceneCharacterRender(
        scene_id="scene_001",
        character_id="char_001",
        render_path="/tmp/render.png",
        scene_context="INT. COFFEE SHOP - DAY",
    )
    collection.add_render(render)

    d = collection.to_dict()
    assert isinstance(d, dict)
    assert "renders" in d
    assert isinstance(d["renders"], list)
    assert len(d["renders"]) == 1
    assert d["renders"][0]["scene_id"] == "scene_001"


def test_scene_character_render_collection_iteration(temp_dir):
    """Collection should be iterable, yielding SceneCharacterRender objects."""
    from ai_consistent_char.models import SceneCharacterRender, SceneCharacterRenderCollection

    collection = SceneCharacterRenderCollection()
    render1 = SceneCharacterRender(
        scene_id="scene_001",
        character_id="char_001",
        render_path="/tmp/render1.png",
        scene_context="INT. COFFEE SHOP - DAY",
    )
    render2 = SceneCharacterRender(
        scene_id="scene_002",
        character_id="char_002",
        render_path="/tmp/render2.png",
        scene_context="EXT. PARK - NIGHT",
    )
    collection.add_render(render1)
    collection.add_render(render2)

    renders = list(collection)
    assert len(renders) == 2
    assert all(isinstance(r, SceneCharacterRender) for r in renders)


def test_scene_character_render_collection_empty_collection(temp_dir):
    """Empty collection should be falsy."""
    from ai_consistent_char.models import SceneCharacterRenderCollection

    collection = SceneCharacterRenderCollection()
    assert not collection
    assert len(collection) == 0


def test_scene_character_render_collection_len(temp_dir):
    """len() should return the number of renders."""
    from ai_consistent_char.models import SceneCharacterRender, SceneCharacterRenderCollection

    collection = SceneCharacterRenderCollection()
    assert len(collection) == 0

    render = SceneCharacterRender(
        scene_id="scene_001",
        character_id="char_001",
        render_path="/tmp/render.png",
        scene_context="INT. COFFEE SHOP - DAY",
    )
    collection.add_render(render)
    assert len(collection) == 1


def test_scene_character_render_collection_bool(temp_dir):
    """Collection should be truthy when it has renders."""
    from ai_consistent_char.models import SceneCharacterRender, SceneCharacterRenderCollection

    collection = SceneCharacterRenderCollection()
    assert not bool(collection)

    render = SceneCharacterRender(
        scene_id="scene_001",
        character_id="char_001",
        render_path="/tmp/render.png",
        scene_context="INT. COFFEE SHOP - DAY",
    )
    collection.add_render(render)
    assert bool(collection)


# ---------------------------------------------------------------------------
# Tests: ReferenceSheetGenerator (reference_sheet_generator.py)
# ---------------------------------------------------------------------------


def test_reference_sheet_generator_initialization(temp_dir, mock_provider):
    """ReferenceSheetGenerator takes a provider and output_dir."""
    from ai_consistent_char.reference_sheet_generator import ReferenceSheetGenerator

    generator = ReferenceSheetGenerator(
        provider=mock_provider,
        output_dir=temp_dir / "refs",
    )
    assert generator.output_dir == temp_dir / "refs"
    assert generator.output_dir.exists()


def test_reference_sheet_generator_generate_for_registry(temp_dir, mock_provider):
    """generate_for_registry() generates images and profiles for all characters."""
    from ai_consistent_char.reference_sheet_generator import ReferenceSheetGenerator
    from ai_movie_gen_suite.models import Character, CharacterRegistry

    generator = ReferenceSheetGenerator(
        provider=mock_provider,
        output_dir=temp_dir / "refs",
    )

    registry = CharacterRegistry()
    registry.add_character(
        Character(
            id="char_001",
            name="Alice",
            role="PROTAGONIST",
            physical_description="tall woman with red hair",
            personality_traits=["brave", "curious"],
            motivation="Find the treasure",
            voice_notes="Slightly raspy",
            costume_notes="Leather jacket",
            visual_anchor="red hair, leather jacket",
            backstory="Former explorer",
            arc_summary="Learns to trust others",
        )
    )
    registry.add_character(
        Character(
            id="char_002",
            name="Bob",
            role="ANTAGONIST",
            physical_description="short man with glasses",
            personality_traits=["cunning", "ruthless"],
            motivation="Take over the world",
            voice_notes="Deep, menacing",
            costume_notes="Black suit",
            visual_anchor="glasses, black suit",
            backstory="Former CEO",
            arc_summary="Redeemed by love",
        )
    )

    image_paths = generator.generate_for_registry(registry)

    assert len(image_paths) == 2
    assert "char_001" in image_paths
    assert "char_002" in image_paths

    # Check that profile JSON files were created
    profile_path = temp_dir / "refs" / "char_001_profile.json"
    assert profile_path.exists()
    profile = json.loads(profile_path.read_text())
    assert profile["name"] == "Alice"
    assert profile["id"] == "char_001"


# ---------------------------------------------------------------------------
# Tests: SceneCharacterRenderer (scene_character_renderer.py)
# ---------------------------------------------------------------------------


def test_scene_character_renderer_render_scene(temp_dir, mock_provider):
    """render_scene() renders characters for a single scene."""
    from ai_consistent_char.scene_character_renderer import SceneCharacterRenderer
    from ai_movie_gen_suite.models import Scene

    renderer = SceneCharacterRenderer(
        provider=mock_provider,
        reference_images={"char_001": "/tmp/ref1.png", "char_002": "/tmp/ref2.png"},
        output_dir=temp_dir / "renders",
    )

    scene = Scene(
        scene_id="scene_001",
        scene_heading="INT. COFFEE SHOP - DAY",
        action="Alice and Bob sit at a table.",
    )

    renders = renderer.render_scene(scene, ["char_001", "char_002"])
    assert len(renders) == 2
    assert all(r.scene_id == "scene_001" for r in renders)


def test_scene_character_renderer_render_script(temp_dir, mock_provider):
    """render_script() renders all characters in all scenes."""
    from ai_consistent_char.scene_character_renderer import SceneCharacterRenderer
    from ai_movie_gen_suite.models import Character, CharacterRegistry, Script, Scene

    renderer = SceneCharacterRenderer(
        provider=mock_provider,
        reference_images={"char_001": "/tmp/ref1.png"},
        output_dir=temp_dir / "renders",
    )

    script = Script(
        title="Test Script",
        logline="A test script for character consistency.",
        genre="Drama",
        scenes=[
            Scene(
                scene_id="scene_001",
                scene_heading="INT. COFFEE SHOP - DAY",
                action="Alice enters the coffee shop.",
            ),
            Scene(
                scene_id="scene_002",
                scene_heading="EXT. PARK - NIGHT",
                action="Alice walks through the park.",
            ),
        ],
    )

    registry = CharacterRegistry()
    registry.add_character(
        Character(
            id="char_001",
            name="Alice",
            role="PROTAGONIST",
            physical_description="tall woman with red hair",
            personality_traits=["brave"],
            motivation="Find the treasure",
            voice_notes="Slightly raspy",
            costume_notes="Leather jacket",
            visual_anchor="red hair",
            backstory="Former explorer",
            arc_summary="Learns to trust others",
        )
    )

    collection = renderer.render_script(script, registry)
    assert len(collection) == 2  # One render per scene (Alice appears in both)
