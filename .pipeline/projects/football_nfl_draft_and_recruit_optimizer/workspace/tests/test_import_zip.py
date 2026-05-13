"""Tests for import_zip.py and import_cloud_zip.py — smart selective importers for pipeline_extract_*.zip files."""
from __future__ import annotations

import json
import pathlib
import tempfile
import zipfile
from unittest import mock

import pytest

# We import the module functions directly (not via CLI) to test them in isolation.
import import_zip
import import_cloud_zip


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def tmp_root(tmp_path: pathlib.Path) -> pathlib.Path:
    """A temporary directory that serves as the 'project root' for imports."""
    return tmp_path


@pytest.fixture
def sample_zip(tmp_path: pathlib.Path) -> pathlib.Path:
    """Create a realistic pipeline_extract_*.zip with known contents.

    Structure inside the zip:
        .pipeline/projects/newsletter/state/current_idea.json
        .pipeline/projects/newsletter/workspace/main.py
        .pipeline/projects/newsletter/workspace/utils.py
        .pipeline/projects/newsletter/phases/phase_1/tasks.md
        .pipeline/projects/newsletter/phases/phase_1/validation_report.md
        .pipeline/projects/newsletter/phases/phase_2/tasks.md
        .pipeline/projects/blog/state/current_idea.json
        .pipeline/projects/blog/workspace/index.py
        .pipeline/queues/executor.jsonl
        .pipeline/state/global_state.json
        .pipeline/shared_libs/utils.py
        master_ideas.md
        MANIFEST.json
    """
    zip_path = tmp_path / "pipeline_extract_20260101_120000.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # ── newsletter project ──
        zf.writestr(
            ".pipeline/projects/newsletter/state/current_idea.json",
            json.dumps({"title": "Newsletter", "status": "phase_2_executing", "phase": 2, "total_phases": 3}),
        )
        zf.writestr(".pipeline/projects/newsletter/workspace/main.py", "# newsletter main\nprint('hi')\n")
        zf.writestr(".pipeline/projects/newsletter/workspace/utils.py", "# newsletter utils\n")
        zf.writestr(
            ".pipeline/projects/newsletter/phases/phase_1/tasks.md",
            "- [x] Task 1\n- [ ] Task 2\n",
        )
        zf.writestr(
            ".pipeline/projects/newsletter/phases/phase_1/validation_report.md",
            "## Validation\nAll good.\n",
        )
        zf.writestr(
            ".pipeline/projects/newsletter/phases/phase_2/tasks.md",
            "- [ ] Task A\n- [ ] Task B\n",
        )

        # ── blog project ──
        zf.writestr(
            ".pipeline/projects/blog/state/current_idea.json",
            json.dumps({"title": "Blog", "status": "phase_1_planning", "phase": 1, "total_phases": 2}),
        )
        zf.writestr(".pipeline/projects/blog/workspace/index.py", "# blog index\n")

        # ── global files ──
        zf.writestr(".pipeline/queues/executor.jsonl", '{"task": "build"}\n')
        zf.writestr(".pipeline/state/global_state.json", json.dumps({"version": 1}))
        zf.writestr(".pipeline/shared_libs/utils.py", "# shared utils\n")

        # ── root files ──
        zf.writestr("master_ideas.md", "# Master Ideas\n")
        zf.writestr("MANIFEST.json", json.dumps({"extracted_at": "2026-01-01"}))

    return zip_path


@pytest.fixture
def zip_with_double_workspace(tmp_path: pathlib.Path) -> pathlib.Path:
    """Create a zip that contains workspace/workspace/ double-nesting."""
    zip_path = tmp_path / "pipeline_extract_double.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            ".pipeline/projects/newsletter/state/current_idea.json",
            json.dumps({"title": "Newsletter", "status": "phase_1_executing", "phase": 1, "total_phases": 3}),
        )
        # Double-nested workspace
        zf.writestr(
            ".pipeline/projects/newsletter/workspace/workspace/main.py",
            "# double-nested main\n",
        )
        zf.writestr(
            ".pipeline/projects/newsletter/workspace/workspace/sub/deep.py",
            "# deep file\n",
        )
        # Also a normal file at the right level
        zf.writestr(
            ".pipeline/projects/newsletter/workspace/config.py",
            "# config\n",
        )
    return zip_path


@pytest.fixture
def zip_with_stray_phases(tmp_path: pathlib.Path) -> pathlib.Path:
    """Create a zip with stray phase files inside workspace/phases/."""
    zip_path = tmp_path / "pipeline_extract_stray.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            ".pipeline/projects/newsletter/state/current_idea.json",
            json.dumps({"title": "Newsletter", "status": "phase_1_executing", "phase": 1, "total_phases": 3}),
        )
        zf.writestr(
            ".pipeline/projects/newsletter/workspace/main.py",
            "# main\n",
        )
        # Stray phases inside workspace
        zf.writestr(
            ".pipeline/projects/newsletter/workspace/phases/validation_report.md",
            "## Validation Report\nStray file.\n",
        )
        zf.writestr(
            ".pipeline/projects/newsletter/workspace/phases/review.md",
            "## Review\nStray review.\n",
        )
    return zip_path


# ── should_skip tests ────────────────────────────────────────────────────────


class TestShouldSkip:
    def test_skips_pycache(self):
        assert import_zip.should_skip("__pycache__/foo.pyc") is True

    def test_skips_pytest_cache(self):
        assert import_zip.should_skip(".pytest_cache/.gitignore") is True

    def test_skips_node_modules(self):
        assert import_zip.should_skip("node_modules/pkg/index.js") is True

    def test_skips_venv(self):
        assert import_zip.should_skip(".venv/bin/python") is True

    def test_skips_git(self):
        assert import_zip.should_skip(".git/HEAD") is True

    def test_skips_pyc_extension(self):
        assert import_zip.should_skip("foo.pyc") is True

    def test_skips_pyo_extension(self):
        assert import_zip.should_skip("foo.pyo") is True

    def test_skips_log_extension(self):
        assert import_zip.should_skip("output.log") is True

    def test_skips_manifest(self):
        assert import_zip.should_skip("MANIFEST.json") is True

    def test_does_not_skip_normal_file(self):
        assert import_zip.should_skip(".pipeline/projects/foo/workspace/main.py") is False

    def test_does_not_skip_json(self):
        assert import_zip.should_skip(".pipeline/projects/foo/state/current_idea.json") is False

    def test_does_not_skip_md(self):
        assert import_zip.should_skip("master_ideas.md") is False

    def test_does_not_skip_shared_libs(self):
        assert import_zip.should_skip(".pipeline/shared_libs/utils.py") is False


# ── file_hash tests ──────────────────────────────────────────────────────────


class TestFileHash:
    def test_hash_of_existing_file(self, tmp_path: pathlib.Path):
        f = tmp_path / "test.txt"
        f.write_text("hello", encoding="utf-8")
        h = import_zip.file_hash(f)
        assert isinstance(h, str)
        assert len(h) == 64  # SHA-256 hex digest

    def test_hash_of_different_contents(self, tmp_path: pathlib.Path):
        f1 = tmp_path / "a.txt"
        f1.write_text("hello", encoding="utf-8")
        f2 = tmp_path / "b.txt"
        f2.write_text("world", encoding="utf-8")
        assert import_zip.file_hash(f1) != import_zip.file_hash(f2)

    def test_hash_of_same_contents(self, tmp_path: pathlib.Path):
        f1 = tmp_path / "a.txt"
        f1.write_text("hello", encoding="utf-8")
        f2 = tmp_path / "b.txt"
        f2.write_text("hello", encoding="utf-8")
        assert import_zip.file_hash(f1) == import_zip.file_hash(f2)


# ── zip_entry_hash tests ─────────────────────────────────────────────────────


class TestZipEntryHash:
    def test_hash_matches_file_content(self, tmp_path: pathlib.Path):
        zip_path = tmp_path / "test.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("hello.txt", "world content")

        with zipfile.ZipFile(zip_path, "r") as zf:
            h = import_zip.zip_entry_hash(zf, "hello.txt")

        # Verify by reading the entry directly
        entry_content = zf.read("hello.txt")
        import hashlib
        expected = hashlib.sha256(entry_content).hexdigest()
        assert h == expected

    def test_different_entries_different_hashes(self, tmp_path: pathlib.Path):
        zip_path = tmp_path / "test.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("a.txt", "aaa")
            zf.writestr("b.txt", "bbb")

        with zipfile.ZipFile(zip_path, "r") as zf:
            ha = import_zip.zip_entry_hash(zf, "a.txt")
            hb = import_zip.zip_entry_hash(zf, "b.txt")
        assert ha != hb


# ── find_latest_zip tests ────────────────────────────────────────────────────


class TestFindLatestZip:
    @mock.patch.object(import_zip.pathlib.Path, "home")
    def test_finds_latest_zip(self, mock_home, tmp_path):
        downloads = tmp_path / "Downloads"
        downloads.mkdir()

        # Create two zips with different mtimes
        z1 = downloads / "pipeline_extract_20260101_120000.zip"
        z1.write_bytes(b"fake")
        z1.touch()

        z2 = downloads / "pipeline_extract_20260102_120000.zip"
        z2.write_bytes(b"fake")
        z2.touch()

        # z2 is newer
        mock_home.return_value = downloads
        result = import_zip.find_latest_zip()
        assert result == z2

    def test_finds_zip_in_current_dir(self, tmp_path):
        # Create a zip in tmp_path
        z = tmp_path / "pipeline_extract_20260101_120000.zip"
        z.write_bytes(b"fake")

        with mock.patch.object(import_zip.pathlib.Path, "home", return_value=tmp_path):
            with mock.patch.object(import_zip.pathlib.Path, "cwd", return_value=tmp_path):
                result = import_zip.find_latest_zip()
                assert result == z

    def test_no_zips_raises(self, tmp_path):
        downloads = tmp_path / "Downloads"
        downloads.mkdir()

        with mock.patch.object(import_zip.pathlib.Path, "home", return_value=downloads):
            with mock.patch.object(import_zip.pathlib.Path, "cwd", return_value=downloads):
                with pytest.raises(SystemExit):
                    import_zip.find_latest_zip()


# ── import_zip function tests ────────────────────────────────────────────────


class TestImportZip:
    def test_imports_new_files(self, tmp_root: pathlib.Path, sample_zip: pathlib.Path):
        """Import should create new files in dest_root."""
        import_zip.import_zip(sample_zip, dest_root=tmp_root, yes=True)

        # Check newsletter files
        assert (tmp_root / ".pipeline/projects/newsletter/state/current_idea.json").exists()
        assert (tmp_root / ".pipeline/projects/newsletter/workspace/main.py").exists()
        assert (tmp_root / ".pipeline/projects/newsletter/workspace/utils.py").exists()
        assert (tmp_root / ".pipeline/projects/newsletter/phases/phase_1/tasks.md").exists()
        assert (tmp_root / ".pipeline/projects/newsletter/phases/phase_1/validation_report.md").exists()
        assert (tmp_root / ".pipeline/projects/newsletter/phases/phase_2/tasks.md").exists()

        # Check blog files
        assert (tmp_root / ".pipeline/projects/blog/state/current_idea.json").exists()
        assert (tmp_root / ".pipeline/projects/blog/workspace/index.py").exists()

        # Check queues & state
        assert (tmp_root / ".pipeline/queues/executor.jsonl").exists()
        assert (tmp_root / ".pipeline/state/global_state.json").exists()
        assert (tmp_root / ".pipeline/shared_libs/utils.py").exists()

        # Check root files
        assert (tmp_root / "master_ideas.md").exists()
        assert (tmp_root / "MANIFEST.json").exists()

    def test_skips_unchanged_files(self, tmp_root: pathlib.Path, sample_zip: pathlib.Path):
        """If a file already exists with same content, it should be skipped."""
        # Pre-create the newsletter main.py with same content
        main_py = tmp_root / ".pipeline/projects/newsletter/workspace/main.py"
        main_py.parent.mkdir(parents=True, exist_ok=True)
        main_py.write_text("# newsletter main\nprint('hi')\n", encoding="utf-8")

        import_zip.import_zip(sample_zip, dest_root=tmp_root, yes=True)

        # main.py should NOT have been overwritten (content should be identical)
        assert main_py.exists()
        assert main_py.read_text(encoding="utf-8") == "# newsletter main\nprint('hi')\n"

    def test_overwrites_changed_files(self, tmp_root: pathlib.Path, sample_zip: pathlib.Path):
        """If a file exists but content differs, it should be overwritten."""
        main_py = tmp_root / ".pipeline/projects/newsletter/workspace/main.py"
        main_py.parent.mkdir(parents=True, exist_ok=True)
        main_py.write_text("# old content\n", encoding="utf-8")

        import_zip.import_zip(sample_zip, dest_root=tmp_root, yes=True)

        assert main_py.read_text(encoding="utf-8") == "# newsletter main\nprint('hi')\n"

    def test_dry_run_writes_nothing(self, tmp_root: pathlib.Path, sample_zip: pathlib.Path):
        """--dry-run should not create any files."""
        import_zip.import_zip(sample_zip, dest_root=tmp_root, dry_run=True)

        assert not (tmp_root / ".pipeline").exists()

    def test_project_filter(self, tmp_root: pathlib.Path, sample_zip: pathlib.Path):
        """--project should only import matching projects."""
        import_zip.import_zip(sample_zip, dest_root=tmp_root, yes=True, project="blog")

        assert (tmp_root / ".pipeline/projects/blog").exists()
        assert not (tmp_root / ".pipeline/projects/newsletter").exists()

    def test_project_filter_partial_match(self, tmp_root: pathlib.Path, sample_zip: pathlib.Path):
        """Project filter should support partial matches."""
        import_zip.import_zip(sample_zip, dest_root=tmp_root, yes=True, project="news")

        assert (tmp_root / ".pipeline/projects/newsletter").exists()
        assert not (tmp_root / ".pipeline/projects/blog").exists()

    def test_only_state_skips_workspace(self, tmp_root: pathlib.Path, sample_zip: pathlib.Path):
        """--only-state should skip workspace/ files but keep state/phases."""
        import_zip.import_zip(sample_zip, dest_root=tmp_root, yes=True, only_state=True)

        # State files should exist
        assert (tmp_root / ".pipeline/projects/newsletter/state/current_idea.json").exists()
        assert (tmp_root / ".pipeline/projects/newsletter/phases/phase_1/tasks.md").exists()

        # Workspace files should NOT exist
        assert not (tmp_root / ".pipeline/projects/newsletter/workspace/main.py").exists()
        assert not (tmp_root / ".pipeline/projects/newsletter/workspace/utils.py").exists()

    def test_only_state_keeps_shared_libs(self, tmp_root: pathlib.Path, sample_zip: pathlib.Path):
        """--only-state should keep shared_libs/."""
        import_zip.import_zip(sample_zip, dest_root=tmp_root, yes=True, only_state=True)

        assert (tmp_root / ".pipeline/shared_libs/utils.py").exists()

    def test_only_state_keeps_queues(self, tmp_root: pathlib.Path, sample_zip: pathlib.Path):
        """--only-state should keep queues/."""
        import_zip.import_zip(sample_zip, dest_root=tmp_root, yes=True, only_state=True)

        assert (tmp_root / ".pipeline/queues/executor.jsonl").exists()

    def test_nothing_to_import(self, tmp_root: pathlib.Path, sample_zip: pathlib.Path):
        """If all files already exist with same content, nothing should be imported."""
        # First import
        import_zip.import_zip(sample_zip, dest_root=tmp_root, yes=True)

        # Second import should report nothing to do
        import_zip.import_zip(sample_zip, dest_root=tmp_root, yes=True)

        # Files should still exist
        assert (tmp_root / ".pipeline/projects/newsletter/workspace/main.py").exists()

    def test_creates_parent_directories(self, tmp_root: pathlib.Path, sample_zip: pathlib.Path):
        """Import should create all necessary parent directories."""
        # Start with empty dest
        assert not (tmp_root / ".pipeline").exists()

        import_zip.import_zip(sample_zip, dest_root=tmp_root, yes=True)

        assert (tmp_root / ".pipeline").exists()
        assert (tmp_root / ".pipeline/projects").exists()
        assert (tmp_root / ".pipeline/projects/newsletter").exists()


# ── fix_double_workspace tests ───────────────────────────────────────────────


class TestFixDoubleWorkspace:
    def test_flattens_double_nesting(self, tmp_path: pathlib.Path, zip_with_double_workspace: pathlib.Path):
        """Double-nested workspace should be flattened."""
        # Extract to a temp dir first
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = pathlib.Path(tmp_dir)
            with zipfile.ZipFile(zip_with_double_workspace, "r") as zf:
                zf.extractall(tmp)

            remote_pipeline = tmp / ".pipeline"
            remote_proj = remote_pipeline / "projects" / "newsletter"

            moved = import_zip.fix_double_workspace(remote_proj)

            # Files should now be in workspace/ not workspace/workspace/
            ws = remote_proj / "workspace"
            assert (ws / "main.py").exists()
            assert (ws / "sub" / "deep.py").exists()
            assert (ws / "config.py").exists()
            assert not (ws / "workspace").exists()
            assert moved > 0

    def test_no_double_nesting_returns_zero(self, tmp_path: pathlib.Path, sample_zip: pathlib.Path):
        """If there's no double-nesting, return 0."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = pathlib.Path(tmp_dir)
            with zipfile.ZipFile(sample_zip, "r") as zf:
                zf.extractall(tmp)

            remote_pipeline = tmp / ".pipeline"
            remote_proj = remote_pipeline / "projects" / "newsletter"

            moved = import_zip.fix_double_workspace(remote_proj)
            assert moved == 0


# ── fix_stray_phases tests ───────────────────────────────────────────────────


class TestFixStrayPhases:
    def test_moves_stray_phases(self, tmp_path: pathlib.Path, zip_with_stray_phases: pathlib.Path):
        """Stray phase files should be moved to the correct location."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = pathlib.Path(tmp_dir)
            with zipfile.ZipFile(zip_with_stray_phases, "r") as zf:
                zf.extractall(tmp)

            remote_pipeline = tmp / ".pipeline"
            remote_proj = remote_pipeline / "projects" / "newsletter"

            moved = import_zip.fix_stray_phases(remote_proj)

            # Files should be in phases/ not workspace/phases/
            phases = remote_proj / "phases"
            assert (phases / "validation_report.md").exists()
            assert (phases / "review.md").exists()
            assert not (remote_proj / "workspace" / "phases").exists()
            assert moved > 0

    def test_no_stray_phases_returns_zero(self, tmp_path: pathlib.Path, sample_zip: pathlib.Path):
        """If there are no stray phases, return 0."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = pathlib.Path(tmp_dir)
            with zipfile.ZipFile(sample_zip, "r") as zf:
                zf.extractall(tmp)

            remote_pipeline = tmp / ".pipeline"
            remote_proj = remote_pipeline / "projects" / "newsletter"

            moved = import_zip.fix_stray_phases(remote_proj)
            assert moved == 0


# ── merge_state tests ────────────────────────────────────────────────────────


class TestMergeState:
    def test_remote_ahead_updates_local(self, tmp_path: pathlib.Path):
        """If remote status is more advanced, local should be updated."""
        local = tmp_path / "local.json"
        local.write_text(json.dumps({"status": "phase_1_planning", "phase": 1}), encoding="utf-8")

        remote = tmp_path / "remote.json"
        remote.write_text(json.dumps({"status": "phase_2_executing", "phase": 2}), encoding="utf-8")

        result = import_zip.merge_state(local, remote)
        assert result is True
        updated = json.loads(local.read_text(encoding="utf-8"))
        assert updated["status"] == "phase_2_executing"

    def test_local_ahead_keeps_local(self, tmp_path: pathlib.Path):
        """If local status is more advanced, local should NOT be updated."""
        local = tmp_path / "local.json"
        local.write_text(json.dumps({"status": "phase_3_executing", "phase": 3}), encoding="utf-8")

        remote = tmp_path / "remote.json"
        remote.write_text(json.dumps({"status": "phase_1_planning", "phase": 1}), encoding="utf-8")

        result = import_zip.merge_state(local, remote)
        assert result is False
        updated = json.loads(local.read_text(encoding="utf-8"))
        assert updated["status"] == "phase_3_executing"

    def test_same_status_keeps_local(self, tmp_path: pathlib.Path):
        """If statuses are equal, local should NOT be updated."""
        local = tmp_path / "local.json"
        local.write_text(json.dumps({"status": "phase_2_executing", "phase": 2}), encoding="utf-8")

        remote = tmp_path / "remote.json"
        remote.write_text(json.dumps({"status": "phase_2_executing", "phase": 2}), encoding="utf-8")

        result = import_zip.merge_state(local, remote)
        assert result is False

    def test_remote_no_file_creates_local(self, tmp_path: pathlib.Path):
        """If local doesn't exist, remote should be copied."""
        local = tmp_path / "local.json"
        remote = tmp_path / "remote.json"
        remote.write_text(json.dumps({"status": "phase_1_planning", "phase": 1}), encoding="utf-8")

        result = import_zip.merge_state(local, remote)
        assert result is True
        assert local.exists()
        updated = json.loads(local.read_text(encoding="utf-8"))
        assert updated["status"] == "phase_1_planning"

    def test_invalid_json_returns_false(self, tmp_path: pathlib.Path):
        """If remote JSON is invalid, return False."""
        local = tmp_path / "local.json"
        local.write_text(json.dumps({"status": "phase_1_planning"}), encoding="utf-8")

        remote = tmp_path / "remote.json"
        remote.write_text("not json", encoding="utf-8")

        result = import_zip.merge_state(local, remote)
        assert result is False


# ── print_manifest tests ───────────────────────────────────────────────────────


class TestPrintManifest:
    def test_manifest_shows_projects(self, tmp_path: pathlib.Path, sample_zip: pathlib.Path):
        """Manifest should show project names and statuses."""
        dest = tmp_path / "dest"
        import_zip.import_zip(sample_zip, dest_root=dest, yes=True)

        import io
        import sys
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        import_zip.print_manifest()

        output = sys.stdout.getvalue()
        sys.stdout = old_stdout

        assert "newsletter" in output
        assert "Blog" in output
        assert "phase_2_executing" in output
        assert "phase_1_planning" in output

    def test_manifest_with_master_plan(self, tmp_path: pathlib.Path, sample_zip: pathlib.Path):
        """Manifest should show master plan indicator."""
        dest = tmp_path / "dest"
        import_zip.import_zip(sample_zip, dest_root=dest, yes=True)

        # Add a master plan
        (dest / ".pipeline/projects/newsletter/state").mkdir(parents=True, exist_ok=True)
        (dest / ".pipeline/projects/newsletter/state/master_plan.md").write_text("# Plan\n")

        import io
        import sys
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        import_zip.print_manifest()

        output = sys.stdout.getvalue()
        sys.stdout = old_stdout

        assert "✅" in output  # master plan present

    def test_manifest_with_double_nesting_warning(self, tmp_path: pathlib.Path, zip_with_double_workspace: pathlib.Path):
        """Manifest should warn about double-nesting."""
        dest = tmp_path / "dest"
        import_zip.import_zip(zip_with_double_workspace, dest_root=dest, yes=True)

        import io
        import sys
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        import_zip.print_manifest()

        output = sys.stdout.getvalue()
        sys.stdout = old_stdout

        assert "⚠️" in output


# ── import_cloud_zip specific tests ────────────────────────────────────────


class TestImportCloudZip:
    def test_import_cloud_zip_basic(self, tmp_path: pathlib.Path, sample_zip: pathlib.Path):
        """Basic import_cloud_zip import should work."""
        import import_cloud_zip

        # Create a fake project root
        project_root = tmp_path / "project"
        project_root.mkdir()
        (project_root / ".pipeline").mkdir()

        with mock.patch.object(import_cloud_zip, "PROJECT_ROOT", project_root):
            with mock.patch.object(import_cloud_zip, "PIPELINE_DIR", project_root / ".pipeline"):
                import_cloud_zip.import_zip(sample_zip)

        # Files should be merged
        dest = project_root / ".pipeline"
        assert (dest / "projects/newsletter/workspace/main.py").exists()
        assert (dest / "projects/newsletter/phases/phase_1/tasks.md").exists()

    def test_import_cloud_zip_manifest_only(self, tmp_path: pathlib.Path):
        """Calling with 'manifest' arg should print manifest without importing."""
        import import_cloud_zip

        project_root = tmp_path / "project"
        project_root.mkdir()
        proj_dir = project_root / ".pipeline/projects/test_proj/state"
        proj_dir.mkdir(parents=True)
        (proj_dir / "current_idea.json").write_text(
            json.dumps({"title": "Test", "status": "complete", "phase": 1, "total_phases": 1}),
            encoding="utf-8",
        )

        with mock.patch.object(import_cloud_zip, "PROJECT_ROOT", project_root):
            with mock.patch.object(import_cloud_zip, "PIPELINE_DIR", project_root / ".pipeline"):
                import io
                import sys
                old_stdout = sys.stdout
                sys.stdout = io.StringIO()

                import_cloud_zip.import_zip("manifest")

                output = sys.stdout.getvalue()
                sys.stdout = old_stdout

                assert "Test" in output

    def test_import_cloud_zip_fixes_double_workspace(self, tmp_path: pathlib.Path, zip_with_double_workspace: pathlib.Path):
        """import_cloud_zip should fix double-nesting during import."""
        import import_cloud_zip

        project_root = tmp_path / "project"
        project_root.mkdir()
        (project_root / ".pipeline").mkdir()

        with mock.patch.object(import_cloud_zip, "PROJECT_ROOT", project_root):
            with mock.patch.object(import_cloud_zip, "PIPELINE_DIR", project_root / ".pipeline"):
                import_cloud_zip.import_zip(zip_with_double_workspace)

        dest = project_root / ".pipeline"
        ws = dest / "projects/newsletter/workspace"
        # After fix, files should be at workspace/ level, not workspace/workspace/
        assert (ws / "main.py").exists()
        assert not (ws / "workspace").exists()

    def test_import_cloud_zip_fixes_stray_phases(self, tmp_path: pathlib.Path, zip_with_stray_phases: pathlib.Path):
        """import_cloud_zip should fix stray phases during import."""
        import import_cloud_zip

        project_root = tmp_path / "project"
        project_root.mkdir()
        (project_root / ".pipeline").mkdir()

        with mock.patch.object(import_cloud_zip, "PROJECT_ROOT", project_root):
            with mock.patch.object(import_cloud_zip, "PIPELINE_DIR", project_root / ".pipeline"):
                import_cloud_zip.import_zip(zip_with_stray_phases)

        dest = project_root / ".pipeline"
        phases = dest / "projects/newsletter/phases"
        assert (phases / "validation_report.md").exists()
        assert (phases / "review.md").exists()


# ── Integration: full import_cloud_zip flow ──────────────────────────────────


class TestImportCloudZipIntegration:
    def test_full_flow_with_all_fixes(self, tmp_path: pathlib.Path):
        """Test the full import_cloud_zip flow with double-nesting and stray phases."""
        import import_cloud_zip

        # Create a zip with both issues
        zip_path = tmp_path / "pipeline_extract_full.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(
                ".pipeline/projects/test_proj/state/current_idea.json",
                json.dumps({"title": "Test", "status": "phase_1_executing", "phase": 1, "total_phases": 3}),
            )
            # Double-nested workspace
            zf.writestr(
                ".pipeline/projects/test_proj/workspace/workspace/code.py",
                "# code\n",
            )
            # Stray phase
            zf.writestr(
                ".pipeline/projects/test_proj/workspace/phases/validation_report.md",
                "## Validation\n",
            )
            # Normal file
            zf.writestr(
                ".pipeline/projects/test_proj/workspace/config.py",
                "# config\n",
            )

        project_root = tmp_path / "project"
        project_root.mkdir()
        (project_root / ".pipeline").mkdir()

        with mock.patch.object(import_cloud_zip, "PROJECT_ROOT", project_root):
            with mock.patch.object(import_cloud_zip, "PIPELINE_DIR", project_root / ".pipeline"):
                import_cloud_zip.import_zip(zip_path)

        dest = project_root / ".pipeline"
        ws = dest / "projects/test_proj/workspace"
        phases = dest / "projects/test_proj/phases"

        # Double-nesting fixed
        assert (ws / "code.py").exists()
        assert not (ws / "workspace").exists()

        # Stray phases fixed
        assert (phases / "validation_report.md").exists()

        # Normal file preserved
        assert (ws / "config.py").exists()

    def test_state_merge_preserves_local_advancement(self, tmp_path: pathlib.Path):
        """Local state that is more advanced should not be overwritten by cloud."""
        import import_cloud_zip

        project_root = tmp_path / "project"
        project_root.mkdir()
        local_state = project_root / ".pipeline/projects/test_proj/state/current_idea.json"
        local_state.parent.mkdir(parents=True, exist_ok=True)
        local_state.write_text(
            json.dumps({"title": "Test", "status": "phase_3_executing", "phase": 3, "total_phases": 5}),
            encoding="utf-8",
        )

        zip_path = tmp_path / "pipeline_extract.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(
                ".pipeline/projects/test_proj/state/current_idea.json",
                json.dumps({"title": "Test", "status": "phase_1_planning", "phase": 1, "total_phases": 5}),
            )

        (project_root / ".pipeline").mkdir(exist_ok=True)

        with mock.patch.object(import_cloud_zip, "PROJECT_ROOT", project_root):
            with mock.patch.object(import_cloud_zip, "PIPELINE_DIR", project_root / ".pipeline"):
                import_cloud_zip.import_zip(zip_path)

        # Local should still have phase_3
        updated = json.loads(local_state.read_text(encoding="utf-8"))
        assert updated["status"] == "phase_3_executing"

    def test_state_merge_applies_remote_when_ahead(self, tmp_path: pathlib.Path):
        """Remote state that is more advanced should overwrite local."""
        import import_cloud_zip

        project_root = tmp_path / "project"
        project_root.mkdir()
        local_state = project_root / ".pipeline/projects/test_proj/state/current_idea.json"
        local_state.parent.mkdir(parents=True, exist_ok=True)
        local_state.write_text(
            json.dumps({"title": "Test", "status": "phase_1_planning", "phase": 1, "total_phases": 5}),
            encoding="utf-8",
        )

        zip_path = tmp_path / "pipeline_extract.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(
                ".pipeline/projects/test_proj/state/current_idea.json",
                json.dumps({"title": "Test", "status": "phase_2_executing", "phase": 2, "total_phases": 5}),
            )

        (project_root / ".pipeline").mkdir(exist_ok=True)

        with mock.patch.object(import_cloud_zip, "PROJECT_ROOT", project_root):
            with mock.patch.object(import_cloud_zip, "PIPELINE_DIR", project_root / ".pipeline"):
                import_cloud_zip.import_zip(zip_path)

        # Local should now have phase_2
        updated = json.loads(local_state.read_text(encoding="utf-8"))
        assert updated["status"] == "phase_2_executing"
