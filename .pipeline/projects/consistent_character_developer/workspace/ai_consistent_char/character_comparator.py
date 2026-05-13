"""Character comparator — detects drift between reference and scene renders."""

from __future__ import annotations

import logging
import pathlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ai_consistent_char.quality_checker import QualityChecker

logger = logging.getLogger(__name__)


@dataclass
class DriftReport:
    """Drift assessment between a reference image and a scene render."""
    character_id: str
    scene_id: str
    reference_path: str
    render_path: str
    drift_score: float  # 0.0 = identical, 1.0 = completely different
    drifted: bool
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "character_id": self.character_id,
            "scene_id": self.scene_id,
            "reference_path": self.reference_path,
            "render_path": self.render_path,
            "drift_score": self.drift_score,
            "drifted": self.drifted,
            "notes": self.notes,
        }


class CharacterComparator:
    """Compares reference images against scene renders to detect character drift.

    In a production implementation this would use perceptual hashing (e.g.,
    imagehash) or an embedding-based similarity metric. Here we use a fast
    file-based heuristic so tests work without image libraries.
    """

    def __init__(self, drift_threshold: float = 0.3):
        """Initialize the comparator.

        Args:
            drift_threshold: Drift score above this value is flagged as drift
                             (0 = no tolerance, 1 = allow everything).
        """
        if not 0.0 <= drift_threshold <= 1.0:
            raise ValueError("drift_threshold must be between 0.0 and 1.0")
        self.drift_threshold = drift_threshold
        self._checker = QualityChecker()

    def compare(self, character_id: str, scene_id: str, reference_path: str, render_path: str) -> DriftReport:
        """Compare a single render against its reference image.

        Args:
            character_id: The character's ID.
            scene_id: The scene this render belongs to.
            reference_path: Path to the reference image.
            render_path: Path to the scene render.

        Returns:
            A DriftReport with drift score and pass/fail.
        """
        notes: List[str] = []

        ref_p = pathlib.Path(reference_path)
        ren_p = pathlib.Path(render_path)

        # Existence checks
        if not ref_p.exists():
            return DriftReport(
                character_id=character_id,
                scene_id=scene_id,
                reference_path=reference_path,
                render_path=render_path,
                drift_score=1.0,
                drifted=True,
                notes=["Reference image not found"],
            )
        if not ren_p.exists():
            return DriftReport(
                character_id=character_id,
                scene_id=scene_id,
                reference_path=reference_path,
                render_path=render_path,
                drift_score=1.0,
                drifted=True,
                notes=["Render image not found"],
            )

        # Compute fingerprints
        ref_hash = self._checker.compute_image_fingerprint(reference_path)
        ren_hash = self._checker.compute_image_fingerprint(render_path)

        if ref_hash == ren_hash:
            # Identical files — dummy provider or identical content
            drift_score = 0.0
            notes.append("Files are byte-identical (likely dummy/stub renders)")
        else:
            # Different content — use file-size delta as a heuristic proxy
            ref_size = ref_p.stat().st_size
            ren_size = ren_p.stat().st_size
            max_size = max(ref_size, ren_size)
            if max_size == 0:
                drift_score = 0.0
            else:
                size_diff_ratio = abs(ref_size - ren_size) / max_size
                # Heuristic: files of similar size are less drifted
                drift_score = round(min(size_diff_ratio, 1.0), 3)
            notes.append(f"Size delta heuristic: ref={ref_size}b render={ren_size}b")

        drifted = drift_score > self.drift_threshold

        return DriftReport(
            character_id=character_id,
            scene_id=scene_id,
            reference_path=reference_path,
            render_path=render_path,
            drift_score=drift_score,
            drifted=drifted,
            notes=notes,
        )

    def compare_collection(self, reference_map: Dict[str, str], collection: Any) -> List[DriftReport]:
        """Compare all renders in a SceneCharacterRenderCollection against references.

        Args:
            reference_map: Dict mapping character_id -> reference_image_path.
            collection: SceneCharacterRenderCollection with .renders list.

        Returns:
            List of DriftReports.
        """
        reports: List[DriftReport] = []
        for render in collection.renders:
            char_id = render.character_id
            scene_id = render.scene_id
            ref_path = reference_map.get(char_id, "")
            if not ref_path:
                reports.append(DriftReport(
                    character_id=char_id,
                    scene_id=scene_id,
                    reference_path="",
                    render_path=render.render_path,
                    drift_score=1.0,
                    drifted=True,
                    notes=[f"No reference image registered for character '{char_id}'"],
                ))
            else:
                reports.append(self.compare(char_id, scene_id, ref_path, render.render_path))
        return reports

    def summary(self, reports: List[DriftReport]) -> Dict[str, Any]:
        """Summarise a list of drift reports.

        Args:
            reports: List of DriftReports.

        Returns:
            Dict with drift stats.
        """
        if not reports:
            return {"total": 0, "drifted": 0, "ok": 0, "avg_drift": 0.0, "drift_rate": 0.0}
        drifted = sum(1 for r in reports if r.drifted)
        avg_drift = sum(r.drift_score for r in reports) / len(reports)
        return {
            "total": len(reports),
            "drifted": drifted,
            "ok": len(reports) - drifted,
            "avg_drift": round(avg_drift, 3),
            "drift_rate": round(drifted / len(reports), 3),
        }
