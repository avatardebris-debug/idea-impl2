"""
block_registry v0 — skill/prompt block catalog + role sockets + promote pipeline.

Layout under PIPELINE_DIR:
  state/block_registry/blocks/{block_id}.json   (block.v1)
  state/block_registry/sockets.json             (attachments)

Sockets are fixed role slots; only verified (or sandboxed if socket allows)
blocks may attach. Promote path: register (draft) → sandbox → promote (verified).
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pipeline.paths import get_pipeline_dir, state_dir

SCHEMA = "block.v1"
BLOCK_STATUSES = frozenset({"draft", "sandboxed", "verified", "revoked"})
BLOCK_KINDS = frozenset({"skill", "prompt"})
RISK_CLASSES = frozenset({"low", "medium", "high"})

# Default max skill body size for sandbox (bytes).
DEFAULT_MAX_BYTES = 200_000

# Socket definitions (code defaults). Override via sockets.json "defs" key optional.
# allow_sandboxed: if True, attach accepts status sandboxed in addition to verified.
DEFAULT_SOCKETS: dict[str, dict[str, Any]] = {
    "executor.pre_task_skills": {
        "name": "executor.pre_task_skills",
        "cardinality": "list",
        "max_n": 8,
        "allow_sandboxed": False,
        "kinds": ["skill", "prompt"],
        "description": "Skills/prompts injected before executor task work",
    },
    "manager.blocker_skill": {
        "name": "manager.blocker_skill",
        "cardinality": "single",
        "max_n": 1,
        "allow_sandboxed": False,
        "kinds": ["skill"],
        "description": "Optional manager blocker-identifier skill",
    },
    "goal.policy_skill": {
        "name": "goal.policy_skill",
        "cardinality": "single",
        "max_n": 1,
        "allow_sandboxed": False,
        "kinds": ["skill"],
        "description": "Optional goal-policy skill body",
    },
    "phase_planner.skill": {
        "name": "phase_planner.skill",
        "cardinality": "single",
        "max_n": 1,
        "allow_sandboxed": False,
        "kinds": ["skill"],
        "description": "Optional phase planner skill",
    },
}

# Obvious secret patterns (static sandbox).
_SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("private_key_header", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    (
        "generic_api_key_assign",
        re.compile(
            r"(?i)\b(?:api[_-]?key|secret[_-]?key|access[_-]?token)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{20,}"
        ),
    ),
    ("openai_sk", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")),
    ("xai_key", re.compile(r"\bxai-[A-Za-z0-9]{20,}\b")),
]

__all__ = [
    "SCHEMA",
    "DEFAULT_SOCKETS",
    "registry_root",
    "blocks_dir",
    "sockets_path",
    "list_sockets",
    "get_socket",
    "list_blocks",
    "get_block",
    "register_block_from_skill",
    "register_block_from_prompt_file",
    "sandbox_block",
    "promote_block",
    "revoke_block",
    "attach_block",
    "detach_block",
    "resolve_socket_skills",
    "load_socket_skill_bodies",
    "allowed_attach_statuses",
]


def _iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def registry_root() -> Path:
    d = state_dir() / "block_registry"
    d.mkdir(parents=True, exist_ok=True)
    return d


def blocks_dir() -> Path:
    d = registry_root() / "blocks"
    d.mkdir(parents=True, exist_ok=True)
    return d


def sockets_path() -> Path:
    return registry_root() / "sockets.json"


def _normalize_name(name: str) -> str:
    return (name or "").strip().lower().replace("_", "-")


def _block_id(kind: str, name: str) -> str:
    n = _normalize_name(name)
    k = (kind or "").strip().lower()
    if k not in BLOCK_KINDS:
        raise ValueError(f"kind must be one of {sorted(BLOCK_KINDS)}")
    if not n:
        raise ValueError("name is required")
    return f"{k}_{n}"


def _block_path(block_id: str) -> Path:
    safe = (block_id or "").strip()
    if not safe or "/" in safe or "\\" in safe or ".." in safe:
        raise ValueError(f"invalid block_id: {block_id!r}")
    return blocks_dir() / f"{safe}.json"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _default_attachments() -> dict[str, Any]:
    return {name: [] for name in DEFAULT_SOCKETS}


def _load_sockets_file() -> dict[str, Any]:
    path = sockets_path()
    if not path.is_file():
        return {
            "schema": "sockets.v1",
            "updated_at": _iso(),
            "attachments": _default_attachments(),
            "defs_override": {},
        }
    try:
        data = _load_json(path)
    except (OSError, json.JSONDecodeError):
        return {
            "schema": "sockets.v1",
            "updated_at": _iso(),
            "attachments": _default_attachments(),
            "defs_override": {},
        }
    if not isinstance(data, dict):
        data = {}
    att = data.get("attachments")
    if not isinstance(att, dict):
        att = {}
    # Ensure all default sockets exist
    for name in DEFAULT_SOCKETS:
        if name not in att or not isinstance(att[name], list):
            att[name] = []
    data["attachments"] = att
    if "defs_override" not in data or not isinstance(data.get("defs_override"), dict):
        data["defs_override"] = {}
    return data


def _save_sockets_file(data: dict[str, Any]) -> None:
    data = dict(data)
    data["schema"] = "sockets.v1"
    data["updated_at"] = _iso()
    _save_json(sockets_path(), data)


def _socket_def(name: str) -> dict[str, Any]:
    """Merge DEFAULT_SOCKETS with optional defs_override from sockets.json."""
    name = (name or "").strip()
    base = DEFAULT_SOCKETS.get(name)
    if base is None:
        raise KeyError(f"unknown socket: {name}")
    data = _load_sockets_file()
    override = (data.get("defs_override") or {}).get(name) or {}
    out = dict(base)
    if isinstance(override, dict):
        for k in ("max_n", "allow_sandboxed", "kinds", "description", "cardinality"):
            if k in override:
                out[k] = override[k]
    out["name"] = name
    return out


def allowed_attach_statuses(socket_name: str) -> frozenset[str]:
    sdef = _socket_def(socket_name)
    allowed = {"verified"}
    if sdef.get("allow_sandboxed"):
        allowed.add("sandboxed")
    return frozenset(allowed)


def list_sockets() -> list[dict[str, Any]]:
    """Return socket defs + current attachments."""
    data = _load_sockets_file()
    att = data.get("attachments") or {}
    out: list[dict[str, Any]] = []
    for name in DEFAULT_SOCKETS:
        sdef = _socket_def(name)
        block_ids = list(att.get(name) or [])
        out.append(
            {
                **sdef,
                "block_ids": block_ids,
                "allowed_statuses": sorted(allowed_attach_statuses(name)),
            }
        )
    return out


def get_socket(name: str) -> dict[str, Any]:
    name = (name or "").strip()
    if name not in DEFAULT_SOCKETS:
        raise KeyError(f"unknown socket: {name}")
    data = _load_sockets_file()
    sdef = _socket_def(name)
    return {
        **sdef,
        "block_ids": list((data.get("attachments") or {}).get(name) or []),
        "allowed_statuses": sorted(allowed_attach_statuses(name)),
    }


def get_block(block_id: str) -> dict[str, Any] | None:
    path = _block_path(block_id)
    if not path.is_file():
        return None
    try:
        return _load_json(path)
    except (OSError, json.JSONDecodeError):
        return None


def list_blocks(*, kind: str | None = None, status: str | None = None) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    d = blocks_dir()
    for path in sorted(d.glob("*.json")):
        try:
            rec = _load_json(path)
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(rec, dict):
            continue
        if kind and str(rec.get("kind") or "") != kind:
            continue
        if status and str(rec.get("status") or "") != status:
            continue
        out.append(rec)
    return out


def _save_block(rec: dict[str, Any]) -> Path:
    bid = str(rec.get("id") or "")
    if not bid:
        raise ValueError("block id required")
    rec["updated_at"] = _iso()
    path = _block_path(bid)
    _save_json(path, rec)
    return path


def _provenance_for_skill_path(skill_dir: Path) -> str:
    try:
        from pipeline.pipeline_config import PROJECT_ROOT

        resolved = skill_dir.resolve()
        if PROJECT_ROOT.resolve() in resolved.parents or resolved.is_relative_to(
            PROJECT_ROOT.resolve()
        ):
            return "project"
    except Exception:
        pass
    s = str(skill_dir).replace("\\", "/").lower()
    if "/bundled/" in s or s.endswith("/bundled") or "/bundled/skills" in s:
        return "bundled"
    return "local"


def _relative_source(path: Path) -> str:
    """Prefer path relative to PROJECT_ROOT or PIPELINE_DIR; else absolute."""
    path = path.resolve()
    try:
        from pipeline.pipeline_config import PROJECT_ROOT

        return str(path.relative_to(PROJECT_ROOT.resolve())).replace("\\", "/")
    except Exception:
        pass
    try:
        return str(path.relative_to(get_pipeline_dir().resolve())).replace("\\", "/")
    except Exception:
        return str(path)


def _new_block(
    *,
    kind: str,
    name: str,
    source_path: str,
    provenance: str,
    risk_class: str = "low",
) -> dict[str, Any]:
    n = _normalize_name(name)
    bid = _block_id(kind, n)
    now = _iso()
    return {
        "schema": SCHEMA,
        "id": bid,
        "kind": kind,
        "name": n,
        "status": "draft",
        "source_path": source_path,
        "provenance": provenance,
        "oracle": {"name": "skill_sandbox_fixture", "pass": None},
        "risk_class": risk_class if risk_class in RISK_CLASSES else "low",
        "created_at": now,
        "updated_at": now,
        "sandbox_report": None,
        "promote_notes": "",
    }


def register_block_from_skill(
    name: str,
    *,
    force: bool = False,
    risk_class: str = "low",
) -> dict[str, Any]:
    """Discover skill via skill_load.find_skill_dir; create draft block.v1."""
    from pipeline.skill_load import find_skill_dir

    n = _normalize_name(name)
    if not n:
        raise ValueError("skill name is required")
    skill_dir = find_skill_dir(n)
    if skill_dir is None:
        raise FileNotFoundError(f"skill not found: {n}")
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        raise FileNotFoundError(f"SKILL.md missing under {skill_dir}")

    bid = _block_id("skill", n)
    existing = get_block(bid)
    if existing is not None and not force:
        if str(existing.get("status")) == "revoked":
            # Re-register revoked as fresh draft
            pass
        else:
            return existing

    rec = _new_block(
        kind="skill",
        name=n,
        source_path=_relative_source(skill_md),
        provenance=_provenance_for_skill_path(skill_dir),
        risk_class=risk_class,
    )
    # Keep absolute path resolution easy: also store resolved when relative fails later
    rec["_resolved_source"] = str(skill_md.resolve())
    _save_block(rec)
    # Drop internal key from public view? Keep for resolve reliability.
    return rec


def register_block_from_prompt_file(
    path: str | Path,
    name: str,
    *,
    force: bool = False,
    risk_class: str = "low",
    provenance: str = "project",
) -> dict[str, Any]:
    """Register a prompt markdown file as draft block."""
    p = Path(path).expanduser()
    if not p.is_file():
        # Try relative to PIPELINE_DIR, factory prompts/, project root
        candidates = [
            get_pipeline_dir() / path,
            Path(__file__).resolve().parent / "prompts" / Path(path).name,
        ]
        try:
            from pipeline.pipeline_config import PROJECT_ROOT

            candidates.append(PROJECT_ROOT / path)
            candidates.append(PROJECT_ROOT / "pipeline" / "prompts" / Path(path).name)
        except Exception:
            pass
        for c in candidates:
            if c.is_file():
                p = c
                break
        else:
            raise FileNotFoundError(f"prompt file not found: {path}")

    n = _normalize_name(name) or _normalize_name(p.stem)
    bid = _block_id("prompt", n)
    existing = get_block(bid)
    if existing is not None and not force:
        if str(existing.get("status")) != "revoked":
            return existing

    rec = _new_block(
        kind="prompt",
        name=n,
        source_path=_relative_source(p),
        provenance=provenance if provenance in ("local", "bundled", "project") else "project",
        risk_class=risk_class,
    )
    rec["_resolved_source"] = str(p.resolve())
    _save_block(rec)
    return rec


def _resolve_source_path(rec: dict[str, Any]) -> Path | None:
    """Resolve block source_path to an existing file."""
    raw_resolved = rec.get("_resolved_source")
    if raw_resolved:
        p = Path(str(raw_resolved))
        if p.is_file():
            return p
    src = str(rec.get("source_path") or "").strip()
    if not src:
        return None
    p = Path(src)
    if p.is_file():
        return p
    candidates: list[Path] = []
    try:
        from pipeline.pipeline_config import PROJECT_ROOT

        candidates.append(PROJECT_ROOT / src)
    except Exception:
        pass
    candidates.append(get_pipeline_dir() / src)
    candidates.append(Path(src).expanduser())
    # Skill re-discovery by name
    if rec.get("kind") == "skill" and rec.get("name"):
        try:
            from pipeline.skill_load import find_skill_dir

            d = find_skill_dir(str(rec["name"]))
            if d is not None and (d / "SKILL.md").is_file():
                candidates.append(d / "SKILL.md")
        except Exception:
            pass
    for c in candidates:
        try:
            if c.is_file():
                return c.resolve()
        except OSError:
            continue
    return None


def _parse_skill_frontmatter_name(text: str) -> str | None:
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end < 0:
        return None
    fm = text[3:end]
    for line in fm.splitlines():
        line = line.strip()
        if line.lower().startswith("name:"):
            return line.split(":", 1)[1].strip().strip("\"'")
    return None


def sandbox_block(
    block_id: str,
    *,
    max_bytes: int = DEFAULT_MAX_BYTES,
    write_trace: bool = True,
) -> dict[str, Any]:
    """Static sandbox checks. On pass → sandboxed; on fail stay draft (or keep status).

    Writes sandbox_report onto the block. Emits goal_trace mode=block_promote.
    """
    rec = get_block(block_id)
    if rec is None:
        raise FileNotFoundError(f"block not found: {block_id}")
    if str(rec.get("status")) == "revoked":
        raise ValueError(f"cannot sandbox revoked block: {block_id}")

    checks: list[dict[str, Any]] = []
    passed = True
    path = _resolve_source_path(rec)

    if path is None or not path.is_file():
        checks.append({"name": "file_exists", "pass": False, "detail": str(rec.get("source_path"))})
        passed = False
        text = ""
        size = 0
    else:
        checks.append({"name": "file_exists", "pass": True, "detail": str(path)})
        try:
            raw = path.read_bytes()
            size = len(raw)
            text = raw.decode("utf-8", errors="replace")
        except OSError as exc:
            checks.append({"name": "readable", "pass": False, "detail": str(exc)})
            passed = False
            text = ""
            size = 0

    if passed:
        if size == 0 or not (text or "").strip():
            checks.append({"name": "non_empty", "pass": False, "detail": f"size={size}"})
            passed = False
        else:
            checks.append({"name": "non_empty", "pass": True, "detail": f"size={size}"})

        if size > max_bytes:
            checks.append(
                {"name": "max_size", "pass": False, "detail": f"{size} > {max_bytes}"}
            )
            passed = False
        else:
            checks.append({"name": "max_size", "pass": True, "detail": f"{size} <= {max_bytes}"})

        secret_hits: list[str] = []
        for label, pat in _SECRET_PATTERNS:
            if pat.search(text):
                secret_hits.append(label)
        if secret_hits:
            checks.append(
                {"name": "no_secrets", "pass": False, "detail": ",".join(secret_hits)}
            )
            passed = False
        else:
            checks.append({"name": "no_secrets", "pass": True, "detail": "ok"})

        if str(rec.get("kind")) == "skill":
            fm_name = _parse_skill_frontmatter_name(text)
            expected = _normalize_name(str(rec.get("name") or ""))
            if not fm_name:
                checks.append(
                    {
                        "name": "frontmatter_name",
                        "pass": False,
                        "detail": "missing YAML name frontmatter",
                    }
                )
                passed = False
            else:
                got = _normalize_name(fm_name)
                ok = got == expected or got.replace("-", "") == expected.replace("-", "")
                checks.append(
                    {
                        "name": "frontmatter_name",
                        "pass": ok,
                        "detail": f"frontmatter={fm_name!r} expected={expected!r}",
                    }
                )
                if not ok:
                    passed = False

    report = {
        "checked_at": _iso(),
        "pass": passed,
        "checks": checks,
        "source": str(path) if path else rec.get("source_path"),
    }
    rec["sandbox_report"] = report
    rec["oracle"] = {"name": "skill_sandbox_fixture", "pass": passed}
    # Only draft (or re-sandbox of sandboxed/verified) moves to sandboxed on pass.
    prev = str(rec.get("status") or "draft")
    if passed and prev in ("draft", "sandboxed"):
        rec["status"] = "sandboxed"
    # verified stays verified if re-sandboxed pass; fail demotes? v0: stay as-is on fail if verified
    elif not passed and prev == "draft":
        rec["status"] = "draft"
    elif not passed and prev == "sandboxed":
        rec["status"] = "draft"  # demote on failed re-sandbox
    _save_block(rec)

    if write_trace:
        _trace_block_action(
            rec,
            action="sandbox",
            ok=passed,
            detail=f"sandbox {'pass' if passed else 'fail'}",
        )
    return rec


def promote_block(
    block_id: str,
    *,
    notes: str = "",
    sandbox_if_needed: bool = False,
    write_trace: bool = True,
) -> dict[str, Any]:
    """Promote sandboxed → verified. With sandbox_if_needed, draft may sandbox then promote."""
    rec = get_block(block_id)
    if rec is None:
        raise FileNotFoundError(f"block not found: {block_id}")
    status = str(rec.get("status") or "")
    if status == "revoked":
        raise ValueError(f"cannot promote revoked block: {block_id}")
    if status == "verified":
        return rec
    if status == "draft":
        if not sandbox_if_needed:
            raise ValueError(
                f"block {block_id} is draft; sandbox first or pass sandbox_if_needed=True"
            )
        rec = sandbox_block(block_id, write_trace=write_trace)
        status = str(rec.get("status") or "")
        if status != "sandboxed":
            raise ValueError(f"sandbox failed; cannot promote {block_id}")
    if status != "sandboxed":
        raise ValueError(f"promote requires sandboxed status, got {status!r}")

    rec["status"] = "verified"
    if notes:
        prev_notes = str(rec.get("promote_notes") or "")
        rec["promote_notes"] = (prev_notes + "\n" + notes).strip() if prev_notes else notes
    rec["oracle"] = {"name": "skill_sandbox_fixture", "pass": True}
    _save_block(rec)

    if write_trace:
        _trace_block_action(rec, action="promote", ok=True, detail="promoted to verified")
    return rec


def revoke_block(block_id: str, *, detach: bool = True, write_trace: bool = True) -> dict[str, Any]:
    """Mark block revoked; optionally detach from all sockets."""
    rec = get_block(block_id)
    if rec is None:
        raise FileNotFoundError(f"block not found: {block_id}")
    rec["status"] = "revoked"
    _save_block(rec)
    if detach:
        data = _load_sockets_file()
        att = data.get("attachments") or {}
        changed = False
        for sock, ids in list(att.items()):
            if not isinstance(ids, list):
                continue
            if block_id in ids:
                att[sock] = [x for x in ids if x != block_id]
                changed = True
        if changed:
            data["attachments"] = att
            _save_sockets_file(data)
    if write_trace:
        _trace_block_action(rec, action="revoke", ok=True, detail="revoked")
    return rec


def attach_block(
    socket_name: str,
    block_id: str,
    *,
    force: bool = False,
) -> dict[str, Any]:
    """Attach block to socket. Rejects draft/revoked unless force=True."""
    sdef = _socket_def(socket_name)
    rec = get_block(block_id)
    if rec is None:
        raise FileNotFoundError(f"block not found: {block_id}")

    status = str(rec.get("status") or "")
    allowed = allowed_attach_statuses(socket_name)
    if not force and status not in allowed:
        raise ValueError(
            f"attach rejected: block status {status!r} not in {sorted(allowed)} "
            f"for socket {socket_name} (use force=True to override)"
        )
    kinds = set(sdef.get("kinds") or ["skill", "prompt"])
    if str(rec.get("kind") or "") not in kinds:
        raise ValueError(
            f"block kind {rec.get('kind')!r} not allowed on socket {socket_name} "
            f"(allowed {sorted(kinds)})"
        )

    data = _load_sockets_file()
    att = data.setdefault("attachments", _default_attachments())
    current = list(att.get(socket_name) or [])
    max_n = int(sdef.get("max_n") or 1)
    cardinality = str(sdef.get("cardinality") or "single")

    if block_id in current:
        return get_socket(socket_name)

    if cardinality == "single" or max_n <= 1:
        current = [block_id]
    else:
        if len(current) >= max_n:
            raise ValueError(
                f"socket {socket_name} full (max_n={max_n}); detach first"
            )
        current.append(block_id)

    att[socket_name] = current
    data["attachments"] = att
    _save_sockets_file(data)
    return get_socket(socket_name)


def detach_block(socket_name: str, block_id: str | None = None) -> dict[str, Any]:
    """Detach one block or clear entire socket when block_id is None."""
    if socket_name not in DEFAULT_SOCKETS:
        raise KeyError(f"unknown socket: {socket_name}")
    data = _load_sockets_file()
    att = data.setdefault("attachments", _default_attachments())
    current = list(att.get(socket_name) or [])
    if block_id is None:
        att[socket_name] = []
    else:
        att[socket_name] = [x for x in current if x != block_id]
    data["attachments"] = att
    _save_sockets_file(data)
    return get_socket(socket_name)


def resolve_socket_skills(socket_name: str) -> list[dict[str, Any]]:
    """Return list of {block_id, path, body, status, name} for attached allowed blocks."""
    sock = get_socket(socket_name)
    allowed = set(sock.get("allowed_statuses") or ["verified"])
    out: list[dict[str, Any]] = []
    for bid in sock.get("block_ids") or []:
        rec = get_block(str(bid))
        if rec is None:
            continue
        st = str(rec.get("status") or "")
        if st not in allowed:
            continue
        path = _resolve_source_path(rec)
        body = ""
        if path is not None and path.is_file():
            try:
                body = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                body = ""
            # Strip skill frontmatter for injection parity with skill_load
            if str(rec.get("kind")) == "skill" and body.startswith("---"):
                end = body.find("\n---", 3)
                if end >= 0:
                    body = body[end + 4 :].lstrip("\n")
        out.append(
            {
                "block_id": rec.get("id"),
                "name": rec.get("name"),
                "kind": rec.get("kind"),
                "status": st,
                "path": str(path) if path else rec.get("source_path"),
                "body": body,
            }
        )
    return out


def load_socket_skill_bodies(
    socket_name: str,
    *,
    max_chars: int = 12000,
    separator: str = "\n\n---\n\n",
) -> str:
    """Concatenate bodies of socket-attached blocks with allowed statuses only."""
    items = resolve_socket_skills(socket_name)
    parts: list[str] = []
    total = 0
    for it in items:
        body = (it.get("body") or "").strip()
        if not body:
            continue
        header = f"### socket skill: {it.get('name') or it.get('block_id')}\n"
        chunk = header + body
        if total + len(chunk) > max_chars:
            remain = max_chars - total
            if remain > 80:
                parts.append(chunk[:remain] + "\n\n…(truncated)…\n")
            break
        parts.append(chunk)
        total += len(chunk)
    return separator.join(parts)


def _trace_block_action(
    rec: dict[str, Any],
    *,
    action: str,
    ok: bool,
    detail: str = "",
) -> None:
    try:
        from pipeline.goal_trace import append_event, finalize_trace, start_trace

        bid = str(rec.get("id") or "unknown")
        tr = start_trace(
            f"block_{action}:{bid}",
            goal_id=f"block_{action}_{bid}_{_iso()[:19].replace(':', '')}",
            mode="block_promote",
            plan=[{"step": 1, "intent": action, "block_id": bid}],
        )
        append_event(
            tr,
            type="tool",
            tool=f"block_registry.{action}",
            args={"block_id": bid, "status": rec.get("status")},
            result_snip=detail[:500],
            ok=ok,
        )
        status = "goal_proven" if ok else "goal_failed"
        finalize_trace(
            tr,
            status=status,
            oracle={
                "name": "skill_sandbox_fixture",
                "pass": ok,
                "evidence": detail,
                "block_id": bid,
                "action": action,
            },
            train_weight=0.0,
        )
    except Exception:
        pass
