"""FastAPI routes for the thesis writer API."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException

from ..models import Draft, Source, CitationStyle
from ..citation.engine import CitationEngine
from ..citation.formatters import APAFormatter, MLAFormatter, ChicagoFormatter, IEEEFormatter
from ..sources import SourceManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["thesis"])

# Module-level source manager instance
_source_manager = SourceManager()


# ── Project routes ────────────────────────────────────────────────

@router.post("/projects/{project_id}/sources")
async def add_source(
    project_id: str,
    title: str,
    authors: list[str],
    year: Optional[int] = None,
    abstract: str = "",
    url: Optional[str] = None,
):
    """Add a source to a project."""
    source = _source_manager.add_manual(
        project_id=project_id,
        title=title,
        authors=authors,
        year=year,
        abstract=abstract,
        url=url,
    )
    return {"status": "ok", "source": source.model_dump()}


@router.get("/projects/{project_id}/sources")
async def get_sources(project_id: str):
    """Get all sources for a project."""
    sources = _source_manager.get_sources(project_id)
    return {"sources": [s.model_dump() for s in sources]}


# ── Draft routes ──────────────────────────────────────────────────

@router.post("/projects/{project_id}/drafts")
async def create_draft(
    project_id: str,
    topic: str,
    title: str,
    citation_style: str = "APA",
):
    """Create a new thesis draft."""
    style_map = {
        "APA": CitationStyle.APA,
        "MLA": CitationStyle.MLA,
        "CHICAGO": CitationStyle.CHICAGO,
        "IEEE": CitationStyle.IEEE,
    }
    style = style_map.get(citation_style, CitationStyle.APA)

    draft = Draft(
        id=f"draft_{project_id}",
        topic=topic,
        title=title,
        citation_style=style,
    )
    return {"status": "ok", "draft": draft.model_dump()}


@router.get("/projects/{project_id}/drafts/{draft_id}")
async def get_draft(project_id: str, draft_id: str):
    """Get a draft by ID."""
    # In production, this would use DraftManager
    return {"draft": None}


@router.post("/projects/{project_id}/drafts/{draft_id}/generate")
async def generate_draft(
    project_id: str,
    draft_id: str,
):
    """Generate a thesis draft."""
    # In production, this would use GenerationPipeline
    return {"status": "ok", "message": "Generation started"}


@router.post("/projects/{project_id}/drafts/{draft_id}/verify")
async def verify_draft(
    project_id: str,
    draft_id: str,
):
    """Verify a thesis draft."""
    # In production, this would use VerificationEngine
    return {"status": "ok", "result": {"is_valid": True, "errors": [], "warnings": []}}


# ── Export routes ─────────────────────────────────────────────────

@router.get("/projects/{project_id}/drafts/{draft_id}/export/markdown")
async def export_markdown(project_id: str, draft_id: str):
    """Export a draft as Markdown."""
    # In production, this would use MarkdownExporter
    return {"status": "ok", "content": "# Draft\n\n"}


@router.get("/projects/{project_id}/drafts/{draft_id}/export/docx")
async def export_docx(project_id: str, draft_id: str):
    """Export a draft as DOCX."""
    # In production, this would use DocxExporter
    return {"status": "ok", "content": ""}
