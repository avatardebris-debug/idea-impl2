"""
pipeline/ideas_sync.py
Completion truth for the idea pipeline.

Source of truth (in order):
  1. .pipeline/state/completions.jsonl  — machine registry
  2. truth.md                           — human-readable list (project root)
  3. .pipeline/projects/*/state         — status == complete

master_ideas.md is your working queue (copy/paste from backup).
Before seeding, completed names are REMOVED from master_ideas.md — not checked [x].
"""

from __future__ import annotations

import json
import pathlib
import re
from datetime import datetime, timezone

from pipeline.pipeline_config import PROJECT_ROOT as _PROJECT_ROOT, get_pipeline_dir

TRUTH_PATH = _PROJECT_ROOT / "truth.md"


def _projects_dir() -> pathlib.Path:
    return get_pipeline_dir() / "projects"


def _completions_path() -> pathlib.Path:
    return get_pipeline_dir() / "state" / "completions.jsonl"

_MAX_DESC = 2000

_TRUTH_HEADER = """# Pipeline completions (source of truth)

`master_ideas.md` is your working queue — copy and paste from backup freely.
Before the runner seeds a new project, any idea listed here is **removed** from
`master_ideas.md` automatically.

Full records (including description) live in `.pipeline/state/completions.jsonl`.
Each entry below: `- slug — title — completed_at` then an indented description line.

**Not listed here:** `budget_exceeded` projects — they stay in `master_ideas.md`.
Use `python reset_budget_exceeded.py` to retry them (does not touch this file).

"""

# Idea lines: checked or unchecked
_IDEA_LINE = re.compile(
    r"^(-?\s*)\[([ xX])\]\s+"
    r"(?:\*\*)?"
    r"(?:\[)?(.+?)(?:\])?"
    r"(?:\*\*)?"
    r"\s*[—–-]\s*",
)


def slugify(title: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", title.lower())
    slug = re.sub(r"[\s_-]+", "_", slug)
    return slug.strip("_") or "unknown"


def normalize_title(title: str) -> str:
    return title.strip().strip("[]").strip().lower()


def _parse_truth_line(line: str) -> tuple[str, str] | None:
    """Parse `- slug — title — iso` or `- slug — title`."""
    line = line.strip()
    if not line.startswith("- ") or line.startswith("#"):
        return None
    body = line[2:].strip()
    parts = [p.strip() for p in re.split(r"\s+[—–-]\s+", body) if p.strip()]
    if len(parts) >= 2:
        return parts[0], parts[1]
    if len(parts) == 1:
        t = parts[0]
        return slugify(t), t
    return None


def collect_complete_slugs(projects_dir: pathlib.Path | None = None) -> dict[str, str]:
    """Only status=complete — never budget_exceeded or in-progress."""
    return {s: r["title"] for s, r in collect_completion_records(projects_dir).items()}


def collect_completion_records(projects_dir: pathlib.Path | None = None) -> dict[str, dict]:
    """
    Full completion records keyed by slug.
    Merges live complete projects, completions.jsonl, and truth.md bullets.
    """
    records: dict[str, dict] = {}
    root = projects_dir or _projects_dir()

    if root.exists():
        for proj in root.iterdir():
            if not proj.is_dir():
                continue
            stf = proj / "state" / "current_idea.json"
            if not stf.exists():
                continue
            try:
                data = json.loads(stf.read_text(encoding="utf-8"))
            except Exception:
                continue
            if data.get("status") != "complete":
                continue
            slug = data.get("_slug") or proj.name
            records[slug] = {
                "slug": slug,
                "title": data.get("title", proj.name),
                "description": (data.get("description") or "")[:_MAX_DESC],
                "completed_at": data.get("completed_at", ""),
                "workspace": str(proj / "workspace"),
            }

    if _completions_path().exists():
        try:
            for line in _completions_path().read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                slug = rec.get("slug", "")
                if not slug:
                    continue
                if slug not in records:
                    records[slug] = rec
                else:
                    if rec.get("description") and not records[slug].get("description"):
                        records[slug]["description"] = rec["description"]
                    if rec.get("completed_at"):
                        records[slug]["completed_at"] = rec["completed_at"]
        except OSError:
            pass

    if TRUTH_PATH.exists():
        try:
            lines = TRUTH_PATH.read_text(encoding="utf-8").splitlines()
            i = 0
            while i < len(lines):
                parsed = _parse_truth_line(lines[i])
                if parsed:
                    slug, title = parsed
                    desc = ""
                    if i + 1 < len(lines) and lines[i + 1].strip().startswith("desc:"):
                        desc = lines[i + 1].strip()[5:].strip()
                        i += 1
                    if slug not in records:
                        records[slug] = {
                            "slug": slug,
                            "title": title,
                            "description": desc,
                            "completed_at": "",
                        }
                i += 1
        except OSError:
            pass

    return records


def load_completions_registry(projects_dir: pathlib.Path | None = None) -> dict[str, str]:
    """Slug → title for trim logic (complete only)."""
    return {s: r.get("title", s) for s, r in collect_completion_records(projects_dir).items()}


def get_completion(slug: str, projects_dir: pathlib.Path | None = None) -> dict | None:
    """Lookup one finished project (description, title, workspace path)."""
    return collect_completion_records(projects_dir).get(slug)


def extract_idea_title(line: str) -> str | None:
    """Extract idea title from a master_ideas queue line (any checkbox state)."""
    m = _IDEA_LINE.match(line)
    if m:
        return m.group(3).strip()
    # Bold format without checkbox: `- **Title** —`
    m2 = re.match(r"^- \[[ xX]\]\s+\*\*(.+?)\*\*\s*[—–-]", line)
    if m2:
        return m2.group(1).strip()
    m3 = re.match(r"^- \[[ xX]\]\s+\*\*\[(.+?)\]\*\*\s*[—–-]", line)
    if m3:
        return m3.group(1).strip()
    return None


def _is_line_completed(line: str, registry: dict[str, str]) -> bool:
    title = extract_idea_title(line)
    if not title:
        return False
    slug = slugify(title)
    if slug in registry:
        return True
    nt = normalize_title(title)
    for s, t in registry.items():
        if normalize_title(t) == nt or normalize_title(s) == nt:
            return True
    return False


def trim_completed_from_master_ideas(
    ideas_path: pathlib.Path,
    *,
    projects_dir: pathlib.Path | None = None,
    dry_run: bool = False,
    verbose: bool = True,
) -> int:
    """
    Remove queue lines from master_ideas.md that are already in the completion registry.
    Called before seeding so a pasted backup file is auto-cleaned.
    """
    if not ideas_path.exists():
        if verbose:
            print(f"  [truth] skip trim — not found: {ideas_path}")
        return 0

    registry = load_completions_registry(projects_dir)
    if not registry:
        if verbose:
            print("  [truth] no completions in registry — nothing to trim")
        return 0

    content = ideas_path.read_text(encoding="utf-8")
    lines = content.splitlines()
    kept: list[str] = []
    removed: list[str] = []

    for line in lines:
        if _is_line_completed(line, registry):
            title = extract_idea_title(line) or "?"
            removed.append(title[:60])
        else:
            kept.append(line)

    if not removed:
        if verbose:
            print(f"  [truth] 0 completed ideas to trim from {ideas_path.name}")
        return 0

    if verbose:
        for t in removed[:12]:
            print(f"  [truth] trim: {t}")
        if len(removed) > 12:
            print(f"  [truth] ... +{len(removed) - 12} more")

    if not dry_run:
        new_content = "\n".join(kept)
        if content.endswith("\n"):
            new_content += "\n"
        ideas_path.write_text(new_content, encoding="utf-8")
        if verbose:
            print(f"  [truth] removed {len(removed)} line(s) from {ideas_path.name}")

    return len(removed)


def _append_truth_entry(
    slug: str,
    title: str,
    completed_at: str,
    description: str = "",
) -> None:
    if not TRUTH_PATH.exists():
        TRUTH_PATH.write_text(_TRUTH_HEADER, encoding="utf-8")
    try:
        body = TRUTH_PATH.read_text(encoding="utf-8")
        if f"- {slug} " in body:
            return
    except OSError:
        body = ""
    block = f"- {slug} — {title} — {completed_at}\n"
    desc = (description or "").strip()
    if desc:
        one_line = " ".join(desc.split())
        if len(one_line) > 500:
            one_line = one_line[:497] + "..."
        block += f"  desc: {one_line}\n"
    try:
        with TRUTH_PATH.open("a", encoding="utf-8") as f:
            f.write(block)
    except OSError:
        pass


def register_completion(
    slug: str,
    title: str,
    description: str = "",
    *,
    workspace: str = "",
) -> None:
    """Append to completions.jsonl (idempotent per slug). Includes description for revisit."""
    _completions_path().parent.mkdir(parents=True, exist_ok=True)
    slug = slug.strip()
    title = title.strip()
    description = (description or "").strip()[:_MAX_DESC]
    if not slug:
        return
    try:
        if _completions_path().exists():
            for line in _completions_path().read_text(encoding="utf-8").splitlines()[-500:]:
                if not line.strip():
                    continue
                try:
                    if json.loads(line).get("slug") == slug:
                        return
                except json.JSONDecodeError:
                    continue
    except OSError:
        pass
    completed_at = datetime.now(timezone.utc).isoformat()
    record = {
        "slug": slug,
        "title": title,
        "description": description,
        "completed_at": completed_at,
        "workspace": workspace,
    }
    with _completions_path().open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    _append_truth_entry(slug, title, completed_at, description)


def record_completion(
    slug: str,
    title: str,
    ideas_path: pathlib.Path | None = None,
    description: str = "",
    *,
    workspace: str = "",
) -> int:
    """
    On project complete: register truth + remove from master_ideas queue.
    Does NOT run for budget_exceeded — only caller _mark_complete (status=complete).
    """
    register_completion(slug, title, description, workspace=workspace)
    mi = ideas_path or (_PROJECT_ROOT / "master_ideas.md")
    if mi.exists():
        return trim_completed_from_master_ideas(mi, verbose=False)
    return 0


def prepare_master_ideas_for_seed(
    ideas_path: pathlib.Path,
    *,
    projects_dir: pathlib.Path | None = None,
    verbose: bool = True,
) -> int:
    """Call before seed_from_master_list — trim completed from working queue."""
    return trim_completed_from_master_ideas(
        ideas_path, projects_dir=projects_dir, verbose=verbose,
    )


# Legacy alias used by extract.py --sync-ideas
def sync_master_ideas(
    ideas_path: pathlib.Path,
    *,
    projects_dir: pathlib.Path | None = None,
    dry_run: bool = False,
    verbose: bool = True,
) -> int:
    return trim_completed_from_master_ideas(
        ideas_path, projects_dir=projects_dir, dry_run=dry_run, verbose=verbose,
    )


def rebuild_truth_from_registry(projects_dir: pathlib.Path | None = None) -> int:
    """Regenerate truth.md from registry (e.g. after import or manual jsonl edit)."""
    records = collect_completion_records(projects_dir)
    lines = [_TRUTH_HEADER.rstrip(), ""]
    for slug in sorted(records.keys()):
        rec = records[slug]
        title = rec.get("title", slug)
        completed_at = rec.get("completed_at", "")
        lines.append(f"- {slug} — {title} — {completed_at}")
        desc = (rec.get("description") or "").strip()
        if desc:
            one_line = " ".join(desc.split())
            if len(one_line) > 500:
                one_line = one_line[:497] + "..."
            lines.append(f"  desc: {one_line}")
    TRUTH_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Refresh completions.jsonl from project state (full descriptions)
    _completions_path().parent.mkdir(parents=True, exist_ok=True)
    with _completions_path().open("w", encoding="utf-8") as f:
        for slug in sorted(records.keys()):
            rec = records[slug]
            row = {
                "slug": slug,
                "title": rec.get("title", slug),
                "description": (rec.get("description") or "")[:_MAX_DESC],
                "completed_at": rec.get("completed_at") or "",
                "workspace": rec.get("workspace", ""),
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    return len(records)
