"""Tests for SOP Store (CRUD operations)."""

import pytest
from pathlib import Path
import tempfile

from drop_servicing_tool.sop_store import (
    list_sops, get_sop_path, get_sop, save_sop, create_sop, delete_sop
)
from drop_servicing_tool.sop_schema import SOP, SOPInput, SOPStep


class TestListSops:
    """Tests for list_sops function."""

    def test_list_empty_directory(self, tmp_path):
        """Test listing SOPs in empty directory."""
        sops = list_sops(tmp_path)
        assert sops == []

    def test_list_sops_with_files(self, tmp_path):
        """Test listing SOPs with YAML files."""
        # Create some SOP files
        (tmp_path / "sop1.yaml").write_text("name: sop1", encoding="utf-8")
        (tmp_path / "sop2.yaml").write_text("name: sop2", encoding="utf-8")
        (tmp_path / "sop3.yaml").write_text("name: sop3", encoding="utf-8")

        sops = list_sops(tmp_path)
        assert sops == ["sop1", "sop2", "sop3"]

    def test_list_sops_excludes_non_yaml(self, tmp_path):
        """Test that non-YAML files are excluded."""
        (tmp_path / "sop1.yaml").write_text("name: sop1", encoding="utf-8")
        (tmp_path / "sop1.txt").write_text("not a sop", encoding="utf-8")
        (tmp_path / "readme.md").write_text("# README", encoding="utf-8")

        sops = list_sops(tmp_path)
        assert sops == ["sop1"]


class TestGetSopPath:
    """Tests for get_sop_path function."""

    def test_get_sop_path_exists(self, tmp_path):
        """Test getting path for existing SOP."""
        sop_path = tmp_path / "test_sop.yaml"
        sop_path.write_text("name: test", encoding="utf-8")

        path = get_sop_path("test_sop", tmp_path)
        assert path == sop_path

    def test_get_sop_path_not_found(self, tmp_path):
        """Test getting path for non-existent SOP."""
        path = get_sop_path("nonexistent", tmp_path)
        assert path is None


class TestGetSop:
    """Tests for get_sop function."""

    def test_get_valid_sop(self, tmp_path):
        """Test loading a valid SOP."""
        sop_data = {
            "name": "test_sop",
            "description": "Test SOP",
            "inputs": [
                {"name": "input1", "type": "string", "required": True}
            ],
            "steps": [
                {"name": "step1", "description": "Step 1"}
            ]
        }
        sop_path = tmp_path / "test_sop.yaml"
        sop_path.write_text(str(sop_data), encoding="utf-8")

        sop = get_sop("test_sop", tmp_path)
        assert sop.name == "test_sop"
        assert len(sop.steps) == 1

    def test_get_sop_not_found(self):
        """Test getting non-existent SOP."""
        with pytest.raises(FileNotFoundError, match="SOP 'nonexistent' not found"):
            get_sop("nonexistent")


class TestSaveSop:
    """Tests for save_sop function."""

    def test_save_sop(self, tmp_path):
        """Test saving an SOP."""
        sop = SOP(
            name="test_sop",
            description="Test SOP",
            inputs=[SOPInput(name="input1", type="string", required=True)],
            steps=[SOPStep(name="step1", description="Step 1")],
            metadata={"version": "1.0"}
        )

        path = save_sop(sop, tmp_path)
        assert path == tmp_path / "test_sop.yaml"
        assert path.exists()

        # Verify content
        content = path.read_text(encoding="utf-8")
        assert "name: test_sop" in content
        assert "description: Test SOP" in content

    def test_save_sop_creates_directory(self, tmp_path):
        """Test that save_sop creates the directory if it doesn't exist."""
        sub_dir = tmp_path / "subdir"
        sop = SOP(
            name="test_sop",
            description="Test SOP",
            steps=[SOPStep(name="step1", description="Step 1")]
        )

        path = save_sop(sop, sub_dir)
        assert path.exists()
        assert sub_dir.exists()


class TestCreateSop:
    """Tests for create_sop function."""

    def test_create_sop_from_dict(self, tmp_path):
        """Test creating SOP from dict."""
        sop_data = {
            "name": "new_sop",
            "description": "New SOP",
            "steps": [
                {"name": "step1", "description": "Step 1"}
            ]
        }

        path = create_sop("new_sop", sop_data, tmp_path)
        assert path == tmp_path / "new_sop.yaml"
        assert path.exists()

    def test_create_sop_from_yaml_string(self, tmp_path):
        """Test creating SOP from YAML string."""
        yaml_content = """
name: new_sop
description: New SOP
steps:
  - name: step1
    description: Step 1
"""

        path = create_sop("new_sop", yaml_content, tmp_path)
        assert path == tmp_path / "new_sop.yaml"
        assert path.exists()

    def test_create_sop_creates_directory(self, tmp_path):
        """Test that create_sop creates the directory if needed."""
        sub_dir = tmp_path / "subdir"
        sop_data = {
            "name": "new_sop",
            "description": "New SOP",
            "steps": [{"name": "step1", "description": "Step 1"}]
        }

        path = create_sop("new_sop", sop_data, sub_dir)
        assert path.exists()
        assert sub_dir.exists()


class TestDeleteSop:
    """Tests for delete_sop function."""

    def test_delete_sop_exists(self, tmp_path):
        """Test deleting an existing SOP."""
        sop_path = tmp_path / "test_sop.yaml"
        sop_path.write_text("name: test", encoding="utf-8")

        result = delete_sop("test_sop", tmp_path)
        assert result is True
        assert not sop_path.exists()

    def test_delete_sop_not_found(self, tmp_path):
        """Test deleting non-existent SOP."""
        result = delete_sop("nonexistent", tmp_path)
        assert result is False

    def test_delete_sop_removes_file(self, tmp_path):
        """Test that delete_sop actually removes the file."""
        sop_path = tmp_path / "test_sop.yaml"
        sop_path.write_text("name: test", encoding="utf-8")

        delete_sop("test_sop", tmp_path)
        assert not sop_path.exists()


class TestSopStoreIntegration:
    """Integration tests for SOP store operations."""

    def test_create_and_load_sop(self, tmp_path):
        """Test creating and then loading an SOP."""
        sop_data = {
            "name": "test_sop",
            "description": "Test SOP",
            "inputs": [
                {"name": "input1", "type": "string", "required": True}
            ],
            "steps": [
                {"name": "step1", "description": "Step 1"}
            ]
        }

        # Create SOP
        create_sop("test_sop", sop_data, tmp_path)

        # Load SOP
        sop = get_sop("test_sop", tmp_path)
        assert sop.name == "test_sop"
        assert len(sop.steps) == 1

    def test_create_update_delete_cycle(self, tmp_path):
        """Test create, update, and delete cycle."""
        # Create
        sop_data = {
            "name": "test_sop",
            "description": "Initial",
            "steps": [{"name": "step1", "description": "Step 1"}]
        }
        create_sop("test_sop", sop_data, tmp_path)

        # Update (create again with same name)
        sop_data["description"] = "Updated"
        create_sop("test_sop", sop_data, tmp_path)

        # Verify update
        sop = get_sop("test_sop", tmp_path)
        assert sop.description == "Updated"

        # Delete
        assert delete_sop("test_sop", tmp_path) is True
        assert get_sop("test_sop", tmp_path) is None

    def test_list_sops_after_operations(self, tmp_path):
        """Test listing SOPs after various operations."""
        # Create multiple SOPs
        for i in range(3):
            sop_data = {
                "name": f"sop_{i}",
                "description": f"SOP {i}",
                "steps": [{"name": "step1", "description": "Step 1"}]
            }
            create_sop(f"sop_{i}", sop_data, tmp_path)

        # List should show all
        sops = list_sops(tmp_path)
        assert len(sops) == 3

        # Delete one
        delete_sop("sop_1", tmp_path)

        # List should show remaining
        sops = list_sops(tmp_path)
        assert len(sops) == 2
        assert "sop_1" not in sops
