"""SQLite storage layer for thesis project metadata."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from datetime import datetime

from .models import BibliographyEntry, CitationStyle, Draft, InlineCitation, Section, SectionName, Source, ThesisProject


class Database:
    """Thin SQLite wrapper for thesis project persistence."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    # ── helpers ────────────────────────────────────────────────

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    topic TEXT NOT NULL,
                    sources TEXT NOT NULL DEFAULT '[]',
                    draft TEXT,
                    citation_style TEXT NOT NULL DEFAULT 'apa',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.commit()

    # ── helpers to serialise / deserialise ─────────────────────

    @staticmethod
    def _src_to_dict(s: Source) -> Dict[str, Any]:
        d = s.model_dump()
        d["created_at"] = s.created_at.isoformat()
        return d

    @staticmethod
    def _src_from_dict(d: Dict[str, Any]) -> Source:
        return Source(**d)

    @staticmethod
    def _draft_to_dict(d: Draft) -> Dict[str, Any]:
        result = d.model_dump()
        result["generated_at"] = d.generated_at.isoformat()
        return result

    @staticmethod
    def _draft_from_dict(d: Dict[str, Any]) -> Draft:
        # Rebuild nested models
        sections = [Section(**s) for s in d.get("sections", [])]
        bib = [BibliographyEntry(**b) for b in d.get("bibliography", [])]
        inline_cites = [InlineCitation(**c) for sec in sections for c in sec.get("inline_citations", [])]
        # Re-attach inline_citations to sections
        idx = 0
        for sec in sections:
            sec.inline_citations = []
            while idx < len(inline_cites) and inline_cites[idx].position < 1000000:
                sec.inline_citations.append(inline_cites[idx])
                idx += 1
        return Draft(
            topic=d["topic"],
            sections=sections,
            bibliography=bib,
            citation_style=CitationStyle(d["citation_style"]),
            generated_at=d.get("generated_at"),
        )

    # ── CRUD ───────────────────────────────────────────────────

    def create_project(self, topic: str) -> ThesisProject:
        project = ThesisProject(topic=topic)
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO projects (id, topic, sources, draft, citation_style, created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
                (
                    project.id,
                    project.topic,
                    json.dumps([self._src_to_dict(s) for s in project.sources]),
                    None,
                    project.citation_style.value,
                    project.created_at.isoformat(),
                    project.updated_at.isoformat(),
                ),
            )
            conn.commit()
        return project

    def get_project(self, project_id: str) -> Optional[ThesisProject]:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        if not row:
            return None
        sources = [self._src_from_dict(s) for s in json.loads(row["sources"])]
        draft = self._draft_from_dict(json.loads(row["draft"])) if row["draft"] else None
        return ThesisProject(
            id=row["id"],
            topic=row["topic"],
            sources=sources,
            draft=draft,
            citation_style=CitationStyle(row["citation_style"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def update_project(self, project: ThesisProject) -> None:
        with self._conn() as conn:
            conn.execute(
                "UPDATE projects SET topic=?, sources=?, draft=?, citation_style=?, updated_at=? WHERE id=?",
                (
                    project.topic,
                    json.dumps([self._src_to_dict(s) for s in project.sources]),
                    json.dumps(self._draft_to_dict(project.draft)) if project.draft else None,
                    project.citation_style.value,
                    project.updated_at.isoformat(),
                    project.id,
                ),
            )
            conn.commit()

    def add_source_to_project(self, project_id: str, source: Source) -> bool:
        project = self.get_project(project_id)
        if not project:
            return False
        project.add_source(source)
        self.update_project(project)
        return True

    def remove_source_from_project(self, project_id: str, source_id: str) -> bool:
        project = self.get_project(project_id)
        if not project:
            return False
        removed = project.remove_source(source_id)
        if removed:
            self.update_project(project)
        return removed

    def set_citation_style(self, project_id: str, style: CitationStyle) -> bool:
        project = self.get_project(project_id)
        if not project:
            return False
        project.citation_style = style
        self.update_project(project)
        return True

    def set_draft(self, project_id: str, draft: Draft) -> bool:
        project = self.get_project(project_id)
        if not project:
            return False
        project.draft = draft
        self.update_project(project)
        return True

    def list_projects(self) -> List[ThesisProject]:
        with self._conn() as conn:
            rows = conn.execute("SELECT * FROM projects ORDER BY updated_at DESC").fetchall()
        projects = []
        for row in rows:
            sources = [self._src_from_dict(s) for s in json.loads(row["sources"])]
            draft = self._draft_from_dict(json.loads(row["draft"])) if row["draft"] else None
            projects.append(ThesisProject(
                id=row["id"],
                topic=row["topic"],
                sources=sources,
                draft=draft,
                citation_style=CitationStyle(row["citation_style"]),
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            ))
        return projects

