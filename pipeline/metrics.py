"""
pipeline/metrics.py
Pipeline run metrics collection and prompt versioning.

Tracks per-run stats (retry rates, stall rates, tokens, costs) and
snapshots prompts with diffs from baseline for manual review.

Usage:
    from pipeline.metrics import RunMetrics
    metrics = RunMetrics.start(provider="ollama", model="qwen3.6:35b")
    metrics.record_project_complete(slug, phases, retries, tokens)
    metrics.record_project_stalled(slug, reason)
    metrics.finish()  # writes summary + snapshot
"""

from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
from datetime import datetime, timezone
from dataclasses import dataclass, field

PROJECT_ROOT = pathlib.Path(__file__).parent.parent
PROMPTS_DIR = PROJECT_ROOT / "pipeline" / "prompts"
from pipeline.pipeline_config import get_pipeline_dir


def _versions_dir() -> pathlib.Path:
    return get_pipeline_dir() / "prompt_versions"


def _metrics_dir() -> pathlib.Path:
    return get_pipeline_dir() / "metrics"


# ---------------------------------------------------------------------------
# Prompt versioning
# ---------------------------------------------------------------------------

def _next_version() -> str:
    """Return next version string like 'v001', 'v002', etc."""
    _versions_dir().mkdir(parents=True, exist_ok=True)
    existing = sorted(p.name for p in _versions_dir().iterdir() if p.is_dir() and p.name.startswith("v"))
    if not existing:
        return "v001"
    last_num = int(existing[-1][1:])
    return f"v{last_num + 1:03d}"


def snapshot_prompts(changelog: str = "") -> str:
    """Save a versioned snapshot of the current prompt files.

    Returns the version string (e.g. 'v002').
    """
    version = _next_version()
    dest = _versions_dir() / version
    dest.mkdir(parents=True, exist_ok=True)

    # Copy all prompt files
    for f in PROMPTS_DIR.glob("*.md"):
        shutil.copy2(f, dest / f.name)

    # Also snapshot constitution.yaml
    const_path = PROJECT_ROOT / "constitution.yaml"
    if const_path.exists():
        shutil.copy2(const_path, dest / "constitution.yaml")

    # Generate diff from v001 baseline (if not the first version)
    if version != "v001":
        baseline_dir = _versions_dir() / "v001"
        if baseline_dir.exists():
            _generate_diff(baseline_dir, dest, dest / "diff_from_baseline.patch")

    # Write changelog
    meta = {
        "version": version,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "changelog": changelog,
        "files": [f.name for f in dest.glob("*.md")],
    }
    (dest / "metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    return version


def _generate_diff(baseline_dir: pathlib.Path, current_dir: pathlib.Path,
                   output_path: pathlib.Path) -> None:
    """Generate a unified diff between two prompt directories."""
    diffs = []
    all_baseline_files = sorted(list(baseline_dir.glob("*.md")) + list(baseline_dir.glob("*.yaml")))
    for f in all_baseline_files:
        current_f = current_dir / f.name
        if not current_f.exists():
            diffs.append(f"--- {f.name} (DELETED)\n")
            continue

        old_lines = f.read_text(encoding="utf-8").splitlines(keepends=True)
        new_lines = current_f.read_text(encoding="utf-8").splitlines(keepends=True)

        if old_lines != new_lines:
            import difflib
            diff = difflib.unified_diff(old_lines, new_lines,
                                        fromfile=f"baseline/{f.name}",
                                        tofile=f"current/{f.name}")
            diffs.extend(diff)

    # Check for new files not in baseline
    all_current_files = sorted(list(current_dir.glob("*.md")) + list(current_dir.glob("*.yaml")))
    for f in all_current_files:
        if not (baseline_dir / f.name).exists():
            diffs.append(f"+++ {f.name} (NEW)\n")

    if diffs:
        output_path.write_text("".join(diffs), encoding="utf-8")


def get_current_version() -> str | None:
    """Return the latest version string, or None if no snapshots exist."""
    _versions_dir().mkdir(parents=True, exist_ok=True)
    existing = sorted(p.name for p in _versions_dir().iterdir() if p.is_dir() and p.name.startswith("v"))
    return existing[-1] if existing else None


# ---------------------------------------------------------------------------
# Run metrics
# ---------------------------------------------------------------------------

@dataclass
class ProjectMetric:
    slug: str
    status: str = "in_progress"   # complete | stalled | in_progress
    phases_completed: int = 0
    tasks_completed: int = 0       # checkboxes marked [x] across all phases
    total_retries: int = 0
    validator_retries: int = 0
    tokens_used: int = 0
    stall_tokens: int = 0          # tokens burned during 0-task stall periods
    wall_clock_seconds: float = 0
    stall_reason: str = ""


@dataclass
class RunMetrics:
    """Collects metrics for a single pipeline run."""

    run_id: str = ""
    provider: str = ""
    model: str = ""
    prompt_version: str = ""
    started_at: str = ""
    finished_at: str = ""
    projects: dict[str, ProjectMetric] = field(default_factory=dict)

    @classmethod
    def start(cls, provider: str = "", model: str = "") -> "RunMetrics":
        """Start a new metrics collection run."""
        now = datetime.now(timezone.utc)
        run_id = now.strftime("%Y%m%d_%H%M%S")

        # Get or create prompt version
        version = get_current_version()
        if not version:
            version = snapshot_prompts("Initial baseline snapshot")

        return cls(
            run_id=run_id,
            provider=provider,
            model=model,
            prompt_version=version,
            started_at=now.isoformat(),
        )

    def record_project_start(self, slug: str) -> None:
        if slug not in self.projects:
            self.projects[slug] = ProjectMetric(slug=slug)

    def record_project_complete(self, slug: str, phases: int = 0,
                                 retries: int = 0, tokens: int = 0) -> None:
        pm = self.projects.setdefault(slug, ProjectMetric(slug=slug))
        pm.status = "complete"
        pm.phases_completed = phases
        pm.total_retries = retries
        pm.tokens_used = tokens

    def record_project_stalled(self, slug: str, reason: str = "") -> None:
        pm = self.projects.setdefault(slug, ProjectMetric(slug=slug))
        pm.status = "stalled"
        pm.stall_reason = reason

    def record_retry(self, slug: str, retry_type: str = "validator") -> None:
        pm = self.projects.setdefault(slug, ProjectMetric(slug=slug))
        pm.total_retries += 1
        if retry_type == "validator":
            pm.validator_retries += 1

    def record_tokens(self, slug: str, tokens: int) -> None:
        pm = self.projects.setdefault(slug, ProjectMetric(slug=slug))
        pm.tokens_used += tokens

    def record_task_complete(self, slug: str, count: int = 1) -> None:
        """Record N tasks marked [x] for a project (called by runner task-count monitor)."""
        pm = self.projects.setdefault(slug, ProjectMetric(slug=slug))
        pm.tasks_completed += count

    def record_stall_tokens(self, slug: str, tokens: int) -> None:
        """Record tokens burned while the executor was in a 0-task stall period."""
        pm = self.projects.setdefault(slug, ProjectMetric(slug=slug))
        pm.stall_tokens += tokens
        pm.tokens_used += tokens

    def finish(self) -> pathlib.Path:
        """Finalize metrics and write summary to disk. Returns path to summary."""
        self.finished_at = datetime.now(timezone.utc).isoformat()

        run_dir = _metrics_dir() / self.run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        # Aggregate stats
        completed = [p for p in self.projects.values() if p.status == "complete"]
        stalled = [p for p in self.projects.values() if p.status == "stalled"]
        all_projects = list(self.projects.values())

        total_retries = sum(p.total_retries for p in all_projects)
        total_tokens = sum(p.tokens_used for p in all_projects)
        total_tasks  = sum(p.tasks_completed for p in all_projects)
        total_stall_tokens = sum(p.stall_tokens for p in all_projects)

        # Key efficiency metrics
        useful_tok_per_task = total_tokens / max(total_tasks, 1)
        retry_waste_rate    = total_stall_tokens / max(total_tokens, 1)

        summary = {
            "run_id": self.run_id,
            "provider": self.provider,
            "model": self.model,
            "prompt_version": self.prompt_version,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "projects_total": len(all_projects),
            "projects_completed": len(completed),
            "projects_stalled": len(stalled),
            "stall_rate": len(stalled) / max(len(all_projects), 1),
            "total_retries": total_retries,
            "avg_retries_per_project": total_retries / max(len(all_projects), 1),
            "total_tokens": total_tokens,
            "total_tasks_completed": total_tasks,
            "useful_tok_per_task": round(useful_tok_per_task, 1),
            "stall_tokens": total_stall_tokens,
            "retry_waste_rate": round(retry_waste_rate, 4),
            "avg_tokens_per_project": total_tokens / max(len(all_projects), 1),
            "per_project": {
                slug: {
                    "status": pm.status,
                    "phases_completed": pm.phases_completed,
                    "tasks_completed": pm.tasks_completed,
                    "total_retries": pm.total_retries,
                    "validator_retries": pm.validator_retries,
                    "tokens_used": pm.tokens_used,
                    "stall_tokens": pm.stall_tokens,
                    "useful_tok_per_task": round(
                        pm.tokens_used / max(pm.tasks_completed, 1), 1
                    ),
                    "stall_reason": pm.stall_reason,
                }
                for slug, pm in self.projects.items()
            },
        }

        # Write JSON summary
        summary_path = run_dir / "summary.json"
        summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

        # Write human-readable report
        report_lines = [
            f"# Pipeline Run Report — {self.run_id}",
            f"",
            f"- **Provider**: {self.provider}",
            f"- **Model**: {self.model}",
            f"- **Prompt Version**: {self.prompt_version}",
            f"- **Started**: {self.started_at}",
            f"- **Finished**: {self.finished_at}",
            f"",
            f"## Summary",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Projects Total | {len(all_projects)} |",
            f"| Completed | {len(completed)} |",
            f"| Stalled | {len(stalled)} |",
            f"| Stall Rate | {summary['stall_rate']:.1%} |",
            f"| Total Retries | {total_retries} |",
            f"| Avg Retries/Project | {summary['avg_retries_per_project']:.1f} |",
            f"| Total Tokens | {total_tokens:,} |",
            f"| Tasks Completed | {total_tasks:,} |",
            f"| **Useful Tok/Task** | **{useful_tok_per_task:,.0f}** |",
            f"| Stall Tokens Wasted | {total_stall_tokens:,} ({retry_waste_rate:.1%} of total) |",
            f"",
            f"## Per-Project Breakdown",
            f"| Project | Status | Tasks✓ | Retries | Tokens | Useful Tok/Task | Stall Waste |",
            f"|---------|--------|--------|---------|--------|-----------------|-------------|",
        ]
        for pm in sorted(all_projects, key=lambda p: p.slug):
            _utp = round(pm.tokens_used / max(pm.tasks_completed, 1))
            report_lines.append(
                f"| {pm.slug} | {pm.status} | {pm.tasks_completed} "
                f"| {pm.total_retries} | {pm.tokens_used:,} "
                f"| {_utp:,} | {pm.stall_tokens:,} |"
            )

        if stalled:
            report_lines.extend(["", "## Stalled Projects"])
            for pm in stalled:
                report_lines.append(f"- **{pm.slug}**: {pm.stall_reason}")

        report_path = run_dir / "report.md"
        report_path.write_text("\n".join(report_lines), encoding="utf-8")

        # Copy the diff from baseline if we have one
        version_dir = _versions_dir() / self.prompt_version
        diff_path = version_dir / "diff_from_baseline.patch"
        if diff_path.exists():
            shutil.copy2(diff_path, run_dir / "diff_from_baseline.patch")

        return summary_path
