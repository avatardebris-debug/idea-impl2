"""block_registry v0 — sockets, sandbox promote, attach gates."""

from __future__ import annotations

import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _reload_pipeline(monkeypatch: pytest.MonkeyPatch, pipeline: pathlib.Path) -> None:
    monkeypatch.setenv("PIPELINE_DIR", str(pipeline))
    monkeypatch.delenv("PIPELINE_CLOUD", raising=False)
    monkeypatch.setenv("KEEP_GOAL_TRACES", "1")
    from pipeline.pipeline_config import reload_pipeline_dir

    reload_pipeline_dir()


def _write_skill(root: pathlib.Path, name: str, body: str, *, with_frontmatter: bool = True) -> pathlib.Path:
    sk = root / "skills" / name
    sk.mkdir(parents=True, exist_ok=True)
    if with_frontmatter:
        text = f"---\nname: {name}\n---\n\n{body}\n"
    else:
        text = body + "\n"
    path = sk / "SKILL.md"
    path.write_text(text, encoding="utf-8")
    return path


def test_register_draft_skill_from_temp(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    _reload_pipeline(monkeypatch, pipeline)

    skills_root = tmp_path / "skill_roots"
    _write_skill(skills_root, "my-test-skill", "# My Test Skill\n\nDo the thing.")
    monkeypatch.setattr(
        "pipeline.skill_load.skill_search_roots",
        lambda: [skills_root / "skills"],
    )

    from pipeline.block_registry import get_block, register_block_from_skill
    from pipeline.paths import get_pipeline_dir

    assert get_pipeline_dir() == pipeline.resolve()

    rec = register_block_from_skill("my-test-skill")
    assert rec["schema"] == "block.v1"
    assert rec["id"] == "skill_my-test-skill"
    assert rec["kind"] == "skill"
    assert rec["status"] == "draft"
    assert rec["name"] == "my-test-skill"
    assert (pipeline / "state" / "block_registry" / "blocks" / "skill_my-test-skill.json").is_file()
    loaded = get_block("skill_my-test-skill")
    assert loaded is not None
    assert loaded["status"] == "draft"


def test_sandbox_pass_and_secret_fail(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    _reload_pipeline(monkeypatch, pipeline)

    skills_root = tmp_path / "skill_roots"
    _write_skill(skills_root, "clean-skill", "# Clean\n\nSafe instructions only.")
    _write_skill(
        skills_root,
        "leaky-skill",
        "# Leaky\n\napi_key: sk-abcdefghijklmnopqrstuvwxyz0123456789\n",
    )
    monkeypatch.setattr(
        "pipeline.skill_load.skill_search_roots",
        lambda: [skills_root / "skills"],
    )

    from pipeline.block_registry import register_block_from_skill, sandbox_block

    clean = register_block_from_skill("clean-skill")
    out = sandbox_block(clean["id"])
    assert out["status"] == "sandboxed"
    assert out["sandbox_report"]["pass"] is True
    assert out["oracle"]["pass"] is True

    leaky = register_block_from_skill("leaky-skill")
    out2 = sandbox_block(leaky["id"])
    assert out2["status"] == "draft"
    assert out2["sandbox_report"]["pass"] is False
    names = {c["name"] for c in out2["sandbox_report"]["checks"] if not c["pass"]}
    assert "no_secrets" in names


def test_promote_only_when_sandboxed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    _reload_pipeline(monkeypatch, pipeline)

    skills_root = tmp_path / "skill_roots"
    _write_skill(skills_root, "promo-skill", "# Promo\n\nBody.")
    monkeypatch.setattr(
        "pipeline.skill_load.skill_search_roots",
        lambda: [skills_root / "skills"],
    )

    from pipeline.block_registry import (
        promote_block,
        register_block_from_skill,
        sandbox_block,
    )

    rec = register_block_from_skill("promo-skill")
    with pytest.raises(ValueError, match="draft"):
        promote_block(rec["id"])

    sandbox_block(rec["id"])
    promoted = promote_block(rec["id"], notes="v0 ok")
    assert promoted["status"] == "verified"
    assert "v0 ok" in (promoted.get("promote_notes") or "")

    # one-shot sandbox_if_needed
    _write_skill(skills_root, "one-shot", "# One\n\nShot.")
    r2 = register_block_from_skill("one-shot")
    p2 = promote_block(r2["id"], sandbox_if_needed=True)
    assert p2["status"] == "verified"


def test_attach_rejects_draft_accepts_verified(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    _reload_pipeline(monkeypatch, pipeline)

    skills_root = tmp_path / "skill_roots"
    _write_skill(skills_root, "attach-me", "# Attach\n\nMe.")
    monkeypatch.setattr(
        "pipeline.skill_load.skill_search_roots",
        lambda: [skills_root / "skills"],
    )

    from pipeline.block_registry import (
        attach_block,
        promote_block,
        register_block_from_skill,
        sandbox_block,
    )

    rec = register_block_from_skill("attach-me")
    with pytest.raises(ValueError, match="attach rejected"):
        attach_block("executor.pre_task_skills", rec["id"])

    sandbox_block(rec["id"])
    with pytest.raises(ValueError, match="attach rejected"):
        attach_block("executor.pre_task_skills", rec["id"])

    promote_block(rec["id"])
    sock = attach_block("executor.pre_task_skills", rec["id"])
    assert rec["id"] in sock["block_ids"]


def test_resolve_returns_body(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    _reload_pipeline(monkeypatch, pipeline)

    skills_root = tmp_path / "skill_roots"
    _write_skill(skills_root, "resolve-me", "# Resolve Me\n\nUNIQUE_RESOLVE_MARKER_42.")
    monkeypatch.setattr(
        "pipeline.skill_load.skill_search_roots",
        lambda: [skills_root / "skills"],
    )

    from pipeline.block_registry import (
        attach_block,
        load_socket_skill_bodies,
        promote_block,
        register_block_from_skill,
        resolve_socket_skills,
        sandbox_block,
    )

    rec = register_block_from_skill("resolve-me")
    sandbox_block(rec["id"])
    promote_block(rec["id"])
    attach_block("executor.pre_task_skills", rec["id"])

    items = resolve_socket_skills("executor.pre_task_skills")
    assert len(items) == 1
    assert "UNIQUE_RESOLVE_MARKER_42" in items[0]["body"]

    bodies = load_socket_skill_bodies("executor.pre_task_skills")
    assert "UNIQUE_RESOLVE_MARKER_42" in bodies
    assert "resolve-me" in bodies


def test_revoke_detaches_and_blocks_resolve(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    _reload_pipeline(monkeypatch, pipeline)

    skills_root = tmp_path / "skill_roots"
    _write_skill(skills_root, "revoke-me", "# Revoke\n\nBody.")
    monkeypatch.setattr(
        "pipeline.skill_load.skill_search_roots",
        lambda: [skills_root / "skills"],
    )

    from pipeline.block_registry import (
        attach_block,
        get_socket,
        promote_block,
        register_block_from_skill,
        resolve_socket_skills,
        revoke_block,
        sandbox_block,
    )

    rec = register_block_from_skill("revoke-me")
    sandbox_block(rec["id"])
    promote_block(rec["id"])
    attach_block("manager.blocker_skill", rec["id"])
    assert rec["id"] in get_socket("manager.blocker_skill")["block_ids"]

    revoke_block(rec["id"], detach=True)
    assert rec["id"] not in get_socket("manager.blocker_skill")["block_ids"]
    assert resolve_socket_skills("manager.blocker_skill") == []


def test_list_sockets_and_cli_smoke(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    _reload_pipeline(monkeypatch, pipeline)

    from pipeline.block_registry import list_sockets

    socks = list_sockets()
    names = {s["name"] for s in socks}
    assert "executor.pre_task_skills" in names
    assert "manager.blocker_skill" in names
    assert "goal.policy_skill" in names
    assert "phase_planner.skill" in names

    # CLI via importlib (scripts/ is not a package)
    import importlib.util

    cli_path = ROOT / "scripts" / "block_registry.py"
    spec = importlib.util.spec_from_file_location("block_registry_cli", cli_path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    cli_main = mod.main

    skills_root = tmp_path / "skill_roots"
    _write_skill(skills_root, "cli-skill", "# CLI\n\nOk.")
    monkeypatch.setattr(
        "pipeline.skill_load.skill_search_roots",
        lambda: [skills_root / "skills"],
    )

    rc = cli_main(["--pipeline-dir", str(pipeline), "register-skill", "--name", "cli-skill"])
    assert rc == 0
    rc = cli_main(["--pipeline-dir", str(pipeline), "sandbox", "--id", "skill_cli-skill"])
    assert rc == 0
    rc = cli_main(["--pipeline-dir", str(pipeline), "promote", "--id", "skill_cli-skill"])
    assert rc == 0
    rc = cli_main(
        [
            "--pipeline-dir",
            str(pipeline),
            "attach",
            "--socket",
            "executor.pre_task_skills",
            "--id",
            "skill_cli-skill",
        ]
    )
    assert rc == 0
    rc = cli_main(["--pipeline-dir", str(pipeline), "list-blocks"])
    assert rc == 0
    rc = cli_main(["--pipeline-dir", str(pipeline), "list-sockets"])
    assert rc == 0
    rc = cli_main(
        [
            "--pipeline-dir",
            str(pipeline),
            "resolve",
            "--socket",
            "executor.pre_task_skills",
        ]
    )
    assert rc == 0
