"""
pipeline/connector_synthesis.py
Turn ideator COMBINATION / BRIDGE ideas into .pipeline/workflows/connectors/*.yaml
and enrich master_ideas lines with kind:connector requires: ...
"""

from __future__ import annotations

import json
import pathlib
import re
from datetime import datetime, timezone
from typing import Any

import yaml

from pipeline.pipeline_config import PROJECT_ROOT  # noqa: F401
from pipeline.paths import connectors_dir, get_pipeline_dir
from pipeline.slug_util import slugify_title
IDEA_LINE_RE = re.compile(
    r"^\s*-\s*\[[ xX]\]\s*\*\*(.+?)\*\*\s*(?:kind:\s*connector\s*)?"
    r"(?:requires:\s*([\w,\s_-]+?)\s*)?[—–-]\s*(.+)$",
    re.IGNORECASE,
)
GROUP_HEADER_RE = re.compile(
    r"GROUP\s+(?P<num>[1-6])\s*[—–-]\s*(?P<label>[^\n]+)",
    re.IGNORECASE,
)


def _known_project_slugs() -> dict[str, str]:
    """slug -> display title from .pipeline/projects."""
    out: dict[str, str] = {}
    projects = get_pipeline_dir() / "projects"
    if not projects.exists():
        return out
    for d in projects.iterdir():
        if not d.is_dir():
            continue
        slug = d.name
        title = slug.replace("_", " ")
        state_file = d / "state" / "current_idea.json"
        if state_file.exists():
            try:
                state = json.loads(state_file.read_text(encoding="utf-8"))
                title = str(state.get("title", title)).strip("[] ")
            except Exception:
                pass
        out[slug] = title
    return out


def _parse_title_and_desc(line: str) -> tuple[str, str, list[str]]:
    """Return (title, description, existing_requires)."""
    m = IDEA_LINE_RE.match(line.strip())
    if not m:
        return "", "", []
    title = m.group(1).strip()
    existing_req = m.group(2) or ""
    desc = (m.group(3) or "").strip()
    reqs = [r.strip() for r in re.split(r"[,;]+", existing_req) if r.strip()]
    return title, desc, reqs


def parse_ideator_groups(raw_text: str) -> list[dict[str, Any]]:
    """Parse LLM output into grouped idea records."""
    current_group = "unknown"
    items: list[dict[str, Any]] = []

    for line in raw_text.splitlines():
        gh = GROUP_HEADER_RE.search(line)
        if gh:
            label = (gh.group("label") or "").upper()
            num = gh.group("num")
            if num == "5" or "AGENTIC" in label or ("BRIDGE" in label and "AGENTIC" not in label):
                current_group = "agentic" if "AGENTIC" in label else "bridge"
            elif num == "4" or "LEARNING" in label or "RSI" in label:
                current_group = "learning"
            elif num == "3" or "SPEED" in label or "EFFICI" in label:
                current_group = "speed"
            elif num == "2" or "DEBUG" in label or "QUALITY" in label:
                current_group = "debug"
            elif num == "1" or "PIPELINE" in label:
                current_group = "pipeline_core"
            elif num == "6" or "EXPERIMENT" in label:
                current_group = "experiment"
            elif "COMBINATION" in label:
                current_group = "combination"
            elif "BRIDGE" in label:
                current_group = "bridge"
            elif "HARNESS" in label:
                current_group = "harness"
            elif "INDEPENDENT" in label:
                current_group = "independent"
            elif "EXPANSION" in label:
                current_group = "expansion"
            elif "SIMILAR" in label:
                current_group = "similar"
            continue

        if not re.match(r"^\s*-\s*\[[ xX]\]", line):
            continue
        title, desc, reqs = _parse_title_and_desc(line)
        if not title:
            continue
        items.append(
            {
                "group": current_group,
                "title": title,
                "description": desc,
                "requires": reqs,
                "line": line.strip(),
            }
        )
    return items


def resolve_slugs_from_text(text: str, known: dict[str, str]) -> list[str]:
    """Match project slugs mentioned in ideator title/description."""
    lower = text.lower()
    found: list[str] = []

    # Explicit requires: or slugs: in text
    for pat in (
        r"\brequires:\s*([\w,\s_-]+)",
        r"\bslugs?:\s*([\w,\s_-]+)",
        r"\bprojects?:\s*([\w,\s_-]+)",
        r"\bcombines?\s+([\w,\s_-]+)",
    ):
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            for part in re.split(r"[,;]+", m.group(1)):
                s = slugify_title(part.strip())
                if s in known and s not in found:
                    found.append(s)

    # Substring match on slug and title tokens
    for slug, title in sorted(known.items(), key=lambda x: -len(x[0])):
        if slug in lower or slug.replace("_", " ") in lower:
            if slug not in found:
                found.append(slug)
            continue
        # Title words (3+ chars)
        title_tokens = [t for t in re.split(r"\W+", title.lower()) if len(t) >= 4]
        if sum(1 for t in title_tokens if t in lower) >= 2:
            if slug not in found:
                found.append(slug)

    return found[:6]


def _connector_slug(title: str, slugs: list[str]) -> str:
    base = slugify_title(title)
    if len(slugs) >= 2:
        base = f"bridge_{slugs[0]}_{slugs[1]}"
    elif slugs:
        base = f"bridge_{slugs[0]}_{base}"
    else:
        base = f"bridge_{base}"
    return base[:58].strip("_")


def _yaml_for_connector(
    *,
    slug: str,
    title: str,
    purpose: str,
    requires: list[str],
    group: str,
    source_line: str,
) -> dict[str, Any]:
    steps: list[dict[str, Any]] = []
    for i, req in enumerate(requires):
        step: dict[str, Any] = {
            "id": req if len(req) <= 32 else f"step_{i + 1}",
            "type": "capability",
            "capability": req,
            "args": "--help",
            "save_as": req,
        }
        if i > 0:
            step["when"] = f"{{{{ steps.{requires[i - 1]}.ok }}}}"
        steps.append(step)

    if not steps:
        steps = [
            {
                "id": "placeholder",
                "type": "shell",
                "command": f"python scripts/run_workflow.py {slug} --force",
                "save_as": "placeholder",
            }
        ]

    group_note = "combination product scaffold" if group == "combination" else "integration bridge"
    return {
        "slug": slug,
        "title": title,
        "kind": "connector",
        "status": "draft",
        "backend": "native",
        "purpose": (
            f"{purpose}\n\n"
            f"Auto-generated from ideator ({group_note}). "
            f"Source: {source_line[:200]}"
        ).strip(),
        "domains": ["devops"],
        "requires": requires,
        "steps": steps,
    }


def enrich_master_idea_line(line: str, requires: list[str], connector_slug: str) -> str:
    """Add kind:connector, requires:, and connector: slug to a master_ideas line."""
    title, desc, _ = _parse_title_and_desc(line)
    if not title:
        return line
    # Strip duplicate metadata from description
    desc = re.sub(r"\bkind:\s*connector\b", "", desc, flags=re.I).strip()
    desc = re.sub(r"\brequires:\s*[\w,\s_-]+", "", desc, flags=re.I).strip()
    desc = re.sub(r"\bconnector:\s*[\w_-]+", "", desc, flags=re.I).strip()
    desc = desc.strip(" .")
    req_part = f"requires: {', '.join(requires)}" if requires else ""
    meta = "kind:connector"
    if req_part:
        meta += f" {req_part}"
    meta += f" connector: {connector_slug}"
    return f"- [ ] **{title}** {meta} — {desc}"


def synthesize_connectors_from_ideas(
    grouped_ideas: list[dict[str, Any]],
    *,
    groups: tuple[str, ...] = ("bridge", "combination", "agentic"),
) -> dict[str, Any]:
    """Write connector YAML for bridge/combination ideas; return summary."""
    known = _known_project_slugs()
    connectors_dir().mkdir(parents=True, exist_ok=True)

    written: list[str] = []
    skipped: list[str] = []
    enriched_lines: dict[str, str] = {}  # original line -> enriched line

    for item in grouped_ideas:
        group = item.get("group", "")
        if group not in groups:
            continue

        title = item["title"]
        desc = item.get("description", "")
        line = item.get("line", "")
        blob = f"{title} {desc} {line}"

        requires = list(item.get("requires") or [])
        if len(requires) < 2:
            requires = resolve_slugs_from_text(blob, known)
        if item.get("requires"):
            requires = list(dict.fromkeys(list(item["requires"]) + requires))
        requires = list(dict.fromkeys(requires))

        slug = _connector_slug(title, requires)
        path = connectors_dir() / f"{slug}.yaml"
        if path.exists():
            skipped.append(slug)
            enriched_lines[line] = enrich_master_idea_line(line, requires, slug)
            continue

        doc = _yaml_for_connector(
            slug=slug,
            title=title,
            purpose=desc or f"Connect {' + '.join(requires) if requires else 'projects'}",
            requires=requires,
            group=group,
            source_line=line,
        )
        path.write_text(
            yaml.safe_dump(doc, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        written.append(slug)
        enriched_lines[line] = enrich_master_idea_line(line, requires, slug)

    # Register into capability registry if available
    registered = 0
    try:
        from pipeline.pipeline_mode import legacy_mode

        if not legacy_mode():
            from pipeline.workflow_registry import register_workflows

            registered = register_workflows()
    except Exception:
        pass

    return {
        "written": written,
        "skipped": skipped,
        "enriched_lines": enriched_lines,
        "registered": registered,
    }


def process_ideator_generation(raw_text: str, idea_lines: list[str]) -> tuple[list[str], dict[str, Any]]:
    """Parse groups, synthesize connectors, return updated idea lines + summary."""
    grouped = parse_ideator_groups(raw_text)
    summary = synthesize_connectors_from_ideas(grouped)

    if not summary["enriched_lines"]:
        return idea_lines, summary

    updated: list[str] = []
    for line in idea_lines:
        updated.append(summary["enriched_lines"].get(line.strip(), line))
    return updated, summary


def write_synthesis_log(summary: dict[str, Any], ts: str) -> pathlib.Path:
    from pipeline.paths import state_dir

    log_dir = state_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    path = log_dir / f"connector_synthesis_{ts}.md"
    lines = [
        f"# Connector synthesis — {ts}",
        "",
        f"Written: {len(summary.get('written', []))}",
        f"Skipped (exists): {len(summary.get('skipped', []))}",
        "",
    ]
    for s in summary.get("written", []):
        lines.append(f"- created `{s}.yaml`")
    for s in summary.get("skipped", []):
        lines.append(f"- skipped existing `{s}.yaml`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
