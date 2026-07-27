"""
mcp_factory v1 — wrap verified capabilities as local stdio JSONL MCP servers.

Layout under PIPELINE_DIR:
  mcps/mcp_{slug}/server.py
  mcps/mcp_{slug}/manifest.json      (mcp_manifest.v1 + provenance)
  mcps/mcp_{slug}/smoke_report.json  (ping/describe/[invoke] checks)
  mcps/mcp_{slug}/invoke_report.json (durable invoke-oracle evidence)

mcp_manifest.v1 fields (v1 provenance extensions):
  schema, mcp_slug, wraps_capability / capability_slug, transport,
  server_path, tools, status (draft|smoked|verified|revoked),
  wrap_version, content_sha256 (server.py), created_at,
  last_smoke_at, last_smoke_ok, smoked_at, invoke_oracle, revoked_at.

Factory is a separate loop from the software factory: scaffold + smoke +
re-smoke + revoke + best-effort registry insert. Does not invent product
code — only wraps an existing capability_slug via pipeline.capability_tools.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pipeline.paths import get_pipeline_dir, mcps_dir
from pipeline.pipeline_config import PROJECT_ROOT

SCHEMA = "mcp_manifest.v1"
WRAP_VERSION = "1"
TRANSPORT = "stdio_jsonl"
TOOLS = ["ping", "describe", "invoke"]
STATUS_SMOKED = frozenset({"smoked", "verified"})
STATUS_REVOKED = "revoked"

__all__ = [
    "SCHEMA",
    "WRAP_VERSION",
    "TRANSPORT",
    "TOOLS",
    "mcp_slug_for",
    "mcp_dir",
    "is_mcp_smoked",
    "is_mcp_revoked",
    "wrap_capability_as_mcp",
    "smoke_mcp",
    "resmoke_mcp",
    "revoke_mcp",
    "register_mcp",
    "list_mcps",
    "drain_queue",
    "load_invoke_report",
    "load_smoke_report",
]


def _iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    try:
        h = hashlib.sha256()
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def _validate_slug_segment(raw: str, *, label: str = "slug") -> str:
    """Reject path traversal / separators / empty names (raises ValueError)."""
    s = (raw or "").strip()
    if not s:
        raise ValueError(f"{label} is required")
    if s in (".", "..") or s.strip(".") == "":
        raise ValueError(f"unsafe {label}: {raw!r}")
    if (
        ".." in s
        or "/" in s
        or "\\" in s
        or ":" in s
        or s.startswith("~")
        or "\x00" in s
    ):
        raise ValueError(f"unsafe {label}: {raw!r}")
    return s


def mcp_slug_for(capability_slug: str) -> str:
    """Normalize capability slug to mcp_ prefix form (path-safe single segment).

    Rejects ``..``, path separators, drive letters, and empty names so
    ``mcp_dir`` cannot escape ``mcps/``.
    """
    s = _validate_slug_segment(capability_slug, label="capability_slug")
    if s.startswith("mcp_"):
        rest = s[4:]
        if not rest:
            raise ValueError("capability_slug empty after mcp_ prefix")
        # Re-check body alone (whole string already checked for separators)
        _validate_slug_segment(rest, label="capability_slug")
        return s
    return f"mcp_{s}"


def mcp_dir(mcp_slug: str) -> Path:
    """Return mcps/{mcp_slug}/ (does not create). Raises ValueError if unsafe."""
    mslug = mcp_slug_for(mcp_slug)
    base = mcps_dir().resolve()
    target = (base / mslug).resolve()
    try:
        target.relative_to(base)
    except ValueError as exc:
        raise ValueError(f"mcp path escapes mcps/: {mcp_slug!r}") from exc
    return mcps_dir() / mslug


def _clear_sibling_reports(d: Path, *, invoke: bool = True, smoke: bool = False) -> None:
    """Remove durable reports under an MCP dir (best-effort)."""
    names: list[str] = []
    if invoke:
        names.append("invoke_report.json")
    if smoke:
        names.append("smoke_report.json")
    for name in names:
        p = d / name
        if p.is_file():
            try:
                p.unlink()
            except OSError:
                pass


def _capability_from_mcp_slug(mcp_slug: str) -> str:
    s = mcp_slug_for(mcp_slug)
    if s.startswith("mcp_"):
        return s[4:]
    return s


def _server_template(capability_slug: str, mcp_slug: str) -> str:
    """Generate a self-contained stdio JSONL server for one capability."""
    # Escape for embedding in source as string literals
    cap = capability_slug.replace("\\", "\\\\").replace('"', '\\"')
    mslug = mcp_slug.replace("\\", "\\\\").replace('"', '\\"')
    return f'''#!/usr/bin/env python3
"""Auto-generated MCP stdio JSONL server for capability `{cap}`.

Methods: ping, describe, invoke.
Transport: one JSON object per stdin line -> one JSON response per stdout line.
Generated by pipeline.mcp_factory — re-run wrap to regenerate.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

WRAPS_CAPABILITY = "{cap}"
MCP_SLUG = "{mslug}"


def _ensure_factory_path() -> None:
    """Allow import of pipeline.* when launched under PIPELINE_DIR/mcps/."""
    candidates = []
    for key in ("MCP_FACTORY_ROOT", "AICOMPETE_ROOT", "IDEA_IMPL_ROOT"):
        v = (os.environ.get(key) or "").strip()
        if v:
            candidates.append(v)
    # Walk up a few parents looking for a package root that has pipeline/
    here = Path(__file__).resolve().parent
    for p in [here, *here.parents[:6]]:
        if (p / "pipeline" / "__init__.py").is_file():
            candidates.append(str(p))
    for c in candidates:
        if c and c not in sys.path:
            sys.path.insert(0, c)


_ensure_factory_path()


def _handle(req: dict) -> dict:
    method = (req.get("method") or "").strip()
    params = req.get("params") or {{}}
    if not isinstance(params, dict):
        params = {{}}

    if method == "ping":
        return {{"ok": True, "result": "mcp-ok", "mcp_slug": MCP_SLUG}}

    if method == "describe":
        # Always ok=True so smoke can pass without a live registry row.
        try:
            from pipeline.capability_tools import describe_capability

            text = describe_capability(WRAPS_CAPABILITY)
            if not text:
                text = f"capability {{WRAPS_CAPABILITY}}: (empty describe)"
            return {{
                "ok": True,
                "result": text,
                "wraps_capability": WRAPS_CAPABILITY,
                "mcp_slug": MCP_SLUG,
            }}
        except Exception as exc:
            return {{
                "ok": True,
                "result": f"unknown capability {{WRAPS_CAPABILITY}}: {{exc}}",
                "wraps_capability": WRAPS_CAPABILITY,
                "mcp_slug": MCP_SLUG,
            }}

    if method == "invoke":
        args = params.get("args", "")
        if args is None:
            args = ""
        args = str(args)
        cwd = str(params.get("cwd") or "")
        try:
            from pipeline.capability_tools import invoke_capability

            out = invoke_capability(WRAPS_CAPABILITY, args=args, cwd=cwd)
            # capability_tools returns ERROR: ... strings on failure
            ok = not str(out).startswith("ERROR:")
            return {{
                "ok": ok,
                "result": out,
                "wraps_capability": WRAPS_CAPABILITY,
                "mcp_slug": MCP_SLUG,
            }}
        except Exception as exc:
            return {{"ok": False, "error": str(exc), "mcp_slug": MCP_SLUG}}

    return {{"ok": False, "error": f"unknown method: {{method}}", "mcp_slug": MCP_SLUG}}


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError as exc:
            sys.stdout.write(json.dumps({{"ok": False, "error": str(exc)}}) + "\\n")
            sys.stdout.flush()
            continue
        if not isinstance(req, dict):
            sys.stdout.write(
                json.dumps({{"ok": False, "error": "request must be a JSON object"}}) + "\\n"
            )
            sys.stdout.flush()
            continue
        resp = _handle(req)
        sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
'''


def wrap_capability_as_mcp(
    capability_slug: str,
    *,
    entrypoint: str | None = None,
    cwd: str | None = None,
    force: bool = False,
) -> dict:
    """Scaffold mcps/mcp_{slug}/server.py + manifest.json.

    Returns mcp_manifest.v1 as a dict. If the MCP dir already exists and
    *force* is False, reloads and returns the existing manifest (rewriting
    only missing pieces). Server always implements ping/describe/invoke;
    invoke routes through capability_tools.invoke_capability.
    """
    # Path-safe normalize (rejects .. / separators)
    mslug = mcp_slug_for(capability_slug)
    wraps = mslug[4:] if mslug.startswith("mcp_") else mslug

    root = mcps_dir()
    root.mkdir(parents=True, exist_ok=True)
    d = mcp_dir(mslug)
    d.mkdir(parents=True, exist_ok=True)

    server_path = d / "server.py"
    manifest_path = d / "manifest.json"

    # Force re-wrap: drop stale oracle/smoke evidence for new server binary
    if force:
        _clear_sibling_reports(d, invoke=True, smoke=True)

    if manifest_path.is_file() and not force:
        try:
            existing = json.loads(manifest_path.read_text(encoding="utf-8"))
            if existing.get("schema") == SCHEMA and (d / "server.py").is_file():
                # Keep existing; note skip when already smoked (drain safety)
                st = str(existing.get("status") or "")
                if st == STATUS_REVOKED:
                    existing = dict(existing)
                    existing["skipped"] = True
                    existing["skip_reason"] = "revoked"
                    return existing
                if st in STATUS_SMOKED:
                    existing = dict(existing)
                    existing["skipped"] = True
                    existing["skip_reason"] = "already_smoked"
                return existing
        except (json.JSONDecodeError, OSError):
            pass

    server_src = _server_template(wraps, mslug)
    server_path.write_text(
        server_src,
        encoding="utf-8",
        newline="\n",
    )

    try:
        server_rel = str(server_path.relative_to(get_pipeline_dir())).replace("\\", "/")
    except ValueError:
        server_rel = str(server_path)

    status = "draft"
    last_smoke_at = None
    last_smoke_ok = None
    if (d / "smoke_report.json").is_file() and not force:
        try:
            sr = json.loads((d / "smoke_report.json").read_text(encoding="utf-8"))
            if sr.get("ok"):
                status = "smoked"
            last_smoke_at = sr.get("ts")
            last_smoke_ok = bool(sr.get("ok"))
        except (json.JSONDecodeError, OSError):
            pass

    content_sha = _sha256_text(server_src)
    created = _iso()
    # Preserve created_at when force-rewrapping an existing manifest
    if manifest_path.is_file():
        try:
            prev = json.loads(manifest_path.read_text(encoding="utf-8"))
            if isinstance(prev, dict) and prev.get("created_at"):
                created = str(prev["created_at"])
        except (json.JSONDecodeError, OSError):
            pass

    manifest: dict[str, Any] = {
        "schema": SCHEMA,
        "mcp_slug": mslug,
        "wraps_capability": wraps,
        "capability_slug": wraps,
        "transport": TRANSPORT,
        "server_path": server_rel,
        "tools": list(TOOLS),
        "status": status,
        "wrap_version": WRAP_VERSION,
        "content_sha256": content_sha,
        "created_at": created,
    }
    if last_smoke_at is not None:
        manifest["last_smoke_at"] = last_smoke_at
    if last_smoke_ok is not None:
        manifest["last_smoke_ok"] = last_smoke_ok
    if entrypoint:
        manifest["entrypoint_override"] = entrypoint
    if cwd:
        manifest["cwd_override"] = cwd

    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return manifest


def _load_manifest(mcp_slug: str) -> dict[str, Any] | None:
    path = mcp_dir(mcp_slug) / "manifest.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _save_manifest(manifest: dict[str, Any]) -> Path:
    mslug = str(manifest.get("mcp_slug") or "")
    path = mcp_dir(mslug) / "manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path


def _rpc_line(proc: subprocess.Popen, req: dict, *, timeout_s: float) -> dict:
    """Write one JSON-L request and read one JSON-L response within *timeout_s*.

    Uses a reader thread so a hung MCP server cannot block forever. On timeout
    the process is killed and ``TimeoutError`` is raised.
    """
    assert proc.stdin is not None and proc.stdout is not None
    line = json.dumps(req, ensure_ascii=False) + "\n"
    proc.stdin.write(line)
    proc.stdin.flush()

    box: list[Any] = []
    err: list[BaseException] = []

    def _read() -> None:
        try:
            box.append(proc.stdout.readline())  # type: ignore[union-attr]
        except BaseException as exc:  # noqa: BLE001 — surface to caller
            err.append(exc)

    t = threading.Thread(target=_read, daemon=True)
    t.start()
    budget = max(0.05, float(timeout_s) if timeout_s is not None else 15.0)
    t.join(timeout=budget)
    if t.is_alive():
        try:
            proc.kill()
        except Exception:
            pass
        raise TimeoutError(f"MCP RPC timed out after {budget}s waiting for response")
    if err:
        raise err[0]
    out = box[0] if box else ""
    if not out:
        raise RuntimeError("MCP server closed stdout without response")
    return json.loads(out)


def is_mcp_revoked(mcp_slug: str) -> bool:
    """True if manifest status is revoked."""
    man = _load_manifest(mcp_slug_for(mcp_slug))
    if not man:
        return False
    return str(man.get("status") or "") == STATUS_REVOKED


def is_mcp_smoked(mcp_slug: str) -> bool:
    """True if manifest status is smoked/verified, server.py exists, not revoked."""
    mslug = mcp_slug_for(mcp_slug)
    d = mcp_dir(mslug)
    if not (d / "server.py").is_file():
        return False
    man = _load_manifest(mslug)
    if not man:
        return False
    st = str(man.get("status") or "")
    if st == STATUS_REVOKED:
        return False
    return st in STATUS_SMOKED


def load_invoke_report(mcp_slug: str) -> dict[str, Any] | None:
    """Load durable invoke_report.json if present."""
    path = mcp_dir(mcp_slug_for(mcp_slug)) / "invoke_report.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (json.JSONDecodeError, OSError):
        return None


def load_smoke_report(mcp_slug: str) -> dict[str, Any] | None:
    """Load durable smoke_report.json if present."""
    path = mcp_dir(mcp_slug_for(mcp_slug)) / "smoke_report.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (json.JSONDecodeError, OSError):
        return None


def smoke_mcp(
    mcp_slug: str,
    *,
    timeout_s: float = 15.0,
    require_invoke: bool = False,
    invoke_args: str = "--help",
    skip_if_smoked: bool = False,
    force: bool = False,
) -> dict:
    """Spawn server.py; ping + describe required; optional invoke oracle.

    Writes smoke_report.json next to the server. Invoke report policy:
      - require_invoke or invoke ok → write/update invoke_report.json
      - soft smoke with failed invoke → **delete** prior invoke_report
        (restore presence fallback; no stale ok oracle)
      - smoke fails before invoke (ping/describe) → delete prior invoke_report

    Records goal_trace mode=mcp_factory. Updates last_smoke_at on every run.

    *require_invoke*: also require method invoke with *invoke_args* (default
    ``--help``) to return ok. Use for real capability quality bar.
    *skip_if_smoked*: if already smoked/verified and not *force*, return prior
    report without re-spawning (drain-queue bulk safety).
    Revoked MCPs refuse smoke (ok=False) until re-wrapped with force.
    """
    mslug = mcp_slug_for(mcp_slug)
    d = mcp_dir(mslug)
    server = d / "server.py"

    man0 = _load_manifest(mslug)
    # Revoked blocks are never smoked until re-wrap (force=True on wrap).
    if man0 and str(man0.get("status") or "") == STATUS_REVOKED:
        report = {
            "ok": False,
            "mcp_slug": mslug,
            "error": "mcp is revoked; re-wrap with force before smoke/re-smoke",
            "ts": _iso(),
            "manifest_status": STATUS_REVOKED,
        }
        d.mkdir(parents=True, exist_ok=True)
        (d / "smoke_report.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        _clear_sibling_reports(d, invoke=True, smoke=False)
        report["invoke_report_cleared"] = "revoked"
        _trace_smoke(mslug, report)
        return report

    if skip_if_smoked and not force and is_mcp_smoked(mslug):
        prior: dict[str, Any] = {
            "ok": True,
            "mcp_slug": mslug,
            "skipped": True,
            "skip_reason": "already_smoked",
            "server_path": str(server),
            "ts": _iso(),
            "manifest_status": (_load_manifest(mslug) or {}).get("status"),
        }
        # Prefer last smoke_report if present
        sr = d / "smoke_report.json"
        if sr.is_file():
            try:
                old = json.loads(sr.read_text(encoding="utf-8"))
                if isinstance(old, dict) and old.get("ok"):
                    prior["prior_smoke"] = {
                        "ts": old.get("ts"),
                        "checks": [
                            c.get("method") for c in (old.get("checks") or [])
                        ],
                    }
            except (json.JSONDecodeError, OSError):
                pass
        return prior

    if not server.is_file():
        ts_miss = _iso()
        report = {
            "ok": False,
            "mcp_slug": mslug,
            "error": f"server.py missing under {d}",
            "ts": ts_miss,
        }
        d.mkdir(parents=True, exist_ok=True)
        (d / "smoke_report.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        # Stale invoke success must not outlive a broken server
        _clear_sibling_reports(d, invoke=True, smoke=False)
        report["invoke_report_cleared"] = "server_missing"
        manifest = _load_manifest(mslug)
        if manifest is not None:
            manifest["last_smoke_at"] = ts_miss
            manifest["last_smoke_ok"] = False
            _save_manifest(manifest)
            report["manifest_status"] = manifest.get("status")
        _trace_smoke(mslug, report)
        return report

    env = os.environ.copy()
    factory_root = str(PROJECT_ROOT.resolve())
    env["MCP_FACTORY_ROOT"] = factory_root
    # Ensure pipeline package is importable
    existing_pp = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        factory_root + (os.pathsep + existing_pp if existing_pp else "")
    )
    # Keep caller's PIPELINE_DIR if set; else bind to live get_pipeline_dir
    env.setdefault("PIPELINE_DIR", str(get_pipeline_dir()))
    env.setdefault("PIPELINE_LEGACY", "0")

    checks: list[dict[str, Any]] = []
    ok = True
    error: str | None = None
    proc: subprocess.Popen | None = None
    try:
        proc = subprocess.Popen(
            [sys.executable, "-u", str(server)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            cwd=str(d),
        )
        # ping
        try:
            ping_resp = _rpc_line(
                proc, {"method": "ping", "params": {}}, timeout_s=timeout_s
            )
            ping_ok = bool(ping_resp.get("ok"))
            checks.append({"method": "ping", "ok": ping_ok, "resp": ping_resp})
            if not ping_ok:
                ok = False
                error = f"ping failed: {ping_resp}"
        except Exception as exc:
            ok = False
            error = f"ping error: {exc}"
            checks.append({"method": "ping", "ok": False, "error": str(exc)})

        # describe (must ok=True even if capability unknown)
        if ok:
            try:
                desc_resp = _rpc_line(
                    proc, {"method": "describe", "params": {}}, timeout_s=timeout_s
                )
                desc_ok = bool(desc_resp.get("ok"))
                checks.append(
                    {"method": "describe", "ok": desc_ok, "resp": desc_resp}
                )
                if not desc_ok:
                    ok = False
                    error = error or f"describe failed: {desc_resp}"
            except Exception as exc:
                ok = False
                error = error or f"describe error: {exc}"
                checks.append({"method": "describe", "ok": False, "error": str(exc)})

        # invoke oracle (always attempt when ping+describe ok; hard-fail if require_invoke)
        if ok:
            inv_args = (invoke_args if invoke_args is not None else "--help") or ""
            try:
                inv_resp = _rpc_line(
                    proc,
                    {"method": "invoke", "params": {"args": inv_args}},
                    timeout_s=timeout_s,
                )
                inv_ok = bool(inv_resp.get("ok"))
                checks.append(
                    {
                        "method": "invoke",
                        "ok": inv_ok,
                        "args": inv_args,
                        "resp": inv_resp,
                    }
                )
                if require_invoke and not inv_ok:
                    ok = False
                    error = error or f"invoke failed: {inv_resp}"
            except Exception as exc:
                checks.append(
                    {
                        "method": "invoke",
                        "ok": False,
                        "args": inv_args,
                        "error": str(exc),
                    }
                )
                if require_invoke:
                    ok = False
                    error = error or f"invoke error: {exc}"
    except Exception as exc:
        ok = False
        error = str(exc)
    finally:
        if proc is not None:
            try:
                if proc.stdin:
                    proc.stdin.close()
            except Exception:
                pass
            try:
                proc.kill()
            except Exception:
                pass
            try:
                proc.wait(timeout=3)
            except Exception:
                pass
            # capture residual stderr for diagnostics
            try:
                if proc.stderr:
                    err_tail = proc.stderr.read()
                    if err_tail and not ok:
                        error = (error or "") + f" | stderr: {err_tail[:500]}"
            except Exception:
                pass

    ts = _iso()
    inv_check = next((c for c in checks if c.get("method") == "invoke"), None)
    report: dict[str, Any] = {
        "ok": ok,
        "mcp_slug": mslug,
        "server_path": str(server),
        "checks": checks,
        "ts": ts,
        "timeout_s": timeout_s,
        "require_invoke": bool(require_invoke),
        "invoke_args": invoke_args
        if require_invoke or inv_check is not None
        else None,
    }
    if error:
        report["error"] = error

    (d / "smoke_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # Durable invoke oracle report (sibling of smoke_report).
    # Always keep reports consistent with this smoke run so graph honesty
    # cannot pass on a stale prior invoke_report.ok=true.
    if inv_check is not None and (require_invoke or bool(inv_check.get("ok"))):
        inv_report: dict[str, Any] = {
            "schema": "mcp_invoke_report.v1",
            "ok": bool(inv_check.get("ok")),
            "mcp_slug": mslug,
            "args": inv_check.get("args", invoke_args),
            "require_invoke": bool(require_invoke),
            "ts": ts,
            "check": inv_check,
            "smoke_ok": ok,
        }
        if inv_check.get("error"):
            inv_report["error"] = inv_check["error"]
        elif not inv_check.get("ok"):
            inv_report["error"] = error or "invoke returned not ok"
        (d / "invoke_report.json").write_text(
            json.dumps(inv_report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        report["invoke_report"] = inv_report
    elif inv_check is not None and not inv_check.get("ok"):
        # Soft smoke: invoke failed — drop prior success so presence fallback works
        _clear_sibling_reports(d, invoke=True, smoke=False)
        report["invoke_report_cleared"] = "soft_smoke_invoke_failed"
    elif not ok:
        # Failed before invoke (or no inv check) — drop stale oracle success
        _clear_sibling_reports(d, invoke=True, smoke=False)
        report["invoke_report_cleared"] = "smoke_failed_before_invoke"

    # Update manifest: status + provenance timestamps
    manifest = _load_manifest(mslug)
    if manifest is not None:
        # Refresh content hash if server present
        content_sha = _sha256_file(server)
        if content_sha:
            manifest["content_sha256"] = content_sha
        if not manifest.get("capability_slug"):
            manifest["capability_slug"] = manifest.get("wraps_capability") or (
                _capability_from_mcp_slug(mslug)
            )
        if not manifest.get("wrap_version"):
            manifest["wrap_version"] = WRAP_VERSION
        manifest["last_smoke_at"] = ts
        manifest["last_smoke_ok"] = bool(ok)
        if ok:
            manifest["status"] = "smoked"
            manifest["smoked_at"] = ts
            if inv_check is not None:
                manifest["invoke_oracle"] = {
                    "args": inv_check.get("args", invoke_args),
                    "ok": bool(inv_check.get("ok")),
                    "at": ts,
                }
        else:
            # keep draft/prior smoked; note last smoke failure (do not un-smoke
            # a previously good block on soft re-smoke fail unless was draft)
            if str(manifest.get("status") or "") not in STATUS_SMOKED:
                # leave draft; already not smoked
                pass
            if inv_check is not None:
                manifest["invoke_oracle"] = {
                    "args": inv_check.get("args", invoke_args),
                    "ok": bool(inv_check.get("ok")),
                    "at": ts,
                }
        _save_manifest(manifest)
        report["manifest_status"] = manifest.get("status")

    _trace_smoke(mslug, report)
    return report


def resmoke_mcp(
    mcp_slug: str,
    *,
    timeout_s: float = 15.0,
    require_invoke: bool = True,
    invoke_args: str = "--help",
) -> dict:
    """Re-run smoke checks; always updates smoke_report + last_smoke_at.

    Equivalent to ``smoke_mcp(..., force=True, skip_if_smoked=False)``.
    Default *require_invoke* True (v1 quality bar). Does not un-revoke;
    revoked MCPs still fail until re-wrapped.
    """
    return smoke_mcp(
        mcp_slug,
        timeout_s=timeout_s,
        require_invoke=require_invoke,
        invoke_args=invoke_args,
        skip_if_smoked=False,
        force=True,
    )


def revoke_mcp(
    mcp_slug: str,
    *,
    reason: str = "",
    update_registry: bool = True,
) -> dict:
    """Mark MCP status=revoked so list/smoke_graph treat it as not smoked.

    Detaches from registry use by setting registry status to draft/revoked
    when possible. Does not delete server files (audit-friendly).
    """
    mslug = mcp_slug_for(mcp_slug)
    d = mcp_dir(mslug)
    man = _load_manifest(mslug)
    ts = _iso()
    if man is None:
        # Minimal stub so revoke is durable even without prior wrap
        if not (d / "server.py").is_file() and not d.is_dir():
            return {
                "ok": False,
                "mcp_slug": mslug,
                "error": f"MCP not found under {d}",
                "ts": ts,
            }
        man = {
            "schema": SCHEMA,
            "mcp_slug": mslug,
            "wraps_capability": _capability_from_mcp_slug(mslug),
            "capability_slug": _capability_from_mcp_slug(mslug),
            "transport": TRANSPORT,
            "tools": list(TOOLS),
            "status": STATUS_REVOKED,
            "wrap_version": WRAP_VERSION,
            "created_at": ts,
        }
    else:
        man = dict(man)

    man["status"] = STATUS_REVOKED
    man["revoked_at"] = ts
    if reason:
        man["revoke_reason"] = reason
    man["last_smoke_ok"] = False
    if not man.get("capability_slug"):
        man["capability_slug"] = man.get("wraps_capability") or _capability_from_mcp_slug(
            mslug
        )
    # Drop oracle evidence so graph cannot pass invoke-oracle on a revoked block
    # if status check is skipped by an older client.
    _clear_sibling_reports(d, invoke=True, smoke=False)
    _save_manifest(man)

    registry_note = "registry_not_touched"
    if update_registry:
        try:
            from pipeline.capability_registry import _connect, _now  # type: ignore

            conn = _connect()
            conn.execute(
                """
                UPDATE capabilities
                SET status = 'draft', updated_at = ?
                WHERE slug = ? AND kind = 'mcp'
                """,
                (_now(), mslug),
            )
            conn.commit()
            conn.close()
            registry_note = "registry_demoted_draft"
            man["registry_note"] = registry_note
            _save_manifest(man)
        except Exception as exc:
            registry_note = f"registry_skip: {exc}"
            try:
                man["registry_note"] = registry_note
                _save_manifest(man)
            except Exception:
                pass

    result = {
        "ok": True,
        "mcp_slug": mslug,
        "status": STATUS_REVOKED,
        "revoked_at": ts,
        "reason": reason or None,
        "registry_note": registry_note,
        "is_mcp_smoked": is_mcp_smoked(mslug),
    }
    _trace_revoke(mslug, result)
    return result


def _trace_revoke(mcp_slug: str, result: dict[str, Any]) -> None:
    """Best-effort goal_trace for revoke (closed outcome=revoked)."""
    try:
        from pipeline.goal_trace import (
            OUTCOME_FAILED,
            OUTCOME_REVOKED,
            append_event,
            finalize_trace,
            start_trace,
        )

        wraps = _capability_from_mcp_slug(mcp_slug)
        tr = start_trace(
            f"MCP factory revoke for {mcp_slug} (wraps {wraps})",
            goal_id=f"mcp_revoke_{uuid.uuid4().hex[:10]}",
            mode="mcp_factory",
            plan=[{"step": 1, "intent": "revoke", "tool": "mcp.revoke"}],
        )
        append_event(
            tr,
            type="tool",
            tool="mcp.revoke",
            args={"mcp_slug": mcp_slug, "reason": result.get("reason")},
            result_snip=json.dumps(result, ensure_ascii=False)[:1500],
            ok=bool(result.get("ok")),
        )
        ok = bool(result.get("ok"))
        finalize_trace(
            tr,
            status="revoked" if ok else "goal_failed",
            outcome=OUTCOME_REVOKED if ok else OUTCOME_FAILED,
            oracle={
                "name": "mcp_revoke",
                "pass": ok,
                "evidence": f"revoked {mcp_slug}",
            },
            train_weight=0.5 if ok else 0.1,
            claim="mcp_smoke",
        )
        result["goal_trace_id"] = tr.get("goal_id")
    except Exception as exc:
        result["goal_trace_error"] = str(exc)


def _trace_smoke(mcp_slug: str, report: dict[str, Any]) -> None:
    """Best-effort goal_trace.v1 with mode=mcp_factory + closed outcomes.

    smoke_report.json remains the durable oracle for graph smoke; goal_trace
    mirrors the same ok/fail for learning hygiene (medium train_weight on pass).
    """
    try:
        from pipeline.goal_trace import (
            FAILURE_INVOKE,
            FAILURE_SMOKE,
            OUTCOME_FAILED,
            OUTCOME_PROVEN,
            append_event,
            finalize_trace,
            start_trace,
        )

        wraps = _capability_from_mcp_slug(mcp_slug)
        plan = [
            {"step": 1, "intent": "ping", "tool": "mcp.ping"},
            {"step": 2, "intent": "describe", "tool": "mcp.describe"},
        ]
        if any(c.get("method") == "invoke" for c in (report.get("checks") or [])):
            plan.append({"step": 3, "intent": "invoke", "tool": "mcp.invoke"})
        tr = start_trace(
            f"MCP factory smoke for {mcp_slug} (wraps {wraps})",
            goal_id=f"mcp_smoke_{uuid.uuid4().hex[:10]}",
            mode="mcp_factory",
            plan=plan,
        )
        for ch in report.get("checks") or []:
            append_event(
                tr,
                type="tool",
                tool=f"mcp.{ch.get('method', '?')}",
                args={"mcp_slug": mcp_slug},
                result_snip=json.dumps(ch, ensure_ascii=False)[:1500],
                ok=bool(ch.get("ok")),
            )
        ok = bool(report.get("ok"))
        status = "goal_proven" if ok else "goal_failed"
        fc = None
        if not ok:
            # Prefer invoke_fail when an invoke check failed
            for ch in report.get("checks") or []:
                if ch.get("method") == "invoke" and not ch.get("ok"):
                    fc = FAILURE_INVOKE
                    break
            if fc is None:
                fc = FAILURE_SMOKE
        finalize_trace(
            tr,
            status=status,
            outcome=OUTCOME_PROVEN if ok else OUTCOME_FAILED,
            failure_class=fc,
            oracle={
                "name": "mcp_smoke",
                "pass": ok,
                "evidence": report.get("error") or f"smoke ok for {mcp_slug}",
            },
            train_weight=1.0 if ok else 0.1,
            claim="mcp_smoke",
        )
        report["goal_trace_id"] = tr.get("goal_id")
    except Exception as exc:
        report["goal_trace_error"] = str(exc)


def register_mcp(manifest: dict) -> None:
    """Best-effort insert into capability registry as kind=mcp.

    Writes nothing extra if registry is unavailable; never raises on API
    mismatch — records a note on the manifest when possible.
    """
    if not isinstance(manifest, dict):
        return
    mslug = str(manifest.get("mcp_slug") or "").strip()
    wraps = str(manifest.get("wraps_capability") or _capability_from_mcp_slug(mslug))
    if not mslug:
        return

    server_path = str(manifest.get("server_path") or f"mcps/{mslug}/server.py")
    status = str(manifest.get("status") or "draft")
    # Map factory statuses onto registry statuses
    reg_status = "verified" if status in ("smoked", "verified") else "draft"
    purpose = f"stdio JSONL MCP wrapper for capability {wraps}"
    entry = f"python {server_path}"
    note = "registry_skipped"

    try:
        from pipeline.capability_registry import registry_db

        # Ensure parent dir + schema via _connect if available
        try:
            from pipeline.capability_registry import _connect, _now  # type: ignore

            conn = _connect()
            conn.execute(
                """
                INSERT INTO capabilities (
                    slug, title, kind, status, purpose, domains, entrypoint, import_path,
                    cwd_template, requires, example_invoke, source_project,
                    phase, total_phases, updated_at
                ) VALUES (?, ?, 'mcp', ?, ?, '["mcp"]', ?, '', ?, '[]', ?, ?, 0, 0, ?)
                ON CONFLICT(slug) DO UPDATE SET
                    title=excluded.title,
                    kind='mcp',
                    status=excluded.status,
                    purpose=excluded.purpose,
                    entrypoint=excluded.entrypoint,
                    cwd_template=excluded.cwd_template,
                    example_invoke=excluded.example_invoke,
                    source_project=excluded.source_project,
                    updated_at=excluded.updated_at
                """,
                (
                    mslug,
                    f"MCP: {wraps}",
                    reg_status,
                    purpose,
                    entry,
                    f"mcps/{mslug}",
                    f'echo \'{{"method":"ping"}}\' | python {server_path}',
                    wraps,
                    _now(),
                ),
            )
            conn.commit()
            conn.close()
            note = "registry_ok"
        except Exception as exc:
            # Fallback: raw sqlite if helpers differ
            try:
                import sqlite3

                db = registry_db()
                db.parent.mkdir(parents=True, exist_ok=True)
                conn = sqlite3.connect(db)
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS capabilities (
                        slug TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        kind TEXT NOT NULL,
                        status TEXT NOT NULL,
                        purpose TEXT DEFAULT '',
                        domains TEXT DEFAULT '[]',
                        entrypoint TEXT DEFAULT '',
                        import_path TEXT DEFAULT '',
                        cwd_template TEXT DEFAULT '',
                        requires TEXT DEFAULT '[]',
                        example_invoke TEXT DEFAULT '',
                        source_project TEXT DEFAULT '',
                        phase INTEGER DEFAULT 0,
                        total_phases INTEGER DEFAULT 0,
                        updated_at TEXT NOT NULL
                    )
                    """
                )
                conn.execute(
                    """
                    INSERT INTO capabilities (
                        slug, title, kind, status, purpose, domains, entrypoint,
                        import_path, cwd_template, requires, example_invoke,
                        source_project, phase, total_phases, updated_at
                    ) VALUES (?, ?, 'mcp', ?, ?, '["mcp"]', ?, '', ?, '[]', ?, ?, 0, 0, ?)
                    ON CONFLICT(slug) DO UPDATE SET
                        status=excluded.status, purpose=excluded.purpose,
                        entrypoint=excluded.entrypoint, updated_at=excluded.updated_at
                    """,
                    (
                        mslug,
                        f"MCP: {wraps}",
                        reg_status,
                        purpose,
                        entry,
                        f"mcps/{mslug}",
                        f'echo \'{{"method":"ping"}}\' | python {server_path}',
                        wraps,
                        _iso(),
                    ),
                )
                conn.commit()
                conn.close()
                note = "registry_ok_raw"
            except Exception as exc2:
                note = f"registry_skip: {exc}; {exc2}"
    except Exception as exc:
        note = f"registry_skip: {exc}"

    # Annotate manifest (best-effort, non-fatal)
    try:
        manifest["registry_note"] = note
        if mslug:
            live = _load_manifest(mslug) or dict(manifest)
            live["registry_note"] = note
            _save_manifest(live)
    except Exception:
        pass


def list_mcps() -> list[dict]:
    """List mcp_manifest.v1 dicts under mcps/ (sorted by mcp_slug)."""
    root = mcps_dir()
    if not root.is_dir():
        return []
    out: list[dict] = []
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        man = child / "manifest.json"
        if not man.is_file():
            continue
        try:
            data = json.loads(man.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if isinstance(data, dict):
            out.append(data)
    out.sort(key=lambda m: str(m.get("mcp_slug") or ""))
    return out


def drain_queue(
    *,
    limit: int = 1,
    require_invoke: bool = True,
    invoke_args: str = "--help",
    skip_if_smoked: bool = True,
) -> list[dict]:
    """For each pending mcp_factory job (up to *limit*): wrap + smoke + mark_done.

    Skips re-work when MCP already smoked (*skip_if_smoked*). By default runs
    invoke oracle with ``--help`` (*require_invoke*).

    Returns a list of result dicts (one per job processed).
    """
    from pipeline.mcp_queue import list_pending, load_job, mark_done

    results: list[dict] = []
    pending = list_pending()[: max(0, int(limit))]
    for job_path in pending:
        try:
            job = load_job(job_path)
        except Exception as exc:
            results.append({"ok": False, "error": f"load_job: {exc}", "job_path": str(job_path)})
            try:
                mark_done(job_path, {"ok": False, "error": str(exc)})
            except Exception:
                pass
            continue

        cap = str(job.get("capability_slug") or "").strip()
        job_id = job.get("job_id")
        if not cap:
            res = {"ok": False, "error": "missing capability_slug", "job_id": job_id}
            mark_done(job_path, res)
            results.append(res)
            continue

        try:
            mslug = mcp_slug_for(cap)
            if skip_if_smoked and is_mcp_smoked(mslug):
                man = _load_manifest(mslug) or {"mcp_slug": mslug, "status": "smoked"}
                res = {
                    "ok": True,
                    "skipped": True,
                    "skip_reason": "already_smoked",
                    "job_id": job_id,
                    "capability_slug": cap,
                    "mcp_slug": mslug,
                    "manifest": man,
                }
                mark_done(job_path, res)
                results.append(res)
                continue

            manifest = wrap_capability_as_mcp(cap)
            mslug = str(manifest.get("mcp_slug") or mslug)
            smoke = smoke_mcp(
                mslug,
                require_invoke=require_invoke,
                invoke_args=invoke_args,
                skip_if_smoked=False,
            )
            try:
                register_mcp(
                    manifest
                    if smoke.get("ok")
                    else {**manifest, "status": manifest.get("status", "draft")}
                )
            except Exception as reg_exc:
                smoke = dict(smoke)
                smoke["register_error"] = str(reg_exc)
            res = {
                "ok": bool(smoke.get("ok")),
                "job_id": job_id,
                "capability_slug": cap,
                "mcp_slug": mslug,
                "manifest": manifest,
                "smoke": smoke,
            }
            mark_done(job_path, res)
            results.append(res)
        except Exception as exc:
            res = {
                "ok": False,
                "job_id": job_id,
                "capability_slug": cap,
                "error": str(exc),
            }
            try:
                mark_done(job_path, res)
            except Exception:
                pass
            results.append(res)
    return results
