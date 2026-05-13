"""LLM-powered changelog generator for DocsAI."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from docsai.llm_interface import get_llm
from docsai.utils.git_helper import CommitInfo, GitHelper

logger = logging.getLogger(__name__)


@dataclass
class VersionEntry:
    """Represents a single version entry in a changelog."""
    version: str
    date: str
    categories: Dict[str, List[str]] = field(default_factory=dict)


@dataclass
class ChangelogData:
    """Complete changelog data ready for rendering."""
    current_version: Optional[str]
    current_date: str
    categories: Dict[str, List[str]] = field(default_factory=dict)
    previous_versions: List[VersionEntry] = field(default_factory=list)


class ChangelogGenerator:
    """Generate a versioned changelog from git history data.

    Uses the LLM to summarize commit diffs into human-readable changelog entries,
    categorized by type (Added, Changed, Fixed, Removed, Deprecated).
    """

    def __init__(
        self,
        repo_path: Optional[str | Path] = None,
        llm_provider: str = "openai",
        llm_model: str = "gpt-4o-mini",
        llm_temperature: float = 0.3,
        commit_count: int = 10,
    ):
        """Initialize the changelog generator.

        Args:
            repo_path: Path to the git repository.
            llm_provider: LLM provider to use (e.g., 'openai', 'anthropic').
            llm_model: LLM model name.
            llm_temperature: LLM temperature for generation.
            commit_count: Number of recent commits to analyze.
        """
        self.git_helper = GitHelper(repo_path)
        self.llm_provider = llm_provider
        self.llm_model = llm_model
        self.llm_temperature = llm_temperature
        self.commit_count = commit_count

    def _get_commits(self) -> List[CommitInfo]:
        """Get the recent commits from the repository."""
        return self.git_helper.get_commit_history(self.commit_count)

    def _generate_summary_with_llm(self, commit: CommitInfo) -> str:
        """Generate a human-readable summary of a commit using the LLM.

        Args:
            commit: The CommitInfo to summarize.

        Returns:
            A human-readable summary string.
        """
        llm = get_llm(self.llm_provider, self.llm_model, self.llm_temperature)

        # Prepare the prompt
        files_summary = "\n".join(
            [f"- {entry}" for entry in commit.files_changed[:10]]
        )
        if len(commit.files_changed) > 10:
            files_summary += f"\n- ... and {len(commit.files_changed) - 10} more files"

        prompt = f"""You are a technical writer creating a changelog entry.
Based on the following commit information, write a concise, human-readable
changelog entry (one line, starting with a bullet point).

Commit message: {commit.message}
Files changed:
{files_summary}

Write the changelog entry as a single bullet point. Focus on what changed
and why it matters to users. Do not include technical details about file paths.
Example: "- Added support for dark mode in the settings panel"

Your entry:"""

        try:
            response = llm.generate(prompt)
            # Clean up the response
            summary = response.strip().lstrip("- ").strip()
            if not summary.startswith("-"):
                summary = f"- {summary}"
            return summary
        except Exception as e:
            logger.warning(f"LLM generation failed for commit {commit.short_hash}: {e}")
            # Fallback to commit message
            return f"- {commit.message}"

    def _generate_summary_fallback(self, commit: CommitInfo) -> str:
        """Generate a summary without using the LLM.

        Args:
            commit: The CommitInfo to summarize.

        Returns:
            A fallback summary string.
        """
        # Use the commit message as the summary
        msg = commit.message
        # Clean up conventional commit prefix
        import re
        match = re.match(r"^[a-zA-Z]+(\([a-zA-Z0-9_-]+\))?!?:\s+(.+)$", msg)
        if match:
            msg = match.group(2)
        return f"- {msg}"

    def categorize_commits(self, commits: List[CommitInfo]) -> Dict[str, List[str]]:
        """Categorize commits into changelog categories.

        Args:
            commits: List of CommitInfo objects.

        Returns:
            Dictionary mapping category names to lists of summary strings.
        """
        categories: Dict[str, List[str]] = {
            "Added": [],
            "Changed": [],
            "Fixed": [],
            "Removed": [],
            "Deprecated": [],
        }

        for commit in commits:
            # Determine which categories apply to this commit
            commit_categories = commit.categories
            if not commit_categories:
                commit_categories = ["Changed"]

            # Generate summary
            try:
                summary = self._generate_summary_with_llm(commit)
            except Exception:
                summary = self._generate_summary_fallback(commit)

            # Add to appropriate categories
            for cat in commit_categories:
                if cat in categories:
                    categories[cat].append(summary)

        # Remove empty categories
        categories = {k: v for k, v in categories.items() if v}

        return categories

    def generate_version_entry(
        self,
        version: Optional[str] = None,
        date: Optional[str] = None,
    ) -> VersionEntry:
        """Generate a single version entry for the changelog.

        Args:
            version: Version string. If None, uses next version from git tags.
            date: Date string. If None, uses today's date.

        Returns:
            A VersionEntry object.
        """
        if date is None:
            from datetime import datetime
            date = datetime.now().strftime("%Y-%m-%d")

        if version is None:
            version = self.git_helper.get_next_version("patch")

        commits = self._get_commits()
        categories = self.categorize_commits(commits)

        return VersionEntry(
            version=version,
            date=date,
            categories=categories,
        )

    def generate_changelog_data(
        self,
        version: Optional[str] = None,
        date: Optional[str] = None,
        include_previous: bool = True,
    ) -> ChangelogData:
        """Generate complete changelog data.

        Args:
            version: Version string for the current entry.
            date: Date string for the current entry.
            include_previous: Whether to include previous version entries.

        Returns:
            A ChangelogData object ready for rendering.
        """
        current_entry = self.generate_version_entry(version, date)

        previous_versions: List[VersionEntry] = []
        if include_previous:
            # Get older commits for previous versions
            older_commits = self.git_helper.get_commit_history(
                count=self.commit_count * 3
            )
            # Skip the first N commits (which are for the current version)
            older_commits = older_commits[self.commit_count:]

            if older_commits:
                # Group older commits by approximate version
                # For simplicity, we'll create one previous entry
                prev_categories = self.categorize_commits(older_commits[:self.commit_count])
                prev_version = self.git_helper.get_last_tag() or "0.0.1"
                prev_date = older_commits[0].date if older_commits else date

                previous_versions.append(
                    VersionEntry(
                        version=prev_version,
                        date=prev_date,
                        categories=prev_categories,
                    )
                )

        return ChangelogData(
            current_version=current_entry.version,
            current_date=current_entry.date,
            categories=current_entry.categories,
            previous_versions=previous_versions,
        )

    def generate(
        self,
        version: Optional[str] = None,
        date: Optional[str] = None,
        output_path: Optional[str | Path] = None,
        template_dir: Optional[str | Path] = None,
        template_file: str = "changelog_default.md",
    ) -> str:
        """Generate a changelog and optionally write it to a file.

        Args:
            version: Version string.
            date: Date string.
            output_path: Path to write the changelog file.
            template_dir: Directory containing the template.
            template_file: Template filename.

        Returns:
            The rendered changelog string.
        """
        from docsai.generators.readme_templates import TemplateEngine

        changelog_data = self.generate_changelog_data(version, date)

        # Render using the template engine
        engine = TemplateEngine(
            template_dir=template_dir,
            template_file=template_file,
        )

        rendered = engine.render(
            template_name=template_file,
            current_version=changelog_data.current_version,
            current_date=changelog_data.current_date,
            categories=changelog_data.categories,
            previous_versions=changelog_data.previous_versions,
        )

        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(rendered)
            logger.info(f"Changelog written to {output_path}")

        return rendered
