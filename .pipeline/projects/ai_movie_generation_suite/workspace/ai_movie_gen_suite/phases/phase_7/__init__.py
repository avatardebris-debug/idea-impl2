"""Phase 7 — Collaborative Editing & Review.

Provides:
- ProjectVersionGraph: Git-friendly branching metadata for project artifacts.
- ReviewWorkflow: Comment threads per scene/beat with approve/request-changes states.
- ArtifactMerger: Field-level merge for JSON artifacts with conflict markers.
- AuditLog: Append-only change log for all project mutations.
- Phase7Exporter: Export review state and version graph for downstream consumers.
"""

from ai_movie_gen_suite.phases.phase_7.models import (
    AuditEntry,
    AuditLog,
    Branch,
    BranchPoint,
    Comment,
    CommentThread,
    ConflictMarker,
    MergeResult,
    ProjectVersionGraph,
    ReviewState,
    ReviewWorkflow,
    ReviewerRole,
    Phase7Exporter,
)
from ai_movie_gen_suite.phases.phase_7.merger import ArtifactMerger

__all__ = [
    "AuditEntry",
    "AuditLog",
    "Branch",
    "BranchPoint",
    "Comment",
    "CommentThread",
    "ConflictMarker",
    "MergeResult",
    "ProjectVersionGraph",
    "ReviewState",
    "ReviewWorkflow",
    "ReviewerRole",
    "Phase7Exporter",
    "ArtifactMerger",
]
