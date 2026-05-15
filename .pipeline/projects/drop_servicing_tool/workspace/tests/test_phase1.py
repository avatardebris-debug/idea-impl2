"""Phase 1 — End-to-end verification tests."""

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest
import yaml

# ---- paths ---------------------------------------------------------------

WORKSPACE = Path(__file__).resolve().parent.parent
SOPS_DIR = WORKSPACE / "sops"
PROMPTS_DIR = WORKSPACE / "prompts"


# ---- helpers -------------------------------------------------------------

def _write_temp_sop(name: str, data: dict) -> Path:
    """Write a temporary SOP YAML and return its path."""
    p = SOPS_DIR / f"{name}.yaml"
    p.write_text(yaml.dump(data, default_flow_style=False), encoding="utf-8")
    return p


def _remove_temp_sop(name: str) -> None:
    (SOPS_DIR / f"{name}.yaml").unlink(missing_ok=True)


# ====================================================================
# Task 2 — SOP Schema
# ====================================================================

class TestSOPSchema:
    """Tests for sop_schema.py models and load_sop()."""

    def test_load_valid_blog_post(self):
        from drop_servicing_tool.sop_schema import load_sop

        sop = load_sop(SOPS_DIR / "blog_post.yaml")
        assert sop.name == "blog_post"
        assert len(sop.steps) == 4
        assert sop.inputs[0].name == "topic"
        assert sop.inputs[0].required is True

    def test_load_missing_file(self):
        from drop_servicing_tool.sop_schema import load_sop

        with pytest.raises(FileNotFoundError):
            load_sop(SOPS_DIR / "nonexistent.yaml")

    def test_load_invalid_sop_missing_name(self):
        from drop_servicing_tool.sop_schema import load_sop

        bad = {"description": "no name", "steps": [{"name": "s1", "description": "x"}]}
        _write_temp_sop("bad_no_name", bad)
        try:
            with pytest.raises(Exception):  # Pydantic ValidationError
                load_sop(SOPS_DIR / "bad_no_name.yaml")
        finally:
            _remove_temp_sop("bad_no_name")

    def test_load_invalid_sop_no_steps(self):
        from drop_servicing_tool.sop_schema import load_sop

        bad = {"name": "no_steps", "steps": []}
        _write_temp_sop("bad_no_steps", bad)
        try:
            with pytest.raises(Exception):
                load_sop(SOPS_DIR / "bad_no_steps.yaml")
        finally:
            _remove_temp_sop("bad_no_steps")

    def test_load_invalid_sop_duplicate_steps(self):
        from drop_servicing_tool.sop_schema import load_sop

        bad = {
            "name": "dup_steps",
            "steps": [
                {"name": "s1", "description": "a"},
                {"name": "s1", "description": "b"},
            ],
        }
        _write_temp_sop("bad_dup", bad)
        try:
            with pytest.raises(Exception):
                load_sop(SOPS_DIR / "bad_dup.yaml")
        finally:
            _remove_temp_sop("bad_dup")

    def test_validate_input_missing_required(self):
        from drop_servicing_tool.sop_schema import load_sop, validate_input

        sop = load_sop(SOPS_DIR / "blog_post.yaml")
        with pytest.raises(ValueError, match="(?i)required"):
            validate_input(sop, {})  # topic missing

    def test_validate_input_correct(self):
        from drop_servicing_tool.sop_schema import load_sop, validate_input

        sop = load_sop(SOPS_DIR / "blog_post.yaml")
        result = validate_input(sop, {"topic": "AI"})
        assert result["topic"] == "AI"

    def test_validate_input_wrong_type(self):
        from drop_servicing_tool.sop_schema import load_sop, validate_input

        sop = load_sop(SOPS_DIR / "blog_post.yaml")
        with pytest.raises(ValueError):
            validate_input(sop, {"topic": 123})  # number instead of string


# ====================================================================
# Task 3 — SOP Store
# ====================================================================

class TestSOPStore:
    """Tests for sop_store.py CRUD operations."""

    def test_list_sops_contains_blog_post(self):
        from drop_servicing_tool.sop_store import list_sops

        names = list_sops()
        assert "blog_post" in names

    def test_get_sop_blog_post(self):
        from drop_servicing_tool.sop_store import get_sop

        sop = get_sop("blog_post")
        assert sop.name == "blog_post"

    def test_create_and_delete_sop(self):
        from drop_servicing_tool.sop_store import create_sop, delete_sop, list_sops, get_sop_path

        test_name = "test_crud_sop"
        content = {
            "name": test_name,
            "description": "CRUD test SOP",
            "inputs": [],
            "steps": [{"name": "s1", "description": "step one"}],
        }
        try:
            create_sop(test_name, content)
            assert test_name in list_sops()

            path = get_sop_path(test_name)
            assert path.exists()

            assert delete_sop(test_name) is True
            assert test_name not in list_sops()
        finally:
            delete_sop(test_name)  # cleanup

    def test_delete_nonexistent(self):
        from drop_servicing_tool.sop_store import delete_sop

        assert delete_sop("no_such_sop_xyz") is False

    def test_get_sop_path(self):
        from drop_servicing_tool.sop_store import get_sop_path

        p = get_sop_path("blog_post")
        assert str(p).endswith("blog_post.yaml")


# ====================================================================
# Task 4 — Prompt Template System
# ====================================================================

class TestPromptTemplates:
    """Tests for prompts.py."""

    def test_load_default_template(self):
        from drop_servicing_tool.prompts import load_prompt_template

        tpl = load_prompt_template("default_step")
        assert "{{step_name}}" in tpl

    def test_fill_prompt(self):
        from drop_servicing_tool.prompts import fill_prompt

        tpl = "Hello {{name}}, you are {{age}}."
        result = fill_prompt(tpl, {"name": "Alice", "age": 30})
        assert "Hello Alice, you are 30." == result

    def test_fill_prompt_dict_value(self):
        from drop_servicing_tool.prompts import fill_prompt

        tpl = "Data: {{data}}"
        result = fill_prompt(tpl, {"data": {"key": "val"}})
        assert '"key": "val"' in result

    def test_build_step_prompt(self):
        from drop_servicing_tool.prompts import build_step_prompt
        from drop_servicing_tool.sop_schema import load_sop

        sop = load_sop(SOPS_DIR / "blog_post.yaml")
        prompt = build_step_prompt(sop, 0, {"topic": "AI"}, [])
        assert "AI" in prompt
        assert "research" in prompt  # step name
        assert "N/A" in prompt  # no previous output

    def test_build_step_prompt_with_previous(self):
        from drop_servicing_tool.prompts import build_step_prompt
        from drop_servicing_tool.sop_schema import load_sop

        sop = load_sop(SOPS_DIR / "blog_post.yaml")
        # The executor stores outputs as: {"research": parsed, "raw": raw_output}
        step_outputs = [{"research": {"raw": "research results"}, "raw": "research results"}]
        prompt = build_step_prompt(sop, 1, {"topic": "AI"}, step_outputs)
        assert "research results" in prompt

    def test_load_missing_template(self):
        from drop_servicing_tool.prompts import load_prompt_template

        with pytest.raises(FileNotFoundError):
            load_prompt_template("nonexistent_template_xyz")


# ====================================================================
# Task 5 — Executor Engine
# ====================================================================

class TestExecutor:
    """Tests for executor.py."""

    def test_execute_blog_post_mock(self):
        from drop_servicing_tool.executor import SOPExecutor, execute_sop
        from drop_servicing_tool.sop_store import get_sop

        sop = get_sop("blog_post")
        executor = SOPExecutor(sop)
        result = executor.run({"topic": "AI automation"})

        assert "_sop_name" in result
        assert len(executor.get_step_outputs()) == 4
        assert len(executor.get_execution_log()) == 4

    def test_execute_sop_convenience(self):
        from drop_servicing_tool.executor import execute_sop
        from drop_servicing_tool.executor import MockLLMClient

        result = execute_sop("blog_post", {"topic": "AI"}, llm_client=MockLLMClient())
        assert "_sop_name" in result

    def test_step_outputs_passed(self):
        """Verify that each step receives previous step output."""
        from drop_servicing_tool.executor import SOPExecutor
        from drop_servicing_tool.sop_store import get_sop

        class CountingMockLLM:
            def __init__(self) -> None:
                self.call_count = 0

            def call(self, system_prompt: str, user_prompt: str) -> str:
                self.call_count += 1
                # Include call count in output so we can verify context passing
                return json.dumps({
                    "raw": f"Step {self.call_count} output",
                    "step_name": "counted",
                    "tokens_used": 0,
                })

        sop = get_sop("blog_post")
        client = CountingMockLLM()
        executor = SOPExecutor(sop, client)
        result = executor.run({"topic": "test"})

        assert client.call_count == 4
        assert result["_sop_name"] == "blog_post"

    def test_invalid_input_raises(self):
        from drop_servicing_tool.executor import SOPExecutor
        from drop_servicing_tool.sop_store import get_sop

        sop = get_sop("blog_post")
        executor = SOPExecutor(sop)
        with pytest.raises(ValueError):
            executor.run({})  # missing required 'topic'

    def test_execution_log(self):
        from drop_servicing_tool.executor import SOPExecutor
        from drop_servicing_tool.sop_store import get_sop

        sop = get_sop("blog_post")
        executor = SOPExecutor(sop)
        executor.run({"topic": "test"})
        log = executor.get_execution_log()

        assert len(log) == 4
        assert log[0].step_name == "research"
        assert log[0].duration_seconds >= 0
        assert log[0].error is None

    def test_mock_mode_deterministic(self):
        from drop_servicing_tool.executor import SOPExecutor, MockLLMClient
        from drop_servicing_tool.sop_store import get_sop

        sop = get_sop("blog_post")
        for _ in range(3):
            executor = SOPExecutor(sop, MockLLMClient())
            result = executor.run({"topic": "test"})
            # All runs should produce the same output structure
            assert "_sop_name" in result


# ====================================================================
# Task 6 — CLI
# ====================================================================

class TestCLI:
    """Tests for cli.py via subprocess."""

    @pytest.fixture(autouse=True)
    def _tmp_dir(self, tmp_path: Path):
        """Use a temporary sops directory for CLI tests.

        Uses `exist_ok=True` to avoid conflicts with the autouse
        ``_tmp_env`` fixture from ``conftest.py``, which also creates
        the ``sops`` and ``prompts`` directories under ``tmp_path``.
        """
        self.tmp_dir = tmp_path
        self.tmp_sops = tmp_path / "sops"
        self.tmp_prompts = tmp_path / "prompts"
        # use exist_ok=True to avoid FileExistsError when _tmp_env already created them
        self.tmp_sops.mkdir(parents=True, exist_ok=True)
        self.tmp_prompts.mkdir(parents=True, exist_ok=True)
        # Clear out any SOPs copied by conftest.py's _tmp_env
        for f in self.tmp_sops.glob("*.yaml"):
            f.unlink()
        self._old_env = {}
        import os
        for key in ("DST_SOPS_DIR", "DST_PROMPTS_DIR"):
            self._old_env[key] = os.environ.get(key)
            os.environ[key] = str(self.tmp_sops if key == "DST_SOPS_DIR" else self.tmp_prompts)

    def teardown_method(self) -> None:
        import os
        for key, val in self._old_env.items():
            if val is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = val

    def _run_cli(self, *args: str) -> tuple[int, str, str]:
        """Run the CLI as a subprocess and return (rc, stdout, stderr)."""
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "drop_servicing_tool.cli"] + list(args),
            cwd=WORKSPACE,
            capture_output=True,
            text=True,
            env=os.environ.copy(),
        )
        return result.returncode, result.stdout, result.stderr

    def test_cli_list_empty(self):
        import os
        print(f"ENV: {os.environ.get('DST_SOPS_DIR')}")
        rc, out, err = self._run_cli("list")
        print(f"OUT: {out}")
        assert rc == 0
        assert "No SOPs found" in out or "Available SOPs (0)" in out

    def test_cli_list_with_sop(self):
        # Create an SOP file in the temp directory
        sop_data = {
            "name": "my_sop",
            "description": "test",
            "inputs": [],
            "steps": [{"name": "s1", "description": "x"}],
        }
        (self.tmp_sops / "my_sop.yaml").write_text(yaml.dump(sop_data))

        rc, out, err = self._run_cli("list")
        assert rc == 0
        assert "my_sop" in out

    def test_cli_create(self):
        rc, out, err = self._run_cli("create", "my_new_sop")
        assert rc == 0
        assert "my_new_sop" in out
        assert (self.tmp_sops / "my_new_sop.yaml").exists()

    def test_cli_run_mock(self):
        # Put blog_post SOP in temp sops dir
        blog_sop = {
            "name": "blog_post",
            "description": "Generate a complete blog post from a topic",
            "inputs": [{"name": "topic", "type": "string", "required": True, "description": "The main topic"}],
            "steps": [
                {"name": "research", "description": "Research.", "prompt_template": "default_step", "llm_required": True},
                {"name": "outline", "description": "Outline.", "prompt_template": "default_step", "llm_required": True},
                {"name": "draft", "description": "Draft.", "prompt_template": "default_step", "llm_required": True},
                {"name": "title_options", "description": "Titles.", "prompt_template": "default_step", "llm_required": True},
            ],
            "output_format": "Complete blog post",
        }
        (self.tmp_sops / "blog_post.yaml").write_text(yaml.dump(blog_sop))
        # Copy default_step prompt
        default_tpl = (PROMPTS_DIR / "default_step.md").read_text()
        (self.tmp_prompts / "default_step.md").write_text(default_tpl)

        rc, out, err = self._run_cli(
            "run", "blog_post",
            "--input", '{"topic": "AI automation"}',
            "--mock",
        )
        assert rc == 0
        result = json.loads(out)
        assert "_sop_name" in result

    def test_cli_run_missing_sop(self):
        rc, out, err = self._run_cli("run", "nope", "--input", '{"topic": "x"}')
        assert rc != 0

    def test_cli_run_invalid_json(self):
        rc, out, err = self._run_cli("run", "blog_post", "--input", "not-json")
        assert rc != 0

    def test_cli_run_with_file_input(self, tmp_path: Path):
        # Create input file
        input_file = tmp_path / "input.json"
        input_file.write_text('{"topic": "from file"}')

        # Put blog_post SOP in temp sops dir
        blog_sop = {
            "name": "blog_post",
            "description": "Generate a complete blog post from a topic",
            "inputs": [{"name": "topic", "type": "string", "required": True, "description": "The main topic"}],
            "steps": [
                {"name": "research", "description": "Research.", "prompt_template": "default_step", "llm_required": True},
                {"name": "outline", "description": "Outline.", "prompt_template": "default_step", "llm_required": True},
                {"name": "draft", "description": "Draft.", "prompt_template": "default_step", "llm_required": True},
                {"name": "title_options", "description": "Titles.", "prompt_template": "default_step", "llm_required": True},
            ],
            "output_format": "Complete blog post",
        }
        (self.tmp_sops / "blog_post.yaml").write_text(yaml.dump(blog_sop))
        default_tpl = (PROMPTS_DIR / "default_step.md").read_text()
        (self.tmp_prompts / "default_step.md").write_text(default_tpl)

        rc, out, err = self._run_cli(
            "run", "blog_post",
            "--input", f"@{input_file}",
            "--mock",
        )
        assert rc == 0

    def test_cli_run_with_output_dir(self, tmp_path: Path):
        blog_sop = {
            "name": "blog_post",
            "description": "Generate a complete blog post from a topic",
            "inputs": [{"name": "topic", "type": "string", "required": True, "description": "The main topic"}],
            "steps": [
                {"name": "research", "description": "Research.", "prompt_template": "default_step", "llm_required": True},
                {"name": "outline", "description": "Outline.", "prompt_template": "default_step", "llm_required": True},
                {"name": "draft", "description": "Draft.", "prompt_template": "default_step", "llm_required": True},
                {"name": "title_options", "description": "Titles.", "prompt_template": "default_step", "llm_required": True},
            ],
            "output_format": "Complete blog post",
        }
        (self.tmp_sops / "blog_post.yaml").write_text(yaml.dump(blog_sop))
        default_tpl = (PROMPTS_DIR / "default_step.md").read_text()
        (self.tmp_prompts / "default_step.md").write_text(default_tpl)

        out_dir = tmp_path / "output"
        rc, out, err = self._run_cli(
            "run", "blog_post",
            "--input", '{"topic": "test"}',
            "--mock",
            "--output-dir", str(out_dir),
        )
        assert rc == 0
        assert (out_dir / "blog_post_output.json").exists()
        assert (out_dir / "blog_post_log.json").exists()


# ====================================================================
# Task 7 — Blog Post SOP end-to-end
# ====================================================================

class TestBlogPostSOP:
    """Integration tests for the blog_post SOP."""

    def test_blog_post_all_steps_executed(self):
        from drop_servicing_tool.executor import SOPExecutor
        from drop_servicing_tool.sop_store import get_sop

        sop = get_sop("blog_post")
        executor = SOPExecutor(sop)
        result = executor.run({"topic": "AI automation"})

        assert len(executor.get_step_outputs()) == 4
        log = executor.get_execution_log()
        step_names = [l.step_name for l in log]
        assert step_names == ["research", "outline", "draft", "title_options"]

    def test_blog_post_output_has_all_keys(self):
        from drop_servicing_tool.executor import SOPExecutor
        from drop_servicing_tool.sop_store import get_sop

        sop = get_sop("blog_post")
        executor = SOPExecutor(sop)
        result = executor.run({"topic": "AI automation"})

        assert "research" in result
        assert "outline" in result
        assert "draft" in result
        assert "title_options" in result
        assert "_sop_name" in result

    def test_blog_post_output_is_dict(self):
        from drop_servicing_tool.executor import SOPExecutor
        from drop_servicing_tool.sop_store import get_sop

        sop = get_sop("blog_post")
        executor = SOPExecutor(sop)
        result = executor.run({"topic": "AI automation"})

        assert isinstance(result, dict)

    def test_invalid_sop_yaml_rejected(self):
        """Ensure malformed SOP YAML is rejected."""
        from drop_servicing_tool.sop_schema import load_sop

        bad_yaml = SOPS_DIR / "bad_invalid.yaml"
        bad_yaml.write_text("name: bad\nsteps: not_a_list\n")
        try:
            with pytest.raises(Exception):
                load_sop(bad_yaml)
        finally:
            bad_yaml.unlink(missing_ok=True)
