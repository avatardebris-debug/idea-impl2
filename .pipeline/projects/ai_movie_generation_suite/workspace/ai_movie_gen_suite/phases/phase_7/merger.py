"""ArtifactMerger — field-level merge for JSON artifacts with conflict markers.

This module provides the core merge logic used by the Phase 7 collaborative
editing system. It implements three-way merge (base, source, target) with
conflict detection and resolution.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ai_movie_gen_suite.phases.phase_7.models import (
    ArtifactMerger as _ArtifactMergerBase,
    ArtifactType,
    ConflictMarker,
    MergeResult,
)


class ArtifactMerger(_ArtifactMergerBase):
    """Field-level merge for JSON artifacts with conflict markers.

    Supports three-way merge: base (common ancestor), source (incoming),
    target (current branch). Conflicts are detected when both source and
    target modify the same field differently from base.
    """

    def merge(
        self,
        base: Dict[str, Any],
        source: Dict[str, Any],
        target: Dict[str, Any],
        artifact_type: ArtifactType,
        source_branch: str,
        target_branch: str,
    ) -> MergeResult:
        """Merge source into target, using base as the common ancestor.

        Args:
            base: Common ancestor artifact state.
            source: Incoming changes from the source branch.
            target: Current branch artifact state.
            artifact_type: Type of artifact being merged.
            source_branch: Name of the source branch.
            target_branch: Name of the target branch.

        Returns:
            MergeResult with merged data and any conflicts found.
        """
        merged = self._deep_merge(base, source, target, artifact_type, source_branch, target_branch)
        return merged

    def _deep_merge(
        self,
        base: Dict[str, Any],
        source: Dict[str, Any],
        target: Dict[str, Any],
        artifact_type: ArtifactType,
        source_branch: str,
        target_branch: str,
    ) -> MergeResult:
        """Perform the actual three-way merge.

        Merge rules:
        - New keys in source only: always merge in
        - New keys in target only: always keep
        - Same value in source and target: no conflict
        - Only target changed (source == base): keep target
        - Only source changed (target == base): keep source
        - Both changed differently: conflict — keep target by default
        """
        merged: Dict[str, Any] = {}
        conflicts: List[ConflictMarker] = []
        merged_keys: List[str] = []
        skipped_keys: List[str] = []

        all_keys = set(list(base.keys()) + list(source.keys()) + list(target.keys()))

        for key in all_keys:
            in_base = key in base
            in_source = key in source
            in_target = key in target

            base_val = base.get(key)
            source_val = source.get(key)
            target_val = target.get(key)

            if in_source and not in_base:
                # New key in source — always merge
                merged[key] = source_val
                merged_keys.append(key)
            elif in_target and not in_base:
                # New key in target — always keep
                merged[key] = target_val
                merged_keys.append(key)
            elif in_source and in_target:
                if source_val == target_val:
                    # No conflict — same value
                    merged[key] = source_val
                    merged_keys.append(key)
                elif source_val == base_val:
                    # Only target changed — keep target
                    merged[key] = target_val
                    merged_keys.append(key)
                elif target_val == base_val:
                    # Only source changed — keep source
                    merged[key] = source_val
                    merged_keys.append(key)
                else:
                    # Both changed differently — conflict
                    field_path = f"{artifact_type.value}.{key}"
                    conflict = ConflictMarker(
                        field_path=field_path,
                        base_value=base_val,
                        source_value=source_val,
                        target_value=target_val,
                    )
                    conflicts.append(conflict)
                    # Default resolution: keep target (current branch)
                    merged[key] = target_val
                    skipped_keys.append(key)
            elif in_source:
                merged[key] = source_val
                merged_keys.append(key)
            elif in_target:
                merged[key] = target_val
                merged_keys.append(key)
            else:
                skipped_keys.append(key)

        success = len(conflicts) == 0
        return MergeResult(
            success=success,
            merged_data=merged,
            conflicts=conflicts,
            merged_keys=merged_keys,
            skipped_keys=skipped_keys,
        )

    def resolve_conflict(
        self,
        result: MergeResult,
        conflict_index: int,
        resolution: str,
        resolver: str,
    ) -> None:
        """Resolve a specific conflict by choosing source or target value.

        Args:
            result: The MergeResult containing the conflict.
            conflict_index: Index of the conflict to resolve.
            resolution: "source" or "target".
            resolver: User who resolved the conflict.
        """
        if conflict_index >= len(result.conflicts):
            return
        conflict = result.conflicts[conflict_index]
        field_key = conflict.field_path.split(".")[-1]

        if resolution == "source":
            result.merged_data[field_key] = conflict.source_value
        elif resolution == "target":
            result.merged_data[field_key] = conflict.target_value
        else:
            return

        conflict.resolution = resolution
        conflict.resolved_at = datetime.now(timezone.utc)
        conflict.resolved_by = resolver

        # Check if all conflicts are now resolved
        if all(c.resolution is not None for c in result.conflicts):
            result.success = True

    def apply_merge(
        self,
        base: Dict[str, Any],
        source: Dict[str, Any],
        target: Dict[str, Any],
        artifact_type: ArtifactType,
        source_branch: str,
        target_branch: str,
    ) -> Dict[str, Any]:
        """Convenience method: merge and return only the merged data."""
        result = self.merge(base, source, target, artifact_type, source_branch, target_branch)
        return result.merged_data

    def export_conflict_report(
        self,
        result: MergeResult,
        output_path: Path,
    ) -> Path:
        """Export a human-readable conflict report."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        report_lines = [
            "# Merge Conflict Report",
            f"Generated: {datetime.now(timezone.utc).isoformat()}",
            f"Total conflicts: {len(result.conflicts)}",
            f"Success: {result.success}",
            "",
            "## Merged Keys",
        ]

        for key in result.merged_keys:
            report_lines.append(f"- {key}")

        report_lines.append("")
        report_lines.append("## Skipped Keys")
        for key in result.skipped_keys:
            report_lines.append(f"- {key}")

        if result.conflicts:
            report_lines.append("")
            report_lines.append("## Conflicts")
            for i, conflict in enumerate(result.conflicts):
                report_lines.append(f"\n### Conflict {i + 1}: {conflict.field_path}")
                report_lines.append(f"- Base: {json.dumps(conflict.base_value, indent=4)}")
                report_lines.append(f"- Source: {json.dumps(conflict.source_value, indent=4)}")
                report_lines.append(f"- Target: {json.dumps(conflict.target_value, indent=4)}")
                if conflict.resolution:
                    report_lines.append(f"- Resolution: {conflict.resolution} (by {conflict.resolved_by})")
                else:
                    report_lines.append("- Resolution: PENDING")

        output_path.write_text("\n".join(report_lines))
        return output_path
