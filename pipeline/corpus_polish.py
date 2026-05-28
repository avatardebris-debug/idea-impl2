"""
pipeline/corpus_polish.py
Wire polish queue / --polish runs to corpus re-collection with lineage refresh.

When the runner queues polish work, projects are tagged with
corpus_force_refresh_on_complete. On the next terminal completion,
collect_project runs with force_refresh=True (bumps corpus_generation).

Usage:
    # Retroactively refresh corpus for polish-queue projects already complete
    python -m pipeline.corpus_collector --collect-polish-queue

    # Or standalone
    python -m pipeline.corpus_polish --collect-complete [--dry-run]
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from pipeline.paths import projects_dir
from pipeline.pipeline_config import PROJECT_ROOT

logger = logging.getLogger(__name__)

CORPUS_REFRESH_FLAG = "corpus_force_refresh_on_complete"
POLISH_NOTES_KEY = "polish_notes"


def resolve_polish_queue_path(polish_path: Path | None = None) -> Path:
    if polish_path is not None:
        return polish_path.resolve()
    return (PROJECT_ROOT / "polish_queue.md").resolve()


def should_force_refresh_corpus(state: dict[str, Any]) -> bool:
    """True when this completion should supersede prior corpus rows."""
    if state.get(CORPUS_REFRESH_FLAG):
        return True
    if state.get(POLISH_NOTES_KEY):
        return True
    return False


def tag_polish_corpus_refresh(state: dict[str, Any]) -> None:
    """Mark state so the next completion re-collects corpus with a new generation."""
    state[CORPUS_REFRESH_FLAG] = True


def _slugify_title(title: str) -> str:
    from pipeline.polish_mode import slugify_title
    return slugify_title(title)


def _queue_entry_slugs(raw_title: str, notes: str, slug_from_title: str) -> set[str]:
    slugs = {slug_from_title, _slugify_title(raw_title)}
    for match in re.finditer(r"\[([^\]]+)\]", notes):
        candidate = match.group(1).strip()
        if candidate:
            slugs.add(candidate)
            slugs.add(_slugify_title(candidate))
    return {s for s in slugs if s and s != "unknown"}


def slug_on_polish_queue(
    project_slug: str,
    polish_path: Path | None = None,
) -> bool:
    """True if an unchecked polish_queue.md entry matches this project slug."""
    from pipeline.polish_mode import _iter_polish_queue_lines

    path = resolve_polish_queue_path(polish_path)
    if not path.exists():
        return False
    for raw_title, notes, slug in _iter_polish_queue_lines(path):
        if project_slug in _queue_entry_slugs(raw_title, notes, slug):
            return True
    return False


def check_off_polish_queue(
    project_slug: str,
    polish_path: Path | None = None,
    *,
    dry_run: bool = False,
) -> bool:
    """Mark matching unchecked queue line as done ([x]). Returns True if updated."""
    from pipeline.polish_mode import _iter_polish_queue_lines

    path = resolve_polish_queue_path(polish_path)
    if not path.exists():
        return False

    lines = path.read_text(encoding="utf-8").splitlines()
    changed = False
    for i, line in enumerate(lines):
        match = re.match(r"- \[ \]\s+\*\*(.+?)\*\*\s*[—–-]\s*(.*)", line)
        if not match:
            continue
        raw_title = match.group(1).strip().strip("[]")
        notes = match.group(2).strip()
        slug = _slugify_title(raw_title)
        if project_slug not in _queue_entry_slugs(raw_title, notes, slug):
            continue
        lines[i] = line.replace("- [ ]", "- [x]", 1)
        changed = True

    if changed and not dry_run:
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return changed


def project_phases_done(state: dict[str, Any]) -> bool:
    phase = int(state.get("phase", 1))
    total = int(state.get("total_phases", 1))
    return phase >= total


def clear_refresh_flag(project_dir: Path, state: dict[str, Any]) -> None:
    if not state.pop(CORPUS_REFRESH_FLAG, None):
        return
    state_path = project_dir / "state" / "current_idea.json"
    try:
        state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except OSError as exc:
        logger.debug("corpus_polish: could not clear refresh flag: %s", exc)


def _maybe_tag_recommend_polish(project_dir: Path, state: dict[str, Any], result) -> None:
    if not result.recommend_polish or result.passed:
        return
    state["corpus_closeout_recommend_polish"] = True
    state_path = project_dir / "state" / "current_idea.json"
    try:
        state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except OSError:
        pass


def collect_on_project_complete(project_dir: Path, state: dict[str, Any]) -> int:
    """
    Called from runner _mark_complete: gate once, then collect corpus.
    """
    from pipeline.corpus_collector import collect_project
    from pipeline.corpus_paths import raw_dir as _raw_dir
    from pipeline.corpus_gate import should_skip_collect
    from pipeline.pipeline_activity import log_activity, maybe_sync_output_repo

    slug = state.get("_slug") or project_dir.name
    force = should_force_refresh_corpus(state)

    blocked, gate_result = should_skip_collect(project_dir, state)
    if blocked:
        if gate_result:
            _maybe_tag_recommend_polish(project_dir, state, gate_result)
        return 0

    gate_passed = gate_result.passed if gate_result else True
    if gate_result:
        _maybe_tag_recommend_polish(project_dir, state, gate_result)

    n = collect_project(
        project_dir,
        state,
        force_refresh=force,
        skip_gate=True,
        gate_passed=gate_passed,
    )

    if n:
        label = "refreshed" if force else "collected"
        print(f"  [corpus] +{n} fine-tune pairs ({label}) -> {_raw_dir()}")
        log_activity(
            "corpus_collected",
            slug=slug,
            pairs_added=n,
            corpus_dir=str(_raw_dir()),
            force_refresh=force,
        )
        maybe_sync_output_repo(f"corpus: {slug} (+{n} pairs)")

    if force:
        clear_refresh_flag(project_dir, state)
        if (
            state.get("status") in ("complete", "budget_exceeded")
            and project_phases_done(state)
            and slug_on_polish_queue(slug)
        ):
            if check_off_polish_queue(slug):
                print(f"  [polish] Checked off '{slug}' in polish_queue.md")

    return n


def collect_polish_queue_complete(
    *,
    polish_path: Path | None = None,
    verbose: bool = True,
    dry_run: bool = False,
    use_continuation: bool = True,
) -> dict[str, int]:
    """
    For each unchecked polish_queue entry whose project is terminal and phases-done,
    force-refresh corpus and check off the queue line.
    """
    from pipeline.corpus_collector import collect_project
    from pipeline.polish_mode import _iter_polish_queue_lines

    path = resolve_polish_queue_path(polish_path)
    results: dict[str, int] = {}

    if not path.exists():
        if verbose:
            print(f"  [corpus-polish] No queue at {path}")
        return results

    seen_slugs: set[str] = set()
    for raw_title, notes, slug in _iter_polish_queue_lines(path):
        project_slug: str | None = None
        for candidate in sorted(_queue_entry_slugs(raw_title, notes, slug)):
            if (projects_dir() / candidate / "state" / "current_idea.json").exists():
                project_slug = candidate
                break
        if not project_slug:
            if verbose:
                print(f"  [corpus-polish] skip '{raw_title}' — no matching project dir")
            continue
        if project_slug in seen_slugs:
            continue
        seen_slugs.add(project_slug)

        project_dir = projects_dir() / project_slug
        state_path = project_dir / "state" / "current_idea.json"
        if not state_path.exists():
            if verbose:
                print(f"  [corpus-polish] skip {project_slug} — no state")
            continue

        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except Exception as exc:
            if verbose:
                print(f"  [corpus-polish] skip {project_slug} — {exc}")
            continue

        status = state.get("status", "")
        if status not in ("complete", "budget_exceeded"):
            if verbose:
                print(
                    f"  [corpus-polish] skip {project_slug} — "
                    f"status={status} (run --polish first)"
                )
            continue

        if not project_phases_done(state):
            if verbose:
                p, t = state.get("phase", 1), state.get("total_phases", 1)
                print(
                    f"  [corpus-polish] skip {project_slug} — "
                    f"phases {p}/{t} not finished"
                )
            continue

        if dry_run:
            if verbose:
                print(f"  [corpus-polish] would refresh {project_slug}")
            results[project_slug] = 0
            continue

        tag_polish_corpus_refresh(state)
        n = collect_project(
            project_dir,
            state,
            force_refresh=True,
            use_continuation=use_continuation,
            skip_gate=False,
        )
        clear_refresh_flag(project_dir, state)
        if check_off_polish_queue(project_slug, path):
            if verbose:
                print(f"  [corpus-polish] checked off {project_slug} in queue")
        results[project_slug] = n
        if verbose:
            print(f"  [corpus-polish] {project_slug}: +{n} records (force_refresh)")

    if verbose:
        total = sum(results.values())
        print(f"\n  [corpus-polish] Done. {len(results)} project(s), {total} new record(s).")
    return results


def _cli() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Polish queue → corpus refresh helpers")
    parser.add_argument(
        "--collect-complete",
        action="store_true",
        help="Force-refresh corpus for polish-queue projects that are fully complete",
    )
    parser.add_argument("--polish-queue", default=None, metavar="PATH")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-continuation", action="store_true")
    args = parser.parse_args()

    if not args.collect_complete:
        parser.print_help()
        return

    pq = Path(args.polish_queue) if args.polish_queue else None
    collect_polish_queue_complete(
        polish_path=pq,
        dry_run=args.dry_run,
        use_continuation=not args.no_continuation,
    )


if __name__ == "__main__":
    _cli()
