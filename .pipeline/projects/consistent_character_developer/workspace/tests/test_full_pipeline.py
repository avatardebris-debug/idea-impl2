"""Full pipeline integration test for ai_consistent_char.

Tests the complete pipeline from script generation through character consistency
to scene rendering, verifying end-to-end functionality.
"""

import json
import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from ai_consistent_char.image_provider import DummyCharacterImageProvider
from ai_consistent_char.pipeline_extension import PipelineExtension
from ai_consistent_char.reference_sheet_generator import ReferenceSheetGenerator
from ai_consistent_char.scene_character_renderer import SceneCharacterRenderer
from ai_consistent_char.scene_description_engine import SceneDescriptionEngine
from ai_movie_gen_suite.models import Character, CharacterRegistry, Scene, Script


# ── Test harness ────────

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"
results = []


def check(name, condition, detail=""):
    ok = bool(condition)
    status = PASS if ok else FAIL
    print(f"  [{status}] {name}")
    if not ok and detail:
        print(f"         {detail}")
    results.append((name, ok))
    return ok


def make_character_registry():
    """Create a test CharacterRegistry with 3 characters."""
    return CharacterRegistry(
        characters={
            "hero": Character(
                id="hero",
                name="Alice",
                role="protagonist",
                motivation="Find the lost artifact",
                physical_description="Tall, red hair, green eyes",
                personality_traits=["brave", "curious"],
                voice_notes="Strong, confident",
                costume_notes="Leather jacket, boots",
                visual_anchor="red hair and green eyes",
                backstory="Explorer and adventurer",
                arc_summary="From lost to found",
                reference_image_path="",
            ),
            "villain": Character(
                id="villain",
                name="Bob",
                role="antagonist",
                motivation="Steal the artifact",
                physical_description="Short, bald, scarred",
                personality_traits=["cunning", "ruthless"],
                voice_notes="Deep, menacing",
                costume_notes="Black suit, sunglasses",
                visual_anchor="bald head and scar",
                backstory="Former explorer turned thief",
                arc_summary="From power to redemption",
                reference_image_path="",
            ),
            "ally": Character(
                id="ally",
                name="Charlie",
                role="supporting",
                motivation="Help Alice find the artifact",
                physical_description="Medium height, brown hair, glasses",
                personality_traits=["loyal", "resourceful"],
                voice_notes="Friendly, energetic",
                costume_notes="Hiking gear, backpack",
                visual_anchor="glasses and backpack",
                backstory="Old friend of Alice",
                arc_summary="From helper to hero",
                reference_image_path="",
            ),
        }
    )


def make_script():
    """Create a test Script with 3 scenes."""
    return Script(
        title="Test Movie",
        logline="A hero fights a villain with help from an ally.",
        genre="Action",
        scenes=[
            Scene(
                scene_id="1",
                scene_heading="INT. CAVE - DAY",
                action="Alice enters the cave. Bob watches from the shadows.",
            ),
            Scene(
                scene_id="2",
                scene_heading="EXT. MOUNTAIN - NIGHT",
                action="Alice climbs the mountain. Bob pursues her. Charlie helps Alice.",
            ),
            Scene(
                scene_id="3",
                scene_heading="INT. CAVE - NIGHT",
                action="Alice and Charlie confront Bob. They fight.",
            ),
        ],
    )


# ── Test 1: Full pipeline integration ──────
print("\nTest 1: Full pipeline integration")
with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp)

    # Mock pipeline
    class MockPipeline:
        def __init__(self):
            self.state = {}

    pipeline = MockPipeline()
    extension = PipelineExtension(pipeline)
    provider = DummyCharacterImageProvider()
    extension.add_character_consistency(provider, tmp, generate_renders=True)

    script = make_script()
    registry = make_character_registry()

    # Set reference_image_path
    ref_dir = tmp / "refs"
    ref_dir.mkdir()
    for char_id in registry.characters:
        ref_path = ref_dir / f"{char_id}.png"
        provider.generate_reference_image(char_id, "test", ref_path)
        registry.characters[char_id].reference_image_path = str(ref_path)

    # Run character consistency
    collection = extension.run_character_consistency(script, registry)

    check("Collection not None", collection is not None)
    check("Collection has renders", len(collection.renders) > 0)

    # Generate reference sheets
    ref_generator = ReferenceSheetGenerator(provider, tmp)
    ref_generator.generate_for_registry(registry)

    # Verify reference sheets
    check("hero ref sheet exists", (tmp / "hero_reference.png").exists())
    check("villain ref sheet exists", (tmp / "villain_reference.png").exists())
    check("ally ref sheet exists", (tmp / "ally_reference.png").exists())
    check("hero profile exists", (tmp / "hero_profile.json").exists())
    check("villain profile exists", (tmp / "villain_profile.json").exists())
    check("ally profile exists", (tmp / "ally_profile.json").exists())


# ── Test 2: Scene description engine ──────
print("\nTest 2: Scene description engine")
registry = make_character_registry()
engine = SceneDescriptionEngine(registry)
script = make_script()

# Describe all scenes
all_descriptions = engine.describe_script(script)
check("All scenes described", len(all_descriptions) == 3)
check("Scene 1 has descriptions", len(all_descriptions.get("1", [])) > 0)
check("Scene 2 has descriptions", len(all_descriptions.get("2", [])) > 0)
check("Scene 3 has descriptions", len(all_descriptions.get("3", [])) > 0)

# Check individual scene descriptions
scene1_descs = all_descriptions.get("1", [])
if scene1_descs:
    desc = scene1_descs[0]
    check("Scene 1 description has scene_id", desc.scene_id == "1")
    check("Scene 1 description has character_id", desc.character_id in registry.characters)
    check("Scene 1 description has visual_cues", len(desc.visual_cues) > 0)


# ── Test 3: Scene character renderer ──────
print("\nTest 3: Scene character renderer")
with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp)
    registry = make_character_registry()
    script = make_script()

    # Set reference_image_path
    ref_dir = tmp / "refs"
    ref_dir.mkdir()
    for char_id in registry.characters:
        ref_path = ref_dir / f"{char_id}.png"
        provider = DummyCharacterImageProvider()
        provider.generate_reference_image(char_id, "test", ref_path)
        registry.characters[char_id].reference_image_path = str(ref_path)

    # Build reference-image lookup
    ref_images = {
        char_id: char.reference_image_path
        for char_id, char in registry.characters.items()
        if char.reference_image_path
    }

    output_dir = tmp / "renders"
    renderer = SceneCharacterRenderer(provider, ref_images, output_dir)

    # Render all scenes
    for scene in script.scenes:
        present = renderer._detect_present_characters(scene, registry)
        renders = renderer.render_scene(scene, present)
        check(f"Scene {scene.scene_id} rendered {len(renders)} characters", len(renders) > 0)


# ── Test 4: Pipeline extension integration ──────
print("\nTest 4: Pipeline extension integration")
with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp)

    class MockPipeline:
        def __init__(self):
            self.state = {}

    pipeline = MockPipeline()
    extension = PipelineExtension(pipeline)
    provider = DummyCharacterImageProvider()
    extension.add_character_consistency(provider, tmp, generate_renders=True)

    script = make_script()
    registry = make_character_registry()

    # Set reference_image_path
    ref_dir = tmp / "refs"
    ref_dir.mkdir()
    for char_id in registry.characters:
        ref_path = ref_dir / f"{char_id}.png"
        provider.generate_reference_image(char_id, "test", ref_path)
        registry.characters[char_id].reference_image_path = str(ref_path)

    collection = extension.run_character_consistency(script, registry)

    check("Extension returns collection", collection is not None)
    check("Extension has renders", len(collection.renders) > 0)

    # Verify collection structure
    check("Collection has to_dict", hasattr(collection, "to_dict"))
    check("Collection has get_renders_for_scene", hasattr(collection, "get_renders_for_scene"))


# ── Test 5: Reference sheet generator ──────
print("\nTest 5: Reference sheet generator")
with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp)
    registry = make_character_registry()
    provider = DummyCharacterImageProvider()
    generator = ReferenceSheetGenerator(provider, tmp)
    generator.generate_for_registry(registry)

    # Check all reference sheets
    for char_id in registry.characters:
        check(f"{char_id} ref sheet exists", (tmp / f"{char_id}_reference.png").exists())
        check(f"{char_id} profile exists", (tmp / f"{char_id}_profile.json").exists())

        # Verify profile content
        profile = json.loads((tmp / f"{char_id}_profile.json").read_text())
        check(f"{char_id} profile has name", profile.get("name") == registry.characters[char_id].name)
        check(f"{char_id} profile has id", profile.get("id") == char_id)


# ── Test 6: Error handling ──────
print("\nTest 6: Error handling")
with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp)

    # Test with empty registry
    empty_registry = CharacterRegistry(characters={})
    engine = SceneDescriptionEngine(empty_registry)
    script = make_script()
    descriptions = engine.describe_script(script)
    check("Empty registry returns empty descriptions", all(len(v) == 0 for v in descriptions.values()))

    # Test with missing character
    registry = make_character_registry()
    registry.characters["missing"] = Character(
        id="missing",
        name="Missing",
        role="unknown",
        motivation="",
        physical_description="",
        personality_traits=[],
        voice_notes="",
        costume_notes="",
        visual_anchor="",
        backstory="",
        arc_summary="",
        reference_image_path="",
    )
    engine = SceneDescriptionEngine(registry)
    descriptions = engine.describe_script(script)
    check("Missing character handled gracefully", len(descriptions) == 3)


# ── Summary ──
print(f"\n{'='*50}")
passed = sum(1 for _, ok in results if ok)
total = len(results)
color = "\033[32m" if passed == total else "\033[31m"
print(f"{color}{passed}/{total} tests passed\033[0m")
if passed < total:
    print("\nFailed tests:")
    for name, ok in results:
        if not ok:
            print(f"  - {name}")
    sys.exit(1)
else:
    print("All tests passed — ai_consistent_char is ready.")
