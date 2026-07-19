"""Engine interface + shared result type for dual-engine pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class EngineResult:
    """Outcome of one engine step (implement, review, fix, debug, deep_review)."""

    success: bool
    step: str = ""
    exit_code: int = 0
    log_path: str = ""
    summary: str = ""
    dry_run: bool = False
    error: str = ""
    command: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "step": self.step,
            "exit_code": self.exit_code,
            "log_path": self.log_path,
            "summary": self.summary,
            "dry_run": self.dry_run,
            "error": self.error,
            "command": self.command,
            "extra": self.extra,
        }


@runtime_checkable
class Engine(Protocol):
    """Minimal engine protocol — run one logical skill step for a phase."""

    name: str

    def run_phase_step(
        self,
        slug: str,
        phase: int,
        step: str,
        *,
        project_dir: Any = None,
        workspace: Any = None,
        prompt_file: Any = None,
        extra: dict[str, Any] | None = None,
    ) -> EngineResult:
        """Execute *step* for *slug* / *phase*. Return structured result."""
        ...
