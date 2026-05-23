"""Primitive base class and data model for robot action primitives."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

VALID_CATEGORIES = frozenset({
    "locomotion", "manipulation", "observation", "force", "control_flow"
})


@dataclass
class Primitive(ABC):
    """Base class defining the canonical interface for all robot action primitives.

    Every concrete primitive subclass must define:
      - name: unique identifier for the primitive
      - category: one of 'locomotion', 'manipulation', 'observation', 'force', 'control_flow'
      - parameters: dict describing expected parameters
      - description: human-readable description
      - preconditions: list of strings describing preconditions
      - postconditions: list of strings describing postconditions

    Subclasses should call super().__init__() with all required keyword arguments.
    """

    name: str
    category: str
    parameters: Dict[str, str]
    description: str = ""
    preconditions: List[str] = field(default_factory=list)
    postconditions: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate fields after dataclass initialization."""
        # Validate name
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError(f"Primitive 'name' must be a non-empty string, got: {self.name!r}")
        if not self.name.islower() and '_' not in self.name:
            raise ValueError(
                f"Primitive 'name' must be lowercase with underscores, got: {self.name!r}"
            )

        # Validate category
        if not isinstance(self.category, str):
            raise TypeError(
                f"Primitive 'category' must be a string, got: {type(self.category).__name__}"
            )
        if self.category not in VALID_CATEGORIES:
            raise ValueError(
                f"Primitive 'category' must be one of {VALID_CATEGORIES}, got: {self.category!r}"
            )

        # Validate parameters
        if not isinstance(self.parameters, dict):
            raise TypeError(
                f"Primitive 'parameters' must be a dict, got: {type(self.parameters).__name__}"
            )
        for k, v in self.parameters.items():
            if not isinstance(k, str):
                raise TypeError(
                    f"Primitive 'parameters' keys must be strings, got key type: {type(k).__name__}"
                )
            if not isinstance(v, str):
                raise TypeError(
                    f"Primitive 'parameters' values must be strings, got value type for key '{k}': {type(v).__name__}"
                )

        # Validate description
        if not isinstance(self.description, str):
            raise TypeError(
                f"Primitive 'description' must be a string, got: {type(self.description).__name__}"
            )

        # Validate preconditions
        if not isinstance(self.preconditions, list):
            raise TypeError(
                f"Primitive 'preconditions' must be a list, got: {type(self.preconditions).__name__}"
            )
        for i, p in enumerate(self.preconditions):
            if not isinstance(p, str):
                raise TypeError(
                    f"Primitive 'preconditions'[{i}] must be a string, got: {type(p).__name__}"
                )

        # Validate postconditions
        if not isinstance(self.postconditions, list):
            raise TypeError(
                f"Primitive 'postconditions' must be a list, got: {type(self.postconditions).__name__}"
            )
        for i, p in enumerate(self.postconditions):
            if not isinstance(p, str):
                raise TypeError(
                    f"Primitive 'postconditions'[{i}] must be a string, got: {type(p).__name__}"
                )

    def __repr__(self):
        return f"<{self.__class__.__name__}(name='{self.name}', category='{self.category}')>"

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """Execute this primitive with the given parameters.

        Subclasses must implement this method. It should validate the
        provided kwargs against self.parameters and raise ValueError
        or TypeError on invalid input.

        Returns:
            Any: Result of the execution.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__}.execute() is not implemented"
        )
