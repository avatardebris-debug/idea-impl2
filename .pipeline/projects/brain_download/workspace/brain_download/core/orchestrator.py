"""DESSC Orchestrator — main entry point for the Brain Download framework."""

from __future__ import annotations

from brain_download.config.domain_profiles import get_domain_profile
from brain_download.config.learning_models import DESSCConfig, get_dessc_config
from brain_download.core.compression_engine import generate_compression_map
from brain_download.core.deconstruction_engine import deconstruct_topic
from brain_download.core.models import CourseOutline, SkillTree, StakesConfig
from brain_download.core.output_formatters import to_json, to_markdown
from brain_download.core.selection_matrix import pareto_filter
from brain_download.core.sequencing_engine import sequence_skills
from brain_download.core.stakes_calculator import generate_stakes


class DESSCOrchestrator:
    """Orchestrates the full DESSC pipeline for a given topic."""

    def __init__(self, config: DESSCConfig | None = None):
        self.config = config or get_dessc_config()

    def run(
        self,
        topic_name: str,
        domain: str = "general",
        target_audience: str = "beginner",
        desired_outcome: str = "Mastery of core concepts",
        module_size: int | None = None,
        target_density: str = "high",
        stakes_config: StakesConfig | None = None,
    ) -> dict:
        """Run the full DESSC pipeline.

        Args:
            topic_name: Name of the topic to deconstruct.
            domain: Domain for domain-specific hints.
            target_audience: Target audience level.
            desired_outcome: Desired learning outcome.
            module_size: Number of skills per module.
            target_density: Compression density level.
            stakes_config: Stakes configuration.

        Returns:
            A dict with keys: 'outline', 'tree', 'stakes', 'compression_maps', 'json', 'markdown'.
        """
        # Step 1: Deconstruct
        tree = deconstruct_topic(
            topic_name=topic_name,
            domain=domain,
            target_audience=target_audience,
            desired_outcome=desired_outcome,
            config=self.config,
        )

        # Step 2: Select (Pareto filtering)
        if self.config.enable_pareto_filtering:
            tree = pareto_filter(tree, self.config.pareto_threshold)

        # Step 3: Sequence
        ms = module_size or self.config.default_module_size
        outline = sequence_skills(tree, module_size=ms)

        # Step 4: Stakes
        stakes = generate_stakes(outline, stakes_config or StakesConfig())

        # Step 5: Compression
        compression_maps = generate_compression_map(outline, tree, target_density)

        # Output
        json_output = to_json(outline, tree, stakes, compression_maps)
        markdown_output = to_markdown(outline, tree, stakes, compression_maps)

        return {
            "outline": outline,
            "tree": tree,
            "stakes": stakes,
            "compression_maps": compression_maps,
            "json": json_output,
            "markdown": markdown_output,
        }


def brain_download(
    topic_name: str,
    domain: str = "general",
    target_audience: str = "beginner",
    desired_outcome: str = "Mastery of core concepts",
    module_size: int | None = None,
    target_density: str = "high",
    stakes_config: StakesConfig | None = None,
    config: DESSCConfig | None = None,
) -> dict:
    """Convenience function to run the full DESSC pipeline.

    Args:
        topic_name: Name of the topic to deconstruct.
        domain: Domain for domain-specific hints.
        target_audience: Target audience level.
        desired_outcome: Desired learning outcome.
        module_size: Number of skills per module.
        target_density: Compression density level.
        stakes_config: Stakes configuration.
        config: DESSC configuration.

    Returns:
        A dict with keys: 'outline', 'tree', 'stakes', 'compression_maps', 'json', 'markdown'.
    """
    orchestrator = DESSCOrchestrator(config)
    return orchestrator.run(
        topic_name=topic_name,
        domain=domain,
        target_audience=target_audience,
        desired_outcome=desired_outcome,
        module_size=module_size,
        target_density=target_density,
        stakes_config=stakes_config,
    )
