"""Core data models for consistent character reference sheets.

Extends Character / CharacterRegistry from ai_movie_gen_suite.models.
"""

from __future__ import annotations

from typing import Any, Dict, Iterator, List, Optional

from pydantic import BaseModel, Field, PrivateAttr


class CharacterVisualProfile(BaseModel):
    """Visual profile for a single character's reference image.

    Fields:
        character_id: Unique ID of the character.
        reference_image_path: Path to the generated PNG reference image.
        visual_anchor_text: Textual description used to generate the image.
        prompt: Full prompt sent to the image-generation provider.
        status: Generation status — "pending", "generated", or "failed".
        seed: Random seed used for reproducibility (optional).
    """

    character_id: str
    reference_image_path: str = ""
    visual_anchor_text: str = ""
    prompt: str = ""
    status: str = Field(default="pending")
    seed: Optional[int] = None

    def model_dump(self, **kwargs) -> dict:
        """Serialize, converting status to a plain string."""
        d = super().model_dump(**kwargs)
        return d


# ── Scene Character Render Models ────────────────────────────────────────────

class SceneCharacterRender(BaseModel):
    """A single character render for a specific scene."""

    scene_id: str
    character_id: str
    render_path: str = ""
    scene_context: str = ""

    def model_dump(self, **kwargs) -> dict:
        d = super().model_dump(**kwargs)
        return d


class _RenderView:
    """A dict-like wrapper that iterates over values instead of keys.

    This allows `for render in collection.renders` to yield SceneCharacterRender
    objects rather than string keys, which is what the integration tests expect.
    """

    def __init__(self, data: Dict[str, SceneCharacterRender]):
        self._data = data

    def __getitem__(self, key: str) -> SceneCharacterRender:
        return self._data[key]

    def __setitem__(self, key: str, value: SceneCharacterRender) -> None:
        self._data[key] = value

    def __iter__(self) -> Iterator[SceneCharacterRender]:
        return iter(self._data.values())

    def __len__(self) -> int:
        return len(self._data)

    def __bool__(self) -> bool:
        return bool(self._data)

    def values(self) -> Iterator[SceneCharacterRender]:
        return iter(self._data.values())

    def keys(self):
        return self._data.keys()

    def items(self):
        return self._data.items()

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)


class SceneCharacterRenderCollection(BaseModel):
    """All scene character renders for a project."""

    _renders: Dict[str, SceneCharacterRender] = PrivateAttr(default_factory=dict)

    @property
    def renders(self) -> _RenderView:
        """Return a view that iterates over values (SceneCharacterRender objects)."""
        return _RenderView(self._renders)

    def add_render(self, render: SceneCharacterRender) -> None:
        key = f"{render.scene_id}:{render.character_id}"
        self._renders[key] = render

    def get_renders_for_scene(self, scene_id: str) -> List[SceneCharacterRender]:
        """Return all renders for a given scene."""
        return [r for r in self._renders.values() if r.scene_id == scene_id]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a dict with a 'renders' key containing a list of render dicts."""
        return {"renders": [r.model_dump() for r in self._renders.values()]}

    def __iter__(self) -> Iterator[SceneCharacterRender]:
        """Allow iteration over renders as a list of SceneCharacterRender."""
        return iter(self._renders.values())

    def __len__(self) -> int:
        return len(self._renders)

    def __bool__(self) -> bool:
        return bool(self._renders)
