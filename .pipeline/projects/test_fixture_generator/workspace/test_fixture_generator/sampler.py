"""
sampler.py — Real-data fixture extraction from pipeline workspace files.

Scans actual project output (JSON, CSV) already produced by the pipeline and
extracts representative rows/records as named fixture files.  Tests that use
these fixtures are testing against data the pipeline *already processed* —
not against hand-crafted happy-path examples.

Usage
-----
    from test_fixture_generator.sampler import Sampler

    s = Sampler(pipeline_root=Path("c:/Users/avata/aicompete/idea impl/.pipeline/projects"))
    # Sample 5 rows from every CSV in the workspace trees and save fixtures
    saved = s.sample_all(output_dir=Path("tests/fixtures"), n=5)
"""

from __future__ import annotations

import csv
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class SampledFixture:
    source_path: Path        # where the real data came from
    fixture_path: Path       # where the fixture was written
    row_count: int           # how many rows were captured
    file_type: str           # "json" | "csv"
    schema: Dict[str, str]   # inferred field -> python type name


class Sampler:
    """
    Walks real pipeline workspace files and extracts sample rows as test fixtures.
    By default avoids __pycache__, .git, and .pytest_cache dirs.
    """

    _SKIP_DIRS = {"__pycache__", ".git", ".pytest_cache", ".venv", "node_modules"}

    def __init__(
        self,
        pipeline_root: Path,
        seed: int = 42,
    ):
        self.pipeline_root = Path(pipeline_root)
        self._rng = random.Random(seed)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def find_data_files(self) -> List[Path]:
        """Return all JSON and CSV files under the pipeline root."""
        found: List[Path] = []
        for ext in ("*.json", "*.csv"):
            for p in self.pipeline_root.rglob(ext):
                if any(skip in p.parts for skip in self._SKIP_DIRS):
                    continue
                if p.stat().st_size == 0:
                    continue
                found.append(p)
        return sorted(found)

    def sample_csv(self, path: Path, n: int = 5) -> Optional[Dict[str, Any]]:
        """
        Sample up to `n` rows from a CSV.
        Returns None if the file is unreadable or has no data rows.
        """
        try:
            with open(path, newline="", encoding="utf-8", errors="replace") as f:
                reader = csv.DictReader(f)
                rows = [dict(r) for r in reader]
        except Exception:
            return None

        if not rows:
            return None

        sampled = self._rng.sample(rows, min(n, len(rows)))
        schema = self._infer_schema_from_rows(sampled)
        return {"rows": sampled, "schema": schema, "source": str(path)}

    def sample_json(self, path: Path, n: int = 5) -> Optional[Dict[str, Any]]:
        """
        Sample up to `n` records from a JSON file.
        Handles: list-of-dicts, dict, nested {results: [...]} envelopes.
        Returns None if unreadable or structurally unsuitable.
        """
        try:
            raw = path.read_text(encoding="utf-8", errors="replace")
            data = json.loads(raw)
        except Exception:
            return None

        records = self._extract_records(data, n)
        if not records:
            return None

        schema = self._infer_schema_from_rows(records)
        return {"rows": records, "schema": schema, "source": str(path)}

    def sample_all(
        self,
        output_dir: Path,
        n: int = 5,
        max_files: int = 50,
    ) -> List[SampledFixture]:
        """
        Find all data files, sample each, and write fixtures to output_dir.
        Returns a list of SampledFixture metadata objects.
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        data_files = self.find_data_files()[:max_files]
        results: List[SampledFixture] = []

        for path in data_files:
            ext = path.suffix.lower()
            if ext == ".csv":
                payload = self.sample_csv(path, n)
                ftype = "csv"
            elif ext == ".json":
                payload = self.sample_json(path, n)
                ftype = "json"
            else:
                continue

            if not payload:
                continue

            # Derive a safe fixture filename from the source path
            safe_name = "_".join(path.parts[-3:]).replace(" ", "_")
            safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in safe_name)
            fixture_path = output_dir / f"sample__{safe_name}.json"

            fixture_path.write_text(
                json.dumps(payload, indent=2, default=str),
                encoding="utf-8",
            )

            results.append(SampledFixture(
                source_path=path,
                fixture_path=fixture_path,
                row_count=len(payload["rows"]),
                file_type=ftype,
                schema=payload["schema"],
            ))

        return results

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _extract_records(self, data: Any, n: int) -> List[Dict[str, Any]]:
        """Normalise varied JSON shapes into a list of flat dicts."""
        if isinstance(data, list):
            records = [r for r in data if isinstance(r, dict)]
        elif isinstance(data, dict):
            # Try common envelope keys first
            for key in ("results", "data", "items", "records", "rows"):
                if key in data and isinstance(data[key], list):
                    records = [r for r in data[key] if isinstance(r, dict)]
                    break
            else:
                # Treat the whole dict as one record
                records = [data]
        else:
            return []

        if not records:
            return []

        return self._rng.sample(records, min(n, len(records)))

    @staticmethod
    def _infer_schema_from_rows(rows: List[Dict[str, Any]]) -> Dict[str, str]:
        """Return a field -> python-type-name mapping inferred from sampled rows."""
        schema: Dict[str, str] = {}
        if not rows:
            return schema
        for key in rows[0]:
            for row in rows:
                val = row.get(key)
                if val is None:
                    continue
                schema[key] = type(val).__name__
                break
            else:
                schema[key] = "NoneType"
        return schema
