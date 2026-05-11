"""Pipeline Orchestrator — Coordinates the AI movie generation pipeline.

Orchestrates the sequence: Logline -> Beat Sheet -> Characters -> Script -> Scene Descriptions -> Output.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ai_movie_gen_suite.formatters.fdx_formatter import FDXFormatter
from ai_movie_gen_suite.formatters.json_formatter import JSONFormatter
from ai_movie_gen_suite.formatters.yaml_formatter import YAMLFormatter
from ai_movie_gen_suite.models import (
    BeatSheet,
    CharacterRegistry,
    SceneDescriptionCollection,
    Script,
)
from ai_movie_gen_suite.stages.beat_generator import BeatGenerator
from ai_movie_gen_suite.stages.character_generator import CharacterGenerator
from ai_movie_gen_suite.stages.script_writer import ScriptWriter
from ai_movie_gen_suite.stages.scene_description_engine import SceneDescriptionEngine

logger = logging.getLogger(__name__)


class PipelineConfig:
    """Configuration for the movie generation pipeline."""

    def __init__(
        self,
        logline: str,
        title: str,
        genre: str,
        tone: str = "",
        output_format: str = "json",
        output_dir: str = "./output",
        use_llm: bool = False,
        llm_client: Any = None,
    ):
        self.logline = logline
        self.title = title
        self.genre = genre
        self.tone = tone
        self.output_format = output_format
        self.output_dir = output_dir
        self.use_llm = use_llm
        self.llm_client = llm_client


class MovieGenerationPipeline:
    """Orchestrates the AI movie generation pipeline."""

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.beat_sheet: Optional[BeatSheet] = None
        self.character_registry: Optional[CharacterRegistry] = None
        self.script: Optional[Script] = None
        self.scene_descriptions: Optional[SceneDescriptionCollection] = None
        self._results: Dict[str, Any] = {}

    def run(self) -> Dict[str, Any]:
        """Run the full pipeline."""
        logger.info("Starting AI movie generation pipeline")
        logger.info(f"Title: {self.config.title}")
        logger.info(f"Genre: {self.config.genre}")
        logger.info(f"Tone: {self.config.tone or 'Not specified'}")

        # Step 1: Generate beat sheet
        self._generate_beat_sheet()

        # Step 2: Generate characters
        self._generate_characters()

        # Step 3: Write script
        self._write_script()

        # Step 4: Generate scene descriptions
        self._generate_scene_descriptions()

        # Step 5: Format output
        self._format_output()

        logger.info("Pipeline complete")
        return self._results

    def _generate_beat_sheet(self) -> None:
        """Generate the beat sheet."""
        logger.info("Step 1: Generating beat sheet")
        generator = BeatGenerator(
            logline=self.config.logline,
            genre=self.config.genre,
            tone=self.config.tone,
        )

        if self.config.use_llm and self.config.llm_client:
            self.beat_sheet = generator.generate_with_llm(
                llm_client=self.config.llm_client,
            )
        else:
            self.beat_sheet = generator.generate_beat_sheet()

        self._results["beat_sheet"] = self.beat_sheet.model_dump()
        logger.info(f"Beat sheet generated with {len(self.beat_sheet.beats)} beats")

    def _generate_characters(self) -> None:
        """Generate character profiles."""
        logger.info("Step 2: Generating characters")
        generator = CharacterGenerator(
            logline=self.config.logline,
            genre=self.config.genre,
            tone=self.config.tone,
        )

        if self.config.use_llm and self.config.llm_client:
            self.character_registry = generator.generate_with_llm(
                llm_client=self.config.llm_client,
            )
        else:
            self.character_registry = generator.generate_characters()

        self._results["characters"] = self.character_registry.model_dump()
        logger.info(f"Generated {len(self.character_registry.characters)} characters")

    def _write_script(self) -> None:
        """Write the screenplay."""
        logger.info("Step 3: Writing script")
        writer = ScriptWriter(
            title=self.config.title,
            logline=self.config.logline,
            genre=self.config.genre,
            beat_sheet=self.beat_sheet,
            character_registry=self.character_registry,
        )

        if self.config.use_llm and self.config.llm_client:
            self.script = writer.write_with_llm(
                llm_client=self.config.llm_client,
            )
        else:
            self.script = writer.write_script()

        self._results["script"] = self.script.model_dump()
        logger.info(f"Script written with {len(self.script.scenes)} scenes")

    def _generate_scene_descriptions(self) -> None:
        """Generate scene descriptions."""
        logger.info("Step 4: Generating scene descriptions")
        engine = SceneDescriptionEngine(
            script=self.script,
            beat_sheet=self.beat_sheet,
            character_registry=self.character_registry,
            tone=self.config.tone,
        )

        if self.config.use_llm and self.config.llm_client:
            self.scene_descriptions = engine.generate_with_llm(
                llm_client=self.config.llm_client,
            )
        else:
            self.scene_descriptions = engine.generate_descriptions()

        self._results["scene_descriptions"] = self.scene_descriptions.model_dump()
        logger.info(f"Generated {len(self.scene_descriptions.descriptions)} scene descriptions")

    def _format_output(self) -> None:
        """Format and save output files."""
        logger.info("Step 5: Formatting output")

        if self.config.output_format == "json":
            formatter = JSONFormatter(
                script=self.script,
                beat_sheet=self.beat_sheet,
                characters=self.character_registry,
                scene_descriptions=self.scene_descriptions,
            )
            output_path = f"{self.config.output_dir}/{self.config.title.lower().replace(' ', '_')}.json"
            formatter.save(output_path)
            self._results["output_path"] = output_path
            logger.info(f"JSON output saved to {output_path}")

        elif self.config.output_format == "yaml":
            formatter = YAMLFormatter(
                script=self.script,
                beat_sheet=self.beat_sheet,
                characters=self.character_registry,
                scene_descriptions=self.scene_descriptions,
            )
            output_path = f"{self.config.output_dir}/{self.config.title.lower().replace(' ', '_')}.yaml"
            formatter.save(output_path)
            self._results["output_path"] = output_path
            logger.info(f"YAML output saved to {output_path}")

        elif self.config.output_format == "fdx":
            formatter = FDXFormatter(
                script=self.script,
                scene_descriptions=self.scene_descriptions,
            )
            output_path = f"{self.config.output_dir}/{self.config.title.lower().replace(' ', '_')}.fdx"
            formatter.save(output_path)
            self._results["output_path"] = output_path
            logger.info(f"FDX output saved to {output_path}")

        else:
            raise ValueError(f"Unsupported output format: {self.config.output_format}")

    def get_results(self) -> Dict[str, Any]:
        """Get the pipeline results."""
        return self._results
