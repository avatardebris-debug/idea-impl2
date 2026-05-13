"""Quality checker — validates generated reference images for consistency."""

from __future__ import annotations

import hashlib
import logging
import os
import pathlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class QualityReport:
    """Quality assessment for a character's reference images and renders."""
    character_id: str
    reference_image_path: str
    score: float  # 0.0 - 1.0
    passed: bool
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    render_scores: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "character_id": self.character_id,
            "reference_image_path": self.reference_image_path,
            "score": self.score,
            "passed": self.passed,
            "issues": self.issues,
            "warnings": self.warnings,
            "render_scores": self.render_scores,
        }


class QualityChecker:
    """Validates reference images and detects consistency drift in renders.

    For testing environments without real image-comparison libraries,
    uses file-based heuristics (size, existence, checksums).
    """

    def __init__(self, quality_threshold: float = 0.85):
        """Initialize the quality checker.

        Args:
            quality_threshold: Minimum score (0-1) for a check to PASS.
        """
        if not 0.0 <= quality_threshold <= 1.0:
            raise ValueError("quality_threshold must be between 0.0 and 1.0")
        self.quality_threshold = quality_threshold

    def check_reference_image(self, character_id: str, image_path: str) -> QualityReport:
        """Check that a reference image meets quality requirements.

        Args:
            character_id: The character's ID.
            image_path: Path to the reference image file.

        Returns:
            A QualityReport with score, issues, and pass/fail.
        """
        issues: List[str] = []
        warnings: List[str] = []
        score = 1.0

        # Check file exists
        p = pathlib.Path(image_path)
        if not p.exists():
            issues.append(f"Reference image not found: {image_path}")
            return QualityReport(
                character_id=character_id,
                reference_image_path=image_path,
                score=0.0,
                passed=False,
                issues=issues,
            )

        # Check file is non-empty
        size = p.stat().st_size
        if size == 0:
            issues.append("Reference image file is empty (0 bytes)")
            score -= 0.5
        elif size < 100:
            warnings.append(f"Reference image is very small ({size} bytes) — may be a stub")
            score -= 0.1

        # Check extension
        suffix = p.suffix.lower()
        if suffix not in (".png", ".jpg", ".jpeg", ".webp", ".gif"):
            warnings.append(f"Unusual image format: {suffix}")
            score -= 0.05

        # Check readable
        try:
            with open(p, "rb") as f:
                header = f.read(8)
            if len(header) < 4:
                issues.append("Could not read image header — file may be corrupt")
                score -= 0.3
        except OSError as e:
            issues.append(f"Could not read image: {e}")
            score -= 0.5

        score = max(0.0, min(1.0, round(score, 3)))
        passed = score >= self.quality_threshold and len(issues) == 0

        return QualityReport(
            character_id=character_id,
            reference_image_path=image_path,
            score=score,
            passed=passed,
            issues=issues,
            warnings=warnings,
        )

    def check_registry(self, registry: Any) -> List[QualityReport]:
        """Run quality checks for all characters in a registry.

        Args:
            registry: CharacterRegistry with .characters dict.

        Returns:
            List of QualityReports, one per character.
        """
        reports: List[QualityReport] = []
        for char_id, character in registry.characters.items():
            ref_path = getattr(character, "reference_image_path", "") or ""
            if not ref_path:
                reports.append(QualityReport(
                    character_id=char_id,
                    reference_image_path="",
                    score=0.0,
                    passed=False,
                    issues=["No reference_image_path set on character"],
                ))
            else:
                reports.append(self.check_reference_image(char_id, ref_path))
        return reports

    def compute_image_fingerprint(self, image_path: str) -> Optional[str]:
        """Compute a content hash of an image file.

        Args:
            image_path: Path to the image.

        Returns:
            SHA-256 hex digest, or None if file not found.
        """
        p = pathlib.Path(image_path)
        if not p.exists():
            return None
        with open(p, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()

    def summary(self, reports: List[QualityReport]) -> Dict[str, Any]:
        """Summarise a list of quality reports.

        Args:
            reports: List of QualityReports.

        Returns:
            Dict with overall pass rate, avg score, and per-character results.
        """
        if not reports:
            return {"total": 0, "passed": 0, "failed": 0, "avg_score": 0.0, "pass_rate": 0.0}
        passed = sum(1 for r in reports if r.passed)
        avg = sum(r.score for r in reports) / len(reports)
        return {
            "total": len(reports),
            "passed": passed,
            "failed": len(reports) - passed,
            "avg_score": round(avg, 3),
            "pass_rate": round(passed / len(reports), 3),
        }
