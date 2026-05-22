"""Data models for the Brain Download core engine."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Topic:
    """Represents the learning topic to deconstruct."""
    name: str
    domain: str = "general"
    description: str = ""
    target_audience: str = "beginner"
    desired_outcome: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Topic:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> Topic:
        return cls.from_dict(json.loads(json_str))


@dataclass
class SkillNode:
    """A single node in the skill tree representing a sub-skill or concept."""
    id: str
    name: str
    description: str = ""
    importance: float = 0.5  # 0.0 to 1.0
    level: int = 1
    prerequisites: list[str] = field(default_factory=list)  # IDs of prerequisite nodes
    estimated_minutes: int = 30
    is_pareto_essential: bool = False
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SkillNode:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> SkillNode:
        return cls.from_dict(json.loads(json_str))


@dataclass
class SkillTree:
    """A hierarchical tree of skills for a given topic."""
    topic: Topic
    root_nodes: list[SkillNode] = field(default_factory=list)
    all_nodes: list[SkillNode] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "topic": self.topic.to_dict(),
            "root_nodes": [n.to_dict() for n in self.root_nodes],
            "all_nodes": [n.to_dict() for n in self.all_nodes],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SkillTree:
        topic = Topic.from_dict(data["topic"])
        root_nodes = [SkillNode.from_dict(n) for n in data.get("root_nodes", [])]
        all_nodes = [SkillNode.from_dict(n) for n in data.get("all_nodes", [])]
        return cls(
            topic=topic,
            root_nodes=root_nodes,
            all_nodes=all_nodes,
            metadata=data.get("metadata", {}),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> SkillTree:
        return cls.from_dict(json.loads(json_str))


@dataclass
class CourseModule:
    """A module in the course outline grouping related skills."""
    id: str
    title: str
    description: str = ""
    skills: list[str] = field(default_factory=list)  # SkillNode IDs
    estimated_minutes: int = 30
    prerequisites: list[str] = field(default_factory=list)  # Module IDs
    order: int = 0
    compression_map: dict[str, Any] | None = None
    stakes_config: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CourseModule:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> CourseModule:
        return cls.from_dict(json.loads(json_str))


@dataclass
class CourseOutline:
    """The complete sequenced course outline."""
    topic: Topic
    modules: list[CourseModule] = field(default_factory=list)
    total_estimated_minutes: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "topic": self.topic.to_dict(),
            "modules": [m.to_dict() for m in self.modules],
            "total_estimated_minutes": self.total_estimated_minutes,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CourseOutline:
        topic = Topic.from_dict(data["topic"])
        modules = [CourseModule.from_dict(m) for m in data.get("modules", [])]
        return cls(
            topic=topic,
            modules=modules,
            total_estimated_minutes=data.get("total_estimated_minutes", 0),
            metadata=data.get("metadata", {}),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> CourseOutline:
        return cls.from_dict(json.loads(json_str))


@dataclass
class StakesMechanism:
    """A single accountability mechanism for a module."""
    id: str
    name: str
    description: str
    type: str  # social, financial, temporal, identity-based
    impact_score: float  # 0.0 to 1.0
    effort_required: str  # low, medium, high
    implementation_steps: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StakesMechanism:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> StakesMechanism:
        return cls.from_dict(json.loads(json_str))


@dataclass
class StakesConfig:
    """Stakes configuration for a module."""
    module_id: str = ""
    mechanisms: list[StakesMechanism] = field(default_factory=list)
    prefer_social: bool = False
    prefer_financial: bool = False
    prefer_portfolio: bool = False
    prefer_credential: bool = False
    max_mechanisms: int = 3

    def to_dict(self) -> dict[str, Any]:
        return {
            "module_id": self.module_id,
            "mechanisms": [m.to_dict() for m in self.mechanisms],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StakesConfig:
        mechanisms = [StakesMechanism.from_dict(m) for m in data.get("mechanisms", [])]
        return cls(module_id=data["module_id"], mechanisms=mechanisms)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> StakesConfig:
        return cls.from_dict(json.loads(json_str))


@dataclass
class CompressionMap:
    """Compression map for a module."""
    module_id: str
    module_title: str = ""
    skip_list: list[str] = field(default_factory=list)
    emphasize_list: list[str] = field(default_factory=list)
    compress_ratio: float = 1.0  # 0.0 to 1.0, lower = more compressed
    estimated_time_savings: int = 0  # minutes saved
    density_target: str = "high"  # low, medium, high
    # Additional fields for compatibility
    essential_skills: list[str] = field(default_factory=list)
    compressed_skills: list[str] = field(default_factory=list)
    skipped_skills: list[str] = field(default_factory=list)
    total_skills_in_module: int = 0
    compression_ratio: float = 1.0
    compressed_count: int = 0
    skipped_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CompressionMap:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> CompressionMap:
        return cls.from_dict(json.loads(json_str))
