"""
pipeline/run_context.py
Explicit run configuration for the pipeline (replaces scattered module globals).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

RunMode = Literal["single", "from_list", "polish", "resume"]


@dataclass(frozen=True)
class RunContext:
    mode: RunMode
    ideas_path: Path
    legacy: bool
    polish_path: Path | None = None

    def is_polish_queue(self, path: Path) -> bool:
        if self.mode == "polish":
            return True
        if self.polish_path is not None and path.resolve() == self.polish_path.resolve():
            return True
        return path.name.lower() == "polish_queue.md"
