"""Verification engine for thesis drafts.

Checks for structural integrity, citation consistency, and basic
plagiarism indicators.
"""

from __future__ import annotations

import logging
import re
from typing import List, Optional, Tuple

from ..models import Draft, DraftSection, Source
from ..citation.engine import CitationEngine

logger = logging.getLogger(__name__)


class VerificationEngine:
    """Verifies thesis drafts for quality and consistency."""

    def __init__(self, citation_engine: CitationEngine):
        self.citation_engine = citation_engine

    def verify(self, draft: Draft) -> VerificationResult:
        """Run all verification checks on a draft."""
        errors: List[str] = []
        warnings: List[str] = []

        # Check structure
        structure_errors = self._check_structure(draft)
        errors.extend(structure_errors)

        # Check citations
        citation_errors, citation_warnings = self._check_citations(draft)
        errors.extend(citation_errors)
        warnings.extend(citation_warnings)

        # Check for basic plagiarism indicators
        plagiarism_warnings = self._check_plagiarism_indicators(draft)
        warnings.extend(plagiarism_warnings)

        return VerificationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def _check_structure(self, draft: Draft) -> List[str]:
        """Check draft structure."""
        errors = []
        if not draft.topic:
            errors.append("Draft has no topic.")
        if not draft.sections:
            errors.append("Draft has no sections.")
        if not draft.abstract:
            errors.append("Draft has no abstract.")

        # Check for required sections
        required_sections = {"Introduction", "Conclusion"}
        existing_sections = {s.name for s in draft.sections}
        missing = required_sections - existing_sections
        if missing:
            errors.append(f"Missing required sections: {', '.join(missing)}")

        return errors

    def _check_citations(self, draft: Draft) -> Tuple[List[str], List[str]]:
        """Check citation consistency."""
        errors = []
        warnings = []

        # Check for uncited claims (heuristic: sentences with "according to", "studies show", etc.)
        suspicious_patterns = [
            r"\baccording to\b",
            r"\bstudies?\s+show\b",
            r"\bresearch\s+indicates\b",
            r"\bas\s+noted\s+by\b",
        ]

        for section in draft.sections:
            for sentence in re.split(r'[.!?]+', section.content):
                sentence = sentence.strip()
                if not sentence:
                    continue
                for pattern in suspicious_patterns:
                    if re.search(pattern, sentence, re.IGNORECASE):
                        # Check if there's a citation nearby
                        if not re.search(r'\(\w+,\s*\d{4}\)|\[\d+\]', sentence):
                            warnings.append(
                                f"Possible uncited claim in {section.name}: '{sentence[:50]}...'"
                            )

        return errors, warnings

    def _check_plagiarism_indicators(self, draft: Draft) -> List[str]:
        """Check for basic plagiarism indicators."""
        warnings = []

        # Check for excessive repetition
        for section in draft.sections:
            words = section.content.lower().split()
            if len(words) > 100:
                # Check for repeated phrases
                for i in range(len(words) - 10):
                    phrase = " ".join(words[i:i + 10])
                    if phrase in " ".join(words[i + 10:]):
                        warnings.append(
                            f"Possible repetition in {section.name}: '{phrase[:30]}...'"
                        )
                        break

        return warnings


class VerificationResult:
    """Result of a verification check."""

    def __init__(self, is_valid: bool, errors: List[str], warnings: List[str]):
        self.is_valid = is_valid
        self.errors = errors
        self.warnings = warnings

    def __str__(self) -> str:
        status = "PASS" if self.is_valid else "FAIL"
        lines = [f"Verification {status}:"]
        if self.errors:
            lines.append("Errors:")
            for error in self.errors:
                lines.append(f"  - {error}")
        if self.warnings:
            lines.append("Warnings:")
            for warning in self.warnings:
                lines.append(f"  - {warning}")
        return "\n".join(lines)
