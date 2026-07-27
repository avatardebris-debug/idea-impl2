"""
external_ingest v1 — manual pin → static scan → human approve → promote.

Layout under PIPELINE_DIR:
  external/
    assets/{asset_id}/
      asset.json          (external_asset.v1)
      payload/            (quarantined snapshot of source)
      scan_report.json    (static scan report)
    promoted/{asset_id}.json   (external_* draft for later phases)
    audit.jsonl           (append-only human-gate audit)

Kinds: skill | software | mcp | external_mcp
Statuses: quarantined | scanned | approved | rejected | promoted | revoked

No live git clone required for tests. Optional --allow-url is CLI-only and
default-off (not implemented as auto-pull; path/fixture pin only in library).

Human gate: promote is impossible without prior approve.
Compose/attempt must reference promoted ids only — never git-clone at attempt.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pipeline.paths import external_dir as paths_external_dir

log = logging.getLogger(__name__)

SCHEMA = "external_asset.v1"
PROMOTED_SCHEMA = "external_promoted.v1"

ASSET_KINDS = frozenset({"skill", "software", "mcp", "external_mcp"})
ASSET_STATUSES = frozenset(
    {
        "quarantined",
        "scanned",
        "approved",
        "rejected",
        "promoted",
        "revoked",
    }
)
RISK_CLASSES = frozenset({"low", "medium", "high"})

# Default caps (bytes). Total payload tree; per-file text scan size.
DEFAULT_MAX_TOTAL_BYTES = 50 * 1024 * 1024  # 50 MiB
DEFAULT_MAX_FILE_BYTES = 2 * 1024 * 1024  # 2 MiB per scanned text file

# Extensions never accepted in quarantine payload (static policy).
DISALLOWED_EXTENSIONS = frozenset(
    {
        ".exe",
        ".dll",
        ".so",
        ".dylib",
        ".bat",
        ".cmd",
        ".com",
        ".msi",
        ".scr",
        ".vbs",
        ".ps1",
    }
)

# License filenames (case-insensitive match on name)
_LICENSE_NAMES = frozenset(
    {
        "license",
        "license.md",
        "license.txt",
        "licence",
        "licence.md",
        "licence.txt",
        "copying",
        "copying.md",
        "copying.txt",
    }
)

_ID_RE = re.compile(r"^[a-z0-9](?:[a-z0-9._-]*[a-z0-9])?$")

# Reuse block_registry secret patterns when available; keep local fallback.
def _secret_patterns() -> list[tuple[str, re.Pattern[str]]]:
    try:
        from pipeline.block_registry import _SECRET_PATTERNS

        return list(_SECRET_PATTERNS)
    except Exception:
        return [
            (
                "private_key_header",
                re.compile(
                    r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |ENCRYPTED )?PRIVATE KEY-----"
                ),
            ),
            ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
            ("openai_sk", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
            ("xai_key", re.compile(r"\bxai-[A-Za-z0-9_-]{20,}\b")),
            (
                "generic_api_key_assign",
                re.compile(
                    r"(?i)\b(?:api[_-]?key|secret[_-]?key|access[_-]?token)\s*[:=]\s*"
                    r"['\"]?[A-Za-z0-9_\-]{16,}"
                ),
            ),
            (
                "env_style_secret",
                re.compile(
                    r"(?i)\b[A-Z0-9_]*(?:API[_-]?KEY|SECRET(?:[_-]?KEY)?|TOKEN|"
                    r"PASSWORD|PRIVATE[_-]?KEY)\s*=\s*\S{16,}"
                ),
            ),
        ]


__all__ = [
    "SCHEMA",
    "PROMOTED_SCHEMA",
    "ASSET_KINDS",
    "ASSET_STATUSES",
    "external_dir",
    "assets_dir",
    "promoted_dir",
    "audit_path",
    "pin_asset",
    "scan_asset",
    "approve_asset",
    "reject_asset",
    "promote_asset",
    "revoke_asset",
    "get_asset",
    "list_assets",
    "show_asset",
    "content_sha256_tree",
]


def _iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def external_dir() -> Path:
    """Ensure and return $PIPELINE_DIR/external/ (path from pipeline.paths).

    Path resolution lives in ``pipeline.paths.external_dir`` (no mkdir).
    This wrapper mkdir's so pin/scan/audit never race missing parents.
    """
    d = paths_external_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d


def assets_dir() -> Path:
    d = external_dir() / "assets"
    d.mkdir(parents=True, exist_ok=True)
    return d


def promoted_dir() -> Path:
    d = external_dir() / "promoted"
    d.mkdir(parents=True, exist_ok=True)
    return d


def audit_path() -> Path:
    return external_dir() / "audit.jsonl"


def _validate_id(asset_id: str) -> str:
    s = (asset_id or "").strip().lower()
    if not s:
        raise ValueError("asset id is required")
    if ".." in s or "/" in s or "\\" in s or ":" in s or "\x00" in s:
        raise ValueError(f"invalid asset id (path segments not allowed): {asset_id!r}")
    if not _ID_RE.match(s):
        raise ValueError(
            f"invalid asset id {asset_id!r}: use lowercase letters, digits, "
            f"dot, hyphen, or underscore"
        )
    return s


def _validate_kind(kind: str) -> str:
    k = (kind or "").strip().lower()
    if k not in ASSET_KINDS:
        raise ValueError(f"kind must be one of {sorted(ASSET_KINDS)}; got {kind!r}")
    return k


def _validate_risk(risk_class: str) -> str:
    r = (risk_class or "medium").strip().lower()
    if r not in RISK_CLASSES:
        raise ValueError(f"risk_class must be one of {sorted(RISK_CLASSES)}")
    return r


def _asset_root(asset_id: str) -> Path:
    safe = _validate_id(asset_id)
    return assets_dir() / safe


def _asset_json_path(asset_id: str) -> Path:
    return _asset_root(asset_id) / "asset.json"


def _payload_dir(asset_id: str) -> Path:
    return _asset_root(asset_id) / "payload"


def _scan_report_path(asset_id: str) -> Path:
    return _asset_root(asset_id) / "scan_report.json"


def _promoted_path(asset_id: str) -> Path:
    return promoted_dir() / f"{_validate_id(asset_id)}.json"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _actor() -> str:
    for key in ("EXTERNAL_INGEST_ACTOR", "USER", "USERNAME"):
        v = (os.environ.get(key) or "").strip()
        if v:
            return v
    return "unknown"


def append_audit(
    action: str,
    *,
    asset_id: str | None = None,
    ok: bool = True,
    detail: str = "",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Append one audit line (jsonl). Always creates parent dirs."""
    rec: dict[str, Any] = {
        "t": _iso(),
        "action": action,
        "actor": _actor(),
        "asset_id": asset_id,
        "ok": ok,
        "detail": (detail or "")[:2000],
    }
    if extra:
        rec["extra"] = extra
    path = audit_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
    return rec


def content_sha256_tree(root: Path) -> str:
    """Stable content hash of a file or directory tree (path-relative, sorted)."""
    root = root.resolve()
    h = hashlib.sha256()
    if root.is_file():
        h.update(b"FILE\0")
        h.update(root.name.encode("utf-8", errors="replace"))
        h.update(b"\0")
        with root.open("rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    if not root.is_dir():
        raise FileNotFoundError(f"not a file or directory: {root}")

    entries: list[tuple[str, Path]] = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Deterministic walk: sort in place
        dirnames.sort()
        filenames.sort()
        base = Path(dirpath)
        for name in filenames:
            p = base / name
            # Skip broken symlinks; refuse symlink escape later in scan
            try:
                rel = p.relative_to(root).as_posix()
            except ValueError:
                continue
            entries.append((rel, p))

    for rel, p in sorted(entries, key=lambda x: x[0]):
        h.update(rel.encode("utf-8", errors="replace"))
        h.update(b"\0")
        if p.is_symlink():
            try:
                target = os.readlink(p)
            except OSError:
                target = ""
            h.update(b"LINK\0")
            h.update(str(target).encode("utf-8", errors="replace"))
            h.update(b"\0")
            continue
        if not p.is_file():
            continue
        h.update(b"FILE\0")
        try:
            with p.open("rb") as fh:
                for chunk in iter(lambda: fh.read(65536), b""):
                    h.update(chunk)
        except OSError as exc:
            h.update(f"ERR:{exc}".encode("utf-8", errors="replace"))
        h.update(b"\0")
    return h.hexdigest()


def _default_id_from_source(source: Path, kind: str) -> str:
    base = source.stem if source.is_file() else source.name
    base = re.sub(r"[^a-z0-9._-]+", "-", base.strip().lower()).strip(".-_")
    if not base:
        base = "asset"
    # Keep id readable; kind prefix for draft external_* naming later
    candidate = f"{kind}_{base}"
    # Clamp length
    if len(candidate) > 80:
        candidate = candidate[:80].rstrip(".-_")
    return _validate_id(candidate)


def _copy_into_quarantine(source: Path, dest: Path) -> None:
    """Copy file or directory into dest (dest becomes the payload root content)."""
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)

    source = source.resolve()
    if source.is_file():
        # Place single file under payload/ with original name
        shutil.copy2(source, dest / source.name)
        return

    if not source.is_dir():
        raise FileNotFoundError(f"source not found: {source}")

    # Copy tree, refusing path escape / absolute symlink destinations at copy time
    for dirpath, dirnames, filenames in os.walk(source, followlinks=False):
        dirnames.sort()
        filenames.sort()
        cur = Path(dirpath)
        try:
            rel_dir = cur.relative_to(source)
        except ValueError as exc:
            raise ValueError(f"path escape during walk: {cur}") from exc
        # Disallow ".." segments in relative path
        if ".." in rel_dir.parts:
            raise ValueError(f"path traversal in source tree: {rel_dir}")
        target_dir = dest / rel_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        for name in filenames:
            if name in (".", "..") or ".." in name:
                raise ValueError(f"path traversal filename: {name!r}")
            src_f = cur / name
            # Resolve and ensure still under source (symlink escape)
            if src_f.is_symlink():
                # Copy link target content only if it resolves under source
                try:
                    resolved = src_f.resolve(strict=True)
                except OSError as exc:
                    raise ValueError(f"broken symlink: {src_f}") from exc
                try:
                    resolved.relative_to(source)
                except ValueError as exc:
                    raise ValueError(
                        f"symlink escapes source root: {src_f} -> {resolved}"
                    ) from exc
            dst_f = target_dir / name
            if src_f.is_file() or src_f.is_symlink():
                shutil.copy2(src_f, dst_f, follow_symlinks=True)


def get_asset(asset_id: str) -> dict[str, Any] | None:
    path = _asset_json_path(asset_id)
    if not path.is_file():
        return None
    try:
        return _load_json(path)
    except (OSError, json.JSONDecodeError):
        return None


def list_assets(
    *,
    kind: str | None = None,
    status: str | None = None,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    root = assets_dir()
    if not root.is_dir():
        return out
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        rec_path = child / "asset.json"
        if not rec_path.is_file():
            continue
        try:
            rec = _load_json(rec_path)
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


def show_asset(asset_id: str) -> dict[str, Any]:
    """Return asset record + optional scan report + promoted path existence."""
    rec = get_asset(asset_id)
    if rec is None:
        raise FileNotFoundError(f"asset not found: {asset_id}")
    result: dict[str, Any] = {"asset": rec}
    sp = _scan_report_path(asset_id)
    if sp.is_file():
        try:
            result["scan_report"] = _load_json(sp)
        except (OSError, json.JSONDecodeError):
            result["scan_report"] = None
    pp = _promoted_path(asset_id)
    result["promoted_path"] = str(pp) if pp.is_file() else None
    result["payload_dir"] = str(_payload_dir(asset_id))
    return result


def pin_asset(
    source_path: str | Path,
    *,
    kind: str,
    asset_id: str | None = None,
    force: bool = False,
    license_note: str = "",
    risk_class: str = "medium",
    commit_sha: str | None = None,
    source_url: str | None = None,
    write_trace: bool = True,
) -> dict[str, Any]:
    """Snapshot local path/dir into quarantine and write external_asset.v1.

    Does not fetch URLs. Re-pin same id requires force=True.
    """
    kind = _validate_kind(kind)
    risk = _validate_risk(risk_class)
    source = Path(source_path).expanduser()
    if not source.exists():
        raise FileNotFoundError(f"source not found: {source}")
    # Resolve for stable source_url_or_path; do not require under factory root
    try:
        source_resolved = source.resolve()
    except OSError:
        source_resolved = source

    aid = _validate_id(asset_id) if asset_id else _default_id_from_source(source, kind)

    existing = get_asset(aid)
    if existing is not None and not force:
        raise FileExistsError(
            f"asset {aid!r} already exists (status={existing.get('status')}); "
            f"pass force=True to re-pin"
        )

    root = _asset_root(aid)
    if force and root.exists():
        # Wipe prior quarantine tree (keep nothing stale)
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)
    payload = _payload_dir(aid)

    try:
        _copy_into_quarantine(source_resolved, payload)
    except Exception:
        # Best-effort cleanup of partial pin
        if root.exists() and not existing:
            shutil.rmtree(root, ignore_errors=True)
        raise

    content_hash = content_sha256_tree(payload)
    pin: dict[str, Any] = {"content_sha256": content_hash}
    if commit_sha:
        pin["commit_sha"] = str(commit_sha).strip()

    source_ref = source_url.strip() if source_url else str(source_resolved)

    rec: dict[str, Any] = {
        "schema": SCHEMA,
        "id": aid,
        "kind": kind,
        "source_url_or_path": source_ref,
        "pin": pin,
        "license_note": (license_note or "").strip(),
        "status": "quarantined",
        "risk_class": risk,
        "created_at": _iso(),
        "updated_at": _iso(),
        "quarantine_path": str(payload),
        "approval": None,
        "rejection": None,
        "promote_notes": "",
        "presence_smoke": None,
    }
    _save_json(_asset_json_path(aid), rec)
    append_audit(
        "pin",
        asset_id=aid,
        ok=True,
        detail=f"pinned {kind} from {source_ref}",
        extra={"content_sha256": content_hash, "force": force},
    )
    if write_trace:
        _trace_action(rec, action="pin", ok=True, detail=f"pin {aid}")
    return rec


def _iter_payload_files(payload: Path) -> list[Path]:
    files: list[Path] = []
    if not payload.exists():
        return files
    for dirpath, dirnames, filenames in os.walk(payload, followlinks=False):
        dirnames.sort()
        filenames.sort()
        base = Path(dirpath)
        for name in filenames:
            files.append(base / name)
    return files


def _find_license_note(payload: Path) -> str:
    """Return short license note from LICENSE* if present."""
    if not payload.is_dir():
        return ""
    for p in sorted(payload.rglob("*")):
        if not p.is_file():
            continue
        if p.name.lower() in _LICENSE_NAMES:
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                return f"found {p.name} (unreadable)"
            first = " ".join(text.strip().splitlines()[:3])[:240]
            return f"{p.name}: {first}" if first else f"found {p.name}"
    return ""


def scan_asset(
    asset_id: str,
    *,
    max_total_bytes: int = DEFAULT_MAX_TOTAL_BYTES,
    max_file_bytes: int = DEFAULT_MAX_FILE_BYTES,
    write_trace: bool = True,
) -> dict[str, Any]:
    """Static scan on quarantined payload. No network.

    On pass → status scanned; on fail → rejected (with report).
    """
    rec = get_asset(asset_id)
    if rec is None:
        raise FileNotFoundError(f"asset not found: {asset_id}")
    status = str(rec.get("status") or "")
    if status in ("revoked",):
        raise ValueError(f"cannot scan revoked asset: {asset_id}")
    if status == "promoted":
        raise ValueError(f"asset already promoted: {asset_id}; re-pin with force to rescan")

    payload = _payload_dir(asset_id)
    checks: list[dict[str, Any]] = []
    passed = True
    total_size = 0
    secret_hits: list[str] = []
    bad_ext: list[str] = []
    path_escape: list[str] = []

    if not payload.is_dir():
        checks.append(
            {"name": "payload_exists", "pass": False, "detail": str(payload)}
        )
        passed = False
    else:
        checks.append({"name": "payload_exists", "pass": True, "detail": str(payload)})

        # Re-hash and compare pin
        try:
            live_hash = content_sha256_tree(payload)
            pin_hash = (rec.get("pin") or {}).get("content_sha256")
            ok_hash = bool(pin_hash) and live_hash == pin_hash
            checks.append(
                {
                    "name": "content_hash_match",
                    "pass": ok_hash,
                    "detail": f"live={live_hash} pin={pin_hash}",
                }
            )
            if not ok_hash:
                passed = False
        except OSError as exc:
            checks.append(
                {"name": "content_hash_match", "pass": False, "detail": str(exc)}
            )
            passed = False

        files = _iter_payload_files(payload)
        if not files:
            checks.append({"name": "non_empty", "pass": False, "detail": "no files"})
            passed = False
        else:
            checks.append(
                {"name": "non_empty", "pass": True, "detail": f"files={len(files)}"}
            )

        patterns = _secret_patterns()
        for fpath in files:
            try:
                rel = fpath.relative_to(payload).as_posix()
            except ValueError:
                path_escape.append(str(fpath))
                passed = False
                continue
            if ".." in Path(rel).parts or rel.startswith("/") or rel.startswith("\\"):
                path_escape.append(rel)
                passed = False
                continue
            # Symlink that points outside payload
            if fpath.is_symlink():
                try:
                    resolved = fpath.resolve(strict=False)
                    resolved.relative_to(payload.resolve())
                except (OSError, ValueError):
                    path_escape.append(rel)
                    passed = False
                    continue

            ext = fpath.suffix.lower()
            if ext in DISALLOWED_EXTENSIONS:
                bad_ext.append(rel)
                passed = False
                continue

            try:
                size = fpath.stat().st_size
            except OSError as exc:
                checks.append(
                    {"name": "readable", "pass": False, "detail": f"{rel}: {exc}"}
                )
                passed = False
                continue
            total_size += size

            # Text-ish secret scan for modest files
            if size <= max_file_bytes and size > 0:
                try:
                    raw = fpath.read_bytes()
                except OSError:
                    continue
                # Skip obvious binary (NUL in first 8k)
                sample = raw[:8192]
                if b"\x00" in sample:
                    continue
                text = raw.decode("utf-8", errors="replace")
                for label, pat in patterns:
                    if pat.search(text):
                        secret_hits.append(f"{label}:{rel}")

        if total_size > max_total_bytes:
            checks.append(
                {
                    "name": "max_size",
                    "pass": False,
                    "detail": f"{total_size} > {max_total_bytes}",
                }
            )
            passed = False
        else:
            checks.append(
                {
                    "name": "max_size",
                    "pass": True,
                    "detail": f"{total_size} <= {max_total_bytes}",
                }
            )

        if path_escape:
            checks.append(
                {
                    "name": "path_escape",
                    "pass": False,
                    "detail": ",".join(path_escape[:20]),
                }
            )
            passed = False
        else:
            checks.append({"name": "path_escape", "pass": True, "detail": "ok"})

        if bad_ext:
            checks.append(
                {
                    "name": "disallowed_extensions",
                    "pass": False,
                    "detail": ",".join(bad_ext[:20]),
                }
            )
            passed = False
        else:
            checks.append(
                {"name": "disallowed_extensions", "pass": True, "detail": "ok"}
            )

        if secret_hits:
            checks.append(
                {
                    "name": "no_secrets",
                    "pass": False,
                    "detail": ",".join(secret_hits[:30]),
                }
            )
            passed = False
        else:
            checks.append({"name": "no_secrets", "pass": True, "detail": "ok"})

        # License note (informational; does not fail scan if missing)
        found_license = _find_license_note(payload)
        if found_license:
            if not rec.get("license_note"):
                rec["license_note"] = found_license
            checks.append(
                {
                    "name": "license_note",
                    "pass": True,
                    "detail": found_license[:200],
                }
            )
        else:
            checks.append(
                {
                    "name": "license_note",
                    "pass": True,
                    "detail": rec.get("license_note") or "none found (informational)",
                }
            )

    report: dict[str, Any] = {
        "checked_at": _iso(),
        "pass": passed,
        "checks": checks,
        "total_bytes": total_size,
        "content_sha256": (rec.get("pin") or {}).get("content_sha256"),
    }
    _save_json(_scan_report_path(asset_id), report)
    rec["scan_report"] = report
    rec["updated_at"] = _iso()

    if passed:
        # Allow re-scan of approved → stay approved? Spec: scanned on pass.
        # If already approved, keep approved; if quarantined/rejected → scanned.
        if status not in ("approved", "promoted"):
            rec["status"] = "scanned"
        # rejected → scanned if now clean
        if status == "rejected":
            rec["status"] = "scanned"
            rec["rejection"] = None
    else:
        rec["status"] = "rejected"
        # Prefer secret_fail naming for audit
        fail_names = [c["name"] for c in checks if not c.get("pass")]
        rec["rejection"] = {
            "at": _iso(),
            "actor": "scan",
            "reason": "scan_failed:" + ",".join(fail_names),
        }

    _save_json(_asset_json_path(asset_id), rec)
    append_audit(
        "scan",
        asset_id=asset_id,
        ok=passed,
        detail="scan pass" if passed else "scan fail",
        extra={"status": rec["status"], "checks_failed": [
            c["name"] for c in checks if not c.get("pass")
        ]},
    )
    if write_trace:
        fc = None
        if not passed:
            for c in checks:
                if c.get("name") == "no_secrets" and not c.get("pass"):
                    fc = "secret_fail"
                    break
            if fc is None:
                for c in checks:
                    if c.get("name") == "path_escape" and not c.get("pass"):
                        fc = "path_fail"
                        break
            if fc is None:
                fc = "sandbox_fail"
        _trace_action(
            rec,
            action="scan",
            ok=passed,
            detail="scan pass" if passed else "scan fail",
            failure_class=fc,
        )
    return rec


def approve_asset(
    asset_id: str,
    *,
    notes: str = "",
    actor: str | None = None,
    write_trace: bool = True,
) -> dict[str, Any]:
    """Human approve after scan. Requires status scanned (or re-approve approved)."""
    rec = get_asset(asset_id)
    if rec is None:
        raise FileNotFoundError(f"asset not found: {asset_id}")
    status = str(rec.get("status") or "")
    if status in ("rejected", "quarantined", "revoked"):
        raise ValueError(
            f"cannot approve asset in status {status!r}; scan must pass first "
            f"(status=scanned)"
        )
    if status == "promoted":
        raise ValueError(f"asset already promoted: {asset_id}")
    if status not in ("scanned", "approved"):
        raise ValueError(f"cannot approve from status {status!r}")

    who = (actor or _actor()).strip() or "unknown"
    rec["status"] = "approved"
    rec["approval"] = {
        "at": _iso(),
        "actor": who,
        "notes": (notes or "").strip(),
    }
    rec["rejection"] = None
    rec["updated_at"] = _iso()
    _save_json(_asset_json_path(asset_id), rec)
    append_audit(
        "approve",
        asset_id=asset_id,
        ok=True,
        detail=notes or "approved",
        extra={"actor": who},
    )
    if write_trace:
        _trace_action(rec, action="approve", ok=True, detail=f"approved by {who}")
    return rec


def reject_asset(
    asset_id: str,
    *,
    reason: str = "",
    actor: str | None = None,
    write_trace: bool = True,
) -> dict[str, Any]:
    """Human reject. Sets status rejected + reason."""
    rec = get_asset(asset_id)
    if rec is None:
        raise FileNotFoundError(f"asset not found: {asset_id}")
    status = str(rec.get("status") or "")
    if status == "promoted":
        raise ValueError(f"cannot reject promoted asset {asset_id}; revoke instead")
    if status == "revoked":
        raise ValueError(f"asset already revoked: {asset_id}")

    who = (actor or _actor()).strip() or "unknown"
    rec["status"] = "rejected"
    rec["rejection"] = {
        "at": _iso(),
        "actor": who,
        "reason": (reason or "rejected").strip(),
    }
    rec["approval"] = None
    rec["updated_at"] = _iso()
    _save_json(_asset_json_path(asset_id), rec)
    append_audit(
        "reject",
        asset_id=asset_id,
        ok=True,
        detail=reason or "rejected",
        extra={"actor": who},
    )
    if write_trace:
        _trace_action(
            rec,
            action="reject",
            ok=True,
            detail=reason or "rejected",
            outcome_override="human_rejected",
        )
    return rec


def _presence_smoke(kind: str, payload: Path) -> dict[str, Any]:
    """Presence-only checks (not field_prove)."""
    checks: list[dict[str, Any]] = []
    ok = True
    kind = kind.lower()

    def has_any(names: list[str]) -> Path | None:
        for n in names:
            p = payload / n
            if p.is_file():
                return p
            # also search one level deep
            matches = list(payload.glob(f"*/{n}"))
            if matches:
                return matches[0]
        return None

    if kind == "skill":
        p = has_any(["SKILL.md", "skill.md"])
        if p is None:
            # rglob limited
            found = list(payload.rglob("SKILL.md"))[:1]
            p = found[0] if found else None
        if p is None:
            checks.append({"name": "skill_md", "pass": False, "detail": "SKILL.md missing"})
            ok = False
        else:
            checks.append({"name": "skill_md", "pass": True, "detail": str(p.name)})
    elif kind == "software":
        markers = [
            "main.py",
            "__main__.py",
            "pyproject.toml",
            "setup.py",
            "ENTRYPOINT",
            "entrypoint",
            "Makefile",
            "package.json",
        ]
        p = has_any(markers)
        if p is None:
            checks.append(
                {
                    "name": "entrypoint_marker",
                    "pass": False,
                    "detail": f"none of {markers}",
                }
            )
            ok = False
        else:
            checks.append(
                {"name": "entrypoint_marker", "pass": True, "detail": p.name}
            )
    elif kind in ("mcp", "external_mcp"):
        p = has_any(["server.py", "manifest.json", "mcp.json"])
        if p is None:
            found = list(payload.rglob("server.py"))[:1]
            p = found[0] if found else None
        if p is None:
            checks.append(
                {
                    "name": "mcp_stub",
                    "pass": False,
                    "detail": "server.py/manifest.json missing",
                }
            )
            ok = False
        else:
            checks.append({"name": "mcp_stub", "pass": True, "detail": p.name})
    else:
        checks.append({"name": "kind", "pass": False, "detail": f"unknown kind {kind}"})
        ok = False

    return {"pass": ok, "checks": checks, "checked_at": _iso()}


def promote_asset(
    asset_id: str,
    *,
    notes: str = "",
    write_trace: bool = True,
) -> dict[str, Any]:
    """Promote approved asset → external_* draft under promoted/.

    **Blocked without prior approve.** Presence smoke only (not field_prove).
    Writes goal_trace with trust=external and low train_weight.
    """
    rec = get_asset(asset_id)
    if rec is None:
        raise FileNotFoundError(f"asset not found: {asset_id}")
    status = str(rec.get("status") or "")
    if status == "promoted":
        # Idempotent return of existing
        return rec
    if status != "approved":
        raise ValueError(
            f"promote blocked: asset {asset_id} status={status!r}; "
            f"require status=approved (human gate). "
            f"Sequence: pin → scan → approve → promote"
        )
    approval = rec.get("approval")
    if not isinstance(approval, dict) or not approval.get("actor"):
        raise ValueError(
            f"promote blocked: missing approval record on {asset_id}"
        )

    payload = _payload_dir(asset_id)
    if not payload.is_dir():
        raise ValueError(f"quarantine payload missing for {asset_id}")

    # Pin hash must still match
    live_hash = content_sha256_tree(payload)
    pin_hash = (rec.get("pin") or {}).get("content_sha256")
    if not pin_hash or live_hash != pin_hash:
        raise ValueError(
            f"content hash mismatch; re-scan before promote: {asset_id}"
        )

    smoke = _presence_smoke(str(rec.get("kind") or ""), payload)
    rec["presence_smoke"] = smoke
    if not smoke.get("pass"):
        # Keep approved; do not promote on presence fail
        rec["updated_at"] = _iso()
        _save_json(_asset_json_path(asset_id), rec)
        append_audit(
            "promote",
            asset_id=asset_id,
            ok=False,
            detail="presence smoke failed",
            extra={"smoke": smoke},
        )
        if write_trace:
            _trace_action(
                rec,
                action="promote",
                ok=False,
                detail="presence smoke failed",
                failure_class="smoke_fail",
            )
        raise ValueError(
            f"presence smoke failed for {asset_id}: "
            + ",".join(
                c["name"] for c in smoke.get("checks") or [] if not c.get("pass")
            )
        )

    kind = str(rec.get("kind") or "software")
    draft_id = f"external_{kind}_{rec.get('id')}"
    # Avoid double external_ if id already prefixed
    if str(rec.get("id") or "").startswith("external_"):
        draft_id = str(rec.get("id"))

    promoted: dict[str, Any] = {
        "schema": PROMOTED_SCHEMA,
        "id": draft_id,
        "external_asset_id": rec.get("id"),
        "kind": kind,
        "status": "draft",  # registry-style draft; not field_proven
        "trust": "external",
        "pin": dict(rec.get("pin") or {}),
        "source_url_or_path": rec.get("source_url_or_path"),
        "license_note": rec.get("license_note") or "",
        "risk_class": rec.get("risk_class") or "medium",
        "approval": rec.get("approval"),
        "presence_smoke": smoke,
        "quarantine_path": str(payload),
        "promoted_at": _iso(),
        "notes": (notes or "").strip(),
        # Graph nodes may only reference this id after promote — never clone source
        "compose_hint": (
            "Reference this promoted id only; do not git-clone source at attempt time."
        ),
    }
    _save_json(_promoted_path(asset_id), promoted)

    rec["status"] = "promoted"
    if notes:
        prev = str(rec.get("promote_notes") or "")
        rec["promote_notes"] = (prev + "\n" + notes).strip() if prev else notes
    rec["promoted_id"] = draft_id
    rec["promoted_at"] = promoted["promoted_at"]
    rec["updated_at"] = _iso()
    _save_json(_asset_json_path(asset_id), rec)

    append_audit(
        "promote",
        asset_id=asset_id,
        ok=True,
        detail=f"promoted as {draft_id}",
        extra={"promoted_id": draft_id, "content_sha256": pin_hash},
    )
    if write_trace:
        _trace_action(
            rec,
            action="promote",
            ok=True,
            detail=f"promoted as {draft_id}",
            claim="external_promote",
        )
    return rec


def revoke_asset(
    asset_id: str,
    *,
    reason: str = "",
    write_trace: bool = True,
) -> dict[str, Any]:
    """Mark asset revoked; leave quarantine on disk for audit."""
    rec = get_asset(asset_id)
    if rec is None:
        raise FileNotFoundError(f"asset not found: {asset_id}")
    rec["status"] = "revoked"
    rec["updated_at"] = _iso()
    rec["revocation"] = {
        "at": _iso(),
        "actor": _actor(),
        "reason": (reason or "revoked").strip(),
    }
    _save_json(_asset_json_path(asset_id), rec)
    # Soft-delete promoted draft if present
    pp = _promoted_path(asset_id)
    if pp.is_file():
        try:
            data = _load_json(pp)
            data["status"] = "revoked"
            data["revoked_at"] = _iso()
            _save_json(pp, data)
        except (OSError, json.JSONDecodeError):
            pass
    append_audit(
        "revoke",
        asset_id=asset_id,
        ok=True,
        detail=reason or "revoked",
    )
    if write_trace:
        _trace_action(
            rec,
            action="revoke",
            ok=True,
            detail=reason or "revoked",
            outcome_override="revoked",
        )
    return rec


def _trace_action(
    rec: dict[str, Any],
    *,
    action: str,
    ok: bool,
    detail: str = "",
    failure_class: str | None = None,
    outcome_override: str | None = None,
    claim: str | None = None,
) -> None:
    """Emit goal_trace with trust=external (Phase 3 clamp → low train_weight)."""
    try:
        from pipeline.goal_trace import (
            EXTERNAL_MAX_TRAIN_WEIGHT,
            OUTCOME_FAILED,
            OUTCOME_HUMAN_REJECTED,
            OUTCOME_PROVEN,
            OUTCOME_REVOKED,
            append_event,
            finalize_trace,
            start_trace,
        )

        aid = str(rec.get("id") or "unknown")
        tr = start_trace(
            f"external_{action}:{aid}",
            goal_id=f"external_{action}_{aid}_{_iso()[:19].replace(':', '')}",
            mode="external",
            plan=[{"step": 1, "intent": action, "asset_id": aid}],
        )
        append_event(
            tr,
            type="tool",
            tool=f"external_ingest.{action}",
            args={"asset_id": aid, "status": rec.get("status"), "kind": rec.get("kind")},
            result_snip=detail[:500],
            ok=ok,
        )
        if outcome_override == "revoked" or action == "revoke":
            outcome = OUTCOME_REVOKED
            status = "revoked"
            fc = None
            tw: float | None = 0.5
        elif outcome_override == "human_rejected" or action == "reject":
            outcome = OUTCOME_HUMAN_REJECTED
            status = "human_rejected"
            fc = None
            tw = 0.0
        elif ok:
            outcome = OUTCOME_PROVEN
            status = "goal_proven"
            fc = None
            # Even "success" is external — clamp applies; set explicit low weight
            tw = EXTERNAL_MAX_TRAIN_WEIGHT if action == "promote" else 0.0
        else:
            outcome = OUTCOME_FAILED
            status = "goal_failed"
            fc = failure_class or "sandbox_fail"
            tw = 0.0

        finalize_trace(
            tr,
            status=status,
            outcome=outcome,
            failure_class=fc,
            oracle={
                "name": "external_ingest",
                "pass": ok,
                "evidence": detail,
                "asset_id": aid,
                "action": action,
            },
            train_weight=tw,
            trust="external",
            claim=claim or "external_ingest",
        )
    except Exception:
        log.debug("external_ingest goal_trace failed", exc_info=True)
