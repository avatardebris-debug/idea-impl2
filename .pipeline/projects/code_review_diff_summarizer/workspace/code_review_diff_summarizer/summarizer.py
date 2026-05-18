"""
Code Review Diff Summarizer
============================
Parses raw `git diff` text and produces a structured, human-readable briefing.

Features:
  - Per-file change stats (additions, deletions, net delta)
  - Function-level change detection (parses @@ hunk headers + AST context)
  - Risk flagging:
      * Large hunks (>50 lines changed in one place)
      * New files with no tests detected
      * Binary files
      * Changes to known-sensitive paths (config, .env, secrets)
      * Deleted files
  - Markdown briefing output
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Risk flag definitions
# ---------------------------------------------------------------------------

class RiskLevel(str):
    INFO = "INFO"
    WARN = "WARN"
    HIGH = "HIGH"


@dataclass
class RiskFlag:
    level: str
    message: str


_SENSITIVE_PATTERNS = re.compile(
    r"(\.env|secret|password|credential|api[_-]key|token|private[_-]key|\.pem|\.p12)",
    re.IGNORECASE,
)

_BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico",
    ".pdf", ".docx", ".xlsx", ".zip", ".tar", ".gz",
    ".pyc", ".exe", ".dll", ".so",
}

_HUNK_HEADER_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)")


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class HunkSummary:
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    context: str            # anything after @@ on the same line (often fn name)
    additions: int = 0
    deletions: int = 0

    @property
    def total_changed(self) -> int:
        return self.additions + self.deletions


@dataclass
class FileSummary:
    path: str
    old_path: Optional[str]         # set when file was renamed
    is_new: bool
    is_deleted: bool
    is_binary: bool
    additions: int
    deletions: int
    hunks: List[HunkSummary] = field(default_factory=list)
    risk_flags: List[RiskFlag] = field(default_factory=list)

    @property
    def net_delta(self) -> int:
        return self.additions - self.deletions

    @property
    def extension(self) -> str:
        return PurePosixPath(self.path).suffix.lower()


@dataclass
class DiffSummary:
    files: List[FileSummary] = field(default_factory=list)
    total_additions: int = 0
    total_deletions: int = 0
    risk_flags: List[RiskFlag] = field(default_factory=list)

    @property
    def files_changed(self) -> int:
        return len(self.files)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "files_changed": self.files_changed,
            "total_additions": self.total_additions,
            "total_deletions": self.total_deletions,
            "net_delta": self.total_additions - self.total_deletions,
            "risk_flags": [{"level": f.level, "message": f.message} for f in self.risk_flags],
            "files": [
                {
                    "path": f.path,
                    "old_path": f.old_path,
                    "is_new": f.is_new,
                    "is_deleted": f.is_deleted,
                    "is_binary": f.is_binary,
                    "additions": f.additions,
                    "deletions": f.deletions,
                    "net_delta": f.net_delta,
                    "changed_functions": [h.context.strip() for h in f.hunks if h.context.strip()],
                    "risk_flags": [{"level": r.level, "message": r.message} for r in f.risk_flags],
                }
                for f in self.files
            ],
        }


# ---------------------------------------------------------------------------
# Diff parser
# ---------------------------------------------------------------------------

class DiffParser:
    """Parses a raw git-diff string into structured FileSummary objects."""

    def parse(self, diff_text: str) -> List[FileSummary]:
        files: List[FileSummary] = []
        current: Optional[FileSummary] = None
        current_hunk: Optional[HunkSummary] = None

        for line in diff_text.splitlines():

            # --- New file header ---
            if line.startswith("diff --git "):
                if current:
                    if current_hunk:
                        current.hunks.append(current_hunk)
                        current_hunk = None
                    files.append(current)

                # Extract paths from  diff --git a/<old> b/<new>
                m = re.match(r"diff --git a/(\S+) b/(\S+)", line)
                old_path = m.group(1) if m else None
                new_path = m.group(2) if m else "unknown"
                current = FileSummary(
                    path=new_path,
                    old_path=old_path if old_path != new_path else None,
                    is_new=False,
                    is_deleted=False,
                    is_binary=False,
                    additions=0,
                    deletions=0,
                )
                continue

            if current is None:
                continue

            if line.startswith("new file mode"):
                current.is_new = True
            elif line.startswith("deleted file mode"):
                current.is_deleted = True
            elif line.startswith("Binary files"):
                current.is_binary = True

            # --- Hunk header ---
            hm = _HUNK_HEADER_RE.match(line)
            if hm:
                if current_hunk:
                    current.hunks.append(current_hunk)
                current_hunk = HunkSummary(
                    old_start=int(hm.group(1)),
                    old_count=int(hm.group(2) or 1),
                    new_start=int(hm.group(3)),
                    new_count=int(hm.group(4) or 1),
                    context=hm.group(5),
                )
                continue

            # --- Diff content lines ---
            if current_hunk:
                if line.startswith("+") and not line.startswith("+++"):
                    current_hunk.additions += 1
                    current.additions += 1
                elif line.startswith("-") and not line.startswith("---"):
                    current_hunk.deletions += 1
                    current.deletions += 1

        # Flush last file/hunk
        if current:
            if current_hunk:
                current.hunks.append(current_hunk)
            files.append(current)

        return files


# ---------------------------------------------------------------------------
# Risk analyser
# ---------------------------------------------------------------------------

class RiskAnalyser:
    """Applies heuristic risk checks to FileSummary objects."""

    LARGE_HUNK_THRESHOLD = 50
    LARGE_FILE_THRESHOLD = 200

    def analyse(self, files: List[FileSummary]) -> Tuple[List[FileSummary], List[RiskFlag]]:
        global_flags: List[RiskFlag] = []
        python_files = {f.path for f in files if f.extension == ".py" and not f.is_deleted}
        test_files = {f.path for f in files if re.search(r"test_|_test\.py$", f.path)}

        for f in files:
            # Sensitive path
            if _SENSITIVE_PATTERNS.search(f.path):
                f.risk_flags.append(RiskFlag(RiskLevel.HIGH, f"Sensitive path modified: {f.path}"))
                global_flags.append(RiskFlag(RiskLevel.HIGH, f"Sensitive path in diff: {f.path}"))

            # Binary file
            if f.is_binary:
                f.risk_flags.append(RiskFlag(RiskLevel.INFO, "Binary file changed"))

            # Deleted file
            if f.is_deleted:
                f.risk_flags.append(RiskFlag(RiskLevel.WARN, f"File deleted: {f.path}"))

            # New Python file with no matching test
            if f.is_new and f.extension == ".py" and not re.search(r"test_|_test\.py$", f.path):
                base = PurePosixPath(f.path).stem
                has_test = any(base in t for t in test_files)
                if not has_test:
                    f.risk_flags.append(RiskFlag(RiskLevel.WARN, f"New module '{f.path}' has no matching test file in this diff"))

            # Large hunks
            for hunk in f.hunks:
                if hunk.total_changed >= self.LARGE_HUNK_THRESHOLD:
                    msg = f"Large hunk (+{hunk.additions}/-{hunk.deletions}) at line {hunk.new_start}"
                    if hunk.context.strip():
                        msg += f" in `{hunk.context.strip()}`"
                    f.risk_flags.append(RiskFlag(RiskLevel.WARN, msg))

            # Very large file overall
            if f.additions + f.deletions >= self.LARGE_FILE_THRESHOLD:
                f.risk_flags.append(RiskFlag(RiskLevel.WARN, f"Large file change: +{f.additions}/-{f.deletions} lines"))

        return files, global_flags


# ---------------------------------------------------------------------------
# Markdown report generator
# ---------------------------------------------------------------------------

def _risk_icon(level: str) -> str:
    return {"INFO": "ℹ️", "WARN": "⚠️", "HIGH": "🚨"}.get(level, "•")


def generate_markdown_briefing(summary: DiffSummary) -> str:
    lines: List[str] = []
    lines.append("# Code Review Briefing\n")
    lines.append(f"**Files changed:** {summary.files_changed}  ")
    lines.append(f"**Additions:** `+{summary.total_additions}`  ")
    lines.append(f"**Deletions:** `-{summary.total_deletions}`  ")
    lines.append(f"**Net delta:** `{summary.total_additions - summary.total_deletions:+d}`\n")

    if summary.risk_flags:
        lines.append("## ⚠️ Global Risk Flags\n")
        for flag in summary.risk_flags:
            lines.append(f"- {_risk_icon(flag.level)} **{flag.level}** — {flag.message}")
        lines.append("")

    lines.append("## File-by-File Summary\n")
    for f in summary.files:
        badge = ""
        if f.is_new:
            badge = " 🆕"
        elif f.is_deleted:
            badge = " 🗑️"
        elif f.is_binary:
            badge = " 📦"

        lines.append(f"### `{f.path}`{badge}")
        if f.old_path:
            lines.append(f"_Renamed from `{f.old_path}`_\n")
        lines.append(f"`+{f.additions}` / `-{f.deletions}` (net `{f.net_delta:+d}`)\n")

        if f.hunks:
            changed_fns = [h.context.strip() for h in f.hunks if h.context.strip()]
            if changed_fns:
                lines.append("**Changed functions / areas:**")
                for fn in changed_fns:
                    lines.append(f"  - `{fn}`")
                lines.append("")

        if f.risk_flags:
            for flag in f.risk_flags:
                lines.append(f"- {_risk_icon(flag.level)} **{flag.level}** — {flag.message}")
            lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def summarize_diff(diff_text: str) -> DiffSummary:
    """
    Parse a raw git-diff string and return a fully structured DiffSummary.

    Args:
        diff_text: Raw output from `git diff` or `git diff HEAD~1`.

    Returns:
        DiffSummary with per-file stats, hunk-level function attribution, and risk flags.
    """
    parser = DiffParser()
    files = parser.parse(diff_text)

    analyser = RiskAnalyser()
    files, global_flags = analyser.analyse(files)

    summary = DiffSummary(
        files=files,
        total_additions=sum(f.additions for f in files),
        total_deletions=sum(f.deletions for f in files),
        risk_flags=global_flags,
    )
    return summary
