"""Git helper utilities for reading commit history and diffs."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class CommitInfo:
    """Represents a single git commit."""
    hash: str
    short_hash: str
    author: str
    date: str
    message: str
    files_changed: List[str] = field(default_factory=list)
    diff: str = ""
    categories: List[str] = field(default_factory=list)


@dataclass
class ChangeCategory:
    """Represents a categorized group of changes."""
    category: str
    items: List[str] = field(default_factory=list)


# Conventional commit prefixes mapped to changelog categories
_CONVENTIONAL_PREFIXES: Dict[str, str] = {
    "feat": "Added",
    "feature": "Added",
    "new": "Added",
    "add": "Added",
    "feat!": "Breaking",
    "breaking": "Breaking",
    "BREAKING": "Breaking",
    "fix": "Fixed",
    "bugfix": "Fixed",
    "bug": "Fixed",
    "perf": "Changed",
    "performance": "Changed",
    "improve": "Changed",
    "improvement": "Changed",
    "change": "Changed",
    "refactor": "Changed",
    "refactor!": "Changed",
    "style": "Changed",
    "format": "Changed",
    "chore": "Changed",
    "docs": "Changed",
    "documentation": "Changed",
    "test": "Changed",
    "ci": "Changed",
    "build": "Changed",
    "remove": "Removed",
    "delete": "Removed",
    "rm": "Removed",
    "deprecate": "Deprecated",
    "deprecated": "Deprecated",
    "remove!": "Deprecated",
}


class GitHelper:
    """Helper class for git operations.

    Provides methods to read commit history, extract diffs,
    parse commit messages, and categorize changes.
    """

    def __init__(self, repo_path: Optional[str | Path] = None):
        """Initialize GitHelper.

        Args:
            repo_path: Path to the git repository. Defaults to current directory.
        """
        self._repo_path = Path(repo_path) if repo_path else Path.cwd()

    def _run_git(self, *args: str) -> str:
        """Run a git command and return stdout.

        Args:
            *args: Git command arguments.

        Returns:
            stdout of the git command.

        Raises:
            subprocess.CalledProcessError: If the git command fails.
        """
        result = subprocess.run(
            ["git", "-C", str(self._repo_path)] + list(args),
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode,
                ["git"] + list(args),
                result.stdout,
                result.stderr,
            )
        return result.stdout

    def get_commit_history(
        self,
        count: int = 10,
        format_str: str = "%H|%h|%an|%ad|%s",
        date_format: str = "%Y-%m-%d",
    ) -> List[CommitInfo]:
        """Get the last N commits from the repository.

        Args:
            count: Number of commits to retrieve.
            format_str: Git log format string.
            date_format: Date format for the log.

        Returns:
            List of CommitInfo objects.

        Raises:
            subprocess.CalledProcessError: If git command fails.
        """
        log_output = self._run_git(
            "log",
            f"-{count}",
            f"--format={format_str}",
            f"--date=format:{date_format}",
        )

        commits: List[CommitInfo] = []
        for line in log_output.strip().split("\n"):
            if not line:
                continue
            parts = line.split("|", 4)
            if len(parts) < 5:
                continue
            commit = CommitInfo(
                hash=parts[0],
                short_hash=parts[1],
                author=parts[2],
                date=parts[3],
                message=parts[4],
            )
            # Get file changes for this commit
            try:
                files_output = self._run_git(
                    "diff-tree", "--no-commit-id", "--name-status", "-r", commit.hash
                )
                for file_line in files_output.strip().split("\n"):
                    if file_line:
                        status, filepath = file_line.split("\t", 1)
                        commit.files_changed.append(f"{status}\t{filepath}")
            except subprocess.CalledProcessError:
                # Commit might be the initial commit with no parent
                pass

            # Categorize the commit
            commit.categories = self.categorize_changes(commit.message)

            commits.append(commit)

        return commits

    def get_commit_diff(self, commit_hash: str) -> str:
        """Get the diff for a specific commit.

        Args:
            commit_hash: Full commit hash.

        Returns:
            The diff content as a string.
        """
        return self._run_git("diff", f"{commit_hash}^", commit_hash)

    def parse_commit_message(self, message: str) -> Dict[str, str]:
        """Parse a commit message into its components.

        Handles conventional commit format:
            <type>[optional scope]: <description>

        Args:
            message: The commit message to parse.

        Returns:
            Dictionary with keys: type, scope, description, is_conventional
        """
        result = {
            "type": "",
            "scope": "",
            "description": message,
            "is_conventional": False,
        }

        # Match conventional commit format
        pattern = r"^([a-zA-Z]+)(\([a-zA-Z0-9_-]+\))?!?:\s+(.+)$"
        match = re.match(pattern, message)
        if match:
            result["type"] = match.group(1).lower()
            result["scope"] = match.group(2).strip("()") if match.group(2) else ""
            result["description"] = match.group(3)
            result["is_conventional"] = True

        return result

    def categorize_changes(self, message: str) -> List[str]:
        """Categorize a commit message into changelog categories.

        Args:
            message: The commit message to categorize.

        Returns:
            List of category strings (e.g., ['Added', 'Fixed']).
        """
        parsed = self.parse_commit_message(message)
        categories: List[str] = []

        # Check conventional commit type
        if parsed["is_conventional"] and parsed["type"] in _CONVENTIONAL_PREFIXES:
            categories.append(_CONVENTIONAL_PREFIXES[parsed["type"]])

        # Check for keywords in the description
        desc_lower = parsed["description"].lower()
        for keyword, category in _CONVENTIONAL_PREFIXES.items():
            if keyword in desc_lower and category not in categories:
                categories.append(category)

        # Default category if nothing matched
        if not categories:
            categories.append("Changed")

        return categories

    def get_recent_files(self, count: int = 10) -> List[str]:
        """Get recently modified files from the last N commits.

        Args:
            count: Number of commits to look back.

        Returns:
            List of recently modified file paths.
        """
        commits = self.get_commit_history(count)
        files: List[str] = []
        for commit in commits:
            for file_entry in commit.files_changed:
                status, filepath = file_entry.split("\t", 1)
                if status in ("A", "M", "R"):
                    files.append(filepath)
        return files

    def get_branch_name(self) -> str:
        """Get the current branch name.

        Returns:
            The current branch name, or 'unknown' if not in a git repo.
        """
        try:
            return self._run_git("rev-parse", "--abbrev-ref", "HEAD").strip()
        except subprocess.CalledProcessError:
            return "unknown"

    def get_last_tag(self) -> Optional[str]:
        """Get the most recent tag.

        Returns:
            The most recent tag name, or None if no tags exist.
        """
        try:
            output = self._run_git("describe", "--tags", "--abbrev=0")
            return output.strip()
        except subprocess.CalledProcessError:
            return None

    def get_next_version(self, bump_type: str = "patch") -> str:
        """Calculate the next version number based on bump type.

        Args:
            bump_type: One of 'major', 'minor', 'patch'.

        Returns:
            The next version string.
        """
        last_tag = self.get_last_tag()
        if not last_tag:
            return "0.1.0"

        # Parse version from tag (strip 'v' prefix if present)
        version_str = last_tag.lstrip("v")
        parts = version_str.split(".")

        if len(parts) != 3:
            return "0.1.0"

        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])

        if bump_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif bump_type == "minor":
            minor += 1
            patch = 0
        else:  # patch
            patch += 1

        return f"{major}.{minor}.{patch}"
