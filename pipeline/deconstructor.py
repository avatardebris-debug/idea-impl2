"""
deconstructor v0 — candidate inventory + replacement classification.

Produces deconstruct.v0 JSON under PIPELINE_DIR/deconstructs/.
Does **not** write production graph.v1. Output is proposal-only:
critique, then fill classes via create-skill / MCP factory / block_registry
promote (register → sandbox → promote → attach).

Modes: org | credits | tool_surface | genre | open
See notes/lmao-agi-discuss.md.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pipeline.paths import deconstructs_dir, get_pipeline_dir

SCHEMA = "deconstruct.v0"
MODES = frozenset({"org", "credits", "tool_surface", "genre", "open"})

# Closed replacement classes (align with agi-lmaooo2 / lmao-agi-discuss).
REPLACEMENT_CLASSES = frozenset(
    {
        "skill",
        "prompt",
        "agent_role",
        "mcp_simple",
        "mcp_complex",
        "factory",
        "human",
        "research",
        "process",
        "process_series",
    }
)

# Soft map → graph.v1 / block kinds (hints only; not auto-compiled).
CLASS_TO_GRAPH_KIND = {
    "skill": "skill",
    "prompt": "skill",
    "agent_role": "skill",
    "mcp_simple": "mcp",
    "mcp_complex": "mcp",
    "factory": "software",
    "human": "human",
    "research": "research",
    "process": "connector",
    "process_series": "connector",
}

CLASS_NEXT_ACTION = {
    "skill": "create-skill → block_registry register→sandbox→promote→attach",
    "prompt": "register-prompt → sandbox → promote → attach",
    "agent_role": "create-prompt / role prompt → register-prompt → sandbox → promote",
    "mcp_simple": "mcp_factory wrap verified capability + smoke",
    "mcp_complex": "further deconstruct OR external MCP first (do not flat-dump tools)",
    "factory": "seed software factory / multi-phase project",
    "human": "explicit human node + oracle; do not replace with skill text",
    "research": "Hermes / knowledge path; not field_prove software",
    "process": "connector / workflow later after critique",
    "process_series": "ordered multi-step → connector series or graph later",
}

DEFAULT_MAX_NODES = 20
DEFAULT_MAX_DEPTH = 3

_SLUG_RE = re.compile(r"[^a-z0-9]+")

__all__ = [
    "SCHEMA",
    "MODES",
    "REPLACEMENT_CLASSES",
    "CLASS_TO_GRAPH_KIND",
    "CLASS_NEXT_ACTION",
    "DEFAULT_MAX_NODES",
    "DEFAULT_MAX_DEPTH",
    "slugify_target",
    "seed_candidates",
    "build_deconstruct",
    "critique_deconstruct",
    "save_deconstruct",
    "load_deconstruct",
    "list_deconstructs",
    "plan_fill_actions",
    "from_candidates",
]


def _iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def slugify_target(target: str, *, max_len: int = 48) -> str:
    s = (target or "").strip().lower()
    s = _SLUG_RE.sub("-", s).strip("-")
    if not s:
        s = "untitled"
    return s[:max_len].rstrip("-")


def _cand(
    cid: str,
    name: str,
    replacement_class: str,
    *,
    parent_id: str | None = None,
    depth: int = 0,
    department: str | None = None,
    primary_use: str = "",
    secondary_use: str = "",
    oracle_hint: str = "",
    notes: str = "",
) -> dict[str, Any]:
    rc = (replacement_class or "").strip().lower()
    if rc not in REPLACEMENT_CLASSES:
        rc = "research"
    return {
        "id": cid,
        "name": name,
        "replacement_class": rc,
        "parent_id": parent_id,
        "depth": depth,
        "department": department,
        "primary_use": primary_use or name,
        "secondary_use": secondary_use,
        "oracle_hint": oracle_hint or f"smoke or checklist for {name}",
        "notes": notes,
        "graph_kind_hint": CLASS_TO_GRAPH_KIND.get(rc, "research"),
        "next_action": CLASS_NEXT_ACTION.get(rc, "research"),
    }


def seed_candidates(mode: str, target: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return (candidates, departments) skeleton for a mode.

    Deterministic seeds for fixture eval — not LLM invention. Agents may
    replace/expand via from_candidates / from-json.
    """
    m = (mode or "open").strip().lower()
    if m not in MODES:
        raise ValueError(f"mode must be one of {sorted(MODES)}")
    t = (target or "").strip() or "untitled target"
    slug = slugify_target(t)
    candidates: list[dict[str, Any]] = []
    departments: list[dict[str, Any]] = []

    if m == "open":
        candidates.append(
            _cand(
                f"{slug}_root",
                t,
                "research",
                depth=0,
                primary_use="classify then re-deconstruct with a named mode",
                oracle_hint="human review of class choice",
                notes="open mode: pick org|credits|tool_surface|genre for better seeds",
            )
        )
        return candidates, departments

    if m == "org":
        dept_specs = [
            ("engineering", "mcp_simple", "Build and ship product code"),
            ("product", "process", "Prioritize and specify outcomes"),
            ("ops", "process_series", "Run deploy / support / metrics"),
            ("qc", "human", "Legal/QA gates and liability"),
            ("art", "mcp_complex", "Visual production surface"),
        ]
        for dname, dclass, duse in dept_specs:
            did = f"{slug}_dept_{dname}"
            departments.append(
                {
                    "id": did,
                    "name": dname,
                    "replacement_class": dclass,
                    "primary_use": duse,
                    "oracle_hint": f"department outcome check for {dname}",
                }
            )
            candidates.append(
                _cand(
                    did,
                    f"{dname} (department)",
                    dclass,
                    depth=0,
                    department=dname,
                    primary_use=duse,
                )
            )
            # one level of roles / processes under each department
            if dname == "engineering":
                roles = [
                    ("implementer", "skill", "Execute plan tasks"),
                    ("reviewer", "prompt", "Code review judgment"),
                    ("ci", "mcp_simple", "Test/build tooling"),
                ]
            elif dname == "product":
                roles = [
                    ("roadmap", "process", "Order work by value"),
                    ("acceptance", "human", "Accept done criteria"),
                ]
            elif dname == "ops":
                roles = [
                    ("deploy", "process", "Ship releases"),
                    ("oncall", "human", "Incident judgment"),
                ]
            elif dname == "qc":
                roles = [
                    ("legal_review", "human", "Liability gate"),
                    ("qa_checklist", "skill", "Repeatable QA steps"),
                ]
            else:  # art
                roles = [
                    ("animation", "mcp_complex", "Animation tool cluster — further deconstruct"),
                    ("sprites", "mcp_simple", "2D asset export"),
                    ("art_direction", "human", "Taste / brand judgment"),
                ]
            for rname, rclass, ruse in roles:
                candidates.append(
                    _cand(
                        f"{slug}_{dname}_{rname}",
                        rname,
                        rclass,
                        parent_id=did,
                        depth=1,
                        department=dname,
                        primary_use=ruse,
                    )
                )
        return candidates, departments

    if m == "credits":
        # Typical small game / product credits → replacement classes
        credit_roles = [
            ("director", "human", "Vision and liability"),
            ("producer", "process", "Schedule and coordination"),
            ("programmer", "skill", "Implement systems"),
            ("designer", "prompt", "Mechanics judgment"),
            ("pixel_artist", "mcp_simple", "2D art production tools"),
            ("composer", "human", "Music taste / rights"),
            ("tester", "skill", "Playtest checklist"),
            ("localization", "process", "String pipeline"),
        ]
        root = f"{slug}_credits"
        departments.append(
            {
                "id": root,
                "name": "credits",
                "replacement_class": "process_series",
                "primary_use": f"Credit roles for: {t}",
                "oracle_hint": "each role has class + oracle_hint",
            }
        )
        candidates.append(
            _cand(
                root,
                f"Credits: {t}",
                "process_series",
                depth=0,
                department="credits",
                primary_use="inventory of credit roles",
            )
        )
        for rname, rclass, ruse in credit_roles:
            candidates.append(
                _cand(
                    f"{slug}_{rname}",
                    rname.replace("_", " "),
                    rclass,
                    parent_id=root,
                    depth=1,
                    department="credits",
                    primary_use=ruse,
                )
            )
        return candidates, departments

    if m == "tool_surface":
        root = f"{slug}_surface"
        clusters = [
            ("core_io", "mcp_simple", "Open/save/export entrypoints"),
            ("selection", "mcp_simple", "Select / transform primitives"),
            ("animation", "mcp_complex", "Animation tool cluster — further deconstruct"),
            ("rendering", "mcp_complex", "Render pipeline — cluster before wrap"),
            ("scripting", "factory", "Extension/scripting may need own factory"),
            ("help_docs", "research", "Docs crawl for elicit inventory"),
        ]
        departments.append(
            {
                "id": root,
                "name": "tool_surface",
                "replacement_class": "mcp_complex",
                "primary_use": f"Tool surface for: {t}",
                "oracle_hint": "cluster smoke, not 100 flat tools",
            }
        )
        candidates.append(
            _cand(
                root,
                f"Tool surface: {t}",
                "mcp_complex",
                depth=0,
                department="tool_surface",
                primary_use="cluster tools before MCP wrap",
                notes="Do not dump full API into one graph node",
            )
        )
        for cname, cclass, cuse in clusters:
            candidates.append(
                _cand(
                    f"{slug}_{cname}",
                    cname.replace("_", " "),
                    cclass,
                    parent_id=root,
                    depth=1,
                    department="tool_surface",
                    primary_use=cuse,
                )
            )
        return candidates, departments

    if m == "genre":
        root = f"{slug}_genre"
        layers = [
            ("core_loop", "process", "Primary player loop"),
            ("controls", "skill", "Input / feel checklist"),
            ("levels", "factory", "Level content pipeline"),
            ("enemies", "skill", "Encounter patterns"),
            ("audio", "mcp_simple", "SFX/music tooling"),
            ("difficulty_v1", "research", "Easiest era / ladder step v1"),
            ("difficulty_v2", "research", "Next ladder step after v1 proven"),
            ("qc_playtest", "human", "Fun / fairness judgment"),
        ]
        departments.append(
            {
                "id": root,
                "name": "genre",
                "replacement_class": "process_series",
                "primary_use": f"Genre systems for: {t}",
                "oracle_hint": "playable vertical slice oracle per ladder step",
            }
        )
        candidates.append(
            _cand(
                root,
                f"Genre: {t}",
                "process_series",
                depth=0,
                department="genre",
                primary_use="genre systems inventory",
                notes="Hard super-goals are chains; not one deconstruct call",
            )
        )
        for lname, lclass, luse in layers:
            candidates.append(
                _cand(
                    f"{slug}_{lname}",
                    lname.replace("_", " "),
                    lclass,
                    parent_id=root,
                    depth=1,
                    department="genre",
                    primary_use=luse,
                )
            )
        return candidates, departments

    return candidates, departments


def _normalize_candidate(raw: dict[str, Any], *, index: int) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError(f"candidate[{index}] must be an object")
    name = str(raw.get("name") or raw.get("id") or f"candidate_{index}").strip()
    cid = str(raw.get("id") or slugify_target(name) or f"c{index}").strip()
    rc = str(raw.get("replacement_class") or raw.get("class") or "research").strip().lower()
    if rc not in REPLACEMENT_CLASSES:
        # keep invalid for critique to flag; still store normalized attempt
        pass
    depth = int(raw.get("depth") or 0)
    parent = raw.get("parent_id")
    parent_id = str(parent).strip() if parent not in (None, "") else None
    out = _cand(
        cid,
        name,
        rc if rc in REPLACEMENT_CLASSES else "research",
        parent_id=parent_id,
        depth=depth,
        department=str(raw.get("department") or "") or None,
        primary_use=str(raw.get("primary_use") or name),
        secondary_use=str(raw.get("secondary_use") or ""),
        oracle_hint=str(raw.get("oracle_hint") or ""),
        notes=str(raw.get("notes") or ""),
    )
    if rc not in REPLACEMENT_CLASSES:
        out["replacement_class_raw"] = rc
        out["replacement_class"] = rc  # preserve for critique fail
        out["graph_kind_hint"] = "research"
        out["next_action"] = "fix class to closed enum"
    return out


def critique_deconstruct(
    doc: dict[str, Any],
    *,
    max_nodes: int = DEFAULT_MAX_NODES,
    max_depth: int = DEFAULT_MAX_DEPTH,
) -> dict[str, Any]:
    """Structure critique — size budgets, closed classes, oracle hints, depth."""
    issues: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    schema = str(doc.get("schema") or "")
    if schema != SCHEMA:
        issues.append({"code": "schema", "detail": f"expected {SCHEMA}, got {schema!r}"})

    mode = str(doc.get("mode") or "")
    if mode not in MODES:
        issues.append({"code": "mode", "detail": f"mode must be one of {sorted(MODES)}"})

    cands = doc.get("candidates")
    if not isinstance(cands, list) or not cands:
        issues.append({"code": "empty", "detail": "candidates must be a non-empty list"})
        cands = []

    if len(cands) > max_nodes:
        issues.append(
            {
                "code": "size_budget",
                "detail": f"{len(cands)} candidates > max_nodes={max_nodes}; split or nest",
            }
        )

    ids: set[str] = set()
    for i, c in enumerate(cands):
        if not isinstance(c, dict):
            issues.append({"code": "candidate_type", "detail": f"candidates[{i}] not object"})
            continue
        cid = str(c.get("id") or "")
        if not cid:
            issues.append({"code": "missing_id", "detail": f"candidates[{i}] missing id"})
        elif cid in ids:
            issues.append({"code": "duplicate_id", "detail": cid})
        else:
            ids.add(cid)

        rc = str(c.get("replacement_class") or "")
        if rc not in REPLACEMENT_CLASSES:
            issues.append(
                {
                    "code": "class",
                    "detail": f"{cid or i}: replacement_class {rc!r} not in closed enum",
                }
            )

        depth = int(c.get("depth") or 0)
        if depth > max_depth:
            issues.append(
                {
                    "code": "depth",
                    "detail": f"{cid or i}: depth {depth} > max_depth={max_depth}",
                }
            )

        oh = str(c.get("oracle_hint") or "").strip()
        if not oh:
            warnings.append({"code": "oracle_hint", "detail": f"{cid or i}: empty oracle_hint"})

        if rc in ("mcp_complex", "factory") and depth < max_depth:
            # encourage further deconstruct
            has_child = any(
                isinstance(x, dict) and str(x.get("parent_id") or "") == cid for x in cands
            )
            if not has_child:
                warnings.append(
                    {
                        "code": "further_deconstruct",
                        "detail": f"{cid}: {rc} has no children; consider one more level",
                    }
                )

        if rc == "human":
            # good — force awareness
            pass

    # parent references
    for c in cands:
        if not isinstance(c, dict):
            continue
        pid = c.get("parent_id")
        if pid and str(pid) not in ids:
            issues.append(
                {
                    "code": "parent_missing",
                    "detail": f"{c.get('id')}: parent_id {pid!r} not in candidates",
                }
            )

    if doc.get("production_graph") is True:
        issues.append(
            {
                "code": "not_production",
                "detail": "deconstruct.v0 must not claim production_graph=true",
            }
        )

    ok = len(issues) == 0
    return {
        "ok": ok,
        "issues": issues,
        "warnings": warnings,
        "candidate_count": len(cands),
        "max_nodes": max_nodes,
        "max_depth": max_depth,
    }


def build_deconstruct(
    target: str,
    *,
    mode: str = "open",
    candidates: list[dict[str, Any]] | None = None,
    departments: list[dict[str, Any]] | None = None,
    max_nodes: int = DEFAULT_MAX_NODES,
    max_depth: int = DEFAULT_MAX_DEPTH,
    deconstruct_id: str | None = None,
    notes: str = "",
) -> dict[str, Any]:
    """Build a deconstruct.v0 document (seed or supplied candidates)."""
    m = (mode or "open").strip().lower()
    if m not in MODES:
        raise ValueError(f"mode must be one of {sorted(MODES)}")
    t = (target or "").strip()
    if not t:
        raise ValueError("target is required")

    if candidates is None:
        cands, depts = seed_candidates(m, t)
    else:
        cands = [_normalize_candidate(c, index=i) for i, c in enumerate(candidates)]
        depts = list(departments or [])

    if departments is not None and candidates is not None:
        depts = list(departments)

    did = (deconstruct_id or f"{m}_{slugify_target(t)}").strip()
    did = slugify_target(did, max_len=64)

    doc: dict[str, Any] = {
        "schema": SCHEMA,
        "id": did,
        "mode": m,
        "target": t,
        "created_at": _iso(),
        "updated_at": _iso(),
        "max_nodes": max_nodes,
        "max_depth": max_depth,
        "production_graph": False,
        "status": "candidate",
        "notes": notes
        or "Proposal only — critique then fill classes; do not treat as graph.v1",
        "departments": depts,
        "candidates": cands,
        "critique": {},
    }
    crit = critique_deconstruct(doc, max_nodes=max_nodes, max_depth=max_depth)
    doc["critique"] = crit
    doc["status"] = "candidate_ok" if crit.get("ok") else "candidate_blocked"
    return doc


def from_candidates(
    target: str,
    candidates: list[dict[str, Any]],
    *,
    mode: str = "open",
    departments: list[dict[str, Any]] | None = None,
    deconstruct_id: str | None = None,
    max_nodes: int = DEFAULT_MAX_NODES,
    max_depth: int = DEFAULT_MAX_DEPTH,
    notes: str = "",
) -> dict[str, Any]:
    """Wrap agent- or fixture-supplied candidates into deconstruct.v0."""
    return build_deconstruct(
        target,
        mode=mode,
        candidates=candidates,
        departments=departments,
        deconstruct_id=deconstruct_id,
        max_nodes=max_nodes,
        max_depth=max_depth,
        notes=notes,
    )


def deconstruct_path(deconstruct_id: str) -> Path:
    safe = slugify_target(deconstruct_id, max_len=64)
    if not safe or ".." in safe:
        raise ValueError(f"invalid deconstruct_id: {deconstruct_id!r}")
    return deconstructs_dir() / f"{safe}.json"


def save_deconstruct(doc: dict[str, Any]) -> Path:
    if not isinstance(doc, dict) or str(doc.get("schema")) != SCHEMA:
        raise ValueError(f"doc must be {SCHEMA}")
    did = str(doc.get("id") or "").strip()
    if not did:
        raise ValueError("doc.id required")
    doc = dict(doc)
    doc["updated_at"] = _iso()
    # re-critique on save
    crit = critique_deconstruct(
        doc,
        max_nodes=int(doc.get("max_nodes") or DEFAULT_MAX_NODES),
        max_depth=int(doc.get("max_depth") or DEFAULT_MAX_DEPTH),
    )
    doc["critique"] = crit
    doc["status"] = "candidate_ok" if crit.get("ok") else "candidate_blocked"
    path = deconstruct_path(did)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def load_deconstruct(deconstruct_id: str) -> dict[str, Any] | None:
    path = deconstruct_path(deconstruct_id)
    if not path.is_file():
        # try raw filename
        alt = deconstructs_dir() / f"{deconstruct_id}.json"
        if alt.is_file():
            path = alt
        else:
            return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def list_deconstructs() -> list[dict[str, Any]]:
    root = deconstructs_dir()
    if not root.is_dir():
        return []
    out: list[dict[str, Any]] = []
    for path in sorted(root.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        out.append(
            {
                "id": data.get("id"),
                "mode": data.get("mode"),
                "target": data.get("target"),
                "status": data.get("status"),
                "candidate_count": len(data.get("candidates") or []),
                "critique_ok": (data.get("critique") or {}).get("ok"),
                "path": str(path),
            }
        )
    return out


def plan_fill_actions(doc: dict[str, Any]) -> dict[str, Any]:
    """Map candidates → next factory / promote actions (no execution)."""
    cands = doc.get("candidates") or []
    actions: list[dict[str, Any]] = []
    by_class: dict[str, int] = {}
    for c in cands:
        if not isinstance(c, dict):
            continue
        rc = str(c.get("replacement_class") or "research")
        by_class[rc] = by_class.get(rc, 0) + 1
        actions.append(
            {
                "candidate_id": c.get("id"),
                "name": c.get("name"),
                "replacement_class": rc,
                "graph_kind_hint": c.get("graph_kind_hint")
                or CLASS_TO_GRAPH_KIND.get(rc, "research"),
                "next_action": c.get("next_action") or CLASS_NEXT_ACTION.get(rc, "research"),
                "oracle_hint": c.get("oracle_hint"),
            }
        )
    # Prefer fill order: human/research last; skills/mcp_simple first
    priority = {
        "skill": 0,
        "prompt": 1,
        "mcp_simple": 2,
        "process": 3,
        "process_series": 4,
        "agent_role": 5,
        "factory": 6,
        "mcp_complex": 7,
        "research": 8,
        "human": 9,
    }
    actions.sort(key=lambda a: (priority.get(str(a.get("replacement_class")), 50), str(a.get("name"))))
    return {
        "deconstruct_id": doc.get("id"),
        "target": doc.get("target"),
        "mode": doc.get("mode"),
        "production_graph": False,
        "by_class": by_class,
        "actions": actions,
        "notes": (
            "Do not auto-attach. Skills/prompts need register→sandbox→promote. "
            "mcp_complex needs further deconstruct or external MCP first."
        ),
    }
