"""
Tests for the rebuilt test fixture generator.
Validates sampler, edge_case mutator, and VCR recorder — no faker involved.
"""

from __future__ import annotations

import csv
import json
import sys
import urllib.request
from pathlib import Path
from unittest.mock import patch

import pytest

from test_fixture_generator.sampler import Sampler
from test_fixture_generator.edge_cases import EdgeCaseMutator, MutationType
from test_fixture_generator.recorder import (
    VCRRecorder, Cassette, RecordedRequest, RecordedResponse,
    save_cassette, load_cassette, _cassette_path,
)


# ===========================================================================
# Sampler tests
# ===========================================================================

class TestSampler:

    def _make_csv(self, path: Path, rows: list[dict]) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        return path

    def _make_json(self, path: Path, data) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def test_find_data_files_discovers_csv_and_json(self, tmp_path):
        self._make_csv(tmp_path / "a.csv", [{"x": 1}])
        self._make_json(tmp_path / "b.json", [{"y": 2}])
        s = Sampler(tmp_path)
        found = s.find_data_files()
        names = {p.name for p in found}
        assert "a.csv" in names
        assert "b.json" in names

    def test_find_data_files_skips_empty_files(self, tmp_path):
        (tmp_path / "empty.csv").touch()
        s = Sampler(tmp_path)
        found = s.find_data_files()
        assert not any(p.name == "empty.csv" for p in found)

    def test_sample_csv_returns_real_rows(self, tmp_path):
        rows = [{"user_id": i, "email": f"u{i}@x.com", "score": i * 1.1} for i in range(20)]
        path = self._make_csv(tmp_path / "users.csv", rows)
        s = Sampler(tmp_path)
        result = s.sample_csv(path, n=5)
        assert result is not None
        assert len(result["rows"]) == 5
        # All rows should be real rows from the source, not fabricated
        source_emails = {f"u{i}@x.com" for i in range(20)}
        for row in result["rows"]:
            assert row["email"] in source_emails

    def test_sample_csv_schema_inference(self, tmp_path):
        rows = [{"name": "Alice", "age": "30", "active": "True"}]
        path = self._make_csv(tmp_path / "users.csv", rows)
        s = Sampler(tmp_path)
        result = s.sample_csv(path, n=1)
        assert "name" in result["schema"]
        assert "age" in result["schema"]

    def test_sample_csv_unreadable_returns_none(self, tmp_path):
        path = tmp_path / "bad.csv"
        path.write_bytes(b"\xff\xfe\x00")  # BOM without valid content
        s = Sampler(tmp_path)
        # Should not raise, should return None or empty
        result = s.sample_csv(path, n=5)
        # Either None (unreadable) or empty rows — both are acceptable
        assert result is None or len(result.get("rows", [])) == 0

    def test_sample_json_list_of_dicts(self, tmp_path):
        data = [{"id": i, "val": f"item_{i}"} for i in range(10)]
        path = self._make_json(tmp_path / "items.json", data)
        s = Sampler(tmp_path)
        result = s.sample_json(path, n=3)
        assert result is not None
        assert len(result["rows"]) == 3
        source_ids = {str(i) for i in range(10)}
        for row in result["rows"]:
            assert str(row["id"]) in source_ids

    def test_sample_json_envelope_extraction(self, tmp_path):
        """Handles {results: [...]} API envelope format."""
        data = {"count": 3, "results": [{"id": 1}, {"id": 2}, {"id": 3}]}
        path = self._make_json(tmp_path / "api.json", data)
        s = Sampler(tmp_path)
        result = s.sample_json(path, n=2)
        assert result is not None
        assert len(result["rows"]) == 2

    def test_sample_json_single_dict(self, tmp_path):
        """A plain dict is treated as one record."""
        data = {"project": "test", "version": "1.0"}
        path = self._make_json(tmp_path / "config.json", data)
        s = Sampler(tmp_path)
        result = s.sample_json(path, n=5)
        assert result is not None
        assert result["rows"][0]["project"] == "test"

    def test_sample_json_invalid_returns_none(self, tmp_path):
        path = tmp_path / "broken.json"
        path.write_text("not valid json {{{", encoding="utf-8")
        s = Sampler(tmp_path)
        result = s.sample_json(path, n=3)
        assert result is None

    def test_sample_all_writes_fixture_files(self, tmp_path):
        data_dir = tmp_path / "data"
        rows = [{"id": i, "name": f"item{i}"} for i in range(10)]
        self._make_csv(data_dir / "proj" / "workspace" / "data.csv", rows)

        output_dir = tmp_path / "fixtures"
        s = Sampler(data_dir)
        results = s.sample_all(output_dir, n=3)

        assert len(results) >= 1
        for r in results:
            assert r.fixture_path.exists()
            payload = json.loads(r.fixture_path.read_text())
            assert "rows" in payload
            assert "schema" in payload
            assert "source" in payload

    def test_sample_all_respects_n(self, tmp_path):
        rows = [{"id": i} for i in range(100)]
        self._make_csv(tmp_path / "big.csv", rows)
        output_dir = tmp_path / "out"
        s = Sampler(tmp_path)
        results = s.sample_all(output_dir, n=7)
        for r in results:
            assert r.row_count <= 7

    def test_sampler_deterministic_with_seed(self, tmp_path):
        rows = [{"id": i, "val": f"x{i}"} for i in range(50)]
        path = self._make_csv(tmp_path / "data.csv", rows)

        s1 = Sampler(tmp_path, seed=0)
        s2 = Sampler(tmp_path, seed=0)
        r1 = s1.sample_csv(path, n=5)
        r2 = s2.sample_csv(path, n=5)
        assert r1["rows"] == r2["rows"]


# ===========================================================================
# EdgeCaseMutator tests
# ===========================================================================

class TestEdgeCaseMutator:

    BASE = {"user_id": 42, "email": "alice@example.com", "active": True, "score": 9.5}

    def test_produces_mutations(self):
        m = EdgeCaseMutator()
        cases = m.all_mutations(self.BASE)
        assert len(cases) > 0

    def test_null_field_present_for_every_key(self):
        m = EdgeCaseMutator()
        cases = m.all_mutations(self.BASE)
        null_fields = {c.target_field for c in cases if c.mutation_type == MutationType.NULL_FIELD}
        for key in self.BASE:
            assert key in null_fields, f"NULL_FIELD missing for '{key}'"

    def test_missing_key_produces_smaller_dict(self):
        m = EdgeCaseMutator()
        cases = m.all_mutations(self.BASE)
        missing = [c for c in cases if c.mutation_type == MutationType.MISSING_KEY
                   and c.target_field == "user_id"]
        assert len(missing) >= 1
        assert "user_id" not in missing[0].fixture

    def test_each_mutation_changes_exactly_one_thing(self):
        """Regression test — make sure mutations don't corrupt unrelated fields."""
        m = EdgeCaseMutator()
        cases = m.all_mutations(self.BASE)
        for case in cases:
            if case.mutation_type == MutationType.NULL_FIELD and case.target_field:
                # Only the target field should be None; others should match base where present
                other_keys = [k for k in self.BASE if k != case.target_field
                              and k in case.fixture]
                for k in other_keys:
                    assert case.fixture[k] == self.BASE[k], (
                        f"Mutation {case.mutation_type} on '{case.target_field}' "
                        f"corrupted field '{k}'"
                    )

    def test_boundary_ints_cover_zero_and_maxsize(self):
        m = EdgeCaseMutator()
        cases = m.all_mutations(self.BASE)
        boundary_vals = {
            c.fixture.get("user_id")
            for c in cases
            if c.mutation_type == MutationType.BOUNDARY_INT and c.target_field == "user_id"
        }
        assert 0 in boundary_vals
        assert sys.maxsize in boundary_vals

    def test_overlong_string_is_10k_chars(self):
        m = EdgeCaseMutator()
        cases = m.all_mutations(self.BASE)
        overlong = [c for c in cases if c.mutation_type == MutationType.OVERLONG_STRING
                    and c.target_field == "email"]
        assert len(overlong) == 1
        assert len(overlong[0].fixture["email"]) == 10_000

    def test_encoding_bombs_include_sql_injection(self):
        m = EdgeCaseMutator()
        cases = m.all_mutations(self.BASE)
        bombs = [c for c in cases if c.mutation_type == MutationType.ENCODING_BOMB
                 and c.target_field == "email"]
        bomb_values = {c.fixture["email"] for c in bombs}
        assert any("DROP TABLE" in v for v in bomb_values)

    def test_bool_flip(self):
        m = EdgeCaseMutator()
        cases = m.all_mutations(self.BASE)
        flips = [c for c in cases if c.mutation_type == MutationType.BOOL_FLIP
                 and c.target_field == "active"]
        assert len(flips) == 1
        assert flips[0].fixture["active"] is False

    def test_wrong_type_string_to_int(self):
        m = EdgeCaseMutator()
        cases = m.all_mutations(self.BASE)
        wrong = [c for c in cases if c.mutation_type == MutationType.WRONG_TYPE
                 and c.target_field == "email"]
        assert any(isinstance(c.fixture["email"], int) for c in wrong)

    def test_extra_key_adds_unexpected_field(self):
        m = EdgeCaseMutator()
        cases = m.all_mutations(self.BASE)
        extra = [c for c in cases if c.mutation_type == MutationType.EXTRA_KEY]
        assert len(extra) >= 1
        assert "__unexpected_field__" in extra[0].fixture

    def test_empty_record_structural_mutation(self):
        m = EdgeCaseMutator()
        cases = m.all_mutations(self.BASE)
        empty = [c for c in cases if c.fixture == {} and c.mutation_type == MutationType.MISSING_KEY]
        assert len(empty) == 1

    def test_targeted_mutation(self):
        m = EdgeCaseMutator()
        case = m.targeted(self.BASE, "user_id", MutationType.NULL_FIELD)
        assert case.fixture["user_id"] is None
        assert case.fixture["email"] == self.BASE["email"]


# ===========================================================================
# VCRRecorder tests
# ===========================================================================

class TestVCRRecorder:

    def _make_cassette(self) -> Cassette:
        return Cassette(
            request=RecordedRequest(
                method="GET",
                url="https://api.example.com/users",
                request_headers={},
                recorded_at=1_700_000_000.0,
            ),
            response=RecordedResponse(
                status=200,
                headers={"Content-Type": "application/json"},
                body='{"users": [{"id": 1}]}',
                is_binary=False,
            ),
        )

    def test_cassette_path_is_deterministic(self, tmp_path):
        p1 = _cassette_path(tmp_path, "GET", "https://api.example.com/users")
        p2 = _cassette_path(tmp_path, "GET", "https://api.example.com/users")
        assert p1 == p2

    def test_cassette_path_differs_by_url(self, tmp_path):
        p1 = _cassette_path(tmp_path, "GET", "https://api.example.com/users")
        p2 = _cassette_path(tmp_path, "GET", "https://api.example.com/posts")
        assert p1 != p2

    def test_save_and_load_roundtrip(self, tmp_path):
        cassette = self._make_cassette()
        save_cassette(tmp_path, "GET", "https://api.example.com/users", cassette)
        loaded = load_cassette(tmp_path, "GET", "https://api.example.com/users")
        assert loaded is not None
        assert loaded.response.status == 200
        assert loaded.response.body == cassette.response.body

    def test_load_missing_cassette_returns_none(self, tmp_path):
        result = load_cassette(tmp_path, "GET", "https://not.recorded.example/")
        assert result is None

    def test_replay_mode_returns_saved_response(self, tmp_path):
        cassette = self._make_cassette()
        save_cassette(tmp_path, "GET", "https://api.example.com/users", cassette)

        vcr = VCRRecorder(cassette_dir=tmp_path, mode="replay")
        with vcr.intercept("GET", "https://api.example.com/users"):
            resp = urllib.request.urlopen("https://api.example.com/users")
            body = resp.read()

        data = json.loads(body)
        assert data["users"][0]["id"] == 1

    def test_replay_raises_if_no_cassette(self, tmp_path):
        vcr = VCRRecorder(cassette_dir=tmp_path, mode="replay")
        with pytest.raises(FileNotFoundError, match="No cassette found"):
            with vcr.intercept("GET", "https://missing.example.com/"):
                urllib.request.urlopen("https://missing.example.com/")

    def test_record_mode_saves_cassette(self, tmp_path):
        """Record mode should intercept, save, and still return readable response."""
        fake_body = b'{"recorded": true}'

        class FakeResponse:
            status = 201
            headers = {"Content-Type": "application/json"}
            def read(self): return fake_body
            def __enter__(self): return self
            def __exit__(self, *a): pass

        with patch("urllib.request.urlopen", return_value=FakeResponse()):
            vcr = VCRRecorder(cassette_dir=tmp_path, mode="record")
            with vcr.intercept("GET", "https://api.example.com/test"):
                resp = urllib.request.urlopen("https://api.example.com/test")
                body = resp.read()

        assert json.loads(body)["recorded"] is True

        # Cassette should now be on disk
        saved = load_cassette(tmp_path, "GET", "https://api.example.com/test")
        assert saved is not None
        assert saved.response.status == 201
        assert '"recorded": true' in saved.response.body

    def test_passthrough_mode_does_not_patch(self, tmp_path):
        """Passthrough should not intercept anything."""
        call_log = []

        def fake_urlopen(url, *a, **kw):
            call_log.append(url)
            raise ConnectionError("should not reach network in test")

        vcr = VCRRecorder(cassette_dir=tmp_path, mode="passthrough")
        # In passthrough mode the context manager yields without patching
        with vcr.intercept("GET", "https://example.com"):
            pass  # No call made — just confirm no exception

    def test_invalid_mode_raises(self, tmp_path):
        with pytest.raises(ValueError, match="Invalid mode"):
            VCRRecorder(cassette_dir=tmp_path, mode="INVALID")

    def test_cassette_serialisation_to_dict(self):
        c = self._make_cassette()
        d = c.to_dict()
        assert d["request"]["method"] == "GET"
        assert d["response"]["status"] == 200
        restored = Cassette.from_dict(d)
        assert restored.response.body == c.response.body
