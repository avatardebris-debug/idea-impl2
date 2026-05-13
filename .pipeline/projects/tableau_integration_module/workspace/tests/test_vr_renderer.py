"""Tests for src.vr_renderer.VRRenderer."""

import pytest
from src.vr_scene import VRScene, VRGeometry
from src.vr_renderer import VRRenderer


# ===== VRRenderer =====

class TestVRRendererInit:
    """Tests for VRRenderer initialization."""

    def test_default_values(self):
        """Test that default values are correct."""
        renderer = VRRenderer()
        assert isinstance(renderer.scene, VRScene)
        assert renderer.resolution == (1920, 1080)
        assert renderer.is_rendered is False

    def test_custom_values(self):
        """Test that custom values are set correctly."""
        scene = VRScene(scene_id="custom")
        renderer = VRRenderer(scene=scene, resolution=(1280, 720))
        assert renderer.scene.scene_id == "custom"
        assert renderer.resolution == (1280, 720)
        assert renderer.is_rendered is False

    def test_default_scene(self):
        """Test that default scene is created when none provided."""
        renderer = VRRenderer()
        assert isinstance(renderer.scene, VRScene)
        assert renderer.scene.scene_id == "default"


class TestVRRendererSetScene:
    """Tests for VRRenderer.set_scene."""

    def test_set_scene(self):
        """Test setting a new scene."""
        renderer = VRRenderer()
        new_scene = VRScene(scene_id="new_scene")
        renderer.set_scene(new_scene)
        assert renderer.scene.scene_id == "new_scene"

    def test_set_scene_replaces(self):
        """Test that set_scene replaces the existing scene."""
        old_scene = VRScene(scene_id="old")
        renderer = VRRenderer(scene=old_scene)
        new_scene = VRScene(scene_id="new")
        renderer.set_scene(new_scene)
        assert renderer.scene.scene_id == "new"
        assert renderer.scene is not old_scene


class TestVRRendererRender:
    """Tests for VRRenderer.render."""

    def test_render_returns_dict(self):
        """Test that render returns a dict."""
        renderer = VRRenderer()
        result = renderer.render()
        assert isinstance(result, dict)

    def test_render_contains_scene(self):
        """Test that render output contains scene data."""
        renderer = VRRenderer()
        result = renderer.render()
        assert "scene" in result

    def test_render_contains_resolution(self):
        """Test that render output contains resolution."""
        renderer = VRRenderer(resolution=(1280, 720))
        result = renderer.render()
        assert result["resolution"] == [1280, 720]

    def test_render_contains_is_rendered(self):
        """Test that render output contains is_rendered flag."""
        renderer = VRRenderer()
        result = renderer.render()
        assert result["is_rendered"] is True

    def test_render_contains_render_timestamp(self):
        """Test that render output contains render_timestamp."""
        renderer = VRRenderer()
        result = renderer.render()
        assert "render_timestamp" in result
        assert isinstance(result["render_timestamp"], float)

    def test_render_sets_is_rendered_flag(self):
        """Test that render sets is_rendered flag on renderer."""
        renderer = VRRenderer()
        assert renderer.is_rendered is False
        renderer.render()
        assert renderer.is_rendered is True

    def test_render_with_geometries(self):
        """Test rendering a scene with geometries."""
        scene = VRScene()
        scene.add_geometry(VRGeometry(geometry_id="g1"))
        renderer = VRRenderer(scene=scene)
        result = renderer.render()
        assert len(result["scene"]["geometries"]) == 1
        assert result["scene"]["geometries"][0]["geometry_id"] == "g1"

    def test_render_multiple_times(self):
        """Test rendering multiple times."""
        renderer = VRRenderer()
        result1 = renderer.render()
        result2 = renderer.render()
        assert result1["is_rendered"] is True
        assert result2["is_rendered"] is True


class TestVRRendererToDict:
    """Tests for VRRenderer serialization."""

    def test_to_dict_default(self):
        """Test to_dict with default values."""
        renderer = VRRenderer()
        d = renderer.to_dict()
        assert "scene" in d
        assert "resolution" in d
        assert "is_rendered" in d
        assert d["is_rendered"] is False

    def test_to_dict_after_render(self):
        """Test to_dict after rendering."""
        renderer = VRRenderer()
        renderer.render()
        d = renderer.to_dict()
        assert d["is_rendered"] is True

    def test_to_dict_custom_resolution(self):
        """Test to_dict with custom resolution."""
        renderer = VRRenderer(resolution=(1280, 720))
        d = renderer.to_dict()
        assert d["resolution"] == [1280, 720]

    def test_to_dict_returns_new_dict(self):
        """Test that to_dict returns a new dict."""
        renderer = VRRenderer()
        d1 = renderer.to_dict()
        d2 = renderer.to_dict()
        assert d1 is not d2


class TestVRRendererFromDict:
    """Tests for VRRenderer deserialization."""

    def test_from_dict_default(self):
        """Test from_dict with minimal data."""
        data = {}
        renderer = VRRenderer.from_dict(data)
        assert isinstance(renderer.scene, VRScene)
        assert renderer.resolution == (1920, 1080)
        assert renderer.is_rendered is False

    def test_from_dict_with_data(self):
        """Test from_dict with full data."""
        scene = VRScene(scene_id="test_scene")
        scene.add_geometry(VRGeometry(geometry_id="g1"))
        data = {
            "scene": scene.to_dict(),
            "resolution": [1280, 720],
            "is_rendered": True,
        }
        renderer = VRRenderer.from_dict(data)
        assert renderer.scene.scene_id == "test_scene"
        assert len(renderer.scene.geometries) == 1
        assert renderer.resolution == (1280, 720)
        assert renderer.is_rendered is True

    def test_from_dict_partial(self):
        """Test from_dict with partial data."""
        data = {
            "resolution": [1024, 768],
        }
        renderer = VRRenderer.from_dict(data)
        assert renderer.resolution == (1024, 768)
        assert renderer.is_rendered is False  # default


class TestVRRendererRoundtrip:
    """Tests for VRRenderer serialization roundtrip."""

    def test_roundtrip_default(self):
        """Test roundtrip with default values."""
        renderer = VRRenderer()
        d = renderer.to_dict()
        renderer2 = VRRenderer.from_dict(d)
        assert renderer2.resolution == renderer.resolution
        assert renderer2.is_rendered == renderer.is_rendered

    def test_roundtrip_after_render(self):
        """Test roundtrip after rendering."""
        renderer = VRRenderer()
        renderer.render()
        d = renderer.to_dict()
        renderer2 = VRRenderer.from_dict(d)
        assert renderer2.is_rendered is True
        assert renderer2.resolution == renderer.resolution

    def test_roundtrip_with_geometries(self):
        """Test roundtrip with geometries."""
        scene = VRScene()
        scene.add_geometry(VRGeometry(geometry_id="g1", geometry_type="sphere"))
        renderer = VRRenderer(scene=scene)
        d = renderer.to_dict()
        renderer2 = VRRenderer.from_dict(d)
        assert len(renderer2.scene.geometries) == 1
        assert renderer2.scene.geometries[0].geometry_id == "g1"


class TestVRRendererIntegration:
    """Integration tests for VRRenderer."""

    def test_full_pipeline(self):
        """Test full rendering pipeline."""
        scene = VRScene(scene_id="test")
        scene.add_geometry(VRGeometry(geometry_id="g1", geometry_type="box"))
        scene.add_geometry(VRGeometry(geometry_id="g2", geometry_type="sphere"))
        renderer = VRRenderer(scene=scene, resolution=(1920, 1080))
        result = renderer.render()
        assert result["is_rendered"] is True
        assert result["resolution"] == [1920, 1080]
        assert len(result["scene"]["geometries"]) == 2

    def test_serialize_deserialize_render(self):
        """Test serialize, deserialize, then render."""
        scene = VRScene(scene_id="test")
        scene.add_geometry(VRGeometry(geometry_id="g1"))
        renderer = VRRenderer(scene=scene)
        d = renderer.to_dict()
        renderer2 = VRRenderer.from_dict(d)
        result = renderer2.render()
        assert result["is_rendered"] is True
        assert len(result["scene"]["geometries"]) == 1

    def test_render_empty_scene(self):
        """Test rendering an empty scene."""
        scene = VRScene()
        renderer = VRRenderer(scene=scene)
        result = renderer.render()
        assert result["is_rendered"] is True
        assert len(result["scene"]["geometries"]) == 0

    def test_render_with_custom_camera(self):
        """Test rendering with custom camera settings."""
        scene = VRScene(
            camera_position=[1.0, 2.0, 3.0],
            camera_look_at=[0.0, 0.0, 0.0],
        )
        renderer = VRRenderer(scene=scene)
        result = renderer.render()
        assert result["scene"]["camera_position"] == [1.0, 2.0, 3.0]
        assert result["scene"]["camera_look_at"] == [0.0, 0.0, 0.0]
