"""Advanced hybrid classifier combining ML prototypes with LLM intelligence.

Provides confidence-weighted classification with fallback strategies.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import yaml

from supportagent.llm_adapters import (
    BaseLLMAdapter,
    LLMConfig,
    LLMMessage,
    LLMProvider,
    create_llm_adapter,
)

logger = logging.getLogger(__name__)


@dataclass
class ClassificationResult:
    """Result of a classification operation."""

    category: str
    confidence: float
    reasoning: str
    subcategories: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "subcategories": self.subcategories,
            "metadata": self.metadata,
        }

    @property
    def is_confident(self) -> bool:
        return self.confidence >= 0.7

    @property
    def needs_review(self) -> bool:
        return self.confidence < 0.5


class MLClassifier:
    """Keyword and prototype-based ML classifier (no external dependencies)."""

    def __init__(self, config_path: Optional[str] = None):
        self._category_weights: Dict[str, List[str]] = {}
        self._subcategory_weights: Dict[str, Dict[str, float]] = {}
        self._negative_patterns: Dict[str, List[str]] = {}
        self._load_config(config_path)

    def _load_config(self, config_path: Optional[str]):
        """Load ML classification config."""
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), "config", "ml_category_prototypes.yaml"
            )

        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                data = yaml.safe_load(f) or {}

            for category, config in data.items():
                if isinstance(config, dict):
                    self._category_weights[category] = config.get(
                        "keywords", [category]
                    )
                    self._subcategory_weights[category] = config.get(
                        "subcategories", {}
                    )
                    self._negative_patterns[category] = config.get(
                        "negative_keywords", []
                    )

    def classify(
        self, text: str, categories: Optional[List[str]] = None
    ) -> Tuple[str, float]:
        """Classify text using keyword matching.

        Returns:
            Tuple of (category, confidence)
        """
        text_lower = text.lower()
        scores: Dict[str, float] = {}

        for category, keywords in self._category_weights.items():
            if categories and category not in categories:
                continue

            score = 0.0
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    score += 1.0

            # Normalize by number of keywords
            if keywords:
                score /= len(keywords)

            # Apply negative patterns
            for neg_keyword in self._negative_patterns.get(category, []):
                if neg_keyword.lower() in text_lower:
                    score *= 0.5

            scores[category] = score

        if not scores:
            return (categories[0] if categories else "general"), 0.3

        best_category = max(scores, key=scores.get)
        best_score = min(scores[best_category], 1.0)

        # Scale confidence based on score
        confidence = best_score * 0.8 + 0.1  # Range: 0.1 to 0.9

        return best_category, confidence

    def get_subcategory_scores(
        self, category: str
    ) -> Dict[str, float]:
        """Get subcategory scores for a category."""
        return self._subcategory_weights.get(category, {})


class LLMClassifier:
    """LLM-based classifier with structured output."""

    def __init__(
        self,
        adapter: Optional[BaseLLMAdapter] = None,
        config: Optional[LLMConfig] = None,
    ):
        self.adapter = adapter or create_llm_adapter(
            LLMProvider.MOCK, config
        )

    def classify(
        self,
        text: str,
        categories: List[str],
        system_prompt: Optional[str] = None,
    ) -> ClassificationResult:
        """Classify text using LLM.

        Returns:
            ClassificationResult with category, confidence, and reasoning.
        """
        if system_prompt is None:
            system_prompt = self._default_system_prompt(categories)

        messages = [
            LLMMessage("system", system_prompt),
            LLMMessage("user", text),
        ]

        response = self.adapter.chat(messages, temperature=0.0)

        return self._parse_llm_response(response, categories)

    def _default_system_prompt(self, categories: List[str]) -> str:
        return f"""You are a professional customer support classification assistant.

Your task is to classify customer support tickets into exactly one category from the provided list.

Categories: {', '.join(categories)}

Rules:
1. Choose the SINGLE most appropriate category.
2. If the ticket mentions multiple topics, choose the primary concern.
3. Be objective and evidence-based.
4. If uncertain, choose the most likely category with lower confidence.

Respond in JSON format only:
{{
    "category": "<one of the categories>",
    "confidence": <float 0-1>,
    "reasoning": "<brief explanation>",
    "subcategories": {{"<subcat>": <score 0-1>}}
}}"""

    def _parse_llm_response(
        self, response: LLMResponse, categories: List[str]
    ) -> ClassificationResult:
        """Parse LLM response into ClassificationResult."""
        content = response.content.strip()

        # Remove markdown code blocks if present
        if content.startswith("```"):
            lines = content.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            content = "\n".join(lines)

        try:
            data = json.loads(content)
            category = data.get("category", categories[0] if categories else "general")
            confidence = float(data.get("confidence", 0.5))
            reasoning = data.get("reasoning", "No reasoning provided")
            subcategories = data.get("subcategories", {})

            # Validate category
            if categories and category not in categories:
                logger.warning(
                    f"LLM returned invalid category '{category}'. "
                    f"Using first available category."
                )
                category = categories[0]
                confidence = 0.3

            return ClassificationResult(
                category=category,
                confidence=confidence,
                reasoning=reasoning,
                subcategories=subcategories,
                metadata={"model": response.model, "usage": response.usage},
            )
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return ClassificationResult(
                category=categories[0] if categories else "general",
                confidence=0.3,
                reasoning="Failed to parse LLM response",
            )


class HybridClassifier:
    """Hybrid classifier combining ML and LLM for robust classification.

    Uses ML for fast initial classification and LLM for complex cases.
    Implements confidence-weighted fusion.
    """

    def __init__(
        self,
        ml_config_path: Optional[str] = None,
        llm_config: Optional[LLMConfig] = None,
        llm_adapter: Optional[BaseLLMAdapter] = None,
        ml_threshold: float = 0.7,
        llm_threshold: float = 0.5,
        fallback_to_ml: bool = True,
    ):
        self.ml_classifier = MLClassifier(ml_config_path)
        self.llm_classifier = LLMClassifier(llm_adapter, llm_config)
        self.ml_threshold = ml_threshold
        self.llm_threshold = llm_threshold
        self.fallback_to_ml = fallback_to_ml

    def classify(
        self,
        text: str,
        categories: Optional[List[str]] = None,
        use_llm: Optional[bool] = None,
    ) -> ClassificationResult:
        """Classify text using hybrid approach.

        Args:
            text: Input text to classify.
            categories: Optional list of valid categories.
            use_llm: Force LLM classification (None = auto).

        Returns:
            ClassificationResult with category, confidence, and reasoning.
        """
        # Determine if we should use LLM
        if use_llm is None:
            use_llm = self._should_use_llm(text)

        if use_llm:
            return self._classify_with_llm(text, categories)
        else:
            return self._classify_with_ml(text, categories)

    def _should_use_llm(self, text: str) -> bool:
        """Determine if LLM should be used for this text."""
        # Use LLM for complex/ambiguous cases
        indicators = [
            len(text) > 500,  # Long text
            "?" in text,  # Questions
            "not" in text.lower() and "but" in text.lower(),  # Complex negation
            any(
                word in text.lower()
                for word in ["complex", "confused", "multiple", "both"]
            ),
        ]
        return any(indicators)

    def _classify_with_ml(
        self, text: str, categories: Optional[List[str]]
    ) -> ClassificationResult:
        """Classify using ML approach."""
        category, confidence = self.ml_classifier.classify(text, categories)

        # Get subcategory scores
        subcategories = self.ml_classifier.get_subcategory_scores(category)

        return ClassificationResult(
            category=category,
            confidence=confidence,
            reasoning=f"ML classification with {confidence:.2f} confidence",
            subcategories=subcategories,
            metadata={"method": "ml"},
        )

    def _classify_with_llm(
        self, text: str, categories: Optional[List[str]]
    ) -> ClassificationResult:
        """Classify using LLM approach."""
        valid_categories = categories or list(
            self.ml_classifier._category_weights.keys()
        )

        result = self.llm_classifier.classify(text, valid_categories)

        # If LLM confidence is low, try ML as fallback
        if result.confidence < self.llm_threshold and self.fallback_to_ml:
            ml_category, ml_confidence = self.ml_classifier.classify(
                text, valid_categories
            )
            if ml_confidence > result.confidence:
                logger.info(
                    f"LLM confidence ({result.confidence:.2f}) < ML "
                    f"({ml_confidence:.2f}). Using ML result."
                )
                result.category = ml_category
                result.confidence = ml_confidence
                result.reasoning = (
                    f"LLM confidence too low. Fallback to ML: {result.reasoning}"
                )

        return result

    def classify_batch(
        self,
        texts: List[str],
        categories: Optional[List[str]] = None,
    ) -> List[ClassificationResult]:
        """Classify a batch of texts."""
        return [self.classify(text, categories) for text in texts]

    def get_category_distribution(
        self, texts: List[str], categories: Optional[List[str]] = None
    ) -> Dict[str, int]:
        """Get category distribution for a batch of texts."""
        distribution: Dict[str, int] = {}
        results = self.classify_batch(texts, categories)

        for result in results:
            distribution[result.category] = distribution.get(result.category, 0) + 1

        return distribution
