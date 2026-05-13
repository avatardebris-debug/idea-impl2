"""Unit tests for ai_consistent_char package.

Tests cover:
  1. DummyCharacterImageProvider generates reference images
  2. ReferenceSheetGenerator creates sheets for all characters
  3. SceneCharacterRenderer renders characters per scene
  4. SceneCharacterRenderCollection stores and retrieves renders
  5. PipelineExtension integrates with MovieGenerationPipeline
  6. CLI parses arguments correctly
  7. SceneCharacterRenderer detects present characters
  8. ReferenceSheetGenerator saves JSON profiles
  9. LLMCharacterImageProvider placeholder works
 10. Full pipeline integration with extension
"""

import json
import pathlib
import sys
import tempfile
import textwrap

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from ai_consistent_char.image_provider import (
    CharacterImageProvider,
    DummyCharacterImageProvider,
    LLMCharacterImageProvider,
)
from ai_consistent_char.models import SceneCharacterRender, SceneCharacterRenderCollection
from ai_consistent_char.pipeline_extension import PipelineExtension
from ai_consistent_char.reference_sheet_generator import ReferenceSheetGenerator
from ai_consistent_char.scene_character_renderer import SceneCharacterRenderer
from ai_consistent_char.stages.scene_character_renderer import SceneCharacterRendererStage

from ai_movie_gen_suite.models import Character, CharacterRegistry, Scene, Script


# ── Test harness ────────────────────────────────────────────────────────

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
    """Create a test CharacterRegistry with 2 characters."""
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
        }
    )


def make_script():
    """Create a test Script with 2 scenes."""
    return Script(
        title="Test Movie",
        logline="A hero fights a villain.",
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
                action="Alice climbs the mountain. Bob pursues her.",
            ),
        ],
    )


# ── Test 1: DummyCharacterImageProvider generates reference images ────────
print("\nTest 1: DummyCharacterImageProvider generates reference images")
with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp)
    provider = DummyCharacterImageProvider()
    ref_path = tmp / "ref.png"
    result = provider.generate_reference_image(
        character_id="hero",
        visual_anchor_text="red hair",
        output_path=ref_path,
    )
    check("Reference image file exists", ref_path.exists())
    check("Returned path matches", result == str(ref_path))


# ── Test 2: ReferenceSheetGenerator creates sheets for all characters ─────
print("\nTest 2: ReferenceSheetGenerator creates sheets for all characters")
with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp)
    registry = make_character_registry()
    provider = DummyCharacterImageProvider()
    generator = ReferenceSheetGenerator(provider, tmp)
    image_paths = generator.generate_for_registry(registry)
    check("Generated 2 reference images", len(image_paths) == 2)
    check("hero image exists", (tmp / "hero_reference.png").exists())
    check("villain image exists", (tmp / "villain_reference.png").exists())


# ── Test 3: SceneCharacterRenderer renders characters per scene ────────
print("\nTest 3: SceneCharacterRenderer renders characters per scene")
with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp)
    registry = make_character_registry()
    script = make_script()

    # Set reference_image_path for each character
    ref_dir = tmp / "refs"
    ref_dir.mkdir()
    for char_id in registry.characters:
        ref_path = ref_dir / f"{char_id}.png"
        provider = DummyCharacterImageProvider()
        provider.generate_reference_image(char_id, "test", ref_path)
        registry.characters[char_id].reference_image_path = str(ref_path)

    # Build reference-image lookup from registry
    ref_images = {
        char_id: char.reference_image_path
        for char_id, char in registry.characters.items()
        if char.reference_image_path
    }

    provider = DummyCharacterImageProvider()
    output_dir = tmp / "renders"
    renderer = SceneCharacterRenderer(provider, ref_images, output_dir)

    # Render scene 1
    renders = renderer.render_scene(script.scenes[0], ["hero", "villain"])
    check("Rendered 2 characters for scene 1", len(renders) == 2)
    check("All renders have scene_id='1'", all(r.scene_id == "1" for r in renders))


# ── Test 4: SceneCharacterRenderCollection stores and retrieves renders ─────
print("\nTest 4: SceneCharacterRenderCollection stores and retrieves renders")
collection = SceneCharacterRenderCollection()
r1 = SceneCharacterRender(scene_id="1", character_id="hero", render_path="/a.png")
r2 = SceneCharacterRender(scene_id="1", character_id="villain", render_path="/b.png")
r3 = SceneCharacterRender(scene_id="2", character_id="hero", render_path="/c.png")
collection.add_render(r1)
collection.add_render(r2)
collection.add_render(r3)
check("Collection has 3 renders", len(collection.renders) == 3)
check("get_renders_for_scene('1') returns 2", len(collection.get_renders_for_scene("1")) == 2)
check("get_renders_for_scene('2') returns 1", len(collection.get_renders_for_scene("2")) == 1)
check("to_dict() returns dict", isinstance(collection.to_dict(), dict))


# ── Test 5: PipelineExtension integrates with MovieGenerationPipeline ─────
print("\nTest 5: PipelineExtension integrates with MovieGenerationPipeline")
with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp)

    # Mock pipeline - FIX: use instance attribute to avoid shared mutable default
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
    check("Collection has renders", len(collection.renders) > 0)


# ── Test 6: CLI parses arguments correctly ────────
print("\nTest 6: CLI parses arguments correctly")
from ai_consistent_char.cli import parse_args

args = parse_args([
    "--logline", "Test logline",
    "--title", "Test Title",
    "--genre", "Action",
    "--generate-scene-renders",
    "--output-dir", "/tmp/test_out",
])
check("logline parsed", args.logline == "Test logline")
check("title parsed", args.title == "Test Title")
check("genre parsed", args.genre == "Action")
check("generate_scene_renders is True", args.generate_scene_renders is True)
check("output_dir parsed", args.output_dir == "/tmp/test_out")


# ── Test 7: SceneCharacterRenderer detects present characters ────────
print("\nTest 7: SceneCharacterRenderer detects present characters")
with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp)
    registry = make_character_registry()
    script = make_script()

    renderer = SceneCharacterRenderer(
        provider=DummyCharacterImageProvider(),
        reference_images={},
        output_dir=tmp,
    )

    # Scene 1 has both Alice and Bob
    present = renderer._detect_present_characters(script.scenes[0], registry)
    check("Scene 1 detects both characters", set(present) == {"hero", "villain"})

    # Scene 2 has Alice and Bob
    present = renderer._detect_present_characters(script.scenes[1], registry)
    check("Scene 2 detects both characters", set(present) == {"hero", "villain"})


# ── Test 8: ReferenceSheetGenerator saves JSON profiles ────────
print("\nTest 8: ReferenceSheetGenerator saves JSON profiles")
with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp)
    registry = make_character_registry()
    provider = DummyCharacterImageProvider()
    generator = ReferenceSheetGenerator(provider, tmp)
    generator.generate_for_registry(registry)

    # Check hero profile
    hero_profile = json.loads((tmp / "hero_profile.json").read_text())
    check("hero_profile.json has 'name'", hero_profile.get("name") == "Alice")
    check("hero_profile.json has 'id'", hero_profile.get("id") == "hero")
    check("hero_profile.json has 'reference_image'", "hero_reference.png" in hero_profile.get("reference_image", ""))


# ── Test 9: LLMCharacterImageProvider placeholder works ────────
print("\nTest 9: LLMCharacterImageProvider placeholder works")
with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp)
    provider = LLMCharacterImageProvider(llm_client=None)
    ref_path = tmp / "llm_ref.png"
    result = provider.generate_reference_image("hero", "test", ref_path)
    check("LLM provider generates file", ref_path.exists())
    check("LLM provider returns path", result == str(ref_path))

    render_path = tmp / "llm_render.png"
    render_path = tmp / "llm_render.png"
    result = provider.render_character("hero", str(ref_path), "INT. ROOM", render_path)
    check("LLM provider renders file", pathlib.Path(result).exists())


# ── Test 10: Full pipeline integration with extension ────────
print("\nTest 10: Full pipeline integration with extension")
with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp)

    # Create a full pipeline mock - FIX: use instance attribute
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

    check("Full integration: collection not None", collection is not None)
    check("Full integration: has renders", len(collection.renders) > 0)

    # Generate reference sheets (separate step, not part of the stage)
    ref_generator = ReferenceSheetGenerator(provider, tmp)
    ref_generator.generate_for_registry(registry)

    # Verify reference sheets were created
    check("Full integration: hero ref sheet exists", (tmp / "hero_reference.png").exists())
    check("Full integration: villain ref sheet exists", (tmp / "villain_reference.png").exists())
    check("Full integration: hero profile exists", (tmp / "hero_profile.json").exists())


# ── Summary ────────────────────────────────────────────────────────
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
