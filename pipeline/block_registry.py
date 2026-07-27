"""
block_registry v0 — skill/prompt block catalog + role sockets + promote pipeline.

Layout under PIPELINE_DIR:
  state/block_registry/blocks/{block_id}.json   (block.v1)
  state/block_registry/sockets.json             (attachments)

Sockets are fixed role slots; only verified (or sandboxed if socket allows)
blocks may attach. Promote path: register (draft) → sandbox → promote (verified).

Source paths are confined to allowlisted roots (PROJECT_ROOT, PIPELINE_DIR,
skill search roots, factory prompts/). Promote re-runs sandbox and pins a
content hash so post-sandbox edits cannot skip re-validation.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pipeline.paths import get_pipeline_dir, state_dir

log = logging.getLogger(__name__)

SCHEMA = "block.v1"
BLOCK_STATUSES = frozenset({"draft", "sandboxed", "verified", "revoked"})
BLOCK_KINDS = frozenset({"skill", "prompt"})
RISK_CLASSES = frozenset({"low", "medium", "high"})

# Default max skill body size for sandbox (bytes).
DEFAULT_MAX_BYTES = 200_000

# Socket definitions (code defaults). Override via sockets.json "defs_override".
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

# Obvious secret patterns (static sandbox). Hyphenated keys + env-style assigns.
_SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "private_key_header",
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |ENCRYPTED )?PRIVATE KEY-----"),
    ),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    # sk-proj-…, sk-ant-…, sk-… (hyphens allowed after prefix)
    ("openai_sk", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("xai_key", re.compile(r"\bxai-[A-Za-z0-9_-]{20,}\b")),
    # api_key: / secret_key= / access_token: value forms
    (
        "generic_api_key_assign",
        re.compile(
            r"(?i)\b(?:api[_-]?key|secret[_-]?key|access[_-]?token)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}"
        ),
    ),
    # OPENAI_API_KEY=…, XAI_API_KEY=…, ANTHROPIC_API_KEY=…, FOO_SECRET=…, PASSWORD=…
    (
        "env_style_secret",
        re.compile(
            r"(?i)\b[A-Z0-9_]*(?:API[_-]?KEY|SECRET(?:[_-]?KEY)?|TOKEN|PASSWORD|PRIVATE[_-]?KEY)"
            r"\s*=\s*\S{16,}"
        ),
    ),
]

_NAME_RE = re.compile(r"^[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$")

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
    "assert_source_allowed",
    "allowed_source_roots",
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


def _validate_block_name(name: str) -> str:
    """Normalize and reject path-like / unsafe block names early."""
    n = _normalize_name(name)
    if not n:
        raise ValueError("name is required")
    if ".." in n or "/" in n or "\\" in n:
        raise ValueError(f"invalid block name (path segments not allowed): {name!r}")
    if not _NAME_RE.match(n):
        raise ValueError(
            f"invalid block name {name!r}: use lowercase letters, digits, "
            f"hyphen, or dot (e.g. my-skill)"
        )
    return n


def _block_id(kind: str, name: str) -> str:
    n = _validate_block_name(name)
    k = (kind or "").strip().lower()
    if k not in BLOCK_KINDS:
        raise ValueError(f"kind must be one of {sorted(BLOCK_KINDS)}")
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


def _load_sockets_file(*, strict: bool = False) -> dict[str, Any]:
    """Load sockets.json.

    On corrupt JSON: quarantine the bad file and raise ValueError when
    *strict* is True (CLI list-sockets). Internal callers use strict=False
    but still quarantine and start from empty defaults (logged).
    """
    path = sockets_path()
    empty = {
        "schema": "sockets.v1",
        "updated_at": _iso(),
        "attachments": _default_attachments(),
        "defs_override": {},
    }
    if not path.is_file():
        return empty
    try:
        data = _load_json(path)
    except (OSError, json.JSONDecodeError) as exc:
        quarantine = path.with_suffix(f".corrupt.{_iso()[:19].replace(':', '')}.json")
        try:
            path.replace(quarantine)
            log.error("corrupt sockets.json quarantined to %s: %s", quarantine, exc)
        except OSError:
            log.error("corrupt sockets.json at %s: %s", path, exc)
        if strict:
            raise ValueError(
                f"corrupt sockets.json (quarantined to {quarantine.name if quarantine else path}): {exc}"
            ) from exc
        return empty
    if not isinstance(data, dict):
        data = {}
    att = data.get("attachments")
    if not isinstance(att, dict):
        att = {}
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


def list_sockets(*, strict_sockets: bool = False) -> list[dict[str, Any]]:
    """Return socket defs + current attachments."""
    data = _load_sockets_file(strict=strict_sockets)
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
        # Never surface internal-only keys if present from older records
        rec.pop("_resolved_source", None)
        out.append(rec)
    return out


def _save_block(rec: dict[str, Any]) -> Path:
    bid = str(rec.get("id") or "")
    if not bid:
        raise ValueError("block id required")
    rec = dict(rec)
    rec.pop("_resolved_source", None)  # never persist absolute host paths
    rec["updated_at"] = _iso()
    path = _block_path(bid)
    _save_json(path, rec)
    return path


def _provenance_for_skill_path(skill_dir: Path) -> str:
    try:
        from pipeline.pipeline_config import PROJECT_ROOT

        resolved = skill_dir.resolve()
        root = PROJECT_ROOT.resolve()
        if resolved == root or resolved.is_relative_to(root):
            return "project"
    except Exception:
        pass
    s = str(skill_dir).replace("\\", "/").lower()
    if "/bundled/" in s or s.endswith("/bundled") or "/bundled/skills" in s:
        return "bundled"
    return "local"


def allowed_source_roots() -> list[Path]:
    """Roots under which block source files may live."""
    roots: list[Path] = []
    try:
        from pipeline.pipeline_config import PROJECT_ROOT

        roots.append(PROJECT_ROOT.resolve())
        roots.append((PROJECT_ROOT / "pipeline" / "prompts").resolve())
        roots.append((PROJECT_ROOT / ".grok" / "skills").resolve())
    except Exception:
        pass
    try:
        roots.append(get_pipeline_dir().resolve())
    except Exception:
        pass
    # Grok skill homes (same family as skill_load)
    try:
        import os

        grok_home = Path(os.environ.get("GROK_HOME", Path.home() / ".grok")).expanduser().resolve()
        roots.append(grok_home / "skills")
        roots.append(grok_home / "bundled" / "skills")
        roots.append(grok_home / "installed-plugins")
    except Exception:
        pass
    try:
        from pipeline.skill_load import skill_search_roots

        for r in skill_search_roots():
            try:
                roots.append(Path(r).resolve())
            except OSError:
                continue
    except Exception:
        pass
    # Dedup while preserving order
    seen: set[str] = set()
    out: list[Path] = []
    for r in roots:
        key = str(r)
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def assert_source_allowed(path: Path) -> Path:
    """Resolve *path* and require it under an allowlisted root. Rejects `..` escapes."""
    try:
        resolved = path.expanduser().resolve(strict=False)
    except OSError as exc:
        raise ValueError(f"cannot resolve source path: {path}: {exc}") from exc

    # Reject if original had .. that escapes after resolve from a relative base —
    # resolve() already collapses; we only accept under roots.
    for root in allowed_source_roots():
        try:
            root_r = root.resolve()
        except OSError:
            continue
        try:
            if resolved == root_r or resolved.is_relative_to(root_r):
                return resolved
        except (ValueError, OSError):
            continue
    raise ValueError(
        f"source path not under allowlisted roots "
        f"(PROJECT_ROOT, PIPELINE_DIR, skill roots, factory prompts/): {resolved}"
    )


def _relative_source(path: Path) -> str:
    """Prefer path relative to PROJECT_ROOT or PIPELINE_DIR; else skill-root relative."""
    path = path.resolve()
    try:
        from pipeline.pipeline_config import PROJECT_ROOT

        return str(path.relative_to(PROJECT_ROOT.resolve())).replace("\\", "/")
    except Exception:
        pass
    try:
        return str(path.relative_to(get_pipeline_dir().resolve())).replace("\\", "/")
    except Exception:
        pass
    for root in allowed_source_roots():
        try:
            return str(path.relative_to(root.resolve())).replace("\\", "/")
        except Exception:
            continue
    # Last resort: store name only is unsafe; raise so we never catalog outside roots
    raise ValueError(f"cannot relativize source path under allowlisted roots: {path}")


def _content_sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _new_block(
    *,
    kind: str,
    name: str,
    source_path: str,
    provenance: str,
    risk_class: str = "low",
) -> dict[str, Any]:
    n = _validate_block_name(name)
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
    sandbox: bool = False,
) -> dict[str, Any]:
    """Discover skill via skill_load.find_skill_dir; create draft block.v1.

    When *sandbox* is True, run static sandbox immediately after register
    (habit convenience: register → sandbox without a second CLI step).
    """
    from pipeline.skill_load import find_skill_dir

    n = _validate_block_name(name)
    skill_dir = find_skill_dir(n)
    if skill_dir is None:
        raise FileNotFoundError(f"skill not found: {n}")
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        raise FileNotFoundError(f"SKILL.md missing under {skill_dir}")

    skill_md = assert_source_allowed(skill_md)

    bid = _block_id("skill", n)
    existing = get_block(bid)
    if existing is not None and not force:
        if str(existing.get("status")) == "revoked":
            pass
        else:
            rec = existing
            if sandbox and str(rec.get("status")) == "draft":
                return sandbox_block(rec["id"])
            return rec

    rec = _new_block(
        kind="skill",
        name=n,
        source_path=_relative_source(skill_md),
        provenance=_provenance_for_skill_path(skill_dir),
        risk_class=risk_class,
    )
    _save_block(rec)
    if sandbox:
        return sandbox_block(rec["id"])
    return rec


def register_block_from_prompt_file(
    path: str | Path,
    name: str,
    *,
    force: bool = False,
    risk_class: str = "low",
    provenance: str = "project",
    sandbox: bool = False,
) -> dict[str, Any]:
    """Register a prompt markdown file as draft block.

    Path must resolve under allowlisted roots (PROJECT_ROOT, PIPELINE_DIR,
    factory pipeline/prompts/, skill roots). Absolute paths outside those
    roots are rejected.

    When *sandbox* is True, run static sandbox immediately after register.
    """
    raw = Path(path)
    # Reject obvious escape attempts in the raw string before joining roots
    raw_s = str(path).replace("\\", "/")
    if ".." in Path(raw_s).parts:
        # Still allow if final resolve lands under a root — but try candidates carefully
        pass

    p: Path | None = None
    if raw.expanduser().is_file():
        try:
            p = assert_source_allowed(raw)
        except ValueError:
            p = None

    if p is None:
        candidates: list[Path] = []
        try:
            from pipeline.pipeline_config import PROJECT_ROOT

            candidates.append(PROJECT_ROOT / path)
            candidates.append(PROJECT_ROOT / "pipeline" / "prompts" / Path(path).name)
            candidates.append(Path(__file__).resolve().parent / "prompts" / Path(path).name)
        except Exception:
            pass
        candidates.append(get_pipeline_dir() / path)
        candidates.append(get_pipeline_dir() / "prompts" / Path(path).name)
        for c in candidates:
            try:
                if c.is_file():
                    p = assert_source_allowed(c)
                    break
            except (ValueError, OSError):
                continue
        else:
            raise FileNotFoundError(
                f"prompt file not found under allowlisted roots: {path}"
            )

    assert p is not None
    p = assert_source_allowed(p)

    n = _validate_block_name(name) if name else _validate_block_name(p.stem)
    bid = _block_id("prompt", n)
    existing = get_block(bid)
    if existing is not None and not force:
        if str(existing.get("status")) != "revoked":
            rec = existing
            if sandbox and str(rec.get("status")) == "draft":
                return sandbox_block(rec["id"])
            return rec

    rec = _new_block(
        kind="prompt",
        name=n,
        source_path=_relative_source(p),
        provenance=provenance if provenance in ("local", "bundled", "project") else "project",
        risk_class=risk_class,
    )
    _save_block(rec)
    if sandbox:
        return sandbox_block(rec["id"])
    return rec


def _resolve_source_path(rec: dict[str, Any]) -> Path | None:
    """Resolve block source_path to an existing allowlisted file.

    Does not trust absolute `_resolved_source` from disk (legacy keys ignored).
    Relative paths with `..` only succeed if final resolve stays under roots.
    """
    candidates: list[Path] = []
    src = str(rec.get("source_path") or "").strip()
    if src:
        # Never join raw src that is absolute outside roots without check
        p = Path(src)
        if p.is_absolute():
            candidates.append(p)
        else:
            # Reject path parts that look like pure escape before join? Still check final.
            try:
                from pipeline.pipeline_config import PROJECT_ROOT

                candidates.append(PROJECT_ROOT / src)
            except Exception:
                pass
            candidates.append(get_pipeline_dir() / src)
            for root in allowed_source_roots():
                candidates.append(root / src)

    # Skill re-discovery by name (preferred for skills)
    if rec.get("kind") == "skill" and rec.get("name"):
        try:
            from pipeline.skill_load import find_skill_dir

            d = find_skill_dir(str(rec["name"]))
            if d is not None and (d / "SKILL.md").is_file():
                candidates.insert(0, d / "SKILL.md")
        except Exception:
            pass

    for c in candidates:
        try:
            if not c.is_file():
                continue
            return assert_source_allowed(c)
        except (ValueError, OSError):
            continue
    return None


def _parse_skill_frontmatter_name(text: str) -> str | None:
    # Strip UTF-8 BOM (common when files are written via PowerShell Set-Content)
    if text.startswith("\ufeff"):
        text = text.lstrip("\ufeff")
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


def _detach_block_from_all_sockets(block_id: str) -> None:
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


def _count_capacity_ids(socket_name: str, current: list[str]) -> int:
    """Count attachment slots; drop missing block files from capacity consideration."""
    # Prefer counting only existing blocks so dead ids don't permanently fill max_n.
    n = 0
    for bid in current:
        if get_block(str(bid)) is not None:
            n += 1
    return n


def sandbox_block(
    block_id: str,
    *,
    max_bytes: int = DEFAULT_MAX_BYTES,
    write_trace: bool = True,
) -> dict[str, Any]:
    """Static sandbox checks. On pass → sandboxed; on fail → draft (incl. demote verified).

    Writes sandbox_report + content_sha256. Emits goal_trace mode=block_promote.
    Failed re-sandbox of verified demotes to draft and detaches from sockets.
    """
    rec = get_block(block_id)
    if rec is None:
        raise FileNotFoundError(f"block not found: {block_id}")
    if str(rec.get("status")) == "revoked":
        raise ValueError(f"cannot sandbox revoked block: {block_id}")

    checks: list[dict[str, Any]] = []
    passed = True
    path = _resolve_source_path(rec)
    content_hash: str | None = None
    text = ""
    size = 0

    if path is None or not path.is_file():
        checks.append(
            {"name": "file_exists", "pass": False, "detail": str(rec.get("source_path"))}
        )
        passed = False
    else:
        # Path must stay allowlisted (resolve already checked; re-assert)
        try:
            path = assert_source_allowed(path)
            checks.append({"name": "path_allowed", "pass": True, "detail": str(path)})
        except ValueError as exc:
            checks.append({"name": "path_allowed", "pass": False, "detail": str(exc)})
            passed = False
            path = None

        if path is not None:
            checks.append({"name": "file_exists", "pass": True, "detail": str(path)})
            try:
                raw = path.read_bytes()
                size = len(raw)
                content_hash = _content_sha256(raw)
                text = raw.decode("utf-8", errors="replace")
            except OSError as exc:
                checks.append({"name": "readable", "pass": False, "detail": str(exc)})
                passed = False

    if passed and path is not None:
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

    prev_report = rec.get("sandbox_report") if isinstance(rec.get("sandbox_report"), dict) else {}
    report: dict[str, Any] = {
        "checked_at": _iso(),
        "pass": passed,
        "checks": checks,
        "source": str(path) if path else rec.get("source_path"),
        "content_sha256": content_hash,
    }
    # Keep promote pin when re-sandboxing verified content that still passes
    prev = str(rec.get("status") or "draft")
    if passed and prev == "verified" and content_hash:
        report["promoted_content_sha256"] = content_hash
        if prev_report.get("promoted_at"):
            report["promoted_at"] = prev_report["promoted_at"]
    elif prev_report.get("promoted_content_sha256") and passed and prev == "verified":
        report["promoted_content_sha256"] = prev_report["promoted_content_sha256"]

    rec["sandbox_report"] = report
    rec["oracle"] = {"name": "skill_sandbox_fixture", "pass": passed}

    if passed:
        if prev in ("draft", "sandboxed", "verified"):
            # Pass keeps/sets sandboxed; verified re-sandbox pass stays verified
            if prev == "verified":
                rec["status"] = "verified"
            else:
                rec["status"] = "sandboxed"
    else:
        # Fail always demotes to draft (including verified → draft)
        rec["status"] = "draft"
        if prev == "verified":
            _detach_block_from_all_sockets(str(rec.get("id") or block_id))

    _save_block(rec)

    if write_trace:
        fc = None
        if not passed:
            # Prefer secret_fail when no_secrets check failed
            for ch in checks:
                if ch.get("name") == "no_secrets" and not ch.get("pass"):
                    fc = "secret_fail"
                    break
            if fc is None:
                fc = "sandbox_fail"
        _trace_block_action(
            rec,
            action="sandbox",
            ok=passed,
            detail=f"sandbox {'pass' if passed else 'fail'}",
            failure_class=fc,
        )
    return rec


def promote_block(
    block_id: str,
    *,
    notes: str = "",
    sandbox_if_needed: bool = False,
    write_trace: bool = True,
) -> dict[str, Any]:
    """Promote sandboxed → verified.

    Always re-runs sandbox on the current file content and refuses if checks
    fail or content hash is missing. With sandbox_if_needed, draft may be
    sandboxed then promoted in one step.
    """
    rec = get_block(block_id)
    if rec is None:
        raise FileNotFoundError(f"block not found: {block_id}")
    status = str(rec.get("status") or "")
    if status == "revoked":
        raise ValueError(f"cannot promote revoked block: {block_id}")
    if status == "verified":
        # Still re-validate content has not drifted into secrets
        rec = sandbox_block(block_id, write_trace=write_trace)
        if str(rec.get("status")) != "verified" or not (rec.get("sandbox_report") or {}).get(
            "pass"
        ):
            raise ValueError(
                f"re-sandbox failed for verified block {block_id}; demoted, cannot keep verified"
            )
        return rec

    if status == "draft" and not sandbox_if_needed:
        raise ValueError(
            f"block {block_id} is draft; sandbox first or pass sandbox_if_needed=True"
        )

    # Always re-sandbox current content before promote (covers sandboxed + draft)
    rec = sandbox_block(block_id, write_trace=write_trace)
    status = str(rec.get("status") or "")
    report = rec.get("sandbox_report") or {}
    if status != "sandboxed" or not report.get("pass"):
        raise ValueError(f"sandbox failed; cannot promote {block_id}")
    if not report.get("content_sha256"):
        raise ValueError(f"sandbox missing content hash; cannot promote {block_id}")

    # Final hash check against live file (TOCTOU narrow window)
    path = _resolve_source_path(rec)
    if path is None:
        raise ValueError(f"source missing; cannot promote {block_id}")
    try:
        live_hash = _content_sha256(path.read_bytes())
    except OSError as exc:
        raise ValueError(f"cannot read source for promote: {exc}") from exc
    if live_hash != report.get("content_sha256"):
        raise ValueError(
            f"source changed after sandbox (hash mismatch); re-sandbox before promote: {block_id}"
        )

    rec["status"] = "verified"
    if notes:
        prev_notes = str(rec.get("promote_notes") or "")
        rec["promote_notes"] = (prev_notes + "\n" + notes).strip() if prev_notes else notes
    rec["oracle"] = {"name": "skill_sandbox_fixture", "pass": True}
    # Pin hash at promote time
    rec["sandbox_report"] = {
        **report,
        "promoted_at": _iso(),
        "promoted_content_sha256": live_hash,
    }
    _save_block(rec)

    if write_trace:
        _trace_block_action(
            rec, action="promote", ok=True, detail="promoted to verified", failure_class=None
        )
    return rec


def revoke_block(block_id: str, *, detach: bool = True, write_trace: bool = True) -> dict[str, Any]:
    """Mark block revoked; optionally detach from all sockets."""
    rec = get_block(block_id)
    if rec is None:
        raise FileNotFoundError(f"block not found: {block_id}")
    rec["status"] = "revoked"
    _save_block(rec)
    if detach:
        _detach_block_from_all_sockets(block_id)
    if write_trace:
        _trace_block_action(
            rec, action="revoke", ok=True, detail="revoked", outcome_override="revoked"
        )
    return rec


def attach_block(
    socket_name: str,
    block_id: str,
    *,
    force: bool = False,
) -> dict[str, Any]:
    """Attach block to socket. Rejects draft/revoked unless force=True.

    force=True is break-glass only: id may sit in sockets.json while resolve
    still skips non-allowed statuses. After a later promote, the body becomes
    injectable without a second attach — operators must track this.
    """
    sdef = _socket_def(socket_name)
    rec = get_block(block_id)
    if rec is None:
        raise FileNotFoundError(f"block not found: {block_id}")

    status = str(rec.get("status") or "")
    allowed = allowed_attach_statuses(socket_name)
    if not force and status not in allowed:
        raise ValueError(
            f"attach rejected: block status {status!r} not in {sorted(allowed)} "
            f"for socket {socket_name} (force=True is break-glass; resolve still "
            f"skips non-allowed until status enters allowed set)"
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

    # Prune missing block ids so dead slots do not fill capacity forever
    pruned = [x for x in current if get_block(str(x)) is not None]
    if pruned != current:
        current = pruned

    if cardinality == "single" or max_n <= 1:
        current = [block_id]
    else:
        if _count_capacity_ids(socket_name, current) >= max_n:
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


def _pinned_content_hash(report: dict[str, Any] | None) -> str | None:
    """Prefer promote-time pin; fall back to last sandbox content hash."""
    if not isinstance(report, dict):
        return None
    for key in ("promoted_content_sha256", "content_sha256"):
        v = report.get(key)
        if isinstance(v, str) and len(v) == 64:
            return v
    return None


def _demote_verified_on_drift(rec: dict[str, Any], *, live_hash: str | None) -> dict[str, Any]:
    """Demote verified block to draft, detach sockets, mark sandbox_report failed."""
    bid = str(rec.get("id") or "")
    report = dict(rec.get("sandbox_report") or {})
    report["pass"] = False
    report["drift_detected_at"] = _iso()
    report["drift_live_sha256"] = live_hash
    report.setdefault("checks", []).append(
        {
            "name": "content_hash_pin",
            "pass": False,
            "detail": "live file hash != promoted/sandbox pin; skipped inject",
        }
    )
    rec["sandbox_report"] = report
    rec["oracle"] = {"name": "skill_sandbox_fixture", "pass": False}
    rec["status"] = "draft"
    _save_block(rec)
    if bid:
        _detach_block_from_all_sockets(bid)
    log.warning(
        "block %s source drifted after promote (hash mismatch); demoted to draft and detached",
        bid,
    )
    return rec


def resolve_socket_skills(socket_name: str) -> list[dict[str, Any]]:
    """Return list of {block_id, path, body, status, name} for attached allowed blocks.

    Only statuses in allowed_attach_statuses are included (force-attached draft
    never injects). Paths must remain under allowlisted roots.

    If sandbox_report has promoted_content_sha256 (or content_sha256), the live
    file is re-hashed; mismatch skips inject and demotes verified → draft + detach.
    """
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
        # Skip if latest sandbox_report explicitly failed (stale verified edge)
        report = rec.get("sandbox_report")
        if isinstance(report, dict) and report.get("pass") is False:
            continue
        path = _resolve_source_path(rec)
        body = ""
        raw: bytes | None = None
        if path is not None and path.is_file():
            try:
                raw = path.read_bytes()
                body = raw.decode("utf-8", errors="replace")
            except OSError:
                body = ""
                raw = None

        # Integrity: re-check pinned hash for verified (and any pinned) blocks
        pinned = _pinned_content_hash(report if isinstance(report, dict) else None)
        if pinned is not None:
            if raw is None:
                if st == "verified":
                    _demote_verified_on_drift(rec, live_hash=None)
                continue
            live_hash = _content_sha256(raw)
            if live_hash != pinned:
                if st == "verified":
                    _demote_verified_on_drift(rec, live_hash=live_hash)
                else:
                    log.warning(
                        "block %s content hash mismatch (status=%s); skipping inject",
                        bid,
                        st,
                    )
                continue

        if body and str(rec.get("kind")) == "skill" and body.startswith("---"):
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
    failure_class: str | None = None,
    outcome_override: str | None = None,
) -> None:
    try:
        from pipeline.goal_trace import (
            OUTCOME_FAILED,
            OUTCOME_PROVEN,
            OUTCOME_REVOKED,
            append_event,
            finalize_trace,
            start_trace,
        )

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
        if outcome_override == "revoked" or action == "revoke":
            outcome = OUTCOME_REVOKED
            status = "revoked"
            fc = None
        elif ok:
            outcome = OUTCOME_PROVEN
            status = "goal_proven"
            fc = None
        else:
            outcome = OUTCOME_FAILED
            status = "goal_failed"
            fc = failure_class or "sandbox_fail"
        finalize_trace(
            tr,
            status=status,
            outcome=outcome,
            failure_class=fc,
            oracle={
                "name": "skill_sandbox_fixture",
                "pass": ok,
                "evidence": detail,
                "block_id": bid,
                "action": action,
            },
            train_weight=0.0,  # structural; never high-weight field/goal claim
            claim="block_promote",
        )
    except Exception:
        pass
