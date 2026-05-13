"""
Production Pipeline Module

End-to-end video production orchestrator that chains:
  topic → story → metadata → transcript → quality check → export

Provides a ProjectManager for tracking multiple video projects.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from story_generator import StoryGenerator, StoryResult, VideoFormat, StoryTone
from transcript_builder import TranscriptBuilder
from title_generator import TitleGenerator
from thumbnail_generator import ThumbnailGenerator
from keyword_generator import KeywordGenerator
from template_versioning import TemplateVersionManager


class ProjectStatus(Enum):
    """Status of a video project."""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    APPROVED = "approved"
    EXPORTED = "exported"
    PUBLISHED = "published"


@dataclass
class QualityReport:
    """Quality check results for a video project."""
    passed: bool
    checks: List[Dict[str, Any]] = field(default_factory=list)
    score: float = 0.0  # 0-100
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "passed": self.passed, "score": self.score,
            "checks": self.checks, "issues": self.issues,
            "suggestions": self.suggestions,
        }


@dataclass
class VideoProject:
    """A complete video production project."""
    id: str
    title: str
    topic: str
    status: ProjectStatus = ProjectStatus.DRAFT
    format: VideoFormat = VideoFormat.LONG_FORM
    tone: StoryTone = StoryTone.EDUCATIONAL
    story: Optional[StoryResult] = None
    transcript_text: str = ""
    keywords: List[str] = field(default_factory=list)
    thumbnail_descriptions: List[str] = field(default_factory=list)
    quality_report: Optional[QualityReport] = None
    export_path: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "topic": self.topic,
            "status": self.status.value,
            "format": self.format.value,
            "tone": self.tone.value,
            "story": self.story.to_dict() if self.story else None,
            "transcript_text": self.transcript_text,
            "keywords": self.keywords,
            "thumbnail_descriptions": self.thumbnail_descriptions,
            "quality_report": self.quality_report.to_dict() if self.quality_report else None,
            "export_path": self.export_path,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class ProductionPipeline:
    """End-to-end video production pipeline.

    Chains all studio components: story → metadata → transcript → QA → export.
    """

    def __init__(self, llm_client=None, template_dir: Optional[str] = None):
        self.story_gen = StoryGenerator(llm_client=llm_client)
        self.title_gen = TitleGenerator()
        self.thumb_gen = ThumbnailGenerator()
        self.keyword_gen = KeywordGenerator()
        self.template_mgr = TemplateVersionManager(storage_dir=template_dir)

    def produce(
        self,
        topic: str,
        format: VideoFormat = VideoFormat.LONG_FORM,
        tone: StoryTone = StoryTone.EDUCATIONAL,
        project_id: Optional[str] = None,
    ) -> VideoProject:
        """Run the full production pipeline for a topic.

        Steps:
          1. Generate story outline
          2. Generate title & keywords
          3. Generate thumbnail descriptions
          4. Build transcript from story
          5. Run quality checks

        Returns:
            VideoProject with all components populated.
        """
        pid = project_id or f"proj_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 1. Story
        story = self.story_gen.generate(topic, format=format, tone=tone)

        # 2. Title + keywords
        title_result = self.title_gen.generate_single_title(topic)
        keywords = self.keyword_gen.generate_keywords(topic, num_keywords=20)
        keyword_strings = [kw.keyword for kw in keywords]

        # 3. Thumbnails
        thumbs = self.thumb_gen.generate_thumbnails(topic, num_thumbnails=3)
        thumb_descs = [t.description for t in thumbs]

        # 4. Transcript
        builder = TranscriptBuilder(title=title_result.title)
        t = 0.0
        for beat in story.beats:
            builder.add_section(
                title=beat.name, content=beat.content, start_time=t,
            )
            t = builder.get_sections()[-1].end_time

        # 5. Quality check
        qr = self.quality_check(
            title=title_result.title,
            keywords=keyword_strings,
            story=story,
            transcript_sections=len(builder.get_sections()),
        )

        project = VideoProject(
            id=pid,
            title=title_result.title,
            topic=topic,
            status=ProjectStatus.REVIEW if qr.passed else ProjectStatus.IN_PROGRESS,
            format=format,
            tone=tone,
            story=story,
            transcript_text=story.full_script,
            keywords=keyword_strings,
            thumbnail_descriptions=thumb_descs,
            quality_report=qr,
        )
        return project

    def quality_check(
        self,
        title: str,
        keywords: List[str],
        story: StoryResult,
        transcript_sections: int,
    ) -> QualityReport:
        """Run automated quality checks on project components."""
        checks = []
        issues = []
        suggestions = []
        score = 0.0

        # Title checks
        title_ok = 10 <= len(title) <= 100
        checks.append({"name": "title_length", "passed": title_ok,
                        "detail": f"{len(title)} chars"})
        if title_ok:
            score += 20
        else:
            issues.append(f"Title length ({len(title)}) outside 10-100 range")

        # Keyword checks
        kw_ok = len(keywords) >= 5
        checks.append({"name": "keyword_count", "passed": kw_ok,
                        "detail": f"{len(keywords)} keywords"})
        if kw_ok:
            score += 20
        else:
            issues.append(f"Only {len(keywords)} keywords (need >= 5)")
            suggestions.append("Add more specific long-tail keywords")

        # Story completeness
        story_ok = len(story.beats) >= 3
        checks.append({"name": "story_beats", "passed": story_ok,
                        "detail": f"{len(story.beats)} beats"})
        if story_ok:
            score += 20
        else:
            issues.append("Story too short — needs at least 3 beats")

        # Logline
        logline_ok = len(story.logline) >= 10
        checks.append({"name": "logline", "passed": logline_ok,
                        "detail": f"{len(story.logline)} chars"})
        if logline_ok:
            score += 20
        else:
            suggestions.append("Write a stronger logline (minimum 10 chars)")

        # Transcript
        trans_ok = transcript_sections >= 2
        checks.append({"name": "transcript_sections", "passed": trans_ok,
                        "detail": f"{transcript_sections} sections"})
        if trans_ok:
            score += 20

        passed = score >= 60
        return QualityReport(passed=passed, checks=checks, score=score,
                             issues=issues, suggestions=suggestions)

    def export_project(self, project: VideoProject, output_dir: str) -> str:
        """Export a project to a directory as JSON + transcript files."""
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        # Main project JSON
        proj_file = out / f"{project.id}.json"
        proj_file.write_text(json.dumps(project.to_dict(), indent=2), encoding="utf-8")

        # Transcript SRT
        if project.story:
            builder = TranscriptBuilder(title=project.title)
            t = 0.0
            for beat in project.story.beats:
                builder.add_section(title=beat.name, content=beat.content, start_time=t)
                t = builder.get_sections()[-1].end_time
            builder.export_to_srt(str(out / f"{project.id}.srt"))
            builder.export_to_vtt(str(out / f"{project.id}.vtt"))

        project.export_path = str(out)
        project.status = ProjectStatus.EXPORTED
        return str(proj_file)


class ProjectManager:
    """Manage multiple video projects with persistence."""

    def __init__(self, storage_dir: Optional[str] = None):
        self._projects: Dict[str, VideoProject] = {}
        self._storage_dir = Path(storage_dir) if storage_dir else None
        if self._storage_dir:
            self._storage_dir.mkdir(parents=True, exist_ok=True)

    def add_project(self, project: VideoProject):
        self._projects[project.id] = project
        self._persist(project)

    def get_project(self, project_id: str) -> Optional[VideoProject]:
        return self._projects.get(project_id)

    def list_projects(self, status: Optional[ProjectStatus] = None) -> List[Dict[str, Any]]:
        projects = self._projects.values()
        if status:
            projects = [p for p in projects if p.status == status]
        return [{"id": p.id, "title": p.title, "status": p.status.value,
                 "format": p.format.value, "updated_at": p.updated_at}
                for p in projects]

    def update_status(self, project_id: str, status: ProjectStatus) -> bool:
        proj = self._projects.get(project_id)
        if not proj:
            return False
        proj.status = status
        proj.updated_at = datetime.now().isoformat()
        self._persist(proj)
        return True

    def delete_project(self, project_id: str) -> bool:
        if project_id not in self._projects:
            return False
        del self._projects[project_id]
        if self._storage_dir:
            f = self._storage_dir / f"{project_id}.json"
            f.unlink(missing_ok=True)
        return True

    def _persist(self, project: VideoProject):
        if not self._storage_dir:
            return
        f = self._storage_dir / f"{project.id}.json"
        f.write_text(json.dumps(project.to_dict(), indent=2), encoding="utf-8")
