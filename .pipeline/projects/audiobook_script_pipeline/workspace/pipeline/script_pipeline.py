"""Pipeline orchestrator — chains parser and formatter for audiobook script generation."""

from audiobook_script_pipeline.parser.manuscript_parser import ManuscriptParser, ManuscriptParseError
from audiobook_script_pipeline.formatter.audio_formatter import AudioScriptFormatter


class ScriptPipeline:
    """Chains the manuscript parser and audio script formatter.

    Usage:
        pipeline = ScriptPipeline()
        result = pipeline.run("manuscript.txt")
    """

    def __init__(self, default_pause: float = 1.0):
        """
        Args:
            default_pause: Default pause duration in seconds for the formatter.
        """
        self.parser = ManuscriptParser()
        self.formatter = AudioScriptFormatter(default_pause=default_pause)

    def run(self, filepath: str) -> dict:
        """Run the full pipeline: load → parse → format → return.

        Args:
            filepath: Path to the manuscript text file.

        Returns:
            Complete audio script dict with chapters, each containing
            formatted entries with pacing markers.

        Raises:
            FileNotFoundError: If the manuscript file does not exist.
            PermissionError: If the manuscript file cannot be read.
            ManuscriptParseError: If the manuscript is empty.
            ValueError: If formatting fails.
        """
        try:
            # Step 1: Parse the manuscript
            chapters = self.parser.parse_file(filepath)
        except (FileNotFoundError, PermissionError, ManuscriptParseError):
            raise
        except Exception as e:
            raise ManuscriptParseError(f"Failed to parse manuscript file '{filepath}': {e}")

        try:
            # Step 2: Format into audio script
            audio_script = self.formatter.format_chapters(chapters)
        except ValueError as e:
            raise ValueError(f"Failed to format audio script: {e}")
        except Exception as e:
            raise ValueError(f"Unexpected error during formatting: {e}")

        return audio_script

    def run_from_text(self, text: str) -> dict:
        """Run the pipeline from raw text (no file I/O).

        Args:
            text: Raw manuscript text.

        Returns:
            Complete audio script dict.

        Raises:
            ValueError: If the text is empty or formatting fails.
        """
        if not text or not text.strip():
            raise ValueError("Cannot run pipeline: input text is empty")

        try:
            # Step 1: Parse the manuscript
            chapters = self.parser.parse(text)
        except Exception as e:
            raise ManuscriptParseError(f"Failed to parse manuscript text: {e}")

        try:
            # Step 2: Format into audio script
            audio_script = self.formatter.format_chapters(chapters)
        except ValueError as e:
            raise ValueError(f"Failed to format audio script: {e}")
        except Exception as e:
            raise ValueError(f"Unexpected error during formatting: {e}")

        return audio_script
