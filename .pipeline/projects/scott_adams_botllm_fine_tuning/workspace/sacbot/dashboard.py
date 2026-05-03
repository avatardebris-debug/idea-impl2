"""Pipeline dashboard — real-time text-based display of pipeline status."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class PipelineStats:
    """Statistics for the pipeline dashboard."""
    pending_count: int = 0
    in_progress_count: int = 0
    published_count: int = 0
    failed_count: int = 0
    last_publish_time: Optional[float] = None
    next_publish_time: Optional[float] = None
    topics_researched: int = 0
    content_generated: int = 0
    content_reviewed: int = 0
    uptime_seconds: float = 0.0
    start_time: Optional[float] = None


class PipelineDashboard:
    """Text-based dashboard for pipeline status."""

    def __init__(
        self,
        stats: Optional[PipelineStats] = None,
        title: str = "Scott Adams Bot — Pipeline Dashboard",
    ):
        self.stats = stats or PipelineStats()
        self.title = title

    def render(self) -> str:
        """Render the dashboard as a string."""
        lines = []

        # Title
        lines.append("=" * 60)
        lines.append(self.title.center(60))
        lines.append("=" * 60)

        # Status counts
        lines.append("")
        lines.append("  STATUS COUNTS")
        lines.append("  " + "-" * 30)
        lines.append(f"  Pending:    {self.stats.pending_count:>6}")
        lines.append(f"  In Progress:{self.stats.in_progress_count:>6}")
        lines.append(f"  Published:  {self.stats.published_count:>6}")
        lines.append(f"  Failed:     {self.stats.failed_count:>6}")

        # Pipeline progress
        total = self.stats.published_count + self.stats.failed_count
        lines.append("")
        lines.append("  PIPELINE PROGRESS")
        lines.append("  " + "-" * 30)
        lines.append(f"  Topics Researched:  {self.stats.topics_researched:>6}")
        lines.append(f"  Content Generated:  {self.stats.content_generated:>6}")
        lines.append(f"  Content Reviewed:   {self.stats.content_reviewed:>6}")

        # Timing
        lines.append("")
        lines.append("  TIMING")
        lines.append("  " + "-" * 30)

        if self.stats.last_publish_time:
            last = datetime.fromtimestamp(self.stats.last_publish_time)
            lines.append(f"  Last Publish:       {last.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            lines.append("  Last Publish:       N/A")

        if self.stats.next_publish_time:
            next_time = datetime.fromtimestamp(self.stats.next_publish_time)
            lines.append(f"  Next Publish:       {next_time.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            lines.append("  Next Publish:       N/A")

        if self.stats.start_time:
            uptime = time.time() - self.stats.start_time
            hours = int(uptime // 3600)
            minutes = int((uptime % 3600) // 60)
            lines.append(f"  Uptime:             {hours}h {minutes}m")
        else:
            lines.append("  Uptime:             N/A")

        # Progress bar
        lines.append("")
        lines.append("  PUBLICATION PROGRESS")
        lines.append("  " + "-" * 30)
        if total > 0:
            pct = self.stats.published_count / total * 100
            bar_len = 30
            filled = int(bar_len * pct / 100)
            bar = "█" * filled + "░" * (bar_len - filled)
            lines.append(f"  [{bar}] {pct:.1f}%")
        else:
            lines.append("  [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 0.0%")

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)

    def render_live(self, interval: float = 2.0) -> None:
        """Render the dashboard in a live loop (press Ctrl+C to stop)."""
        try:
            while True:
                # Clear screen (ANSI escape)
                print("\033[2J\033[H", end="")
                print(self.render())
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\nDashboard stopped.")

    def update_stats(self, stats: PipelineStats) -> None:
        """Update the dashboard with new stats."""
        self.stats = stats


def render_dashboard(
    pending: int = 0,
    in_progress: int = 0,
    published: int = 0,
    failed: int = 0,
    last_publish: Optional[float] = None,
    next_publish: Optional[float] = None,
    topics: int = 0,
    generated: int = 0,
    reviewed: int = 0,
) -> str:
    """Convenience function to render a dashboard string.

    Args:
        pending: Number of pending items
        in_progress: Number of in-progress items
        published: Number of published items
        failed: Number of failed items
        last_publish: Unix timestamp of last publish
        next_publish: Unix timestamp of next publish
        topics: Number of topics researched
        generated: Number of content items generated
        reviewed: Number of content items reviewed

    Returns:
        Dashboard string
    """
    stats = PipelineStats(
        pending_count=pending,
        in_progress_count=in_progress,
        published_count=published,
        failed_count=failed,
        last_publish_time=last_publish,
        next_publish_time=next_publish,
        topics_researched=topics,
        content_generated=generated,
        content_reviewed=reviewed,
    )
    dashboard = PipelineDashboard(stats)
    return dashboard.render()
