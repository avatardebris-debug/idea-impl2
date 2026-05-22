"""Phase 7 data models — version graph, review workflow, merge, audit log."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field


# ── Enums ────────────────────────────────────────────────────────────────

class ReviewState(str, Enum):
    """Review outcome for a comment thread."""
    APPROVED = "approved"
    REQUESTS_CHANGES = "requests_changes"
    PENDING = "pending"
    SKIPPED = "skipped"


class ReviewerRole(str, Enum):
    """Role of a reviewer in the workflow."""
    DIRECTOR = "director"
    WRITER = "writer"
    PRODUCER = "producer"
    EDITOR = "editor"
    ART_DIRECTOR = "art_director"


class ArtifactType(str, Enum):
    """Type of project artifact being versioned."""
    BEAT_SHEET = "beat_sheet"
    SCRIPT = "script"
    CHARACTERS = "characters"
    SCENE_DESCRIPTIONS = "scene_descriptions"
    STORYBOARD_PROMPTS = "storyboard_prompts"
    ANIMATIC = "animatic"


class AuditAction(str, Enum):
    """Type of audit log entry."""
    BRANCH_CREATED = "branch_created"
    BRANCH_MERGED = "branch_merged"
    COMMENT_ADDED = "comment_added"
    COMMENT_UPDATED = "comment_updated"
    COMMENT_DELETED = "comment_deleted"
    REVIEW_STATE_CHANGED = "review_state_changed"
    ARTIFACT_MODIFIED = "artifact_modified"
    CONFLICT_RESOLVED = "conflict_resolved"
    EXPORTED = "exported"


# ── Audit Log ────────────────────────────────────────────────────────────

class AuditEntry(BaseModel):
    """Single entry in the append-only audit log."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    action: AuditAction
    actor: str  # user identifier
    artifact_type: ArtifactType
    artifact_id: str  # id of the artifact being modified
    description: str
    diff_summary: str = ""  # brief description of what changed
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AuditLog(BaseModel):
    """Append-only change log for project mutations."""
    entries: List[AuditEntry] = Field(default_factory=list)

    def append(self, entry: AuditEntry) -> None:
        self.entries.append(entry)

    def add(
        self,
        action: AuditAction,
        actor: str,
        artifact_type: ArtifactType,
        artifact_id: str,
        description: str,
        diff_summary: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditEntry:
        entry = AuditEntry(
            action=action,
            actor=actor,
            artifact_type=artifact_type,
            artifact_id=artifact_id,
            description=description,
            diff_summary=diff_summary,
            metadata=metadata or {},
        )
        self.append(entry)
        return entry

    def get_entries_for_artifact(
        self, artifact_id: str
    ) -> List[AuditEntry]:
        return [e for e in self.entries if e.artifact_id == artifact_id]

    def get_entries_for_actor(self, actor: str) -> List[AuditEntry]:
        return [e for e in self.entries if e.actor == actor]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_entries": len(self.entries),
            "entries": [e.model_dump() for e in self.entries],
        }

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2, default=str))

    @classmethod
    def load(cls, path: Path) -> AuditLog:
        if not path.exists():
            return cls()
        data = json.loads(path.read_text())
        entries = [AuditEntry(**e) for e in data.get("entries", [])]
        return cls(entries=entries)


# ── Project Version Graph ────────────────────────────────────────────────

class BranchPoint(BaseModel):
    """A point in the version graph where a branch diverges."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    from_branch: str
    to_branch: str
    description: str
    parent_artifact_snapshot: Dict[str, Any] = Field(default_factory=dict)


class Branch(BaseModel):
    """A named branch in the version graph."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str
    base_branch: str = "main"
    is_active: bool = True
    branch_points: List[BranchPoint] = Field(default_factory=list)
    merged_into: Optional[str] = None
    merged_at: Optional[datetime] = None

    def add_branch_point(self, point: BranchPoint) -> None:
        self.branch_points.append(point)

    def mark_merged(self, into: str, at: Optional[datetime] = None) -> None:
        self.merged_into = into
        self.merged_at = at or datetime.now(timezone.utc)
        self.is_active = False


class ProjectVersionGraph(BaseModel):
    """Git-friendly branching metadata for project artifacts."""
    project_id: str
    branches: Dict[str, Branch] = Field(default_factory=dict)
    branch_points: List[BranchPoint] = Field(default_factory=list)
    current_branch: str = "main"
    artifact_snapshots: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

    def __init__(self, **data):
        super().__init__(**data)
        # Ensure main branch always exists
        if "main" not in self.branches:
            self.branches["main"] = Branch(
                name="main",
                created_by="system",
                base_branch="main",
            )

    def create_branch(
        self,
        name: str,
        actor: str,
        base_branch: str = "main",
        description: str = "",
    ) -> Branch:
        if name in self.branches:
            raise ValueError(f"Branch '{name}' already exists")
        if base_branch not in self.branches:
            raise ValueError(f"Base branch '{base_branch}' does not exist")

        # Capture snapshot of current branch state
        snapshot = {}
        for art_type in ArtifactType:
            key = f"{art_type.value}_{base_branch}"
            if key in self.artifact_snapshots:
                snapshot[key] = self.artifact_snapshots[key]

        branch = Branch(
            name=name,
            created_by=actor,
            base_branch=base_branch,
        )
        self.branches[name] = branch

        bp = BranchPoint(
            from_branch=base_branch,
            to_branch=name,
            description=description or f"Branch created by {actor}",
            parent_artifact_snapshot=snapshot,
        )
        self.branch_points.append(bp)
        branch.add_branch_point(bp)

        return branch

    def switch_branch(self, name: str) -> None:
        if name not in self.branches:
            raise ValueError(f"Branch '{name}' does not exist")
        if not self.branches[name].is_active:
            raise ValueError(f"Branch '{name}' has been merged and is no longer active")
        self.current_branch = name

    def merge_branch(
        self,
        source_branch: str,
        target_branch: str = "main",
        actor: str = "system",
    ) -> MergeResult:
        if source_branch not in self.branches:
            raise ValueError(f"Source branch '{source_branch}' does not exist")
        if target_branch not in self.branches:
            raise ValueError(f"Target branch '{target_branch}' does not exist")

        source = self.branches[source_branch]
        target = self.branches[target_branch]

        # Collect snapshots from source branch
        source_snapshots = {}
        for art_type in ArtifactType:
            key = f"{art_type.value}_{source_branch}"
            if key in self.artifact_snapshots:
                source_snapshots[key] = self.artifact_snapshots[key]

        # Merge: source snapshots overwrite target snapshots
        merged_snapshots = dict(self.artifact_snapshots)
        for key, value in source_snapshots.items():
            merged_snapshots[key] = value

        self.artifact_snapshots = merged_snapshots
        source.mark_merged(target_branch)

        return MergeResult(
            source_branch=source_branch,
            target_branch=target_branch,
            success=True,
            merged_snapshots=merged_snapshots,
            conflicts=[],
        )

    def save_artifact_snapshot(
        self,
        artifact_type: ArtifactType,
        branch: str,
        data: Dict[str, Any],
    ) -> None:
        key = f"{artifact_type.value}_{branch}"
        self.artifact_snapshots[key] = data

    def get_artifact_snapshot(
        self, artifact_type: ArtifactType, branch: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        branch = branch or self.current_branch
        key = f"{artifact_type.value}_{branch}"
        return self.artifact_snapshots.get(key)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "current_branch": self.current_branch,
            "branches": {k: v.model_dump() for k, v in self.branches.items()},
            "branch_points": [bp.model_dump() for bp in self.branch_points],
            "artifact_snapshots": {
                k: v for k, v in self.artifact_snapshots.items()
            },
        }

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2, default=str))

    @classmethod
    def load(cls, path: Path) -> ProjectVersionGraph:
        if not path.exists():
            return cls(project_id="unknown")
        data = json.loads(path.read_text())
        branches = {}
        for name, bdata in data.get("branches", {}).items():
            branches[name] = Branch(**bdata)
        branch_points = [BranchPoint(**bp) for bp in data.get("branch_points", [])]
        artifact_snapshots = data.get("artifact_snapshots", {})
        return cls(
            project_id=data.get("project_id", "unknown"),
            branches=branches,
            branch_points=branch_points,
            current_branch=data.get("current_branch", "main"),
            artifact_snapshots=artifact_snapshots,
        )


# ── Review Workflow ──────────────────────────────────────────────────────

class Comment(BaseModel):
    """A single comment in a review thread."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    author: str
    text: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    is_resolved: bool = False
    line_number: Optional[int] = None  # line in script/beat sheet
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CommentThread(BaseModel):
    """Thread of comments on a specific scene/beat."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    artifact_type: ArtifactType
    artifact_id: str  # scene_id, beat_id, etc.
    comments: List[Comment] = Field(default_factory=list)
    state: ReviewState = ReviewState.PENDING
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None

    @property
    def last_comment(self) -> Optional[Comment]:
        return self.comments[-1] if self.comments else None

    def add_comment(
        self,
        author: str,
        text: str,
        line_number: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Comment:
        comment = Comment(
            author=author,
            text=text,
            line_number=line_number,
            metadata=metadata or {},
        )
        self.comments.append(comment)
        # Update state based on comments
        self._update_state()
        return comment

    def update_state(self, state: ReviewState) -> None:
        self.state = state
        if state == ReviewState.APPROVED:
            self.resolved_at = datetime.now(timezone.utc)

    def _update_state(self) -> None:
        """Auto-update state based on comment content."""
        if not self.comments:
            self.state = ReviewState.PENDING
            return

        # If any comment requests changes, override to that
        for comment in self.comments:
            text_lower = comment.text.lower()
            if any(
                kw in text_lower
                for kw in ["change", "revise", "fix", "modify", "remove", "add"]
            ):
                self.state = ReviewState.REQUESTS_CHANGES
                return

        # If all comments are approvals, set to approved
        if all(
            any(kw in c.text.lower() for kw in ["approve", "looks good", "approved", "ok", "yes"])
            for c in self.comments
        ):
            self.state = ReviewState.APPROVED
        elif any(c.is_resolved for c in self.comments):
            self.state = ReviewState.APPROVED
        else:
            self.state = ReviewState.PENDING

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "artifact_type": self.artifact_type.value,
            "artifact_id": self.artifact_id,
            "state": self.state.value,
            "comment_count": len(self.comments),
            "comments": [c.model_dump() for c in self.comments],
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolved_by": self.resolved_by,
        }


class ReviewWorkflow(BaseModel):
    """Manages review threads across project artifacts."""
    project_id: str
    threads: Dict[str, CommentThread] = Field(default_factory=dict)
    reviewers: Dict[str, ReviewerRole] = Field(default_factory=dict)

    def add_reviewer(self, user_id: str, role: ReviewerRole) -> None:
        self.reviewers[user_id] = role

    def create_thread(
        self,
        artifact_type: ArtifactType,
        artifact_id: str,
        author: str,
        initial_comment: str,
        line_number: Optional[int] = None,
    ) -> CommentThread:
        thread = CommentThread(
            artifact_type=artifact_type,
            artifact_id=artifact_id,
        )
        thread.add_comment(author, initial_comment, line_number)
        self.threads[thread.id] = thread
        return thread

    def get_thread(self, thread_id: str) -> Optional[CommentThread]:
        return self.threads.get(thread_id)

    def get_threads_for_artifact(
        self, artifact_type: ArtifactType, artifact_id: str
    ) -> List[CommentThread]:
        return [
            t for t in self.threads.values()
            if t.artifact_type == artifact_type and t.artifact_id == artifact_id
        ]

    def get_threads_by_state(self, state: ReviewState) -> List[CommentThread]:
        return [t for t in self.threads.values() if t.state == state]

    def resolve_thread(self, thread_id: str, resolver: str) -> bool:
        thread = self.threads.get(thread_id)
        if not thread:
            return False
        thread.resolved_at = datetime.now(timezone.utc)
        thread.resolved_by = resolver
        thread.state = ReviewState.APPROVED
        return True

    def get_summary(self) -> Dict[str, Any]:
        state_counts = {}
        for state in ReviewState:
            state_counts[state.value] = len(self.get_threads_by_state(state))
        return {
            "project_id": self.project_id,
            "total_threads": len(self.threads),
            "state_counts": state_counts,
            "reviewers": {k: v.value for k, v in self.reviewers.items()},
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "threads": {k: v.to_dict() for k, v in self.threads.items()},
            "reviewers": {k: v.value for k, v in self.reviewers.items()},
        }

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2, default=str))

    @classmethod
    def load(cls, path: Path) -> ReviewWorkflow:
        if not path.exists():
            return cls(project_id="unknown")
        data = json.loads(path.read_text())
        threads = {}
        for tid, tdata in data.get("threads", {}).items():
            comments = [Comment(**c) for c in tdata.get("comments", [])]
            threads[tid] = CommentThread(
                id=tdata["id"],
                artifact_type=ArtifactType(tdata["artifact_type"]),
                artifact_id=tdata["artifact_id"],
                comments=comments,
                state=ReviewState(tdata["state"]),
                resolved_at=datetime.fromisoformat(tdata["resolved_at"]) if tdata.get("resolved_at") else None,
                resolved_by=tdata.get("resolved_by"),
            )
        reviewers = {k: ReviewerRole(v) for k, v in data.get("reviewers", {}).items()}
        return cls(
            project_id=data.get("project_id", "unknown"),
            threads=threads,
            reviewers=reviewers,
        )


# ── Merge / Conflict Resolution ──────────────────────────────────────────

class ConflictMarker(BaseModel):
    """Represents a merge conflict at a specific field path."""
    field_path: str  # e.g. "characters.0.name"
    base_value: Any
    source_value: Any
    target_value: Any
    resolution: Optional[str] = None  # "source", "target", "manual"
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None


class MergeResult(BaseModel):
    """Result of a field-level merge operation."""
    success: bool
    merged_data: Dict[str, Any] = Field(default_factory=dict)
    conflicts: List[ConflictMarker] = Field(default_factory=list)
    merged_keys: List[str] = Field(default_factory=list)
    skipped_keys: List[str] = Field(default_factory=list)

    @property
    def has_conflicts(self) -> bool:
        return len(self.conflicts) > 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "merged_data": self.merged_data,
            "conflicts": [c.model_dump() for c in self.conflicts],
            "merged_keys": self.merged_keys,
            "skipped_keys": self.skipped_keys,
        }


class ArtifactMerger(BaseModel):
    """Field-level merge for JSON artifacts with conflict markers."""

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

        Returns a MergeResult with merged data and any conflicts found.
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
        merged = {}
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
        """Resolve a specific conflict by choosing source or target value."""
        if conflict_index >= len(result.conflicts):
            return
        conflict = result.conflicts[conflict_index]
        if resolution == "source":
            result.merged_data[conflict.field_path.split(".")[-1]] = conflict.source_value
        elif resolution == "target":
            result.merged_data[conflict.field_path.split(".")[-1]] = conflict.target_value
        conflict.resolution = resolution
        conflict.resolved_at = datetime.now(timezone.utc)
        conflict.resolved_by = resolver
        if all(c.resolution for c in result.conflicts):
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


# ── Phase 7 Exporter ─────────────────────────────────────────────────────

class Phase7Exporter(BaseModel):
    """Export review state and version graph for downstream consumers."""

    def export(
        self,
        version_graph: ProjectVersionGraph,
        review_workflow: ReviewWorkflow,
        audit_log: AuditLog,
        output_dir: Path,
    ) -> Dict[str, Path]:
        """Export all Phase 7 artifacts to the output directory.

        Returns a dict mapping artifact name to output file path.
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        exported = {}

        # Export version graph
        graph_path = output_dir / "version_graph.json"
        version_graph.save(graph_path)
        exported["version_graph"] = graph_path

        # Export review workflow
        review_path = output_dir / "review_workflow.json"
        review_workflow.save(review_path)
        exported["review_workflow"] = review_path

        # Export audit log
        audit_path = output_dir / "audit_log.json"
        audit_log.save(audit_path)
        exported["audit_log"] = audit_path

        # Export summary manifest
        manifest = {
            "project_id": version_graph.project_id,
            "current_branch": version_graph.current_branch,
            "review_summary": review_workflow.get_summary(),
            "audit_summary": audit_log.to_dict(),
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "files": {k: str(p) for k, p in exported.items()},
        }
        manifest_path = output_dir / "phase7_manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, default=str))
        exported["manifest"] = manifest_path

        # Audit the export
        audit_log.add(
            action=AuditAction.EXPORTED,
            actor="system",
            artifact_type=ArtifactType.SCRIPT,
            artifact_id=version_graph.project_id,
            description=f"Phase 7 artifacts exported to {output_dir}",
            metadata={"files": list(exported.keys())},
        )

        return exported

    def export_branch_diff(
        self,
        version_graph: ProjectVersionGraph,
        branch_a: str,
        branch_b: str,
        artifact_type: ArtifactType,
        output_dir: Path,
    ) -> Optional[Path]:
        """Export a diff between two branches for a specific artifact type."""
        snap_a = version_graph.get_artifact_snapshot(artifact_type, branch_a)
        snap_b = version_graph.get_artifact_snapshot(artifact_type, branch_b)

        if snap_a is None or snap_b is None:
            return None

        output_dir.mkdir(parents=True, exist_ok=True)
        diff_path = output_dir / f"diff_{artifact_type.value}_{branch_a}_vs_{branch_b}.json"

        diff = {
            "artifact_type": artifact_type.value,
            "branch_a": branch_a,
            "branch_b": branch_b,
            "branch_a_snapshot": snap_a,
            "branch_b_snapshot": snap_b,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        diff_path.write_text(json.dumps(diff, indent=2, default=str))
        return diff_path
