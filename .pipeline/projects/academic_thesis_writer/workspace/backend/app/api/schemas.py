"""Pydantic schemas for API request/response validation."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class SourceCreate(BaseModel):
    """Schema for creating a new source."""

    title: str = Field(..., min_length=1, description="Title of the source")
    authors: List[str] = Field(default_factory=list, description="List of authors")
    year: Optional[int] = Field(None, description="Publication year")
    abstract: str = Field(default="", description="Abstract of the source")
    url: Optional[str] = Field(None, description="URL to the source")


class SourceResponse(BaseModel):
    """Schema for source response."""

    id: str
    title: str
    authors: List[str]
    year: Optional[int] = None
    abstract: str = ""
    url: Optional[str] = None
    source_type: str = "manual"

    class Config:
        from_attributes = True


class DraftCreate(BaseModel):
    """Schema for creating a new draft."""

    topic: str = Field(..., min_length=1, description="Thesis topic")
    title: str = Field(..., min_length=1, description="Draft title")
    citation_style: str = Field(default="APA", description="Citation style (APA, MLA, CHICAGO, IEEE)")


class DraftResponse(BaseModel):
    """Schema for draft response."""

    id: str
    topic: str
    citation_style: str
    sections_count: int = 0
    generated_at: Optional[str] = None

    class Config:
        from_attributes = True


class VerificationResult(BaseModel):
    """Schema for verification result."""

    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class GenerationStatus(BaseModel):
    """Schema for generation status."""

    status: str
    message: str
    draft_id: Optional[str] = None
