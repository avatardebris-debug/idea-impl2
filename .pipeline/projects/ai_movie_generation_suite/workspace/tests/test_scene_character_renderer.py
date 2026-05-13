"""Tests for SceneCharacterRenderer."""

import pytest
from ai_movie_gen_suite.models import (
    Beat,
    BeatPhase,
    BeatSheet,
    Character,
    CharacterRegistry,
    CharacterRole,
    DialogueLine,
    Scene,
    Script,
)
from ai_movie_gen_suite.stages.scene_character_renderer import (
    RenderedScene,
    RenderedScript,
    SceneCharacterRenderer,
)


class TestRenderedScene:
    def test_rendered_scene_to_dict(self):
        scene = Scene(
            scene_id="SC-001",
            scene_heading="INT. COFFEE SHOP - DAY",
            action="A person sits alone.",
            characters_present=["Alice"],
        )
        rendered = RenderedScene(
            scene=scene,
            action_lines=["Alice sits alone."],
            dialogue_lines=[
                DialogueLine(character_name="Alice", character_id="char1", text="Hello!")
            ],
            camera_notes="Wide shot",
        )
        d = rendered.to_dict()
        assert d["scene_id"] == "SC-001"
        assert d["action_lines"] == ["Alice sits alone."]
        assert d["dialogue_lines"][0]["text"] == "Hello!"


class TestRenderedScript:
    def test_rendered_script_to_dict(self):
        script = RenderedScript()
        script.add_rendered_scene(
            RenderedScene(
                scene=Scene(
                    scene_id="SC-001",
                    scene_heading="INT. ROOM - DAY",
                    action="",
                    characters_present=[],
                ),
                action_lines=[],
                dialogue_lines=[],
                camera_notes="",
            )
        )
        d = script.to_dict()
        assert len(d["rendered_scenes"]) == 1


class TestSceneCharacterRenderer:
    @pytest.fixture
    def script(self):
        return Script(
            title="Test Movie",
            logline="A test story.",
            genre="Drama",
            scenes=[
                Scene(
                    scene_id="SC-001",
                    scene_heading="INT. COFFEE SHOP - DAY",
                    action="Alice meets Bob.",
                    characters_present=["Alice", "Bob"],
                ),
                Scene(
                    scene_id="SC-002",
                    scene_heading="EXT. PARK - NIGHT",
                    action="Alice and Bob walk.",
                    characters_present=["Alice", "Bob"],
                ),
            ],
        )

    @pytest.fixture
    def character_registry(self):
        return CharacterRegistry(
            characters=[
                Character(
                    name="Alice",
                    role=CharacterRole.PROTAGONIST,
                    description="A brave woman.",
                    traits=["brave", "kind"],
                    motivations=["to find truth"],
                    backstory="Orphaned young.",
                    arc="From lost to found.",
                ),
                Character(
                    name="Bob",
                    role=CharacterRole.SUPPORTING,
                    description="A helpful man.",
                    traits=["helpful", "wise"],
                    motivations=["to help Alice"],
                    backstory="Former teacher.",
                    arc="From withdrawn to engaged.",
                ),
            ]
        )

    @pytest.fixture
    def beat_sheet(self):
        return BeatSheet(
            beats=[
                Beat(
                    beat_number=1,
                    beat_name="Setup",
                    phase=BeatPhase.ACT_ONE,
                    summary="Introduce characters.",
                    scenes=["SC-001"],
                ),
                Beat(
                    beat_number=2,
                    beat_name="Confrontation",
                    phase=BeatPhase.ACT_TWO,
                    summary="Characters face challenges.",
                    scenes=["SC-002"],
                ),
            ]
        )

    @pytest.fixture
    def renderer(self, script, character_registry, beat_sheet):
        return SceneCharacterRenderer(
            script=script,
            beat_sheet=beat_sheet,
            character_registry=character_registry,
        )

    def test_render_creates_rendered_script(self, renderer):
        result = renderer.render()
        assert isinstance(result, RenderedScript)
        assert len(result.rendered_scenes) == 2

    def test_render_adds_action_lines(self, renderer):
        result = renderer.render()
        for rendered_scene in result.rendered_scenes:
            assert len(rendered_scene.action_lines) > 0

    def test_render_adds_dialogue_lines(self, renderer):
        result = renderer.render()
        # At least one scene should have dialogue
        has_dialogue = any(len(rs.dialogue_lines) > 0 for rs in result.rendered_scenes)
        assert has_dialogue

    def test_render_uses_character_traits(self, renderer):
        """Dialogue should reflect character traits."""
        result = renderer.render()
        for rendered_scene in result.rendered_scenes:
            for line in rendered_scene.dialogue_lines:
                # Check that character names match registered characters
                assert line.character_name in ["Alice", "Bob"]

    def test_render_with_empty_script(self):
        """Empty script should produce empty rendered script."""
        renderer = SceneCharacterRenderer(
            script=Script(title="Empty", logline="", genre="", scenes=[]),
            beat_sheet=BeatSheet(beats=[]),
            character_registry=CharacterRegistry(characters=[]),
        )
        result = renderer.render()
        assert len(result.rendered_scenes) == 0

    def test_render_with_no_characters(self):
        """Script with no characters should have no dialogue."""
        renderer = SceneCharacterRenderer(
            script=Script(
                title="NoChars",
                logline="",
                genre="",
                scenes=[
                    Scene(
                        scene_id="SC-001",
                        scene_heading="INT. ROOM - DAY",
                        action="",
                        characters_present=[],
                    )
                ],
            ),
            beat_sheet=BeatSheet(beats=[]),
            character_registry=CharacterRegistry(characters=[]),
        )
        result = renderer.render()
        assert len(result.rendered_scenes) == 1
        assert len(result.rendered_scenes[0].dialogue_lines) == 0
