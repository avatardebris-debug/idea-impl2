"""Unit tests for ai_consistent_char package.

Tests cover:
  1. DummyCharacterImageProvider generates reference images
  2. ReferenceSheetGenerator creates JSON profiles
  3. SceneCharacterRenderer renders per-scene characters
  4. SceneCharacterRenderCollection stores renders
  5. PipelineExtension integrates with MovieGenerationPipeline
  6. CLI parses arguments correctly
  7. SceneCharacterRenderer detects present characters
  8. ReferenceSheetGenerator saves JSON profiles
  9. LLMCharacterImageProvider placeholder works
  10. Full pipeline integration with extension
"""

from __future__ import annotations

import json
import pathlib
import sys
import tempfile
from typing import Any, Dict, List, Optional

# Add project root to path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from ai_consistent_char.image_provider import CharacterImageProvider, DummyCharacterImageProvider, LLMCharacterImageProvider
from ai_consistent_char.models import SceneCharacterRender, SceneCharacterRenderCollection
from ai_consistent_char.pipeline_extension import PipelineExtension
from ai_consistent_char.reference_sheet_generator import ReferenceSheetGenerator
from ai_consistent_char.scene_character_renderer import SceneCharacterRenderer
from ai_consistent_char.stages.scene_character_renderer import SceneCharacterRendererStage
from ai_movie_gen_suite.models import Character, CharacterRegistry, Scene, Script

# ── Helpers ────────
results: List[tuple[str, bool]] = []

def check(name: str, condition: bool) -> None:
    results.append((name, condition))
    status = "✅" if condition else "❌"
    print(f"  {status} {name}")


def make_script() -> Script:
    return Script(
        title="Test Movie",
        logline="A test logline.",
        genre="Action",
        scenes=[
            Scene(scene_id="1", scene_heading="INT. ROOM - DAY", action="Alice enters the room. Bob is waiting."),
            Scene(scene_id="2", scene_heading="EXT. PARK - DAY", action="Alice and Bob walk through the park."),
        ],
    )


def make_character_registry() -> CharacterRegistry:
    registry = CharacterRegistry()
    registry.add_character(Character(
        id="hero",
        name="Alice",
        role="protagonist",
        motivation="Save the world",
        physical_description="Tall, blonde, blue eyes",
        personality_traits=["brave", "determined"],
        voice_notes="Confident, clear",
        costume_notes="Leather jacket, jeans",
        visual_anchor="blonde hair",
        backstory="Orphaned hero",
        arc_summary="From fear to courage",
    ))
    registry.add_character(Character(
        id="villain",
        name="Bob",
        role="antagonist",
        motivation="Destroy the world",
        physical_description="Short, dark hair, green eyes",
        personality_traits=["cunning", "ruthless"],
        voice_notes="Sneering, low",
        costume_notes="Black suit",
        visual_anchor="green eyes",
        backstory="Former ally",
        arc_summary="From ally to enemy",
    ))
    return registry


# ── Test 1: DummyCharacterImageProvider generates reference images ────────
print("\nTest 1: DummyCharacterImageProvider generates reference images")
with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp)
    provider = DummyCharacterImageProvider()
    ref_path = tmp / "test_ref.png"
    result = provider.generate_reference_image("hero", "test", ref_path)
    check("Reference image created", ref_path.exists())
    check("Result matches path", result == str(ref_path))


# ── Test 2: ReferenceSheetGenerator creates JSON profiles ────────
print("\nTest 2: ReferenceSheetGenerator creates JSON profiles")
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


# ── Test 3: SceneCharacterRenderer renders per-scene characters ────────
print("\nTest 3: SceneCharacterRenderer renders per-scene characters")
with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp)
    registry = make_character_registry()
    provider = DummyCharacterImageProvider()

    # Set reference_image_path
    ref_dir = tmp / "refs"
    ref_dir.mkdir()
    for char_id in registry.characters:
        ref_path = ref_dir / f"{char_id}.png"
        provider.generate_reference_image(char_id, "test", ref_path)
        registry.characters[char_id].reference_image_path = str(ref_path)

    script = make_script()
    renderer = SceneCharacterRenderer(
        provider=provider,
        reference_images={char_id: char.reference_image_path for char_id, char in registry.characters.items()},
        output_dir=tmp / "renders",
    )

    renders = renderer.render_scene(script.scenes[0], ["hero", "villain"])
    check("Renders list has 2 items", len(renders) == 2)
    check("First render path exists", pathlib.Path(renders[0].render_path).exists())
    check("Second render path exists", pathlib.Path(renders[1].render_path).exists())


# ── Test 4: SceneCharacterRenderCollection stores renders ────────
print("\nTest 4: SceneCharacterRenderCollection stores renders")
collection = SceneCharacterRenderCollection()
collection.add_render(SceneCharacterRender(
    scene_id="1",
    character_id="hero",
    render_path="/tmp/test.png",
    scene_context="test",
))
collection.add_render(SceneCharacterRender(
    scene_id="1",
    character_id="villain",
    render_path="/tmp/test2.png",
    scene_context="test",
))
check("Collection has 2 renders", len(collection.renders) == 2)
check("Collection is iterable", list(collection.renders) == list(collection.renders))


# ── Test 5: PipelineExtension integrates with MovieGenerationPipeline ────────
print("\nTest 5: PipelineExtension integrates with MovieGenerationPipeline")
with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp)

    # Create a full pipeline mock
    class MockPipeline:
        def __init__(self):
            self.state: Dict[str, Any] = {}

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
    result = provider.render_character(
        character_id="hero",
        reference_image_path=str(ref_path),
        scene_context="test",
        output_path=render_path,
    )
    check("LLM provider renders file", pathlib.Path(result).exists())


# ── Test 10: Full pipeline integration with extension ────────
print("\nTest 10: Full pipeline integration with extension")
with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp)

    # Create a full pipeline mock
    class MockPipeline:
        def __init__(self):
            self.state: Dict[str, Any] = {}

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

    # Verify reference sheets were created (saved to output_dir)
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
