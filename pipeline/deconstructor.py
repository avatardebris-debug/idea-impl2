"""
deconstructor — candidate inventory + replacement classification.

Primary path (intended product):
  **LLM deconstruct** via ``run_llm_deconstruct`` / agent ``deconstructor``
  (prompt ``pipeline/prompts/deconstructor.md``) → JSON → critique → save.

Secondary paths (no LLM):
  - ``from_candidates`` / CLI ``from-json`` — already-built inventory
  - ``build_deconstruct`` / CLI ``build`` — structure *parser* only when the
    target already lists parts (bullets, Dept: a,b). Bare titles do NOT invent
    orgs (that is the LLM's job).

Does **not** write production graph.v1. Proposal only.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pipeline.paths import deconstructs_dir

SCHEMA = "deconstruct.v0"
MODES = frozenset({"org", "credits", "tool_surface", "genre", "open"})

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
_BULLET_RE = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s+")
_HEADER_CHILDREN_RE = re.compile(
    r"^(?P<head>[^:\n]{1,80}?)\s*:\s*(?P<body>.+)$"
)
_CREDITS_DASH_RE = re.compile(
    r"^(?P<role>[A-Za-z][A-Za-z0-9 /&+.-]{0,60}?)\s*[-–—]\s*(?P<who>.+)$"
)
# stopwords when splitting free prose (not used as standalone nodes)
_STOP = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "of",
        "for",
        "to",
        "in",
        "on",
        "with",
        "by",
        "from",
        "as",
        "is",
        "are",
        "be",
        "this",
        "that",
        "these",
        "those",
        "its",
        "into",
        "via",
        "at",
        "our",
        "we",
        "their",
        "mode",
        "org",
        "credits",
        "genre",
        "tool",
        "surface",
        "target",
        "deconstruct",
        "small",
        "large",
        "new",
        "old",
    }
)

# (regex, class) — first match wins. Applied to lowercased name.
_CLASS_RULES: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(
            r"\b("
            r"legal|counsel|compliance|liability|attorney|judge|signer|approver|"
            r"director|ceo|cfo|cto|owner|founder|partner|principal|"
            r"physician|doctor|surgeon|anesthesiologist|attending|radiologist|"
            r"nurse.?manager|charge.?nurse|"
            r"composer|musician|conductor|"
            r"art.?direction|creative.?director|taste|brand.?guard|"
            r"on[- ]?call|incident.?commander|"
            r"acceptance|sign[- ]?off|executive"
            r")\b"
        ),
        "human",
    ),
    (
        re.compile(
            r"\b("
            r"animation|animator|rigging|rendering|renderer|shader|vfx|"
            r"blender|maya|cinema.?4d|unreal|unity.?editor|"
            r"3d|complex.?surface|full.?api|plugin.?host"
            r")\b"
        ),
        "mcp_complex",
    ),
    (
        re.compile(
            r"\b("
            r"cli|api|sdk|export|import|build|ci|cd|git|docker|"
            r"tooling|tool|plugin|mcp|linter|formatter|"
            r"sprite|pixel|texture.?export|audio.?tool|"
            r"mri|scanner|device.?driver|instrument"
            r")\b"
        ),
        "mcp_simple",
    ),
    (
        re.compile(
            r"\b("
            r"engine|platform|framework|factory|product.?line|"
            r"content.?pipeline|level.?pipeline|data.?platform"
            r")\b"
        ),
        "factory",
    ),
    (
        re.compile(
            r"\b("
            r"review|reviewer|critique|critic|design(?:er)?|"
            r"judgment|eval(?:uator)?|triage.?decision|"
            r"mechanics|balance|narrative.?design"
            r")\b"
        ),
        "prompt",
    ),
    (
        re.compile(
            r"\b("
            r"research|survey|study|history|literature|market.?scan|"
            r"difficulty.?ladder|era|genre.?study|docs.?crawl|help.?docs"
            r")\b"
        ),
        "research",
    ),
    (
        re.compile(
            r"\b("
            r"department|division|unit|org|organization|studio|clinic|"
            r"hospital|ward|series|pipeline.?chain|multi[- ]step"
            r")\b"
        ),
        "process_series",
    ),
    (
        re.compile(
            r"\b("
            r"deploy|ops|operations|process|workflow|roadmap|schedule|"
            r"billing|collections|intake|admission|discharge|"
            r"localization|producer|production|coordination|"
            r"core.?loop|controls|levels|enemies|audio.?mix"
            r")\b"
        ),
        "process",
    ),
    (
        re.compile(
            r"\b("
            r"checklist|skill|implement(?:er)?|program(?:mer)?|"
            r"developer|engineer|coding|coder|"
            r"test(?:er|ing)?|qa|playtest|"
            r"triage|scribe|technician|tech\b|"
            r"nurse|cna|phlebotomy|"
            r"pixel.?artist|artist"
            r")\b"
        ),
        "skill",
    ),
]

# Mode default when no keyword matches
_MODE_LEAF_DEFAULT = {
    "org": "skill",
    "credits": "skill",
    "tool_surface": "mcp_simple",
    "genre": "process",
    "open": "research",
}
_MODE_GROUP_DEFAULT = {
    "org": "process_series",
    "credits": "process_series",
    "tool_surface": "mcp_complex",
    "genre": "process_series",
    "open": "process_series",
}

_STRUCTURE_HINTS = {
    "org": (
        "Pass structured org text, e.g.:\n"
        "  Emergency\n"
        "    - triage nurse\n"
        "    - attending physician\n"
        "  Radiology: MRI tech, radiologist\n"
        "  Billing: coder, collections"
    ),
    "credits": (
        "Pass a credits role list, e.g.:\n"
        "  Director - Alice\n"
        "  Programmer - Bob\n"
        "  Composer\n"
        "  Tester"
    ),
    "tool_surface": (
        "Pass tool clusters or commands, e.g.:\n"
        "  Core IO: open, save, export\n"
        "  Animation: keyframe, bake, retarget\n"
        "  Scripting"
    ),
    "genre": (
        "Pass genre systems, e.g.:\n"
        "  core loop\n"
        "  controls\n"
        "  levels\n"
        "  enemies\n"
        "  difficulty ladder v1"
    ),
    "open": (
        "Pass any structured list of parts to classify, or re-run with "
        "mode=org|credits|tool_surface|genre and a structured target."
    ),
}

__all__ = [
    "SCHEMA",
    "MODES",
    "REPLACEMENT_CLASSES",
    "CLASS_TO_GRAPH_KIND",
    "CLASS_NEXT_ACTION",
    "DEFAULT_MAX_NODES",
    "DEFAULT_MAX_DEPTH",
    "slugify_target",
    "classify_name",
    "parse_structure",
    "seed_candidates",
    "deconstruct_target",
    "build_deconstruct",
    "critique_deconstruct",
    "save_deconstruct",
    "load_deconstruct",
    "list_deconstructs",
    "plan_fill_actions",
    "from_candidates",
    "load_deconstructor_system_prompt",
    "build_llm_user_prompt",
    "extract_json_object",
    "doc_from_llm_payload",
    "run_llm_deconstruct",
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


def classify_name(
    name: str,
    *,
    mode: str = "open",
    has_children: bool = False,
    depth: int = 0,
) -> str:
    """Heuristic replacement class from the item's own words + mode bias."""
    m = (mode or "open").strip().lower()
    if m not in MODES:
        m = "open"
    text = (name or "").strip().lower()
    if not text:
        return "research"

    for pat, cls in _CLASS_RULES:
        if pat.search(text):
            return cls

    if has_children or (depth == 0 and m in ("org", "tool_surface", "genre")):
        return _MODE_GROUP_DEFAULT.get(m, "process_series")
    return _MODE_LEAF_DEFAULT.get(m, "research")


def _indent_level(line: str) -> int:
    """Count indent in spaces (tabs → 4)."""
    n = 0
    for ch in line:
        if ch == " ":
            n += 1
        elif ch == "\t":
            n += 4
        else:
            break
    return n


def _clean_item(s: str) -> str:
    s = (s or "").strip()
    s = _BULLET_RE.sub("", s).strip()
    s = s.strip(" \t-–—:;,")
    # drop trailing parenthetical person counts etc.
    s = re.sub(r"\s+\(\d+\)$", "", s).strip()
    return s


def _split_children(body: str) -> list[str]:
    """Split 'a, b; c / d | e' into items."""
    parts = re.split(r"[,;/|]+", body)
    out: list[str] = []
    for p in parts:
        item = _clean_item(p)
        if item and item.lower() not in _STOP and len(item) > 1:
            out.append(item)
    return out


def _looks_structured(lines: list[str]) -> bool:
    if len(lines) <= 1:
        s = lines[0].strip() if lines else ""
        if _BULLET_RE.match(s):
            return True
        hm = _HEADER_CHILDREN_RE.match(s)
        if hm and _split_children(hm.group("body")):
            return True
        if re.search(r"[,;/|]", s):
            return len(_split_children(s)) >= 2
        return False
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        if _BULLET_RE.match(s) or _BULLET_RE.match(ln):
            return True
        hm = _HEADER_CHILDREN_RE.match(s)
        if hm and _split_children(hm.group("body")):
            return True
        if _CREDITS_DASH_RE.match(s):
            return True
    # multiple non-empty plain lines count as a list
    nonempty = [ln.strip() for ln in lines if ln.strip()]
    return len(nonempty) >= 2


def parse_structure(text: str) -> list[dict[str, Any]]:
    """Parse hierarchical / list structure from target text.

    Returns ordered nodes: {name, depth, parent_name, source}.
    parent_name is the nearest enclosing group name (not id).
    """
    raw = (text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not raw:
        return []

    lines = raw.split("\n")
    nodes: list[dict[str, Any]] = []

    # Single-line CSV / list before hierarchical path (avoids one blob node)
    if len([ln for ln in lines if ln.strip()]) == 1 and re.search(r"[,;/|]", raw):
        items = _split_children(raw)
        if len(items) >= 2:
            for it in items:
                nodes.append(
                    {"name": it, "depth": 0, "parent_name": None, "source": "csv"}
                )
            return _dedupe_nodes(nodes)

    if _looks_structured(lines):
        # Optional title line: plain first line, rest structured → root group
        nonempty_idx = [i for i, ln in enumerate(lines) if ln.strip()]
        title_root: str | None = None
        start_i = 0
        if len(nonempty_idx) >= 2:
            first_i = nonempty_idx[0]
            first = lines[first_i].strip()
            rest = [lines[i].strip() for i in nonempty_idx[1:]]
            first_is_plain = (
                not _BULLET_RE.match(first)
                and not _CREDITS_DASH_RE.match(first)
                and not (
                    _HEADER_CHILDREN_RE.match(first)
                    and _split_children(_HEADER_CHILDREN_RE.match(first).group("body"))  # type: ignore[union-attr]
                )
            )
            rest_structured = any(
                _BULLET_RE.match(r)
                or _CREDITS_DASH_RE.match(r)
                or (
                    _HEADER_CHILDREN_RE.match(r)
                    and _split_children(_HEADER_CHILDREN_RE.match(r).group("body"))  # type: ignore[union-attr]
                )
                or _indent_level(lines[nonempty_idx[j + 1]]) > 0
                for j, r in enumerate(rest)
            )
            if first_is_plain and rest_structured:
                title_root = _clean_item(first.rstrip(":"))
                start_i = first_i + 1
                if title_root:
                    nodes.append(
                        {
                            "name": title_root,
                            "depth": 0,
                            "parent_name": None,
                            "source": "title_root",
                        }
                    )

        # Stack of (indent_level, name); seed with title root at -1 indent
        stack: list[tuple[int, str]] = []
        if title_root:
            stack.append((-1, title_root))

        for ln in lines[start_i:]:
            if not ln.strip():
                continue
            # Effective indent: bullets at column 0 still nest under title_root
            raw_indent = _indent_level(ln)
            content = ln.strip()
            has_bullet = bool(_BULLET_RE.match(content))
            # Treat bullet markers as +2 indent so nesting under title works
            indent = raw_indent + (2 if has_bullet else 0)
            if title_root and raw_indent == 0 and has_bullet:
                indent = 2

            # Credits: Role - Person
            cm = _CREDITS_DASH_RE.match(content)
            if cm and not content.rstrip().endswith(":"):
                role = _clean_item(cm.group("role"))
                who = _clean_item(cm.group("who"))
                # strip bullet from role if present
                role = _BULLET_RE.sub("", role).strip() if role else role
                role = _clean_item(role)
                if role:
                    while stack and stack[-1][0] >= indent:
                        stack.pop()
                    parent = stack[-1][1] if stack else None
                    depth = len(stack)
                    nodes.append(
                        {
                            "name": role,
                            "depth": depth,
                            "parent_name": parent,
                            "source": "credits_dash",
                            "secondary_use": who,
                        }
                    )
                    continue

            # Header: child, child  (may be bulleted)
            content_nb = _BULLET_RE.sub("", content).strip()
            hm = _HEADER_CHILDREN_RE.match(content_nb)
            if hm and _split_children(hm.group("body")):
                head = _clean_item(hm.group("head"))
                kids = _split_children(hm.group("body"))
                if head:
                    while stack and stack[-1][0] >= indent:
                        stack.pop()
                    parent = stack[-1][1] if stack else None
                    depth = len(stack)
                    nodes.append(
                        {
                            "name": head,
                            "depth": depth,
                            "parent_name": parent,
                            "source": "header",
                        }
                    )
                    stack.append((indent, head))
                    for kid in kids:
                        nodes.append(
                            {
                                "name": kid,
                                "depth": depth + 1,
                                "parent_name": head,
                                "source": "header_child",
                            }
                        )
                continue

            # Bullet / plain line
            item = _clean_item(content_nb if has_bullet else content)
            if item.endswith(":"):
                item = item[:-1].strip()
            if not item:
                continue

            while stack and stack[-1][0] >= indent:
                stack.pop()
            parent = stack[-1][1] if stack else None
            depth = len(stack)
            nodes.append(
                {
                    "name": item,
                    "depth": depth,
                    "parent_name": parent,
                    "source": "line",
                }
            )
            stack.append((indent, item))

        if nodes:
            return _dedupe_nodes(nodes)

    # Single-line list separators
    if re.search(r"[,;/|]", raw) and "\n" not in raw:
        items = _split_children(raw)
        for it in items:
            nodes.append(
                {"name": it, "depth": 0, "parent_name": None, "source": "csv"}
            )
        if len(nodes) >= 2:
            return _dedupe_nodes(nodes)

    nodes = _extract_from_prose(raw)
    return _dedupe_nodes(nodes)


def _extract_from_prose(text: str) -> list[dict[str, Any]]:
    """Pull candidate parts from free prose without inventing a domain template."""
    nodes: list[dict[str, Any]] = []
    lower = text.lower()

    # Cue phrases: "departments include X, Y and Z"
    cue = re.search(
        r"\b(?:departments?|roles?|teams?|units?|sections?|includes?|with|"
        r"comprising|composed of|systems?|tools?|features?|credits?)\b"
        r"\s*(?:include|includes|are|:)?\s*(.+)$",
        text,
        re.I | re.S,
    )
    if cue:
        tail = cue.group(1)
        # split on commas / and
        parts = re.split(r",|\band\b|&", tail, flags=re.I)
        for p in parts:
            item = _clean_item(p)
            item = re.sub(r"[.!?].*$", "", item).strip()
            if item and len(item) > 1 and item.lower() not in _STOP:
                # drop trailing junk words
                if len(item.split()) <= 6:
                    nodes.append(
                        {
                            "name": item,
                            "depth": 0,
                            "parent_name": None,
                            "source": "prose_cue",
                        }
                    )
        if len(nodes) >= 2:
            return nodes

    # Capitalized multi-word phrases (Title Case runs)
    for m in re.finditer(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})\b", text):
        item = m.group(1).strip()
        if item.lower() in _STOP or len(item) < 3:
            continue
        nodes.append(
            {
                "name": item,
                "depth": 0,
                "parent_name": None,
                "source": "title_case",
            }
        )
    if len(nodes) >= 2:
        return nodes

    # Last resort: significant tokens from the whole string (no template)
    # Only if many tokens — still better than fake studio
    tokens = [
        t
        for t in re.split(r"[^A-Za-z0-9+]+", text)
        if len(t) > 2 and t.lower() not in _STOP
    ]
    # If the whole target is just a short title (1–4 tokens), no structure
    if len(tokens) <= 4:
        return []

    for t in tokens[: DEFAULT_MAX_NODES - 1]:
        nodes.append(
            {
                "name": t,
                "depth": 0,
                "parent_name": None,
                "source": "token",
            }
        )
    return nodes


def _dedupe_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for n in nodes:
        key = f"{n.get('parent_name') or ''}::{(n.get('name') or '').lower()}"
        if key in seen:
            continue
        seen.add(key)
        out.append(n)
    return out


def _needs_structure_doc(
    mode: str, target: str, slug: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Bare title — do not invent a domain template."""
    m = mode if mode in MODES else "open"
    hint = _STRUCTURE_HINTS.get(m, _STRUCTURE_HINTS["open"])
    cands = [
        _cand(
            f"{slug}_needs_structure",
            f"Needs structure: {target.strip()[:80]}",
            "research",
            depth=0,
            primary_use="Provide structured parts to deconstruct",
            oracle_hint="human supplies structured target or from-json inventory",
            notes=(
                "No inventable structure in target. "
                "Deconstructor does not stamp a fixed org template. "
                f"Hint:\n{hint}"
            ),
        )
    ]
    meta = {
        "needs_structure": True,
        "structure_hint": hint,
        "parse_source": "none",
        "parsed_count": 0,
    }
    return cands, [], meta


def deconstruct_target(
    target: str,
    *,
    mode: str = "open",
    max_nodes: int = DEFAULT_MAX_NODES,
    max_depth: int = DEFAULT_MAX_DEPTH,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Parse target → classify → candidates. No fixed domain template."""
    m = (mode or "open").strip().lower()
    if m not in MODES:
        raise ValueError(f"mode must be one of {sorted(MODES)}")
    t = (target or "").strip()
    if not t:
        raise ValueError("target is required")

    slug = slugify_target(t.split("\n")[0], max_len=40)
    parsed = parse_structure(t)

    if not parsed:
        return _needs_structure_doc(m, t, slug)

    # Cap before building (prefer shallower nodes first)
    if len(parsed) > max_nodes:
        parsed = parsed[:max_nodes]

    # Determine which names have children
    children_of: set[str] = set()
    for n in parsed:
        p = n.get("parent_name")
        if p:
            children_of.add(str(p).lower())

    # Map name@depth path → id for parent linking
    # Use unique ids even if names repeat under different parents
    name_to_ids: dict[str, str] = {}  # lower name of last occurrence at path
    id_by_key: dict[str, str] = {}
    candidates: list[dict[str, Any]] = []
    departments: list[dict[str, Any]] = []

    # Root context node (the whole target title) when first line is a title
    # and children exist under depth 0 items — optional. Skip extra root to
    # keep node budget for real parts.

    used_ids: set[str] = set()

    def _unique_id(base: str) -> str:
        bid = slugify_target(base, max_len=40) or "item"
        if bid not in used_ids:
            used_ids.add(bid)
            return bid
        i = 2
        while f"{bid}_{i}" in used_ids:
            i += 1
        uid = f"{bid}_{i}"
        used_ids.add(uid)
        return uid

    sources: set[str] = set()
    for n in parsed:
        name = str(n.get("name") or "").strip()
        if not name:
            continue
        depth = min(int(n.get("depth") or 0), max_depth)
        parent_name = n.get("parent_name")
        has_kids = name.lower() in children_of
        rc = classify_name(name, mode=m, has_children=has_kids, depth=depth)
        # Force depth clamp: if parent would exceed max_depth, promote parent_id null? keep parent if exists
        if depth > max_depth:
            depth = max_depth

        parent_id = None
        if parent_name:
            # find most recent id for that parent name
            parent_id = name_to_ids.get(str(parent_name).lower())

        cid = _unique_id(f"{slug}_{name}")
        key = f"{parent_id or ''}::{name.lower()}"
        id_by_key[key] = cid
        name_to_ids[name.lower()] = cid

        dept = None
        if parent_name and depth >= 1:
            dept = str(parent_name)
        elif has_kids or depth == 0:
            dept = name

        secondary = str(n.get("secondary_use") or "")
        sources.add(str(n.get("source") or "parsed"))

        cand = _cand(
            cid,
            name,
            rc,
            parent_id=parent_id,
            depth=depth,
            department=dept,
            primary_use=f"{m}: {name}",
            secondary_use=secondary,
            oracle_hint=f"acceptance check for '{name}'",
            notes=f"parsed via {n.get('source')}",
        )
        candidates.append(cand)

        if has_kids or (depth == 0 and m == "org"):
            departments.append(
                {
                    "id": cid,
                    "name": name,
                    "replacement_class": rc,
                    "primary_use": cand["primary_use"],
                    "oracle_hint": cand["oracle_hint"],
                }
            )

    if not candidates:
        return _needs_structure_doc(m, t, slug)

    meta = {
        "needs_structure": False,
        "parse_source": ",".join(sorted(sources)) if sources else "parsed",
        "parsed_count": len(candidates),
        "structure_hint": None,
    }
    return candidates, departments, meta


def seed_candidates(
    mode: str, target: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Backward-compatible: deconstruct target (no fixed templates)."""
    cands, depts, _meta = deconstruct_target(target, mode=mode)
    return cands, depts


def _normalize_candidate(raw: dict[str, Any], *, index: int) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError(f"candidate[{index}] must be an object")
    name = str(raw.get("name") or raw.get("id") or f"candidate_{index}").strip()
    cid = str(raw.get("id") or slugify_target(name) or f"c{index}").strip()
    rc = str(raw.get("replacement_class") or raw.get("class") or "").strip().lower()
    if not rc:
        rc = classify_name(name, mode="open")
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
        out["replacement_class"] = rc
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

    if doc.get("needs_structure"):
        warnings.append(
            {
                "code": "needs_structure",
                "detail": "Target had no parseable parts; supply structured list or from-json",
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
        "needs_structure": bool(doc.get("needs_structure")),
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
    """Build a deconstruct.v0 document by parsing target (or supplied candidates)."""
    m = (mode or "open").strip().lower()
    if m not in MODES:
        raise ValueError(f"mode must be one of {sorted(MODES)}")
    t = (target or "").strip()
    if not t:
        raise ValueError("target is required")

    meta: dict[str, Any] = {}
    if candidates is None:
        cands, depts, meta = deconstruct_target(
            t, mode=m, max_nodes=max_nodes, max_depth=max_depth
        )
    else:
        cands = [_normalize_candidate(c, index=i) for i, c in enumerate(candidates)]
        depts = list(departments or [])
        meta = {"needs_structure": False, "parse_source": "supplied", "parsed_count": len(cands)}

    if departments is not None and candidates is not None:
        depts = list(departments)

    title = t.split("\n")[0].strip()
    did = (deconstruct_id or f"{m}_{slugify_target(title)}").strip()
    did = slugify_target(did, max_len=64)

    default_notes = (
        "Proposal only — critique then fill classes; do not treat as graph.v1. "
        "Candidates come from parsing the target, not a fixed domain template."
    )
    if meta.get("needs_structure"):
        default_notes = (
            "Target lacked parseable structure. Provide hierarchical lists, "
            "'Dept: a, b' lines, or use from-json. " + default_notes
        )

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
        "notes": notes or default_notes,
        "needs_structure": bool(meta.get("needs_structure")),
        "parse_source": meta.get("parse_source"),
        "structure_hint": meta.get("structure_hint"),
        "departments": depts,
        "candidates": cands,
        "critique": {},
    }
    crit = critique_deconstruct(doc, max_nodes=max_nodes, max_depth=max_depth)
    doc["critique"] = crit
    if meta.get("needs_structure"):
        doc["status"] = "needs_structure"
    else:
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
    crit = critique_deconstruct(
        doc,
        max_nodes=int(doc.get("max_nodes") or DEFAULT_MAX_NODES),
        max_depth=int(doc.get("max_depth") or DEFAULT_MAX_DEPTH),
    )
    doc["critique"] = crit
    if doc.get("needs_structure"):
        doc["status"] = "needs_structure"
    else:
        doc["status"] = "candidate_ok" if crit.get("ok") else "candidate_blocked"
    path = deconstruct_path(did)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def load_deconstruct(deconstruct_id: str) -> dict[str, Any] | None:
    path = deconstruct_path(deconstruct_id)
    if not path.is_file():
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
                "target": (str(data.get("target") or "")[:80]),
                "status": data.get("status"),
                "needs_structure": data.get("needs_structure"),
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
        # skip pure needs_structure placeholder from fill priority noise
        if "needs structure" in str(c.get("name") or "").lower():
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
    actions.sort(
        key=lambda a: (priority.get(str(a.get("replacement_class")), 50), str(a.get("name")))
    )
    return {
        "deconstruct_id": doc.get("id"),
        "target": doc.get("target"),
        "mode": doc.get("mode"),
        "production_graph": False,
        "needs_structure": bool(doc.get("needs_structure")),
        "by_class": by_class,
        "actions": actions,
        "notes": (
            "Do not auto-attach. Skills/prompts need register→sandbox→promote. "
            "mcp_complex needs further deconstruct or external MCP first. "
            "If needs_structure, re-run with LLM (`run`) or structured target / from-json."
        ),
    }


# ---------------------------------------------------------------------------
# LLM path (primary product)
# ---------------------------------------------------------------------------

_PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
_JSON_FENCE_RE = re.compile(
    r"```(?:json)?\s*(\{.*?\})\s*```",
    re.DOTALL | re.IGNORECASE,
)


def load_deconstructor_system_prompt() -> str:
    path = _PROMPTS_DIR / "deconstructor.md"
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return (
        "You are the deconstructor. Emit deconstruct.v0 JSON with candidates "
        "using closed replacement classes only."
    )


def build_llm_user_prompt(
    target: str,
    *,
    mode: str = "open",
    max_nodes: int = DEFAULT_MAX_NODES,
    max_depth: int = DEFAULT_MAX_DEPTH,
    critique_feedback: str = "",
) -> str:
    m = (mode or "open").strip().lower()
    classes = ", ".join(sorted(REPLACEMENT_CLASSES))
    feedback = ""
    if critique_feedback.strip():
        feedback = (
            "\n## Previous attempt failed critique — fix these issues\n"
            f"{critique_feedback.strip()}\n"
            "Return a corrected full JSON object.\n"
        )
    return (
        f"## Mode\n{m}\n\n"
        f"## Target to deconstruct\n{target.strip()}\n\n"
        f"## Budgets\n"
        f"- max candidates (nodes): {int(max_nodes)}\n"
        f"- max depth: {int(max_depth)}\n"
        f"- closed replacement_class enum: {classes}\n\n"
        f"## Job\n"
        f"Deconstruct THIS target into departments/roles/clusters appropriate to the domain. "
        f"A hospital is not a game studio. Invent 80/20 structure when the target is a short title. "
        f"Every leaf needs replacement_class + oracle_hint.\n"
        f"{feedback}\n"
        f"Respond with a single JSON object only (schema deconstruct.v0).\n"
    )


def extract_json_object(text: str) -> dict[str, Any]:
    """Pull first JSON object from model text (fenced or raw)."""
    raw = (text or "").strip()
    if not raw:
        raise ValueError("empty LLM response")

    # Prefer fenced ```json
    m = _JSON_FENCE_RE.search(raw)
    if m:
        try:
            obj = json.loads(m.group(1))
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            pass

    # Whole string
    try:
        obj = json.loads(raw)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass

    # First { ... last }
    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end > start:
        chunk = raw[start : end + 1]
        try:
            obj = json.loads(chunk)
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError as exc:
            raise ValueError(f"could not parse JSON from LLM response: {exc}") from exc

    raise ValueError("no JSON object found in LLM response")


def doc_from_llm_payload(
    payload: dict[str, Any],
    *,
    target: str,
    mode: str,
    max_nodes: int = DEFAULT_MAX_NODES,
    max_depth: int = DEFAULT_MAX_DEPTH,
    deconstruct_id: str | None = None,
    raw_llm: str = "",
) -> dict[str, Any]:
    """Normalize LLM JSON into a deconstruct.v0 document + critique."""
    m = (mode or str(payload.get("mode") or "open")).strip().lower()
    if m not in MODES:
        m = "open"
    t = (target or str(payload.get("target") or "")).strip()
    if not t:
        raise ValueError("target is required")

    cands_raw = payload.get("candidates")
    if not isinstance(cands_raw, list) or not cands_raw:
        raise ValueError("LLM payload missing non-empty candidates[]")

    cands = [_normalize_candidate(c, index=i) for i, c in enumerate(cands_raw)]
    depts_raw = payload.get("departments")
    depts: list[dict[str, Any]] = []
    if isinstance(depts_raw, list):
        for d in depts_raw:
            if isinstance(d, dict) and d.get("name"):
                depts.append(d)

    title = t.split("\n")[0].strip()
    did = (deconstruct_id or f"{m}_{slugify_target(title)}").strip()
    did = slugify_target(did, max_len=64)

    notes = str(payload.get("notes") or "").strip()
    if not notes:
        notes = "LLM deconstruct proposal — critique then fill classes; not graph.v1"

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
        "notes": notes,
        "needs_structure": False,
        "parse_source": "llm",
        "structure_hint": None,
        "departments": depts,
        "candidates": cands,
        "critique": {},
        "llm_raw_chars": len(raw_llm or ""),
    }
    crit = critique_deconstruct(doc, max_nodes=max_nodes, max_depth=max_depth)
    doc["critique"] = crit
    doc["status"] = "candidate_ok" if crit.get("ok") else "candidate_blocked"
    return doc


def _format_critique_for_retry(crit: dict[str, Any]) -> str:
    issues = crit.get("issues") or []
    lines = [f"- {i.get('code')}: {i.get('detail')}" for i in issues if isinstance(i, dict)]
    return "\n".join(lines) if lines else json.dumps(crit, indent=2)[:2000]


def _chat_llm(
    *,
    system: str,
    user: str,
    provider: str,
    model: str,
    temperature: float,
    request_timeout_s: int,
) -> str:
    from llm_interface import get_llm

    llm = get_llm(
        provider,
        model,
        temperature=temperature,
        think=False,
        num_ctx=8192,
        slug="",
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    resp = llm.chat(messages, tools=None, request_timeout=request_timeout_s)
    return (resp.content or "") if resp is not None else ""


def run_llm_deconstruct(
    target: str,
    *,
    mode: str = "open",
    max_nodes: int = DEFAULT_MAX_NODES,
    max_depth: int = DEFAULT_MAX_DEPTH,
    deconstruct_id: str | None = None,
    provider: str | None = None,
    model: str | None = None,
    temperature: float = 0.4,
    request_timeout_s: int | None = None,
    save: bool = True,
    llm_response: str | None = None,
    llm_caller: Any | None = None,
    max_retries: int = 1,
) -> dict[str, Any]:
    """Call LLM (or inject response) → parse JSON → critique → optional save.

    Parameters
    ----------
    llm_response:
        If set, skip the network LLM call (tests / offline inject).
    llm_caller:
        Optional callable(user_prompt, system_addon='') -> object with .answer
        or str. Used by DeconstructorAgent to reuse call_llm_direct.
    """
    import os

    t = (target or "").strip()
    if not t:
        raise ValueError("target is required")
    m = (mode or "open").strip().lower()
    if m not in MODES:
        raise ValueError(f"mode must be one of {sorted(MODES)}")

    system = load_deconstructor_system_prompt()
    # Keep system prompt bounded for local models (same spirit as planners)
    if len(system) > 6000:
        system = system[:6000] + "\n...(truncated)"

    if request_timeout_s is None:
        try:
            # xAI / cloud may need longer than local; allow both env names
            request_timeout_s = max(
                60,
                int(
                    os.environ.get("DECONSTRUCTOR_LLM_TIMEOUT")
                    or os.environ.get("OLLAMA_PLANNER_TIMEOUT")
                    or "180"
                ),
            )
        except ValueError:
            request_timeout_s = 180

    route_reason = "inject" if llm_response is not None else ""
    if llm_response is None and llm_caller is None:
        from pipeline.llm_route import resolve_pipeline_llm

        provider, model, route_reason = resolve_pipeline_llm(
            provider, model, soft_ollama=True
        )
    else:
        # Still load .env so agent callers see XAI_API_KEY
        try:
            from pipeline.llm_route import ensure_project_dotenv

            ensure_project_dotenv()
        except Exception:
            pass
        if not provider:
            provider = os.environ.get("PIPELINE_PROVIDER", "ollama").strip() or "ollama"
        if not model:
            try:
                from pipeline.pipeline_config import DEFAULT_PIPELINE_MODEL

                model = os.environ.get("PIPELINE_MODEL", "").strip() or DEFAULT_PIPELINE_MODEL
            except Exception:
                model = os.environ.get("PIPELINE_MODEL", "").strip() or "qwen3.6:35b-a3b-q4_K_M"

    feedback = ""
    last_err: Exception | None = None
    doc: dict[str, Any] | None = None

    attempts = max(1, int(max_retries) + 1)
    for attempt in range(attempts):
        user = build_llm_user_prompt(
            t,
            mode=m,
            max_nodes=max_nodes,
            max_depth=max_depth,
            critique_feedback=feedback,
        )
        try:
            if llm_response is not None and attempt == 0:
                raw = llm_response
            elif llm_caller is not None:
                result = llm_caller(user, "")
                if isinstance(result, str):
                    raw = result
                else:
                    raw = str(getattr(result, "answer", None) or result or "")
            else:
                raw = _chat_llm(
                    system=system,
                    user=user,
                    provider=str(provider),
                    model=str(model),
                    temperature=temperature,
                    request_timeout_s=int(request_timeout_s),
                )
            payload = extract_json_object(raw)
            doc = doc_from_llm_payload(
                payload,
                target=t,
                mode=m,
                max_nodes=max_nodes,
                max_depth=max_depth,
                deconstruct_id=deconstruct_id,
                raw_llm=raw,
            )
            doc["llm_provider"] = provider if llm_response is None else "inject"
            doc["llm_model"] = model if llm_response is None else "inject"
            doc["llm_route_reason"] = route_reason
            if (doc.get("critique") or {}).get("ok"):
                break
            feedback = _format_critique_for_retry(doc.get("critique") or {})
            last_err = ValueError(f"critique failed: {feedback}")
            # On inject-only path, do not invent a second response
            if llm_response is not None:
                break
        except Exception as exc:
            last_err = exc
            feedback = f"parse/error: {exc}"
            if llm_response is not None:
                break
            continue

    if doc is None:
        raise ValueError(f"LLM deconstruct failed: {last_err}")

    if save:
        save_deconstruct(doc)
    return doc
