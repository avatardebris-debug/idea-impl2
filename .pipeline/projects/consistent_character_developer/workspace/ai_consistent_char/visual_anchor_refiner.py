"""Visual Anchor Refiner — improves textual descriptions for more consistent image generation."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class VisualAnchorRefiner:
    """Refines visual anchor text for characters using an LLM.

    If no LLM client is available, uses a deterministic rule-based enhancer
    to still improve the descriptions without API calls.
    """

    # Attributes that make for strong visual anchors in image generation
    ANCHOR_KEYWORDS = [
        "hair", "eyes", "height", "build", "skin", "face", "scar",
        "tattoo", "clothing", "costume", "uniform", "age", "beard",
        "mustache", "glasses", "hat", "color",
    ]

    def __init__(self, llm_client: Any = None, llm_config: Any = None):
        """Initialize the refiner.

        Args:
            llm_client: Optional LLM client (e.g., openai.Client).
            llm_config: Optional LLM configuration object.
        """
        self.llm_client = llm_client
        self.llm_config = llm_config
        self._use_llm = llm_client is not None

    def refine_visual_anchor(self, character_id: str, current_anchor: str, physical_description: str) -> str:
        """Refine the visual anchor text for a character.

        Args:
            character_id: The character's ID.
            current_anchor: The existing visual anchor text.
            physical_description: The character's full physical description.

        Returns:
            Improved visual anchor text.
        """
        if self._use_llm:
            return self._refine_with_llm(character_id, current_anchor, physical_description)
        return self._refine_rule_based(current_anchor, physical_description)

    def refine_registry(self, registry: Any) -> Dict[str, str]:
        """Refine visual anchors for all characters in a registry.

        Args:
            registry: A CharacterRegistry object with a .characters dict.

        Returns:
            Dict mapping character_id to refined visual anchor text.
        """
        refined: Dict[str, str] = {}
        for char_id, character in registry.characters.items():
            original = getattr(character, "visual_anchor", "") or ""
            physical = getattr(character, "physical_description", "") or ""
            improved = self.refine_visual_anchor(char_id, original, physical)
            refined[char_id] = improved
            character.visual_anchor = improved
            logger.debug("Refined anchor for '%s': %s -> %s", char_id, original[:40], improved[:40])
        return refined

    def score_anchor(self, anchor: str) -> float:
        """Score an anchor text for specificity (0.0 - 1.0).

        Higher scores indicate more specific, image-generation-friendly descriptions.

        Args:
            anchor: The visual anchor text to score.

        Returns:
            Score from 0.0 (weak) to 1.0 (strong).
        """
        if not anchor:
            return 0.0
        lower = anchor.lower()
        keyword_hits = sum(1 for kw in self.ANCHOR_KEYWORDS if kw in lower)
        word_count = len(anchor.split())
        # Score based on: keyword coverage, word count (optimal 10-30 words)
        keyword_score = min(keyword_hits / 4.0, 1.0)
        length_score = min(word_count / 20.0, 1.0) if word_count <= 20 else max(0, 1.0 - (word_count - 20) / 40.0)
        return round((keyword_score * 0.7 + length_score * 0.3), 3)

    def _refine_rule_based(self, current_anchor: str, physical_description: str) -> str:
        """Deterministic rule-based refinement."""
        parts: List[str] = []

        # Keep existing anchor if it has content
        if current_anchor and current_anchor.strip():
            parts.append(current_anchor.strip())

        # Extract key physical attributes not already in anchor
        existing_lower = current_anchor.lower() if current_anchor else ""
        for sentence in physical_description.replace(";", ".").split("."):
            sentence = sentence.strip()
            if not sentence:
                continue
            s_lower = sentence.lower()
            # Add if it contains anchor keywords and isn't already captured
            for kw in self.ANCHOR_KEYWORDS:
                if kw in s_lower and sentence not in existing_lower:
                    parts.append(sentence)
                    break

        # De-duplicate and join
        seen = set()
        unique_parts = []
        for p in parts:
            normalized = p.lower().strip(".,; ")
            if normalized not in seen:
                seen.add(normalized)
                unique_parts.append(p)

        refined = "; ".join(unique_parts[:4])  # cap at 4 descriptors for clarity
        return refined if refined else current_anchor

    def _refine_with_llm(self, character_id: str, current_anchor: str, physical_description: str) -> str:
        """Refine using LLM (stub — override with real implementation)."""
        # In a real implementation, this would call the LLM API
        # For now, fall back to rule-based
        logger.info("LLM refinement requested but using rule-based fallback for '%s'", character_id)
        return self._refine_rule_based(current_anchor, physical_description)
