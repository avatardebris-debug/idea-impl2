"""ai_consistent_char — Character consistency for AI movie generation.

This package provides tools for generating consistent character representations
across all scenes in a screenplay, including:

- Reference image generation
- Per-scene character rendering
- Reference sheet generation
- Pipeline integration
"""

from __future__ import annotations

from ai_consistent_char.image_provider import (
    CharacterImageProvider,
    DummyCharacterImageProvider,
    LLMCharacterImageProvider,
)
from ai_consistent_char.models import (
    SceneCharacterRender,
    SceneCharacterRenderCollection,
)
from ai_consistent_char.pipeline_extension import PipelineExtension
from ai_consistent_char.reference_sheet_generator import ReferenceSheetGenerator
from ai_consistent_char.scene_character_renderer import SceneCharacterRenderer
from ai_consistent_char.stages.scene_character_renderer import SceneCharacterRendererStage

__all__ = [
    "CharacterImageProvider",
    "DummyCharacterImageProvider",
    "LLMCharacterImageProvider",
    "PipelineExtension",
    "ReferenceSheetGenerator",
    "SceneCharacterRender",
    "SceneCharacterRenderCollection",
    "SceneCharacterRenderer",
    "SceneCharacterRendererStage",
]
