"""Integration tests for the consistent character developer pipeline.

Tests the full end-to-end flow:
  1. Character creation with visual anchors
  2. Reference sheet generation
  3. Scene character rendering
  4. Pipeline extension integration
  5. CLI argument parsing
  6. Multi-character consistency
  7. Scene context preservation
  8. Error handling for missing references
  9. Output directory structure
 10. Full pipeline mock integration
"""

import json
import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from ai_consistent_char.image_provider import DummyCharacterImageProvider
from ai_consistent_char.models import SceneCharacterRender, SceneCharacterRenderCollection
from ai_consistent_char.pipeline_extension import PipelineExtension
from ai_consistent_char.reference_sheet_generator import ReferenceSheetGenerator
from ai_consistent_char.scene_character_renderer import SceneCharacterRenderer
from ai_consistent_char.stages.scene_character_renderer import SceneCharacterRendererStage

from ai_movie_gen_suite.models import Character, CharacterRegistry, Scene, Script


# ── Test harness ───────────────────────────────────────────────────────

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


def make_character_registry(n_characters=3):
    """Create a test CharacterRegistry with n_characters characters."""
    characters = {}
    for i in range(n_characters):
        char_id = f"char_{i}"
        characters[char_id] = Character(
            id=char_id,
            name=f"Character {i}",
            role="protagonist",
            motivation=f"Motive {i}",
            physical_description=f"Description {i}",
            personality_traits=["trait"],
            voice_notes=f"Voice {i}",
            costume_notes=f"Costume {i}",
            visual_anchor=f"Anchor {i}",
            backstory=f"Backstory {i}",
            arc_summary=f"Arc {i}",
            reference_image_path="",
        )
    return CharacterRegistry(characters=characters)


def make_script(n_scenes=3, n_characters=3):
    """Create a test Script with n_scenes scenes and n_characters characters."""
    # Build action text that mentions all character names
    char_names = [f"Character {i}" for i in range(n_characters)]
    action_text = " and ".join(char_names) + " are in scene {i}."
    
    scenes = []
    for i in range(n_scenes):
        scenes.append(
            Scene(
                scene_id=str(i),
                scene_heading=f"INT. LOCATION {i} - DAY",
                action=action_text.format(i=i),
            )
        )
    return Script(
        title="Test Movie",
        logline="Test logline",
        genre="Action",
        scenes=scenes,
    )


# ── Test 1: Full end-to-end flow ────────────────────────────────────
print("\nTest 1: Full end-to-end flow")
with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp)

    # Step 1: Create registry
    registry = make_character_registry(3)
    script = make_script(3)

    # Step 2: Generate reference images
    ref_dir = tmp / "reference_sheets"
    provider = DummyCharacterImageProvider()
    generator = ReferenceSheetGenerator(provider, ref_dir)
    image_paths = generator.generate_for_registry(registry)
    check("Generated reference images", len(image_paths) == 3)

    # Set reference_image_path for each character
    for char_id, path in zip(registry.characters, image_paths):
        registry.characters[char_id].reference_image_path = path

    # Step 3: Render scenes
    renders_dir = tmp / "scene_renders"
    stage = SceneCharacterRendererStage(
        provider=provider,
        output_dir=renders_dir,
    )
    collection = stage.execute(script, registry)
    check("Render collection has renders", len(collection.renders) > 0)

    # Step 4: Verify output structure
    check("reference_sheets dir exists", ref_dir.exists())
    check("scene_renders dir exists", renders_dir.exists())


# ── Test 2: Multi-character consistency ────────────────────────────────────
print("\nTest 2: Multi-character consistency")
with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp)

    registry = make_character_registry(5)
    script = make_script(2, n_characters=5)

    ref_dir = tmp / "refs"
    provider = DummyCharacterImageProvider()
    generator = ReferenceSheetGenerator(provider, ref_dir)
    image_paths = generator.generate_for_registry(registry)

    for char_id, path in zip(registry.characters, image_paths):
        registry.characters[char_id].reference_image_path = path

    renders_dir = tmp / "renders"
    stage = SceneCharacterRendererStage(
        provider=provider,
        output_dir=renders_dir,
    )
    collection = stage.execute(script, registry)

    # All 5 characters should be rendered in each scene
    scene_0_renders = collection.get_renders_for_scene("0")
    check("Scene 0 has 5 renders", len(scene_0_renders) == 5)

    scene_1_renders = collection.get_renders_for_scene("1")
    check("Scene 1 has 5 renders", len(scene_1_renders) == 5)


# ── Test 3: Scene context preservation ────────────────────────────────────
print("\nTest 3: Scene context preservation")
with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp)

    registry = make_character_registry(2)
    script = make_script(2)

    ref_dir = tmp / "refs"
    provider = DummyCharacterImageProvider()
    generator = ReferenceSheetGenerator(provider, ref_dir)
    image_paths = generator.generate_for_registry(registry)

    for char_id, path in zip(registry.characters, image_paths):
        registry.characters[char_id].reference_image_path = path

    renders_dir = tmp / "renders"
    stage = SceneCharacterRendererStage(
        provider=provider,
        output_dir=renders_dir,
    )
    collection = stage.execute(script, registry)

    # Check that scene_id is preserved in renders
    for render in collection.renders:
        check(f"Render {render.character_id} has scene_id={render.scene_id}", render.scene_id in ["0", "1"])


# ── Test 4: Error handling for missing references ────────────────────────────────────
print("\nTest 4: Error handling for missing references")
with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp)

    registry = make_character_registry(2)
    script = make_script(1)

    # Don't set reference_image_path — simulate missing references
    renders_dir = tmp / "renders"
    provider = DummyCharacterImageProvider()
    stage = SceneCharacterRendererStage(
        provider=provider,
        output_dir=renders_dir,
    )

    # Should handle gracefully (no crash)
    try:
        collection = stage.execute(script, registry)
        check("Stage handles missing references gracefully", collection is not None)
    except Exception as e:
        check("Stage handles missing references gracefully", False, str(e))


# ── Test 5: Output directory structure ────────────────────────────────────
print("\nTest 5: Output directory structure")
with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp)

    registry = make_character_registry(2)
    script = make_script(1)

    ref_dir = tmp / "reference_sheets"
    provider = DummyCharacterImageProvider()
    generator = ReferenceSheetGenerator(provider, ref_dir)
    image_paths = generator.generate_for_registry(registry)

    # Set reference_image_path on each character so the renderer can find them
    for char_id, path in zip(registry.characters, image_paths):
        registry.characters[char_id].reference_image_path = path

    renders_dir = tmp / "scene_renders"
    stage = SceneCharacterRendererStage(
        provider=provider,
        output_dir=renders_dir,
    )
    stage.execute(script, registry)

    check("reference_sheets/ exists", ref_dir.exists())
    check("scene_renders/ exists", renders_dir.exists())
    check("reference_sheets/ has .png files", any(ref_dir.glob("*.png")))
    check("scene_renders/ has files", any(renders_dir.iterdir()))


# ── Test 6: Full pipeline mock integration ────────────────────────────────────
print("\nTest 6: Full pipeline mock integration")
with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp)

    class MockPipeline:
        state = {}

    pipeline = MockPipeline()
    extension = PipelineExtension(pipeline)
    provider = DummyCharacterImageProvider()
    extension.add_character_consistency(provider, tmp, generate_renders=True)

    registry = make_character_registry(2)
    script = make_script(1)

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


# ── Test 7: CLI argument parsing ────────────────────────────────────
print("\nTest 7: CLI argument parsing")
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


# ── Test 8: SceneCharacterRenderCollection serialization ────────────────────────────────────
print("\nTest 8: SceneCharacterRenderCollection serialization")
collection = SceneCharacterRenderCollection()
r1 = SceneCharacterRender(scene_id="1", character_id="hero", render_path="/a.png")
r2 = SceneCharacterRender(scene_id="1", character_id="villain", render_path="/b.png")
collection.add_render(r1)
collection.add_render(r2)

d = collection.to_dict()
check("to_dict() returns dict", isinstance(d, dict))
check("to_dict() has 'renders'", "renders" in d)
check("to_dict() renders is list", isinstance(d["renders"], list))
check("to_dict() has 2 renders", len(d["renders"]) == 2)


# ── Test 9: Reference sheet JSON profile structure ────────────────────────────────────
print("\nTest 9: Reference sheet JSON profile structure")
with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp)

    registry = make_character_registry(1)
    provider = DummyCharacterImageProvider()
    generator = ReferenceSheetGenerator(provider, tmp)
    generator.generate_for_registry(registry)

    profile = json.loads((tmp / "char_0_profile.json").read_text())
    check("Profile has 'id'", "id" in profile)
    check("Profile has 'name'", "name" in profile)
    check("Profile has 'reference_image'", "reference_image" in profile)
    check("Profile has 'visual_anchor'", "visual_anchor" in profile)


# ── Test 10: SceneCharacterRenderer detects present characters ────────────────────────────────────
print("\nTest 10: SceneCharacterRenderer detects present characters")
with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp)

    registry = make_character_registry(3)
    script = make_script(2)

    renderer = SceneCharacterRenderer(
        provider=DummyCharacterImageProvider(),
        reference_images={},
        output_dir=tmp,
    )

    # Scene 0 mentions char_0, char_1, and char_2 (default n_characters=3)
    present = renderer._detect_present_characters(script.scenes[0], registry)
    check("Scene 0 detects char_0, char_1, and char_2", set(present) == {"char_0", "char_1", "char_2"})

    # Scene 1 mentions char_0, char_1, and char_2
    present = renderer._detect_present_characters(script.scenes[1], registry)
    check("Scene 1 detects char_0, char_1, and char_2", set(present) == {"char_0", "char_1", "char_2"})


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
    print("All integration tests passed — ai_consistent_char is ready.")
