"""
graph.v1 — tiny goal plan graph store (map, not mind).

Compile a goal + router hits into a versioned node/edge graph, critique it
(missing nodes / missing oracles), and persist under PIPELINE_DIR/graphs/.

No LLM in compile v1. Factories are triggered by missing nodes later (T5).
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

from pipeline.paths import graphs_dir

GRAPH_SCHEMA = "graph.v1"

NODE_KINDS = frozenset(
    {
        "software",
        "connector",
        "skill",
        "mcp",
        "external_mcp",
        "human",
        "research",
    }
)

# Kinds that need a named oracle for critique to pass.
EXECUTABLE_KINDS = frozenset({"software", "connector", "mcp", "skill"})

DEFAULT_ORACLE = "capability_invoke_help"
MCP_ORACLE = "mcp_invoke_help"

# Map registry / router hit kinds onto the closed lego enum.
_KIND_MAP = {
    "project": "software",
    "software": "software",
    "shared_lib": "software",
    "workflow": "connector",
    "connector": "connector",
    "skill": "skill",
    "mcp": "mcp",
    "external_mcp": "external_mcp",
    "human": "human",
    "research": "research",
    "hermes_task": "research",
}

__all__ = [
    "GRAPH_SCHEMA",
    "DEFAULT_ORACLE",
    "MCP_ORACLE",
    "EXECUTABLE_KINDS",
    "compile_goal_graph",
    "critique_graph",
    "smoke_graph",
    "save_graph",
    "load_graph",
    "graph_path",
    "plan_factory_actions",
    "compile_graph_from_smoked_mcps",
]


def _iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_kind(raw: Any) -> str:
    k = str(raw or "").strip().lower()
    if k in NODE_KINDS:
        return k
    return _KIND_MAP.get(k, "software")


def _node_status_from_hit(hit: dict[str, Any]) -> str:
    """verified if hit says verified/requires_ok; missing if explicit; else draft/unknown."""
    raw = hit.get("status")
    if raw is not None and str(raw).strip():
        s = str(raw).strip().lower()
        if s in ("verified", "missing", "draft", "unknown"):
            return s
        if s in ("requires_ok", "ok", "field_proven", "complete"):
            return "verified"
    if hit.get("requires_ok") is True:
        return "verified"
    if hit.get("requires_ok") is False:
        return "draft"
    if hit.get("missing") is True:
        return "missing"
    return "unknown"


def _oracle_for_kind(kind: str, hit: dict[str, Any] | None = None) -> str:
    if hit:
        o = hit.get("oracle")
        if isinstance(o, dict) and o.get("name"):
            return str(o["name"])
        if isinstance(o, str) and o.strip():
            return o.strip()
    if kind == "mcp":
        return MCP_ORACLE
    if kind in EXECUTABLE_KINDS:
        return DEFAULT_ORACLE
    return ""


def _slug_tokens_from_text(text: str) -> set[str]:
    mentioned: set[str] = set()
    for m in re.finditer(r"\b([a-z][a-z0-9_]{2,})\b", (text or "").lower()):
        mentioned.add(m.group(1))
    return mentioned


def _smoked_mcp_nodes_for_goal(
    goal_text: str,
    *,
    already: set[str],
    mentioned: set[str],
    remaining: int,
) -> list[dict[str, Any]]:
    """Include smoked MCPs whose slug or wraps_capability appears in goal text."""
    if remaining <= 0:
        return []
    try:
        from pipeline.mcp_factory import list_mcps
    except Exception:
        return []
    out: list[dict[str, Any]] = []
    try:
        rows = list_mcps()
    except Exception:
        return []
    text_l = (goal_text or "").lower()
    for man in rows:
        if remaining <= 0:
            break
        if not isinstance(man, dict):
            continue
        if str(man.get("status") or "") not in ("smoked", "verified"):
            continue
        mslug = str(man.get("mcp_slug") or "").strip()
        wraps = str(man.get("wraps_capability") or "").strip()
        if not mslug or mslug in already:
            continue
        # Match mcp_foo, foo, or explicit mention
        if (
            mslug.lower() in mentioned
            or wraps.lower() in mentioned
            or mslug.lower() in text_l
            or (wraps and wraps.lower() in text_l)
            or f"mcp_{wraps}".lower() in text_l
        ):
            out.append(
                {
                    "slug": mslug,
                    "kind": "mcp",
                    "label": wraps or mslug,
                    "status": "verified",
                    "oracle": MCP_ORACLE,
                    "requires": [wraps] if wraps else [],
                }
            )
            already.add(mslug)
            remaining -= 1
    return out


def compile_graph_from_smoked_mcps(
    *,
    goal_id: str,
    goal_text: str = "",
    mcp_slugs: list[str] | None = None,
    max_nodes: int = 10,
) -> dict[str, Any]:
    """Build graph.v1 from already-smoked MCPs under PIPELINE_DIR/mcps/.

    If *mcp_slugs* is set, only those (must be smoked). Else all smoked MCPs
    up to *max_nodes*. Primary use: fixture for map-blocks workflow tests.
    """
    from pipeline.mcp_factory import is_mcp_smoked, list_mcps, mcp_slug_for

    max_nodes = max(0, int(max_nodes))
    rows = list_mcps()
    wanted: set[str] | None = None
    if mcp_slugs is not None:
        wanted = {mcp_slug_for(s) for s in mcp_slugs if str(s).strip()}

    hits: list[dict[str, Any]] = []
    for man in rows:
        if not isinstance(man, dict):
            continue
        mslug = str(man.get("mcp_slug") or "").strip()
        if not mslug:
            continue
        if wanted is not None and mslug not in wanted:
            continue
        if str(man.get("status") or "") not in ("smoked", "verified"):
            if wanted is not None and mslug in wanted and not is_mcp_smoked(mslug):
                # explicit request but not ready — still add as missing for plan-factories
                hits.append(
                    {
                        "slug": mslug,
                        "kind": "mcp",
                        "status": "missing",
                        "label": man.get("wraps_capability") or mslug,
                        "oracle": {"name": MCP_ORACLE},
                        "requires": [man.get("wraps_capability")]
                        if man.get("wraps_capability")
                        else [],
                    }
                )
            continue
        hits.append(
            {
                "slug": mslug,
                "kind": "mcp",
                "status": "verified",
                "title": man.get("wraps_capability") or mslug,
                "oracle": {"name": MCP_ORACLE},
                "requires": [man.get("wraps_capability")]
                if man.get("wraps_capability")
                else [],
            }
        )
        if len(hits) >= max_nodes:
            break

    text = goal_text or (
        "Utility MCP workflow fixture: "
        + ", ".join(h["slug"] for h in hits[:max_nodes])
    )
    g = compile_goal_graph(text, goal_id=goal_id, route_hits=hits, max_nodes=max_nodes)
    g["source"] = "smoked_mcps"
    return g


def _connector_nodes_for_goal(
    goal_text: str,
    *,
    already: set[str],
    mentioned: set[str],
    remaining: int,
) -> list[dict[str, Any]]:
    """Best-effort: connectors whose requires match goal text / known slugs."""
    if remaining <= 0:
        return []
    try:
        from pipeline.goal_policy import _list_connector_slugs
    except Exception:
        return []

    out: list[dict[str, Any]] = []
    try:
        pairs = _list_connector_slugs()
    except Exception:
        return []

    for cslug, creq in pairs:
        if remaining <= 0:
            break
        if not cslug or cslug in already:
            continue
        if not creq:
            # only include empty-requires connectors if explicitly mentioned
            if cslug not in mentioned and cslug.replace("-", "_") not in mentioned:
                continue
        else:
            if not all(
                r in mentioned
                or r.replace("-", "_") in mentioned
                or r.replace("_", "-") in mentioned
                for r in creq
            ):
                continue
        out.append(
            {
                "slug": cslug,
                "kind": "connector",
                "label": cslug,
                "status": "draft",
                "oracle": DEFAULT_ORACLE,
                "requires": list(creq or []),
            }
        )
        already.add(cslug)
        remaining -= 1
    return out


def _make_node(
    *,
    index: int,
    slug: str,
    kind: str,
    label: str,
    status: str,
    oracle: str,
    requires: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": f"n{index}",
        "kind": kind,
        "slug": slug,
        "label": label or slug,
        "status": status,
        "oracle": oracle,
        "requires": list(requires or []),
    }


def compile_goal_graph(
    goal_text: str,
    *,
    goal_id: str,
    route_hits: list[dict[str, Any]] | None = None,
    max_nodes: int = 10,
) -> dict[str, Any]:
    """Build a graph.v1 dict from goal text + router hits (no LLM).

    Nodes come from route_hits first, then matching connectors (best-effort).
    Edges are linear control edges in node order. Caps at max_nodes (default 10).
    """
    max_nodes = max(0, int(max_nodes))
    hits = list(route_hits or [])
    now = _iso()
    nodes: list[dict[str, Any]] = []
    seen: set[str] = set()
    mentioned = _slug_tokens_from_text(goal_text)

    for hit in hits:
        if len(nodes) >= max_nodes:
            break
        if not isinstance(hit, dict):
            continue
        slug = str(hit.get("slug") or "").strip()
        if not slug or slug in seen:
            continue
        kind = _normalize_kind(hit.get("kind"))
        status = _node_status_from_hit(hit)
        oracle = _oracle_for_kind(kind, hit)
        label = str(hit.get("title") or hit.get("label") or slug)
        req = hit.get("requires") or hit.get("missing_requires") or []
        if not isinstance(req, list):
            req = []
        nodes.append(
            _make_node(
                index=len(nodes) + 1,
                slug=slug,
                kind=kind,
                label=label,
                status=status,
                oracle=oracle,
                requires=[str(r) for r in req],
            )
        )
        seen.add(slug)
        mentioned.add(slug)
        mentioned.add(slug.replace("-", "_"))

    # Smoked MCPs under PIPELINE_DIR/mcps mentioned in text (or all if include_smoked_mcps)
    remaining = max_nodes - len(nodes)
    if remaining > 0:
        for raw in _smoked_mcp_nodes_for_goal(
            goal_text,
            already=seen,
            mentioned=mentioned,
            remaining=remaining,
        ):
            nodes.append(
                _make_node(
                    index=len(nodes) + 1,
                    slug=raw["slug"],
                    kind="mcp",
                    label=raw["label"],
                    status=raw["status"],
                    oracle=raw["oracle"],
                    requires=raw.get("requires"),
                )
            )
            seen.add(raw["slug"])

    remaining = max_nodes - len(nodes)
    if remaining > 0:
        for raw in _connector_nodes_for_goal(
            goal_text,
            already=seen,
            mentioned=mentioned,
            remaining=remaining,
        ):
            nodes.append(
                _make_node(
                    index=len(nodes) + 1,
                    slug=raw["slug"],
                    kind=raw["kind"],
                    label=raw["label"],
                    status=raw["status"],
                    oracle=raw["oracle"],
                    requires=raw.get("requires"),
                )
            )

    edges: list[dict[str, Any]] = []
    for i in range(len(nodes) - 1):
        edges.append(
            {
                "from": nodes[i]["id"],
                "to": nodes[i + 1]["id"],
                "kind": "control",
            }
        )

    graph: dict[str, Any] = {
        "schema": GRAPH_SCHEMA,
        "goal_id": str(goal_id),
        "goal_text": goal_text or "",
        "created_at": now,
        "updated_at": now,
        "status": "draft",
        "nodes": nodes,
        "edges": edges,
        "critique": {"ok": True, "issues": []},
    }

    critique = critique_graph(graph)
    graph["critique"] = critique
    graph["updated_at"] = _iso()
    if not critique.get("ok"):
        graph["status"] = "blocked"
    elif nodes and all(n.get("status") == "verified" for n in nodes):
        graph["status"] = "executable"
    else:
        graph["status"] = "critiqued"

    return graph


def critique_graph(graph: dict[str, Any]) -> dict[str, Any]:
    """QC a graph.v1 dict: missing nodes and missing oracle names on executables.

    Returns {"ok": bool, "issues": [str, ...]}. Does not mutate graph unless
    caller assigns the result back to graph["critique"].
    """
    issues: list[str] = []
    nodes = graph.get("nodes") if isinstance(graph, dict) else None
    if not isinstance(nodes, list):
        return {"ok": False, "issues": ["graph has no nodes list"]}

    for node in nodes:
        if not isinstance(node, dict):
            issues.append("invalid node entry")
            continue
        nid = node.get("id") or node.get("slug") or "?"
        status = str(node.get("status") or "").lower()
        kind = str(node.get("kind") or "").lower()
        slug = node.get("slug") or nid

        if status == "missing":
            issues.append(f"node {nid} ({slug}) status=missing")

        if kind in EXECUTABLE_KINDS:
            oracle = node.get("oracle")
            name = ""
            if isinstance(oracle, dict):
                name = str(oracle.get("name") or "").strip()
            elif isinstance(oracle, str):
                name = oracle.strip()
            if not name:
                issues.append(
                    f"node {nid} ({slug}) kind={kind} lacks oracle name"
                )

    ok = len(issues) == 0
    return {"ok": ok, "issues": issues}


def _safe_node_slug(slug: str) -> str | None:
    """Reject path traversal / absolute / reserved slugs before joining under PIPELINE_DIR.

    Returns cleaned slug or None if unsafe (separators, ``.`` / ``..``, drive letters).
    A software slug must be a single child name under projects/, not base itself.
    """
    s = (slug or "").strip()
    if not s:
        return None
    # "." / ".." / pure-dot names resolve to base or parent — not a child project
    if s in (".", "..") or s.strip(".") == "":
        return None
    # Absolute / drive / UNC / parent / separator — never join into base dirs
    if (
        ".." in s
        or "/" in s
        or "\\" in s
        or ":" in s
        or s.startswith(("~",))
        or "\x00" in s
    ):
        return None
    return s


def _path_under(base: Any, *parts: str) -> Any | None:
    """Join *parts under *base*; return path only if resolve stays under base."""
    from pathlib import Path

    try:
        root = Path(base).resolve()
        candidate = root.joinpath(*parts).resolve()
        candidate.relative_to(root)
        return candidate
    except (OSError, ValueError, RuntimeError):
        return None


def _registry_capability_row(slug: str) -> dict[str, Any] | None:
    """Public-path registry lookup by slug (no private capability_tools API)."""
    import sqlite3

    from pipeline.paths import registry_db

    db = registry_db()
    if not db.exists():
        return None
    try:
        conn = sqlite3.connect(db)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT slug, title, kind, status, purpose, entrypoint "
            "FROM capabilities WHERE slug = ?",
            (slug,),
        ).fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception:
        return None


def _smoke_software_node(slug: str, node: dict[str, Any]) -> dict[str, Any]:
    """Cheap software check: project state and/or registry row — no field tests."""
    from pipeline.paths import projects_dir

    safe = _safe_node_slug(slug)
    if safe is None:
        return {
            "ok": False,
            "detail": "unsafe_slug",
            "check": "slug_safety",
        }

    detail_parts: list[str] = []
    # Live project under PIPELINE_DIR/projects/ — require state/current_idea.json
    try:
        pdir = _path_under(projects_dir(), safe)
        if pdir is None:
            detail_parts.append("project_path_escape")
        else:
            state_f = pdir / "state" / "current_idea.json"
            if state_f.is_file():
                try:
                    st = json.loads(state_f.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    st = {}
                if isinstance(st, dict):
                    st_status = str(st.get("status") or "")
                    detail_parts.append(f"project_status={st_status or 'present'}")
                    # Any present project with state is enough for cheap smoke
                    return {
                        "ok": True,
                        "detail": "project:" + ",".join(detail_parts),
                        "check": "project_state",
                    }
            elif pdir.is_dir():
                # Empty dir or dir without state is NOT a pass (map honesty)
                detail_parts.append("project_dir_no_state")
    except Exception as exc:
        detail_parts.append(f"project_err={exc}")

    # Capability registry (verified + entrypoint preferred) via public DB path
    try:
        row = _registry_capability_row(safe)
        if row:
            rstatus = str(row.get("status") or "")
            entry = str(row.get("entrypoint") or "").strip()
            detail_parts.append(f"registry_status={rstatus}")
            if entry:
                detail_parts.append("has_entrypoint")
            if rstatus in ("verified", "field_proven", "complete") or entry:
                return {
                    "ok": True,
                    "detail": "registry:" + ",".join(detail_parts),
                    "check": "registry",
                }
            return {
                "ok": False,
                "detail": "registry_not_ready:" + ",".join(detail_parts),
                "check": "registry",
            }
    except Exception as exc:
        detail_parts.append(f"registry_err={exc}")

    # Node already marked verified without local asset → soft fail (honest map)
    nstatus = str(node.get("status") or "").lower()
    if nstatus == "verified":
        return {
            "ok": False,
            "detail": "verified_but_no_project_or_registry:"
            + (",".join(detail_parts) if detail_parts else "empty"),
            "check": "presence",
        }
    return {
        "ok": False,
        "detail": "software_not_found:"
        + (",".join(detail_parts) if detail_parts else "empty"),
        "check": "presence",
    }


def _smoke_connector_node(slug: str) -> dict[str, Any]:
    """Cheap connector check: YAML exists under workflows/connectors/."""
    from pipeline.paths import connectors_dir

    safe = _safe_node_slug(slug)
    if safe is None:
        return {
            "ok": False,
            "detail": "unsafe_slug",
            "check": "slug_safety",
        }

    root = connectors_dir()
    for name in (f"{safe}.yaml", f"{safe}.yml"):
        path = _path_under(root, name)
        if path is not None and path.is_file():
            return {
                "ok": True,
                "detail": f"connector_yaml={path.name}",
                "check": "connector_yaml",
                "path": str(path),
            }
    return {
        "ok": False,
        "detail": f"connector_yaml_missing under {root}",
        "check": "connector_yaml",
    }


def _smoke_mcp_node(slug: str) -> dict[str, Any]:
    """Cheap MCP check: is_mcp_smoked (manifest + server.py); no re-spawn."""
    safe = _safe_node_slug(slug)
    if safe is None:
        return {
            "ok": False,
            "detail": "unsafe_slug",
            "check": "slug_safety",
        }
    try:
        from pipeline.mcp_factory import is_mcp_smoked, mcp_slug_for

        mslug = mcp_slug_for(safe)
        # Re-validate after normalize (mcp_ prefix only; still no path junk)
        if _safe_node_slug(mslug) is None:
            return {
                "ok": False,
                "detail": "unsafe_mcp_slug",
                "check": "slug_safety",
                "mcp_slug": mslug,
            }
        ok = is_mcp_smoked(mslug)
        return {
            "ok": bool(ok),
            "detail": "mcp_smoked" if ok else "mcp_not_smoked",
            "check": "is_mcp_smoked",
            "mcp_slug": mslug,
        }
    except Exception as exc:
        return {
            "ok": False,
            "detail": f"mcp_check_error={exc}",
            "check": "is_mcp_smoked",
        }


def _smoke_skill_node(slug: str) -> dict[str, Any]:
    """Cheap skill check: SKILL.md via skill_load, or verified block_registry row."""
    safe = _safe_node_slug(slug)
    if safe is None:
        return {
            "ok": False,
            "detail": "unsafe_slug",
            "check": "slug_safety",
        }

    skill_load_err = ""
    # 1) filesystem skill
    try:
        from pipeline.skill_load import find_skill_dir

        d = find_skill_dir(safe)
        if d is not None and (d / "SKILL.md").is_file():
            return {
                "ok": True,
                "detail": f"skill_dir={d.name}",
                "check": "skill_load",
                "path": str(d / "SKILL.md"),
            }
    except (OSError, ImportError) as exc:
        skill_load_err = f"skill_load_err={exc}"
    except Exception as exc:
        skill_load_err = f"skill_load_err={exc}"

    # 2) block registry by id or name
    try:
        from pipeline.block_registry import get_block, list_blocks

        rec = get_block(safe)
        if rec is None:
            # try common id forms / name match
            for b in list_blocks(kind="skill"):
                bid = str(b.get("id") or "")
                name = str(b.get("name") or "").lower().replace("_", "-")
                slug_n = safe.lower().replace("_", "-")
                if bid == safe or name == slug_n or bid.endswith(f"-{slug_n}"):
                    rec = b
                    break
        if rec and isinstance(rec, dict):
            st = str(rec.get("status") or "")
            if st in ("verified", "sandboxed"):
                return {
                    "ok": True,
                    "detail": f"block_registry status={st} id={rec.get('id')}",
                    "check": "block_registry",
                    "block_id": rec.get("id"),
                }
            detail = f"block_not_promoted status={st}"
            if skill_load_err:
                detail = f"{detail};{skill_load_err}"
            return {
                "ok": False,
                "detail": detail,
                "check": "block_registry",
            }
    except Exception as exc:
        detail = f"skill_check_error={exc}"
        if skill_load_err:
            detail = f"{detail};{skill_load_err}"
        return {
            "ok": False,
            "detail": detail,
            "check": "skill",
        }

    detail = "skill_not_found (no SKILL.md and no block)"
    if skill_load_err:
        detail = f"{detail};{skill_load_err}"
    return {
        "ok": False,
        "detail": detail,
        "check": "skill",
    }


def smoke_node(node: dict[str, Any]) -> dict[str, Any]:
    """Cheap per-node smoke for one graph node. No LLM, no long field tests."""
    if not isinstance(node, dict):
        return {
            "ok": False,
            "id": "?",
            "slug": "?",
            "kind": "?",
            "detail": "invalid node entry",
            "skipped": False,
        }
    nid = str(node.get("id") or node.get("slug") or "?")
    slug = str(node.get("slug") or nid).strip()
    kind = str(node.get("kind") or "").strip().lower()
    base = {
        "id": nid,
        "slug": slug,
        "kind": kind,
        "node_status": str(node.get("status") or ""),
    }

    if kind not in EXECUTABLE_KINDS:
        return {
            **base,
            "ok": True,
            "skipped": True,
            "detail": f"non-executable kind={kind or 'empty'}",
            "check": "skip",
        }

    if kind == "mcp":
        r = _smoke_mcp_node(slug)
    elif kind == "software":
        r = _smoke_software_node(slug, node)
    elif kind == "connector":
        r = _smoke_connector_node(slug)
    elif kind == "skill":
        r = _smoke_skill_node(slug)
    else:
        r = {"ok": False, "detail": f"unhandled kind={kind}", "check": "unknown"}

    return {
        **base,
        "ok": bool(r.get("ok")),
        "skipped": False,
        "detail": str(r.get("detail") or ""),
        "check": r.get("check"),
        **{k: v for k, v in r.items() if k not in ("ok", "detail", "check")},
    }


def smoke_graph(
    graph: dict[str, Any],
    *,
    mutate: bool = True,
    re_critique: bool = True,
) -> dict[str, Any]:
    """Whole-graph cheap smoke after nodes are resolved (P3).

    Precondition: critique ok (re-runs critique by default); no status=missing
    nodes. Per executable node (software|connector|mcp|skill): cheap presence /
    prior-smoke checks only — no LLM, no long field tests, no MCP re-spawn.

    Returns::

        {
          "ok": bool,           # overall (preconditions + all node smokes)
          "smoke_pass": bool,   # same as ok for callers that key on smoke_pass
          "blocked": bool,      # precondition failed (critique / missing)
          "node_results": [...],
          "issues": [str, ...],
          "ts": iso,
        }

    When *mutate* is True (default), sets graph fields:
      smoke_pass, smoked_at, smoke_report (summary), status smoke_pass|smoke_failed
      (or leaves prior status when blocked by critique before executable path).
    """
    ts = _iso()
    issues: list[str] = []
    node_results: list[dict[str, Any]] = []

    if not isinstance(graph, dict):
        report = {
            "ok": False,
            "smoke_pass": False,
            "blocked": True,
            "node_results": [],
            "issues": ["graph is not a dict"],
            "ts": ts,
        }
        return report

    # --- preconditions ---
    if re_critique:
        crit = critique_graph(graph)
        if mutate:
            graph["critique"] = crit
    else:
        crit = graph.get("critique") if isinstance(graph.get("critique"), dict) else None
        if crit is None:
            crit = critique_graph(graph)
            if mutate:
                graph["critique"] = crit

    if not crit.get("ok"):
        issues.extend(list(crit.get("issues") or []) or ["critique not ok"])
        issues.append("smoke blocked: critique failed")
        report = {
            "ok": False,
            "smoke_pass": False,
            "blocked": True,
            "node_results": [],
            "issues": issues,
            "ts": ts,
            "block_reason": "critique",
        }
        if mutate:
            graph["smoke_pass"] = False
            graph["smoked_at"] = ts
            graph["smoke_report"] = {
                "ok": False,
                "blocked": True,
                "issues": issues,
                "ts": ts,
            }
            # Keep blocked/critiqued status if already non-executable; else mark smoke_failed
            cur = str(graph.get("status") or "")
            if cur not in ("blocked", "draft"):
                graph["status"] = "smoke_failed"
            graph["updated_at"] = ts
        return report

    nodes = graph.get("nodes")
    if not isinstance(nodes, list):
        issues.append("graph has no nodes list")
        report = {
            "ok": False,
            "smoke_pass": False,
            "blocked": True,
            "node_results": [],
            "issues": issues,
            "ts": ts,
            "block_reason": "no_nodes",
        }
        if mutate:
            graph["smoke_pass"] = False
            graph["smoked_at"] = ts
            graph["status"] = "smoke_failed"
            graph["smoke_report"] = report
            graph["updated_at"] = ts
        return report

    missing_nodes = [
        n
        for n in nodes
        if isinstance(n, dict) and str(n.get("status") or "").lower() == "missing"
    ]
    if missing_nodes:
        for n in missing_nodes:
            nid = n.get("id") or n.get("slug") or "?"
            slug = n.get("slug") or nid
            issues.append(f"node {nid} ({slug}) status=missing — resolve before smoke")
        report = {
            "ok": False,
            "smoke_pass": False,
            "blocked": True,
            "node_results": [],
            "issues": issues,
            "ts": ts,
            "block_reason": "missing_nodes",
        }
        if mutate:
            graph["smoke_pass"] = False
            graph["smoked_at"] = ts
            graph["status"] = "smoke_failed"
            graph["smoke_report"] = {
                "ok": False,
                "blocked": True,
                "issues": issues,
                "ts": ts,
            }
            graph["updated_at"] = ts
        return report

    # --- per-node cheap smoke ---
    for node in nodes:
        result = smoke_node(node if isinstance(node, dict) else {})
        node_results.append(result)
        if not result.get("ok") and not result.get("skipped"):
            issues.append(
                f"node {result.get('id')} ({result.get('slug')}) "
                f"kind={result.get('kind')}: {result.get('detail')}"
            )

    all_ok = all(r.get("ok") for r in node_results) if node_results else True
    # Empty graph with critique ok: smoke_pass True (nothing executable to fail)
    smoke_pass = bool(all_ok) and not issues
    report = {
        "ok": smoke_pass,
        "smoke_pass": smoke_pass,
        "blocked": False,
        "node_results": node_results,
        "issues": issues,
        "ts": ts,
    }

    if mutate:
        graph["smoke_pass"] = smoke_pass
        graph["smoked_at"] = ts
        graph["smoke_report"] = {
            "ok": smoke_pass,
            "blocked": False,
            "issues": list(issues),
            "node_count": len(node_results),
            "failed": [
                r.get("slug") for r in node_results if not r.get("ok") and not r.get("skipped")
            ],
            "ts": ts,
        }
        graph["status"] = "smoke_pass" if smoke_pass else "smoke_failed"
        graph["updated_at"] = ts

    return report


def graph_path(goal_id: str) -> Any:
    """Path for a goal graph JSON (does not create directories)."""
    from pathlib import Path

    return graphs_dir() / f"{goal_id}.json"


def save_graph(graph: dict[str, Any]) -> Any:
    """Write graph to graphs_dir()/{goal_id}.json. Returns path."""
    from pathlib import Path

    gid = str(graph.get("goal_id") or "unknown")
    graph = dict(graph)
    graph["updated_at"] = _iso()
    d = graphs_dir()
    d.mkdir(parents=True, exist_ok=True)
    path: Path = d / f"{gid}.json"
    path.write_text(json.dumps(graph, indent=2), encoding="utf-8")
    return path


def load_graph(goal_id: str) -> dict[str, Any] | None:
    """Load graph for goal_id, or None if missing/invalid."""
    path = graphs_dir() / f"{goal_id}.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    return data


def _base_slug_for_mcp(node_slug: str) -> str:
    """Strip mcp_ prefix from node slug if present (MCP factory wraps capability slug)."""
    s = (node_slug or "").strip()
    if s.startswith("mcp_"):
        return s[4:] or s
    return s


def plan_factory_actions(graph: dict[str, Any]) -> dict[str, Any]:
    """After critique: enqueue MCP wraps for missing mcp nodes; handoff software gaps.

    For each node kind==mcp and status==missing: enqueue_wrap(base_slug) where
    base_slug strips a leading ``mcp_`` prefix from node.slug when present.

    For software nodes with status==missing: append to metrics/goal_build_handoffs.jsonl
    only (no software factory seed).

    Returns ``{enqueued: [paths], software_handoffs: [...], issues: [...]}``.
    """
    from pipeline.paths import get_pipeline_dir

    enqueued: list[str] = []
    software_handoffs: list[dict[str, Any]] = []
    issues: list[str] = []

    if not isinstance(graph, dict):
        return {
            "enqueued": enqueued,
            "software_handoffs": software_handoffs,
            "issues": ["graph is not a dict"],
        }

    goal_id = str(graph.get("goal_id") or "") or None
    goal_text = str(graph.get("goal_text") or "")
    nodes = graph.get("nodes")
    if not isinstance(nodes, list):
        return {
            "enqueued": enqueued,
            "software_handoffs": software_handoffs,
            "issues": ["graph has no nodes list"],
        }

    for node in nodes:
        if not isinstance(node, dict):
            issues.append("invalid node entry")
            continue
        kind = str(node.get("kind") or "").strip().lower()
        status = str(node.get("status") or "").strip().lower()
        slug = str(node.get("slug") or "").strip()
        nid = node.get("id") or slug or "?"

        if status != "missing":
            continue

        if kind == "mcp":
            if not slug:
                issues.append(f"node {nid}: mcp missing but no slug")
                continue
            base_slug = _base_slug_for_mcp(slug)
            if not base_slug:
                issues.append(f"node {nid}: empty base_slug after strip")
                continue
            try:
                from pipeline.mcp_queue import enqueue_wrap

                path = enqueue_wrap(
                    base_slug,
                    goal_id=goal_id,
                    reason=f"graph missing mcp node {nid} ({slug})",
                )
                enqueued.append(str(path))
            except Exception as exc:
                issues.append(f"node {nid} ({slug}): enqueue failed: {exc}")

        elif kind == "software":
            handoff = {
                "goal_id": goal_id,
                "node_id": nid,
                "slug": slug,
                "kind": kind,
                "status": status,
                "goal_text": goal_text[:500],
                "reason": f"graph missing software node {nid} ({slug})",
                "policy": "build",
            }
            software_handoffs.append(handoff)
            try:
                metrics = get_pipeline_dir() / "metrics"
                metrics.mkdir(parents=True, exist_ok=True)
                with (metrics / "goal_build_handoffs.jsonl").open(
                    "a", encoding="utf-8"
                ) as f:
                    f.write(json.dumps(handoff, ensure_ascii=False) + "\n")
            except Exception as exc:
                issues.append(f"node {nid} ({slug}): handoff write failed: {exc}")

    return {
        "enqueued": enqueued,
        "software_handoffs": software_handoffs,
        "issues": issues,
    }
