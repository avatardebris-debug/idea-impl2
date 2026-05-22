"""Results Store — persists SOP execution results to disk.

Stores individual task results and queue-level summaries as JSON files.
Supports retrieval by queue_id, task_id, or summary queries.

Usage:
    from drop_servicing_tool.results_store import ResultsStore

    rs = ResultsStore()
    rs.store_result("q1", "t1", {"output": "done"}, metadata={"key": "value"})
    result = rs.get_result("q1", "t1")
    summary = rs.get_summary("q1")
"""

from __future__ import annotations

import json
import os
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"


def _get_results_dir() -> Path:
    """Get the results directory, respecting DST_BULK_BASE_DIR env var."""
    env_dir = os.environ.get("DST_BULK_BASE_DIR")
    if env_dir:
        return Path(env_dir)
    return _DEFAULT_RESULTS_DIR


# ---------------------------------------------------------------------------
# ResultsStore class
# -----------------------------------------------------------------------------------

class ResultsStore:
    """Manages storage and retrieval of SOP execution results.

    Each queue gets its own directory under *results/* with:
        <queue_id>_results.json     — individual task results
        <queue_id>_summary.json     — queue-level summary
    """

    def __init__(self, base_dir: Path | None = None) -> None:
        self._base = base_dir or _get_results_dir()
        self._base.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def store_result(
        self,
        queue_id: str,
        task_id: str,
        result_data: dict,
        tokens_used: int = 0,
        duration_seconds: float = 0.0,
        status: str = "completed",
        error: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        """Store a single task result."""
        results_dir = self._base / queue_id
        results_dir.mkdir(parents=True, exist_ok=True)

        result = {
            "task_id": task_id,
            "result_data": result_data,
            "tokens_used": tokens_used,
            "duration_seconds": duration_seconds,
            "status": status,
            "error": error,
            "metadata": metadata,
        }

        # Read existing results
        results_file = results_dir / "results.json"
        existing: dict = {}
        if results_file.exists():
            existing = json.loads(results_file.read_text(encoding="utf-8"))

        existing[task_id] = result

        results_file.write_text(
            json.dumps(existing, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        # Update summary
        self._update_summary(queue_id)

    def get_result(self, queue_id: str, task_id: str) -> dict:
        """Retrieve a single task result.

        Raises:
            FileNotFoundError: If the queue does not exist.
            KeyError: If the task_id is not found within the queue.
        """
        results_file = self._base / queue_id / "results.json"
        if not results_file.exists():
            raise FileNotFoundError(f"Queue results not found: {queue_id}")

        results = json.loads(results_file.read_text(encoding="utf-8"))
        if task_id not in results:
            raise KeyError(f"Task not found in queue {queue_id!r}: {task_id!r}")
        return results[task_id]

    def get_result_path(self, queue_id: str) -> Path:
        """Return the path to the results file for a queue."""
        return self._base / queue_id / "results.json"

    def get_all_results(self, queue_id: str) -> list[dict]:
        """Retrieve all results for a queue as a list. Returns empty list if not found."""
        results_file = self._base / queue_id / "results.json"
        if not results_file.exists():
            return []

        results = json.loads(results_file.read_text(encoding="utf-8"))
        return list(results.values())

    def get_summary(self, queue_id: str) -> dict:
        """Retrieve or compute a summary for a queue."""
        summary_file = self._base / queue_id / "summary.json"

        # Try to read existing summary
        if summary_file.exists():
            summary = json.loads(summary_file.read_text(encoding="utf-8"))
            # Ensure required fields exist
            if "queue_id" not in summary:
                summary["queue_id"] = queue_id
            if "completed_at" not in summary:
                summary["completed_at"] = None
            return summary

        # Compute summary from results
        summary = self._compute_summary(queue_id)
        summary["queue_id"] = queue_id
        summary["completed_at"] = None
        return summary

    def delete_queue_results(self, queue_id: str) -> bool:
        """Remove all results for a queue. Returns True if it existed."""
        queue_dir = self._base / queue_id
        if queue_dir.exists():
            import shutil
            shutil.rmtree(queue_dir)
            return True
        return False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _update_summary(self, queue_id: str) -> None:
        """Recompute and store summary for a queue."""
        summary = self._compute_summary(queue_id)

        summary_file = self._base / queue_id / "summary.json"
        summary_file.write_text(
            json.dumps(summary, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _compute_summary(self, queue_id: str) -> dict:
        """Compute summary from results without caching."""
        results_file = self._base / queue_id / "results.json"
        if not results_file.exists():
            raise FileNotFoundError(f"Queue results not found: {queue_id}")

        results = json.loads(results_file.read_text(encoding="utf-8"))
        if not results:
            return {
                "total_tasks": 0,
                "completed_tasks": 0,
                "failed_tasks": 0,
                "total_tokens": 0,
                "total_duration": 0.0,
            }

        total_tasks = len(results)
        completed = sum(1 for r in results.values() if r["status"] == "completed")
        failed = sum(1 for r in results.values() if r["status"] == "failed")
        total_tokens = sum(r.get("tokens_used", 0) for r in results.values())
        total_duration = sum(r.get("duration_seconds", 0.0) for r in results.values())

        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed,
            "failed_tasks": failed,
            "total_tokens": total_tokens,
            "total_duration": total_duration,
        }

    # ------------------------------------------------------------------
    # Export methods
    # ------------------------------------------------------------------

    def export_csv(
        self,
        queue_id: str,
        columns: list[str] | None = None,
    ) -> str:
        """Export all results for a queue as a CSV string.

        Args:
            queue_id:  The queue to export.
            columns:   Ordered column names.  Defaults to all top-level keys
                       found across results plus ``"result_data"`` flattened.

        Returns:
            A CSV-formatted string (with a header row).

        Raises:
            FileNotFoundError:  If the queue does not exist.
        """
        import csv
        import io

        results = self.get_all_results(queue_id)
        if not results:
            # Return empty CSV with just a header
            return ""

        # Determine columns from the first result's keys
        if columns is None:
            columns = list(results[0].keys())
            # Ensure result_data comes last
            if "result_data" in columns:
                columns.remove("result_data")
                columns.append("result_data")

        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(columns)

        for result in results:
            row = []
            for col in columns:
                value = result.get(col, "")
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False)
                row.append(value)
            writer.writerow(row)

        return buf.getvalue()

    def export_jsonl(self, queue_id: str) -> str:
        """Export all results for a queue as a JSONL string.

        Each line is a JSON object representing one task result.
        """
        results = self.get_all_results(queue_id)
        lines = [json.dumps(r, ensure_ascii=False) for r in results]
        return "\n".join(lines) + ("\n" if lines else "")

    def export_per_file(
        self,
        queue_id: str,
        output_dir: Path,
    ) -> list[Path]:
        """Write each result as a separate JSON file in *output_dir*.

        Files are named ``<task_id>.json``.

        Returns:
            List of written file paths.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        results = self.get_all_results(queue_id)
        written: list[Path] = []
        for result in results:
            task_id = result["task_id"]
            path = output_dir / f"{task_id}.json"
            path.write_text(
                json.dumps(result, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            written.append(path)
        return written

    def export_cost_report(self, queue_id: str) -> str:
        """Generate a human-readable cost report for a queue."""
        summary = self.get_summary(queue_id)
        results = self.get_all_results(queue_id)

        lines = [
            "=== Cost / Performance Report ===",
            f"Queue: {queue_id}",
            f"Total tasks: {summary['total_tasks']}",
            f"Completed: {summary['completed_tasks']}",
            f"Failed: {summary['failed_tasks']}",
            f"Total tokens used: {summary['total_tokens']}",
            f"Total duration: {summary['total_duration']:.2f}s",
            "",
            "Per-task breakdown:",
        ]

        for result in results:
            task_id = result["task_id"]
            status = result.get("status", "unknown")
            tokens = result.get("tokens_used", 0)
            duration = result.get("duration_seconds", 0.0)
            lines.append(
                f"  - {task_id}: status={status}, tokens={tokens}, duration={duration:.2f}s"
            )

        return "\n".join(lines)
