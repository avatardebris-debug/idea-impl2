"""
reporter.py — Assembles the final unweb Markdown report.

Sections:
  1. Story Summary
  2. People Map (table: name | role | org | connections)
  3. Organization Map (table: name | type | funders | parent)
  4. Connection Graph (edge list)
  5. 🚩 Red Flags
  6. Raw JSON (collapsible)
"""
from __future__ import annotations
from datetime import datetime, timezone


def build_report(graph: dict, source: str = "") -> str:
    now        = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    summary    = graph.get("story_summary", "")
    people     = graph.get("people", [])
    orgs       = graph.get("orgs", [])
    conns      = graph.get("connections", [])
    red_flags  = graph.get("red_flags", [])
    meta       = graph.get("metadata", {})

    lines = [
        "# 🕸️ unweb — Connection Report",
        "",
        f"> **Source:** {source or 'direct input'}  ",
        f"> **Generated:** {now}  ",
        f"> **Entities:** {len(people)} people · {len(orgs)} orgs · {len(conns)} connections  ",
        "",
        "---",
        "",
        "## Story Summary",
        "",
        summary or "_No summary available._",
        "",
        "---",
        "",
    ]

    # People table
    lines += ["## 👤 People Map", ""]
    if people:
        lines += ["| Name | Role | Organization | Notable Connections |",
                  "|---|---|---|---|"]
        for p in people:
            conns_str = "; ".join(p.get("connections", []))[:80]
            lines.append(
                f"| **{p.get('name','')}** | {p.get('role','')} | "
                f"{p.get('org','')} | {conns_str} |"
            )
        lines.append("")
        # Wiki backgrounds
        for p in people:
            wiki = p.get("wiki_summary", "")
            if wiki:
                lines += [f"**{p['name']}:** {wiki[:300]}", ""]
    else:
        lines += ["_No people identified._", ""]

    lines += ["---", ""]

    # Orgs table
    lines += ["## 🏢 Organization Map", ""]
    if orgs:
        lines += ["| Organization | Type | Parent | Known Funders |",
                  "|---|---|---|---|"]
        for o in orgs:
            funders_str = ", ".join(o.get("funders", []))[:80]
            lines.append(
                f"| **{o.get('name','')}** | {o.get('type','')} | "
                f"{o.get('parent','')} | {funders_str} |"
            )
        lines.append("")
        for o in orgs:
            wiki = o.get("wiki_summary", "")
            if wiki:
                lines += [f"**{o['name']}:** {wiki[:300]}", ""]
    else:
        lines += ["_No organizations identified._", ""]

    lines += ["---", ""]

    # Connection graph
    lines += ["## 🔗 Connection Graph", ""]
    if conns:
        for c in conns:
            rel  = c.get("relation", "→")
            ev   = c.get("evidence", "")
            ev_s = f"  *(evidence: {ev[:120]})*" if ev else ""
            lines.append(f"- **{c.get('from','')}** `{rel}` **{c.get('to','')}**{ev_s}")
        lines.append("")
    else:
        lines += ["_No explicit connections extracted._", ""]

    lines += ["---", ""]

    # Red flags
    lines += ["## 🚩 Red Flags", ""]
    if red_flags:
        for rf in red_flags:
            lines.append(f"- {rf}")
        lines.append("")
    else:
        lines += ["_No red flags identified._", ""]

    lines += ["---", "", "<details>", "<summary>Raw JSON</summary>", ""]
    import json
    lines += ["```json", json.dumps(graph, indent=2, ensure_ascii=False)[:8000], "```", "",
              "</details>", ""]

    return "\n".join(lines)


def save_report(report: str, path: str) -> None:
    import pathlib
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(report, encoding="utf-8")
    print(f"  Report saved to {p}")
