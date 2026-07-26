"""block_registry v0 — sockets, sandbox promote, attach gates, path/secret safety."""

from __future__ import annotations

import importlib.util
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


def _write_skill(
    root: pathlib.Path, name: str, body: str, *, with_frontmatter: bool = True
) -> pathlib.Path:
    sk = root / "skills" / name
    sk.mkdir(parents=True, exist_ok=True)
    if with_frontmatter:
        text = f"---\nname: {name}\n---\n\n{body}\n"
    else:
        text = body + "\n"
    path = sk / "SKILL.md"
    path.write_text(text, encoding="utf-8")
    return path


def _skill_roots(monkeypatch: pytest.MonkeyPatch, skills_root: pathlib.Path) -> None:
    monkeypatch.setattr(
        "pipeline.skill_load.skill_search_roots",
        lambda: [skills_root / "skills"],
    )


def test_register_draft_skill_from_temp(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    _reload_pipeline(monkeypatch, pipeline)

    skills_root = tmp_path / "skill_roots"
    _write_skill(skills_root, "my-test-skill", "# My Test Skill\n\nDo the thing.")
    _skill_roots(monkeypatch, skills_root)

    from pipeline.block_registry import get_block, register_block_from_skill
    from pipeline.paths import get_pipeline_dir

    assert get_pipeline_dir() == pipeline.resolve()

    rec = register_block_from_skill("my-test-skill")
    assert rec["schema"] == "block.v1"
    assert rec["id"] == "skill_my-test-skill"
    assert rec["kind"] == "skill"
    assert rec["status"] == "draft"
    assert rec["name"] == "my-test-skill"
    assert "_resolved_source" not in rec
    assert (
        pipeline / "state" / "block_registry" / "blocks" / "skill_my-test-skill.json"
    ).is_file()
    loaded = get_block("skill_my-test-skill")
    assert loaded is not None
    assert loaded["status"] == "draft"
    assert "_resolved_source" not in loaded


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
    _skill_roots(monkeypatch, skills_root)

    from pipeline.block_registry import register_block_from_skill, sandbox_block

    clean = register_block_from_skill("clean-skill")
    out = sandbox_block(clean["id"])
    assert out["status"] == "sandboxed"
    assert out["sandbox_report"]["pass"] is True
    assert out["oracle"]["pass"] is True
    assert out["sandbox_report"].get("content_sha256")

    leaky = register_block_from_skill("leaky-skill")
    out2 = sandbox_block(leaky["id"])
    assert out2["status"] == "draft"
    assert out2["sandbox_report"]["pass"] is False
    names = {c["name"] for c in out2["sandbox_report"]["checks"] if not c["pass"]}
    assert "no_secrets" in names


def test_secret_variants(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    _reload_pipeline(monkeypatch, pipeline)
    skills_root = tmp_path / "skill_roots"
    _skill_roots(monkeypatch, skills_root)

    from pipeline.block_registry import register_block_from_skill, sandbox_block

    cases = [
        ("sk-proj-variant", "sk-proj-abcdefghijklmnopqrstuvwxyz012345"),
        ("env-openai", "OPENAI_API_KEY=sk-abcdefghijklmnopqrstuvwxyz99"),
        ("env-xai", "XAI_API_KEY=xai-abcdefghijklmnopqrstuvwxyz99"),
        (
            "privkey",
            "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA...\n-----END RSA PRIVATE KEY-----",
        ),
    ]
    for name, payload in cases:
        _write_skill(skills_root, name, f"# Bad\n\n{payload}\n")
        rec = register_block_from_skill(name)
        out = sandbox_block(rec["id"])
        assert out["sandbox_report"]["pass"] is False, f"expected secret fail for {name}"
        assert out["status"] == "draft"
        detail = " ".join(
            c.get("detail") or ""
            for c in out["sandbox_report"]["checks"]
            if c.get("name") == "no_secrets"
        )
        assert detail != "ok", f"no_secrets should fail for {name}: {detail}"


def test_promote_only_when_sandboxed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    _reload_pipeline(monkeypatch, pipeline)

    skills_root = tmp_path / "skill_roots"
    _write_skill(skills_root, "promo-skill", "# Promo\n\nBody.")
    _skill_roots(monkeypatch, skills_root)

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
    assert (promoted.get("sandbox_report") or {}).get("promoted_content_sha256")

    _write_skill(skills_root, "one-shot", "# One\n\nShot.")
    r2 = register_block_from_skill("one-shot")
    p2 = promote_block(r2["id"], sandbox_if_needed=True)
    assert p2["status"] == "verified"


def test_promote_rejects_post_sandbox_edit(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """Content change after sandbox must fail promote (re-sandbox catches secrets/edits)."""
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    _reload_pipeline(monkeypatch, pipeline)
    skills_root = tmp_path / "skill_roots"
    path = _write_skill(skills_root, "toctou-skill", "# Clean\n\nOk body.")
    _skill_roots(monkeypatch, skills_root)

    from pipeline.block_registry import (
        promote_block,
        register_block_from_skill,
        sandbox_block,
    )

    rec = register_block_from_skill("toctou-skill")
    sandbox_block(rec["id"])
    # Edit source to inject secret after sandbox pass
    path.write_text(
        "---\nname: toctou-skill\n---\n\n# Bad\n\nOPENAI_API_KEY=sk-abcdefghijklmnopqrstuvwxyz99\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="sandbox failed|cannot promote"):
        promote_block(rec["id"])


def test_attach_rejects_draft_accepts_verified(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    _reload_pipeline(monkeypatch, pipeline)

    skills_root = tmp_path / "skill_roots"
    _write_skill(skills_root, "attach-me", "# Attach\n\nMe.")
    _skill_roots(monkeypatch, skills_root)

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


def test_force_attach_draft_does_not_resolve(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    _reload_pipeline(monkeypatch, pipeline)
    skills_root = tmp_path / "skill_roots"
    _write_skill(skills_root, "force-draft", "# Draft\n\nBody.")
    _skill_roots(monkeypatch, skills_root)

    from pipeline.block_registry import (
        attach_block,
        load_socket_skill_bodies,
        register_block_from_skill,
        resolve_socket_skills,
    )

    rec = register_block_from_skill("force-draft")
    sock = attach_block("executor.pre_task_skills", rec["id"], force=True)
    assert rec["id"] in sock["block_ids"]
    assert resolve_socket_skills("executor.pre_task_skills") == []
    assert load_socket_skill_bodies("executor.pre_task_skills") == ""


def test_resolve_returns_body(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    _reload_pipeline(monkeypatch, pipeline)

    skills_root = tmp_path / "skill_roots"
    _write_skill(skills_root, "resolve-me", "# Resolve Me\n\nUNIQUE_RESOLVE_MARKER_42.")
    _skill_roots(monkeypatch, skills_root)

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
    _skill_roots(monkeypatch, skills_root)

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


def test_prompt_path_reject_outside_roots(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    _reload_pipeline(monkeypatch, pipeline)

    outside = tmp_path / "outside_host" / "secret.md"
    outside.parent.mkdir(parents=True)
    outside.write_text("# host secret file\n", encoding="utf-8")

    from pipeline.block_registry import register_block_from_prompt_file

    with pytest.raises((FileNotFoundError, ValueError)):
        register_block_from_prompt_file(outside, "evil-prompt")

    # Path traversal relative string should not escape into host
    with pytest.raises((FileNotFoundError, ValueError)):
        register_block_from_prompt_file(
            str(pathlib.Path("..") / ".." / outside.name),
            "evil-prompt-2",
        )


def test_prompt_register_under_pipeline_dir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    _reload_pipeline(monkeypatch, pipeline)

    prompt = pipeline / "prompts" / "role.md"
    prompt.parent.mkdir(parents=True)
    prompt.write_text("# Role prompt\n\nBe helpful.\n", encoding="utf-8")

    from pipeline.block_registry import register_block_from_prompt_file, sandbox_block

    rec = register_block_from_prompt_file(prompt, "role-prompt")
    assert rec["id"] == "prompt_role-prompt"
    assert rec["status"] == "draft"
    assert "_resolved_source" not in rec
    out = sandbox_block(rec["id"])
    assert out["status"] == "sandboxed"


def test_kind_mismatch_and_max_n(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    _reload_pipeline(monkeypatch, pipeline)
    skills_root = tmp_path / "skill_roots"
    _skill_roots(monkeypatch, skills_root)

    prompt = pipeline / "prompts" / "p.md"
    prompt.parent.mkdir(parents=True)
    prompt.write_text("# p\n\nbody\n", encoding="utf-8")

    from pipeline.block_registry import (
        attach_block,
        promote_block,
        register_block_from_prompt_file,
        register_block_from_skill,
        sandbox_block,
    )

    prec = register_block_from_prompt_file(prompt, "only-prompt")
    sandbox_block(prec["id"])
    promote_block(prec["id"])
    with pytest.raises(ValueError, match="kind"):
        attach_block("manager.blocker_skill", prec["id"])

    # max_n=1 single socket replaces; list full for phase_planner still single
    _write_skill(skills_root, "s1", "# S1\n\nok")
    _write_skill(skills_root, "s2", "# S2\n\nok")
    r1 = register_block_from_skill("s1")
    r2 = register_block_from_skill("s2")
    sandbox_block(r1["id"])
    sandbox_block(r2["id"])
    promote_block(r1["id"])
    promote_block(r2["id"])
    attach_block("phase_planner.skill", r1["id"])
    # single cardinality replaces
    sock = attach_block("phase_planner.skill", r2["id"])
    assert sock["block_ids"] == [r2["id"]]


def test_allow_sandboxed_override(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    _reload_pipeline(monkeypatch, pipeline)
    skills_root = tmp_path / "skill_roots"
    _write_skill(skills_root, "sand-ok", "# Sand\n\nOk.")
    _skill_roots(monkeypatch, skills_root)

    from pipeline.block_registry import (
        attach_block,
        register_block_from_skill,
        registry_root,
        sandbox_block,
    )
    import json

    # Write defs_override before attach
    sockets = {
        "schema": "sockets.v1",
        "attachments": {n: [] for n in (
            "executor.pre_task_skills",
            "manager.blocker_skill",
            "goal.policy_skill",
            "phase_planner.skill",
        )},
        "defs_override": {
            "executor.pre_task_skills": {"allow_sandboxed": True},
        },
    }
    (registry_root() / "sockets.json").write_text(
        json.dumps(sockets, indent=2), encoding="utf-8"
    )

    rec = register_block_from_skill("sand-ok")
    sandbox_block(rec["id"])
    sock = attach_block("executor.pre_task_skills", rec["id"])
    assert rec["id"] in sock["block_ids"]


def test_verified_demote_on_resandbox_fail(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    _reload_pipeline(monkeypatch, pipeline)
    skills_root = tmp_path / "skill_roots"
    path = _write_skill(skills_root, "demote-me", "# Good\n\nBody.")
    _skill_roots(monkeypatch, skills_root)

    from pipeline.block_registry import (
        attach_block,
        get_block,
        get_socket,
        promote_block,
        register_block_from_skill,
        resolve_socket_skills,
        sandbox_block,
    )

    rec = register_block_from_skill("demote-me")
    sandbox_block(rec["id"])
    promote_block(rec["id"])
    attach_block("executor.pre_task_skills", rec["id"])
    assert resolve_socket_skills("executor.pre_task_skills")

    path.write_text(
        "---\nname: demote-me\n---\n\napi_key: sk-abcdefghijklmnopqrstuvwxyz0123456789\n",
        encoding="utf-8",
    )
    out = sandbox_block(rec["id"])
    assert out["status"] == "draft"
    assert out["sandbox_report"]["pass"] is False
    assert get_block(rec["id"])["status"] == "draft"
    # Detached from sockets on verified demote
    assert rec["id"] not in get_socket("executor.pre_task_skills")["block_ids"]
    assert resolve_socket_skills("executor.pre_task_skills") == []


def test_invalid_block_name(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    _reload_pipeline(monkeypatch, pipeline)

    from pipeline.block_registry import register_block_from_skill

    with pytest.raises(ValueError, match="invalid block name"):
        register_block_from_skill("../evil")
    with pytest.raises(ValueError, match="invalid block name"):
        register_block_from_skill("a/b")


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

    cli_path = ROOT / "scripts" / "block_registry.py"
    spec = importlib.util.spec_from_file_location("block_registry_cli", cli_path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    cli_main = mod.main

    skills_root = tmp_path / "skill_roots"
    _write_skill(skills_root, "cli-skill", "# CLI\n\nOk.")
    _skill_roots(monkeypatch, skills_root)

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
