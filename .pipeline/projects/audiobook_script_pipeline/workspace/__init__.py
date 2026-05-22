"""Audiobook Script Pipeline — converts manuscripts into formatted audio scripts with pacing markers."""

__version__ = "0.1.0"

from audiobook_script_pipeline.parser.manuscript_parser import ManuscriptParser, ManuscriptParseError
from audiobook_script_pipeline.formatter.audio_formatter import AudioScriptFormatter
from audiobook_script_pipeline.pipeline.script_pipeline import ScriptPipeline

__all__ = [
    "ManuscriptParser",
    "ManuscriptParseError",
    "AudioScriptFormatter",
    "ScriptPipeline",
]
