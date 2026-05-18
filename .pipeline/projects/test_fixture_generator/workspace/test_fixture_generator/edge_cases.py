"""
edge_cases.py — Failure-mode fixture mutator.

Takes a valid, working fixture (dict or list of dicts) and systematically
produces variants designed to exercise the error-handling paths in the code
being tested — not the happy path.

Mutation catalogue
------------------
  NULL_FIELD       — sets one field to None
  EMPTY_STRING     — sets a string field to ""
  WRONG_TYPE       — replaces an int with a string, bool with int, etc.
  MISSING_KEY      — removes a required key entirely
  BOUNDARY_INT     — replaces an int with 0, -1, sys.maxsize, 2**31-1
  OVERLONG_STRING  — replaces a string with 10_000 Unicode characters
  ENCODING_BOMB    — injects NUL bytes, surrogates, RTL markers
  EXTRA_KEY        — adds an unexpected field
  NEGATIVE         — negates numeric values
  EMPTY_LIST       — replaces a list field with []
  BOOL_FLIP        — flips booleans

Usage
-----
    from test_fixture_generator.edge_cases import EdgeCaseMutator

    mutator = EdgeCaseMutator()
    base = {"user_id": 42, "email": "a@b.com", "active": True}
    cases = mutator.all_mutations(base)
    # cases is a list of (MutationType, mutated_dict) tuples
"""

from __future__ import annotations

import copy
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class MutationType(str, Enum):
    NULL_FIELD       = "null_field"
    EMPTY_STRING     = "empty_string"
    WRONG_TYPE       = "wrong_type"
    MISSING_KEY      = "missing_key"
    BOUNDARY_INT     = "boundary_int"
    OVERLONG_STRING  = "overlong_string"
    ENCODING_BOMB    = "encoding_bomb"
    EXTRA_KEY        = "extra_key"
    NEGATIVE         = "negative"
    EMPTY_LIST       = "empty_list"
    BOOL_FLIP        = "bool_flip"


@dataclass
class MutationCase:
    mutation_type: MutationType
    target_field: Optional[str]         # which field was mutated (None = structural)
    fixture: Dict[str, Any]
    description: str


class EdgeCaseMutator:
    """
    Produces mutation cases from a single valid fixture dict.
    Each mutation changes exactly one thing so failures can be attributed.
    """

    # Boundary values for integer fields
    _INT_BOUNDARIES = [0, -1, 1, sys.maxsize, -(sys.maxsize + 1), 2**31 - 1, -(2**31)]

    # Strings that historically cause parsing / encoding failures
    _ENCODING_BOMBS = [
        "\x00",                          # NUL byte
        "\ud800",                        # lone surrogate
        "\u202e injected \u202c",        # RTL override
        "نص عربي",                       # Arabic RTL text
        "𝕳𝖊𝖑𝖑𝖔",                         # Mathematical bold (multi-byte)
        "\n\r\t\x0b\x0c",               # Whitespace mix
        "'; DROP TABLE users; --",       # SQL injection attempt
        "<script>alert(1)</script>",     # XSS attempt
    ]

    def all_mutations(self, fixture: Dict[str, Any]) -> List[MutationCase]:
        """Return every applicable mutation for the given fixture."""
        cases: List[MutationCase] = []
        for key, value in fixture.items():
            cases.extend(self._mutate_field(fixture, key, value))

        # Structural mutations (not field-specific)
        cases.extend(self._structural_mutations(fixture))
        return cases

    def targeted(
        self, fixture: Dict[str, Any], field: str, mutation: MutationType
    ) -> MutationCase:
        """Apply a single specific mutation to a specific field."""
        mutated = copy.deepcopy(fixture)
        val = mutated[field]
        result = self._apply(mutated, field, val, mutation)
        return result

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _mutate_field(
        self, fixture: Dict[str, Any], key: str, value: Any
    ) -> List[MutationCase]:
        cases: List[MutationCase] = []

        # NULL_FIELD — always applicable
        m = copy.deepcopy(fixture)
        m[key] = None
        cases.append(MutationCase(MutationType.NULL_FIELD, key, m,
                                  f"Field '{key}' set to None"))

        # MISSING_KEY
        m = copy.deepcopy(fixture)
        del m[key]
        cases.append(MutationCase(MutationType.MISSING_KEY, key, m,
                                  f"Field '{key}' removed entirely"))

        if isinstance(value, str):
            # EMPTY_STRING
            m = copy.deepcopy(fixture); m[key] = ""
            cases.append(MutationCase(MutationType.EMPTY_STRING, key, m,
                                      f"Field '{key}' set to empty string"))

            # WRONG_TYPE — flip to int
            m = copy.deepcopy(fixture); m[key] = 99999
            cases.append(MutationCase(MutationType.WRONG_TYPE, key, m,
                                      f"Field '{key}' changed str→int"))

            # OVERLONG_STRING
            m = copy.deepcopy(fixture); m[key] = "A" * 10_000
            cases.append(MutationCase(MutationType.OVERLONG_STRING, key, m,
                                      f"Field '{key}' set to 10k-char string"))

            # ENCODING_BOMB — one case per bomb string
            for bomb in self._ENCODING_BOMBS:
                m = copy.deepcopy(fixture); m[key] = bomb
                cases.append(MutationCase(MutationType.ENCODING_BOMB, key, m,
                                          f"Field '{key}' = encoding bomb: {repr(bomb[:20])}"))

        elif isinstance(value, bool):
            # BOOL_FLIP
            m = copy.deepcopy(fixture); m[key] = not value
            cases.append(MutationCase(MutationType.BOOL_FLIP, key, m,
                                      f"Field '{key}' flipped bool"))
            # WRONG_TYPE — bool to string
            m = copy.deepcopy(fixture); m[key] = str(value)
            cases.append(MutationCase(MutationType.WRONG_TYPE, key, m,
                                      f"Field '{key}' changed bool→str"))

        elif isinstance(value, int):
            for boundary in self._INT_BOUNDARIES:
                m = copy.deepcopy(fixture); m[key] = boundary
                cases.append(MutationCase(MutationType.BOUNDARY_INT, key, m,
                                          f"Field '{key}' = boundary int {boundary}"))

            # WRONG_TYPE — int to string
            m = copy.deepcopy(fixture); m[key] = str(value)
            cases.append(MutationCase(MutationType.WRONG_TYPE, key, m,
                                      f"Field '{key}' changed int→str"))

            # NEGATIVE
            if value >= 0:
                m = copy.deepcopy(fixture); m[key] = -abs(value) - 1
                cases.append(MutationCase(MutationType.NEGATIVE, key, m,
                                          f"Field '{key}' negated to {m[key]}"))

        elif isinstance(value, float):
            for boundary in [0.0, -1.0, float("inf"), float("-inf"), float("nan")]:
                m = copy.deepcopy(fixture); m[key] = boundary
                cases.append(MutationCase(MutationType.BOUNDARY_INT, key, m,
                                          f"Field '{key}' = float boundary {boundary}"))

        elif isinstance(value, list):
            m = copy.deepcopy(fixture); m[key] = []
            cases.append(MutationCase(MutationType.EMPTY_LIST, key, m,
                                      f"Field '{key}' set to empty list"))

        return cases

    def _structural_mutations(self, fixture: Dict[str, Any]) -> List[MutationCase]:
        """Mutations that affect the shape of the record rather than a single field."""
        cases: List[MutationCase] = []

        # EXTRA_KEY — add an unexpected field
        m = copy.deepcopy(fixture)
        m["__unexpected_field__"] = "injected"
        cases.append(MutationCase(MutationType.EXTRA_KEY, None, m,
                                  "Added unexpected field '__unexpected_field__'"))

        # Completely empty record
        cases.append(MutationCase(MutationType.MISSING_KEY, None, {},
                                  "Completely empty record"))

        return cases

    def _apply(
        self, fixture: Dict[str, Any], field: str, value: Any, mutation: MutationType
    ) -> MutationCase:
        """Apply a single named mutation to one field in an already-deep-copied fixture."""
        if mutation == MutationType.NULL_FIELD:
            fixture[field] = None
        elif mutation == MutationType.EMPTY_STRING:
            fixture[field] = ""
        elif mutation == MutationType.MISSING_KEY:
            del fixture[field]
        elif mutation == MutationType.WRONG_TYPE:
            fixture[field] = str(value) if not isinstance(value, str) else 0
        elif mutation == MutationType.BOUNDARY_INT:
            fixture[field] = 0
        elif mutation == MutationType.OVERLONG_STRING:
            fixture[field] = "X" * 10_000
        elif mutation == MutationType.BOOL_FLIP and isinstance(value, bool):
            fixture[field] = not value
        elif mutation == MutationType.NEGATIVE and isinstance(value, (int, float)):
            fixture[field] = -abs(value) - 1
        elif mutation == MutationType.EMPTY_LIST:
            fixture[field] = []
        elif mutation == MutationType.EXTRA_KEY:
            fixture["__unexpected__"] = "injected"

        return MutationCase(mutation, field, fixture,
                            f"{mutation.value} applied to '{field}'")
