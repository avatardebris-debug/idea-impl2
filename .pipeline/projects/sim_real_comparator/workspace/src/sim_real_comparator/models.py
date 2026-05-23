"""Data models for sim_real_comparator results."""

from pydantic import BaseModel, Field


class FrameResult(BaseModel):
    """Per-frame similarity result."""

    frame_index: int
    ssim: float = Field(..., ge=0.0, le=1.0)
    phash_distance: float = Field(..., ge=0.0, le=1.0)
    clip_similarity: float = Field(..., ge=0.0, le=1.0)
    color_distance: float = Field(..., ge=0.0, le=1.0)


class GlobalResult(BaseModel):
    """Global aggregated similarity result."""

    global_score: float = Field(..., ge=0.0, le=1.0)
    avg_ssim: float = Field(..., ge=0.0, le=1.0)
    avg_phash_similarity: float = Field(..., ge=0.0, le=1.0)
    avg_clip_similarity: float = Field(..., ge=0.0, le=1.0)
    avg_color_distance: float = Field(..., ge=0.0, le=1.0)
    weights: dict = Field(default={"ssim": 0.25, "phash": 0.25, "clip": 0.25, "color": 0.25})
