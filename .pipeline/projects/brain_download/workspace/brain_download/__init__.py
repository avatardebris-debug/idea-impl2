"""Brain Download — automated skill tree deconstruction and course generation."""

__version__ = "1.0.0"

from brain_download.config.domain_profiles import DOMAIN_PROFILES, get_domain_profile
from brain_download.config.learning_models import DESSCConfig, get_dessc_config
from brain_download.core.compression_engine import generate_compression_map, get_compression_map_for_module
from brain_download.core.deconstruction_engine import deconstruct_topic
from brain_download.core.models import (
    CompressionMap,
    CourseModule,
    CourseOutline,
    SkillNode,
    SkillTree,
    StakesConfig,
    StakesMechanism,
    Topic,
)
from brain_download.core.output_formatters import to_json, to_markdown
from brain_download.core.orchestrator import DESSCOrchestrator, brain_download
from brain_download.core.selection_matrix import get_pareto_essential_nodes, get_pareto_non_essential_nodes, pareto_filter
from brain_download.core.sequencing_engine import sequence_skills
from brain_download.core.stakes_calculator import generate_stakes, get_recommended_stakes

__all__ = [
    "__version__",
    "brain_download",
    "DESSCOrchestrator",
    "DESSCConfig",
    "get_dessc_config",
    "DOMAIN_PROFILES",
    "get_domain_profile",
    "deconstruct_topic",
    "pareto_filter",
    "get_pareto_essential_nodes",
    "get_pareto_non_essential_nodes",
    "sequence_skills",
    "generate_stakes",
    "get_recommended_stakes",
    "generate_compression_map",
    "get_compression_map_for_module",
    "to_json",
    "to_markdown",
    "Topic",
    "SkillNode",
    "SkillTree",
    "CourseModule",
    "CourseOutline",
    "StakesMechanism",
    "StakesConfig",
    "CompressionMap",
]
