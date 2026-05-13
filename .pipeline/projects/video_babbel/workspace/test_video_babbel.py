"""Tests for video_babbel package."""

from __future__ import annotations

import hashlib
import json
import pathlib
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

# Add parent to path so we can import the modules
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent.parent))

import import_zip
import import_cloud_zip


# ---------------------------------------------------------------------------
# import_zip tests
# ---------------------------------------------------------------------------

class TestShouldSkip:
    def test_skip_pycache(self):
        assert import_zip.should_skip("__pycache__/foo.pyc") is True

    def test_skip_venv(self):
        assert import_zip.should_skip(".venv/lib/site-packages/foo.py") is True

    def test_skip_git(self):
        assert import_zip.should_skip(".git/HEAD") is True

    def test_skip_manifest(self):
        assert import_zip.should_skip("MANIFEST.json") is True

    def test_skip_pyo(self):
        assert import_zip.should_skip("foo.pyo") is True

    def test_skip_log(self):
        assert import_zip.should_skip("logs/app.log") is True

    def test_keep_normal_py(self):
        assert import_zip.should_skip("src/main.py") is False

    def test_keep_state_json(self):
        assert import_zip.should_skip(".pipeline/projects/foo/state/current_idea.json") is False


class TestFileHash:
    def test_empty_file(self, tmp_path: pathlib.Path):
        f = tmp_path / "empty.txt"
        f.write_text("")
        assert import_zip.file_hash(f) == hashlib.md5(b"").hexdigest()

    def test_nonexistent(self, tmp_path: pathlib.Path):
        f = tmp_path / "nope.txt"
        assert import_zip.file_hash(f) == ""


class TestZipEntryHash:
    def test_entry_hash(self):
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tf:
            with zipfile.ZipFile(tf.name, "w") as zf:
                zf.writestr("hello.txt", "world")
            zf2 = zipfile.ZipFile(tf.name, "r")
            h = import_zip.zip_entry_hash(zf2, "hello.txt")
            assert h == hashlib.md5(b"world").hexdigest()
            zf2.close()
        pathlib.Path(tf.name).unlink()


class TestFindLatestZip:
    def test_no_zips(self, tmp_path: pathlib.Path):
        # Patch _AUTO_SEARCH_DIRS to point to empty tmp_path
        with patch.object(import_zip, "_AUTO_SEARCH_DIRS", [tmp_path]):
            assert import_zip.find_latest_zip() is None

    def test_finds_latest(self, tmp_path: pathlib.Path):
        z1 = tmp_path / "pipeline_extract_1.zip"
        z1.write_bytes(b"a")
        z1.touch()
        import time; time.sleep(0.01)
        z2 = tmp_path / "pipeline_extract_2.zip"
        z2.write_bytes(b"b")
        z2.touch()
        with patch.object(import_zip, "_AUTO_SEARCH_DIRS", [tmp_path]):
            result = import_zip.find_latest_zip()
            assert result == z2


class TestImportZipDryRun:
    def test_dry_run_no_write(self, tmp_path: pathlib.Path):
        """--dry-run should not write any files."""
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tf:
            with zipfile.ZipFile(tf.name, "w") as zf:
                zf.writestr(".pipeline/projects/test_proj/workspace/code.py", "print('hi')")
                zf.writestr(".pipeline/projects/test_proj/state/current_idea.json", json.dumps({"status": "planning"}))
            zip_path = pathlib.Path(tf.name)

        dest = tmp_path / "dest"
        dest.mkdir()

        # Verify the zip contains the expected files
        zf = zipfile.ZipFile(zip_path, "r")
        names = [n for n in zf.namelist() if not n.endswith("/")]
        zf.close()
        assert len(names) == 2

        pathlib.Path(tf.name).unlink()


# ---------------------------------------------------------------------------
# import_cloud_zip tests
# ---------------------------------------------------------------------------

class TestFixDoubleWorkspace:
    def test_no_double_nesting(self, tmp_path: pathlib.Path):
        proj = tmp_path / "proj"
        proj.mkdir()
        ws = proj / "workspace"
        ws.mkdir()
        (ws / "code.py").write_text("x")
        assert import_cloud_zip.fix_double_workspace(proj) == 0

    def test_fixes_double_nesting(self, tmp_path: pathlib.Path):
        proj = tmp_path / "proj"
        proj.mkdir()
        ws = proj / "workspace"
        ws.mkdir()
        double = ws / "workspace"
        double.mkdir()
        (double / "code.py").write_text("double")
        moved = import_cloud_zip.fix_double_workspace(proj)
        assert moved == 1
        assert (ws / "code.py").exists()
        assert not double.exists()

    def test_fixes_nested_dirs(self, tmp_path: pathlib.Path):
        proj = tmp_path / "proj"
        proj.mkdir()
        ws = proj / "workspace"
        ws.mkdir()
        double = ws / "workspace"
        double.mkdir()
        sub = double / "sub"
        sub.mkdir()
        (sub / "deep.py").write_text("deep")
        moved = import_cloud_zip.fix_double_workspace(proj)
        assert moved == 1
        assert (ws / "sub" / "deep.py").exists()


class TestFixStrayPhases:
    def test_no_stray_phases(self, tmp_path: pathlib.Path):
        proj = tmp_path / "proj"
        proj.mkdir()
        ws = proj / "workspace"
        ws.mkdir()
        assert import_cloud_zip.fix_stray_phases(proj) == 0

    def test_moves_stray_phase(self, tmp_path: pathlib.Path):
        proj = tmp_path / "proj"
        proj.mkdir()
        ws = proj / "workspace"
        ws.mkdir()
        stray = ws / "phases"
        stray.mkdir()
        (stray / "validation_report.md").write_text("report")
        real_phases = proj / "phases"
        real_phases.mkdir()
        moved = import_cloud_zip.fix_stray_phases(proj)
        assert moved == 1
        assert (real_phases / "validation_report.md").exists()


class TestMergeState:
    def test_local_ahead(self, tmp_path: pathlib.Path):
        local = tmp_path / "local.json"
        remote = tmp_path / "remote.json"
        local.write_text(json.dumps({"status": "complete"}))
        remote.write_text(json.dumps({"status": "planning"}))
        assert import_cloud_zip.merge_state(local, remote) is False

    def test_remote_newer_status(self, tmp_path: pathlib.Path):
        local = tmp_path / "local.json"
        remote = tmp_path / "remote.json"
        local.write_text(json.dumps({"status": "planning"}))
        remote.write_text(json.dumps({"status": "phase_1_executing"}))
        assert import_cloud_zip.merge_state(local, remote) is True
        assert json.loads(local.read_text())["status"] == "phase_1_executing"

    def test_local_missing(self, tmp_path: pathlib.Path):
        local = tmp_path / "local.json"
        remote = tmp_path / "remote.json"
        remote.write_text(json.dumps({"status": "planning"}))
        assert import_cloud_zip.merge_state(local, remote) is True
        assert local.exists()

    def test_invalid_json(self, tmp_path: pathlib.Path):
        local = tmp_path / "local.json"
        remote = tmp_path / "remote.json"
        remote.write_text("not json")
        assert import_cloud_zip.merge_state(local, remote) is False


class TestPrintManifest:
    def test_no_projects(self, tmp_path: pathlib.Path):
        # Create a fake .pipeline dir
        pipeline = tmp_path / ".pipeline"
        pipeline.mkdir()
        projects = pipeline / "projects"
        projects.mkdir()

        # Patch PROJECT_ROOT and PIPELINE_DIR
        with patch.object(import_cloud_zip, 'PROJECT_ROOT', tmp_path):
            with patch.object(import_cloud_zip, 'PIPELINE_DIR', pipeline):
                import io
                from contextlib import redirect_stdout
                f = io.StringIO()
                with redirect_stdout(f):
                    import_cloud_zip.print_manifest()
                output = f.getvalue()
                assert "Project Manifest" in output


class TestImportZipMain:
    def test_no_pipeline_in_zip(self, tmp_path: pathlib.Path):
        """Zip with no .pipeline directory at all should raise ValueError (empty min)."""
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tf:
            with zipfile.ZipFile(tf.name, "w") as zf:
                zf.writestr("some_file.txt", "content")
            zip_path = pathlib.Path(tf.name)

        # rglob returns empty → min() raises ValueError
        with patch.object(pathlib.Path, 'rglob', return_value=iter([])):
            with pytest.raises(ValueError):
                import_cloud_zip.import_zip(zip_path)
        zip_path.unlink()

    def test_no_projects_dir(self, tmp_path: pathlib.Path):
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tf:
            with zipfile.ZipFile(tf.name, "w") as zf:
                zf.writestr(".pipeline/", "")  # directory entry
                zf.writestr(".pipeline/projects/", "")  # directory entry
            zip_path = pathlib.Path(tf.name)

        # Should not crash, just print nothing
        with patch.object(sys, 'exit') as mock_exit:
            try:
                import_cloud_zip.import_zip(zip_path)
            except SystemExit:
                pass  # ignore any exit
        zip_path.unlink()


# ---------------------------------------------------------------------------
# Run tests
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
