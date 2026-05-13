"""Tests for src.vr_scene.VRScene and VRGeometry."""

import pytest
from src.vr_scene import VRScene, VRGeometry


# ===== VRGeometry =====

class TestVRGeometryInit:
    """Tests for VRGeometry initialization."""

    def test_default_values(self):
        """Test that default values are correct."""
        geom = VRGeometry()
        assert geom.geometry_id == ""
        assert geom.geometry_type == "box"
        assert geom.position == [0.0, 0.0, 0.0]
        assert geom.scale == [1.0, 1.0, 1.0]
        assert geom.color == [1.0, 1.0, 1.0]
        assert geom.label == ""

    def test_custom_values(self):
        """Test that custom values are set correctly."""
        geom = VRGeometry(
            geometry_id="g1",
            geometry_type="sphere",
            position=[1.0, 2.0, 3.0],
            scale=[2.0, 2.0, 2.0],
            color=[0.5, 0.5, 0.5],
            label="test sphere",
        )
        assert geom.geometry_id == "g1"
        assert geom.geometry_type == "sphere"
        assert geom.position == [1.0, 2.0, 3.0]
        assert geom.scale == [2.0, 2.0, 2.0]
        assert geom.color == [0.5, 0.5, 0.5]
        assert geom.label == "test sphere"

    def test_custom_geometry_types(self):
        """Test various geometry types."""
        for gtype in ("box", "sphere", "plane", "cylinder", "cone"):
            geom = VRGeometry(geometry_type=gtype)
            assert geom.geometry_type == gtype


class TestVRGeometryToDict:
    """Tests for VRGeometry serialization."""

    def test_to_dict_default(self):
        """Test to_dict with default values."""
        geom = VRGeometry()
        d = geom.to_dict()
        assert d["geometry_id"] == ""
        assert d["geometry_type"] == "box"
        assert d["position"] == [0.0, 0.0, 0.0]
        assert d["scale"] == [1.0, 1.0, 1.0]
        assert d["color"] == [1.0, 1.0, 1.0]
        assert d["label"] == ""

    def test_to_dict_custom(self):
        """Test to_dict with custom values."""
        geom = VRGeometry(
            geometry_id="g1",
            geometry_type="sphere",
            position=[1.0, 2.0, 3.0],
            scale=[2.0, 2.0, 2.0],
            color=[0.5, 0.5, 0.5],
            label="test",
        )
        d = geom.to_dict()
        assert d["geometry_id"] == "g1"
        assert d["geometry_type"] == "sphere"
        assert d["position"] == [1.0, 2.0, 3.0]
        assert d["scale"] == [2.0, 2.0, 2.0]
        assert d["color"] == [0.5, 0.5, 0.5]
        assert d["label"] == "test"

    def test_to_dict_returns_new_dict(self):
        """Test that to_dict returns a new dict (not a reference)."""
        geom = VRGeometry()
        d1 = geom.to_dict()
        d2 = geom.to_dict()
        assert d1 is not d2


class TestVRGeometryFromDict:
    """Tests for VRGeometry deserialization."""

    def test_from_dict_default(self):
        """Test from_dict with minimal data."""
        data = {}
        geom = VRGeometry.from_dict(data)
        assert geom.geometry_id == ""
        assert geom.geometry_type == "box"
        assert geom.position == [0.0, 0.0, 0.0]
        assert geom.scale == [1.0, 1.0, 1.0]
        assert geom.color == [1.0, 1.0, 1.0]
        assert geom.label == ""

    def test_from_dict_custom(self):
        """Test from_dict with full data."""
        data = {
            "geometry_id": "g1",
            "geometry_type": "sphere",
            "position": [1.0, 2.0, 3.0],
            "scale": [2.0, 2.0, 2.0],
            "color": [0.5, 0.5, 0.5],
            "label": "test",
        }
        geom = VRGeometry.from_dict(data)
        assert geom.geometry_id == "g1"
        assert geom.geometry_type == "sphere"
        assert geom.position == [1.0, 2.0, 3.0]
        assert geom.scale == [2.0, 2.0, 2.0]
        assert geom.color == [0.5, 0.5, 0.5]
        assert geom.label == "test"

    def test_from_dict_partial(self):
        """Test from_dict with partial data."""
        data = {
            "geometry_id": "g2",
            "geometry_type": "plane",
        }
        geom = VRGeometry.from_dict(data)
        assert geom.geometry_id == "g2"
        assert geom.geometry_type == "plane"
        assert geom.position == [0.0, 0.0, 0.0]  # default
        assert geom.scale == [1.0, 1.0, 1.0]  # default
        assert geom.color == [1.0, 1.0, 1.0]  # default
        assert geom.label == ""  # default


class TestVRGeometryRoundtrip:
    """Tests for VRGeometry serialization roundtrip."""

    def test_roundtrip_default(self):
        """Test roundtrip with default values."""
        geom = VRGeometry()
        d = geom.to_dict()
        geom2 = VRGeometry.from_dict(d)
        assert geom2.geometry_id == geom.geometry_id
        assert geom2.geometry_type == geom.geometry_type
        assert geom2.position == geom.position
        assert geom2.scale == geom.scale
        assert geom2.color == geom.color
        assert geom2.label == geom.label

    def test_roundtrip_custom(self):
        """Test roundtrip with custom values."""
        geom = VRGeometry(
            geometry_id="rt1",
            geometry_type="sphere",
            position=[1.0, 2.0, 3.0],
            scale=[2.0, 2.0, 2.0],
            color=[0.5, 0.5, 0.5],
            label="roundtrip test",
        )
        d = geom.to_dict()
        geom2 = VRGeometry.from_dict(d)
        assert geom2.geometry_id == geom.geometry_id
        assert geom2.geometry_type == geom.geometry_type
        assert geom2.position == geom.position
        assert geom2.scale == geom.scale
        assert geom2.color == geom.color
        assert geom2.label == geom.label


# ===== VRScene =====

class TestVRSceneInit:
    """Tests for VRScene initialization."""

    def test_default_values(self):
        """Test that default values are correct."""
        scene = VRScene()
        assert scene.scene_id == "default"
        assert scene.geometries == []
        assert scene.camera_position == [0.0, 0.0, 5.0]
        assert scene.camera_look_at == [0.0, 0.0, 0.0]

    def test_custom_values(self):
        """Test that custom values are set correctly."""
        scene = VRScene(
            scene_id="s1",
            camera_position=[1.0, 2.0, 3.0],
            camera_look_at=[0.0, 0.0, 0.0],
        )
        assert scene.scene_id == "s1"
        assert scene.geometries == []
        assert scene.camera_position == [1.0, 2.0, 3.0]
        assert scene.camera_look_at == [0.0, 0.0, 0.0]


class TestVRSceneAddGeometry:
    """Tests for VRScene.add_geometry."""

    def test_add_single_geometry(self):
        """Test adding a single geometry."""
        scene = VRScene()
        geom = VRGeometry(geometry_id="g1")
        scene.add_geometry(geom)
        assert len(scene.geometries) == 1
        assert scene.geometries[0] is geom

    def test_add_multiple_geometries(self):
        """Test adding multiple geometries."""
        scene = VRScene()
        for i in range(5):
            scene.add_geometry(VRGeometry(geometry_id=f"g{i}"))
        assert len(scene.geometries) == 5

    def test_add_geometry_with_position(self):
        """Test adding a geometry with position."""
        scene = VRScene()
        geom = VRGeometry(geometry_id="g1", position=[1.0, 2.0, 3.0])
        scene.add_geometry(geom)
        assert scene.geometries[0].position == [1.0, 2.0, 3.0]


class TestVRSceneRemoveGeometry:
    """Tests for VRScene.remove_geometry."""

    def test_remove_existing_geometry(self):
        """Test removing an existing geometry."""
        scene = VRScene()
        geom = VRGeometry(geometry_id="g1")
        scene.add_geometry(geom)
        result = scene.remove_geometry("g1")
        assert result is True
        assert len(scene.geometries) == 0

    def test_remove_nonexistent_geometry(self):
        """Test removing a nonexistent geometry."""
        scene = VRScene()
        result = scene.remove_geometry("g1")
        assert result is False

    def test_remove_all_geometries(self):
        """Test removing all geometries."""
        scene = VRScene()
        for i in range(5):
            scene.add_geometry(VRGeometry(geometry_id=f"g{i}"))
        for i in range(5):
            scene.remove_geometry(f"g{i}")
        assert len(scene.geometries) == 0


class TestVRSceneGetGeometryById:
    """Tests for VRScene geometry lookup."""

    def test_get_existing_geometry(self):
        """Test getting an existing geometry by index."""
        scene = VRScene()
        geom = VRGeometry(geometry_id="g1")
        scene.add_geometry(geom)
        assert scene.geometries[0].geometry_id == "g1"

    def test_get_nonexistent_geometry(self):
        """Test getting a nonexistent geometry."""
        scene = VRScene()
        assert len(scene.geometries) == 0

    def test_get_geometry_with_same_id(self):
        """Test getting a geometry with a specific ID."""
        scene = VRScene()
        geom = VRGeometry(geometry_id="g1")
        scene.add_geometry(geom)
        found = [g for g in scene.geometries if g.geometry_id == "g1"]
        assert len(found) == 1


class TestVRSceneGetGeometriesByType:
    """Tests for VRScene geometry filtering."""

    def test_get_geometries_by_type_box(self):
        """Test getting box geometries."""
        scene = VRScene()
        scene.add_geometry(VRGeometry(geometry_type="box"))
        scene.add_geometry(VRGeometry(geometry_type="sphere"))
        boxes = [g for g in scene.geometries if g.geometry_type == "box"]
        assert len(boxes) == 1

    def test_get_geometries_by_type_sphere(self):
        """Test getting sphere geometries."""
        scene = VRScene()
        scene.add_geometry(VRGeometry(geometry_type="box"))
        scene.add_geometry(VRGeometry(geometry_type="sphere"))
        spheres = [g for g in scene.geometries if g.geometry_type == "sphere"]
        assert len(spheres) == 1

    def test_get_geometries_by_type_none(self):
        """Test getting no geometries of a type."""
        scene = VRScene()
        scene.add_geometry(VRGeometry(geometry_type="box"))
        spheres = [g for g in scene.geometries if g.geometry_type == "sphere"]
        assert len(spheres) == 0


class TestVRSceneClearGeometries:
    """Tests for VRScene geometry clearing."""

    def test_clear_geometries(self):
        """Test clearing all geometries."""
        scene = VRScene()
        for i in range(5):
            scene.add_geometry(VRGeometry(geometry_id=f"g{i}"))
        scene.geometries.clear()
        assert len(scene.geometries) == 0

    def test_clear_empty_scene(self):
        """Test clearing an empty scene."""
        scene = VRScene()
        scene.geometries.clear()
        assert len(scene.geometries) == 0


class TestVRSceneToDict:
    """Tests for VRScene serialization."""

    def test_to_dict_default(self):
        """Test to_dict with default values."""
        scene = VRScene()
        d = scene.to_dict()
        assert d["scene_id"] == "default"
        assert d["geometries"] == []
        assert d["camera_position"] == [0.0, 0.0, 5.0]
        assert d["camera_look_at"] == [0.0, 0.0, 0.0]

    def test_to_dict_with_geometries(self):
        """Test to_dict with geometries."""
        scene = VRScene()
        scene.add_geometry(VRGeometry(geometry_id="g1"))
        d = scene.to_dict()
        assert len(d["geometries"]) == 1
        assert d["geometries"][0]["geometry_id"] == "g1"

    def test_to_dict_returns_new_dict(self):
        """Test that to_dict returns a new dict."""
        scene = VRScene()
        d1 = scene.to_dict()
        d2 = scene.to_dict()
        assert d1 is not d2


class TestVRSceneFromDict:
    """Tests for VRScene deserialization."""

    def test_from_dict_default(self):
        """Test from_dict with minimal data."""
        data = {}
        scene = VRScene.from_dict(data)
        assert scene.scene_id == "default"
        assert scene.geometries == []
        assert scene.camera_position == [0.0, 0.0, 5.0]
        assert scene.camera_look_at == [0.0, 0.0, 0.0]

    def test_from_dict_with_geometries(self):
        """Test from_dict with geometries."""
        data = {
            "scene_id": "s1",
            "geometries": [
                {
                    "geometry_id": "g1",
                    "geometry_type": "sphere",
                    "position": [1.0, 2.0, 3.0],
                    "scale": [1.0, 1.0, 1.0],
                    "color": [1.0, 1.0, 1.0],
                    "label": "",
                }
            ],
            "camera_position": [0.0, 0.0, 5.0],
            "camera_look_at": [0.0, 0.0, 0.0],
        }
        scene = VRScene.from_dict(data)
        assert scene.scene_id == "s1"
        assert len(scene.geometries) == 1
        assert scene.geometries[0].geometry_id == "g1"
        assert scene.geometries[0].geometry_type == "sphere"
        assert scene.camera_position == [0.0, 0.0, 5.0]
        assert scene.camera_look_at == [0.0, 0.0, 0.0]


class TestVRSceneRoundtrip:
    """Tests for VRScene serialization roundtrip."""

    def test_roundtrip_default(self):
        """Test roundtrip with default values."""
        scene = VRScene()
        d = scene.to_dict()
        scene2 = VRScene.from_dict(d)
        assert scene2.scene_id == scene.scene_id
        assert len(scene2.geometries) == len(scene.geometries)
        assert scene2.camera_position == scene.camera_position
        assert scene2.camera_look_at == scene.camera_look_at

    def test_roundtrip_with_geometries(self):
        """Test roundtrip with geometries."""
        scene = VRScene()
        scene.add_geometry(VRGeometry(geometry_id="g1", geometry_type="sphere"))
        d = scene.to_dict()
        scene2 = VRScene.from_dict(d)
        assert scene2.scene_id == scene.scene_id
        assert len(scene2.geometries) == len(scene.geometries)
        assert scene2.geometries[0].geometry_id == "g1"
        assert scene2.geometries[0].geometry_type == "sphere"


class TestVRSceneGetGeometryCount:
    """Tests for VRScene geometry count."""

    def test_get_geometry_count_empty(self):
        """Test geometry count on empty scene."""
        scene = VRScene()
        assert len(scene.geometries) == 0

    def test_get_geometry_count_with_geometries(self):
        """Test geometry count with geometries."""
        scene = VRScene()
        for i in range(5):
            scene.add_geometry(VRGeometry(geometry_id=f"g{i}"))
        assert len(scene.geometries) == 5

    def test_get_geometry_count_after_remove(self):
        """Test geometry count after removal."""
        scene = VRScene()
        scene.add_geometry(VRGeometry(geometry_id="g1"))
        scene.remove_geometry("g1")
        assert len(scene.geometries) == 0


class TestVRSceneGetGeometriesByTypeEmpty:
    """Tests for VRScene geometry filtering on empty scene."""

    def test_get_geometries_by_type_empty_scene(self):
        """Test getting geometries by type on empty scene."""
        scene = VRScene()
        boxes = [g for g in scene.geometries if g.geometry_type == "box"]
        assert len(boxes) == 0


class TestVRSceneClearGeometriesAfterAdd:
    """Tests for VRScene geometry clearing after adding."""

    def test_clear_geometries_after_add(self):
        """Test clearing geometries after adding."""
        scene = VRScene()
        scene.add_geometry(VRGeometry(geometry_id="g1"))
        scene.geometries.clear()
        assert len(scene.geometries) == 0
