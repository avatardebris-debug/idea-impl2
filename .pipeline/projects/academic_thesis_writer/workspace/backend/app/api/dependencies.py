"""FastAPI dependencies for the thesis writer API."""

from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, status
from pydantic import BaseModel

from ..citation.engine import CitationEngine
from ..citation.formatters import APAFormatter, MLAFormatter, ChicagoFormatter, IEEEFormatter
from ..models import CitationStyle


class CitationStyleValidator(BaseModel):
    """Validates and converts citation style strings."""

    style: str

    def get_citation_style(self) -> CitationStyle:
        """Convert string to CitationStyle enum."""
        style_map = {
            "APA": CitationStyle.APA,
            "MLA": CitationStyle.MLA,
            "CHICAGO": CitationStyle.CHICAGO,
            "IEEE": CitationStyle.IEEE,
        }
        style = style_map.get(self.style.upper())
        if not style:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid citation style: {self.style}. Must be one of: APA, MLA, CHICAGO, IEEE",
            )
        return style

    def get_formatter(self) -> type:
        """Get the formatter class for the citation style."""
        style_map = {
            CitationStyle.APA: APAFormatter,
            CitationStyle.MLA: MLAFormatter,
            CitationStyle.CHICAGO: ChicagoFormatter,
            CitationStyle.IEEE: IEEEFormatter,
        }
        return style_map[self.get_citation_style()]


def get_citation_engine(citation_style: str = "APA") -> CitationEngine:
    """Dependency to get a CitationEngine instance."""
    style_map = {
        "APA": CitationStyle.APA,
        "MLA": CitationStyle.MLA,
        "CHICAGO": CitationStyle.CHICAGO,
        "IEEE": CitationStyle.IEEE,
    }
    style = style_map.get(citation_style.upper(), CitationStyle.APA)
    return CitationEngine(style=style)


def validate_citation_style(citation_style: str = "APA") -> CitationStyleValidator:
    """Dependency to validate citation style."""
    return CitationStyleValidator(style=citation_style)
