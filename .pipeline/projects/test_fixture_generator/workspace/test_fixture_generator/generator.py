"""
Test Fixture Generator
======================
Generates realistic test fixtures by:
  1. Scanning a project's existing tests for schema hints (field names + types)
  2. Using `faker` to produce realistic, varied data — not hardcoded constants
  3. Supporting JSON, CSV, and mock HTTP response outputs
  4. Accepting an explicit schema dict for direct use without scanning

Schema dict format
------------------
  {
    "field_name": "type"   # type = string|int|float|bool|email|name|uuid|date|url|phone|address|paragraph
  }
"""

from __future__ import annotations

import ast
import csv
import json
import re
import uuid as uuid_mod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from faker import Faker

_faker = Faker()


# ---------------------------------------------------------------------------
# Supported fixture output types
# ---------------------------------------------------------------------------

class FixtureType(str, Enum):
    JSON = "json"
    CSV = "csv"
    TEXT = "text"
    HTTP_RESPONSE = "http_response"


# ---------------------------------------------------------------------------
# Realistic value generation from schema type labels
# ---------------------------------------------------------------------------

_TYPE_GENERATORS: Dict[str, Any] = {
    "string":    lambda: _faker.word(),
    "str":       lambda: _faker.word(),
    "int":       lambda: _faker.random_int(min=1, max=9999),
    "integer":   lambda: _faker.random_int(min=1, max=9999),
    "float":     lambda: round(_faker.pyfloat(min_value=0, max_value=1000, right_digits=2), 2),
    "bool":      lambda: _faker.boolean(),
    "boolean":   lambda: _faker.boolean(),
    "email":     lambda: _faker.email(),
    "name":      lambda: _faker.name(),
    "uuid":      lambda: str(uuid_mod.uuid4()),
    "date":      lambda: _faker.date(),
    "datetime":  lambda: _faker.iso8601(),
    "url":       lambda: _faker.url(),
    "phone":     lambda: _faker.phone_number(),
    "address":   lambda: _faker.address().replace("\n", ", "),
    "paragraph": lambda: _faker.paragraph(),
    "username":  lambda: _faker.user_name(),
    "password":  lambda: _faker.password(length=16),
    "company":   lambda: _faker.company(),
    "city":      lambda: _faker.city(),
    "country":   lambda: _faker.country(),
    "zip":       lambda: _faker.postcode(),
    "ipv4":      lambda: _faker.ipv4(),
    "ipv6":      lambda: _faker.ipv6(),
    "slug":      lambda: _faker.slug(),
    "hex_color": lambda: _faker.hex_color(),
    "sentence":  lambda: _faker.sentence(),
    "id":        lambda: _faker.random_int(min=1, max=999999),
}


def _gen_value(type_hint: str) -> Any:
    """Generate a realistic value for a given type label."""
    key = type_hint.lower().strip()
    gen = _TYPE_GENERATORS.get(key)
    if gen:
        return gen()
    # Fallback: treat unknown as string
    return _faker.word()


def _gen_record(schema: Dict[str, str]) -> Dict[str, Any]:
    return {field: _gen_value(typ) for field, typ in schema.items()}


# ---------------------------------------------------------------------------
# Schema inference from existing test files
# ---------------------------------------------------------------------------

class SchemaInferrer:
    """
    Parses a project's test directory to infer field names and types from:
      - pytest fixture functions (return dict / dataclass literals)
      - Variable assignments like `data = {"email": "test@test.com"}`
    """

    _EMAIL_RE = re.compile(r"[^@]+@[^@]+\.[^@]+")
    _URL_RE = re.compile(r"https?://\S+")
    _UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.I)

    def infer_from_dir(self, tests_dir: Path) -> Dict[str, str]:
        """Walk a tests directory and merge inferred schemas from all .py files."""
        schema: Dict[str, str] = {}
        for path in tests_dir.rglob("test_*.py"):
            schema.update(self._infer_from_file(path))
        return schema

    def _infer_from_file(self, path: Path) -> Dict[str, str]:
        schema: Dict[str, str] = {}
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            return schema

        for node in ast.walk(tree):
            if isinstance(node, ast.Dict):
                for key, value in zip(node.keys, node.values):
                    if not isinstance(key, ast.Constant):
                        continue
                    field_name = str(key.value).lower()
                    inferred = self._infer_type_from_name_and_value(field_name, value)
                    if inferred:
                        schema[key.value] = inferred

        return schema

    def _infer_type_from_name_and_value(self, name: str, value_node: ast.expr) -> Optional[str]:
        # Infer from field name first
        for keyword in ["email", "url", "uuid", "name", "phone", "address", "date",
                        "city", "country", "company", "username", "password", "slug"]:
            if keyword in name:
                return keyword

        if "id" == name or name.endswith("_id"):
            return "id"

        # Infer from literal value
        if isinstance(value_node, ast.Constant):
            v = value_node.value
            if isinstance(v, bool):
                return "bool"
            if isinstance(v, int):
                return "int"
            if isinstance(v, float):
                return "float"
            if isinstance(v, str):
                if self._EMAIL_RE.match(v):
                    return "email"
                if self._URL_RE.match(v):
                    return "url"
                if self._UUID_RE.match(v):
                    return "uuid"
                return "string"

        return "string"


# ---------------------------------------------------------------------------
# Mock HTTP response fixture
# ---------------------------------------------------------------------------

def _generate_http_response(schema: Dict[str, str], count: int, status: int = 200) -> Dict[str, Any]:
    """Generate a realistic mock HTTP JSON API response envelope."""
    records = [_gen_record(schema) for _ in range(count)]
    return {
        "status": status,
        "headers": {
            "Content-Type": "application/json",
            "X-Request-Id": str(uuid_mod.uuid4()),
            "X-RateLimit-Remaining": _faker.random_int(min=0, max=1000),
        },
        "body": {
            "count": count,
            "next": _faker.url() if count > 1 else None,
            "results": records if count > 1 else records[0],
        }
    }


# ---------------------------------------------------------------------------
# Main public API
# ---------------------------------------------------------------------------

def generate_fixture(
    output_path: Path,
    fixture_type: FixtureType,
    schema: Dict[str, str],
    count: int = 1,
    http_status: int = 200,
) -> Path:
    """
    Generate a fixture and write it to disk.

    Args:
        output_path:   Where to write the file.
        fixture_type:  FixtureType.JSON | CSV | TEXT | HTTP_RESPONSE
        schema:        Dict mapping field_name -> type_label.
        count:         Number of records to generate.
        http_status:   Only used for HTTP_RESPONSE; sets the status code.

    Returns:
        The resolved output_path.
    """
    output_path = Path(output_path)

    if fixture_type == FixtureType.JSON:
        records = [_gen_record(schema) for _ in range(count)]
        data = records[0] if count == 1 else records
        output_path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

    elif fixture_type == FixtureType.CSV:
        records = [_gen_record(schema) for _ in range(max(count, 1))]
        with open(output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(schema.keys()))
            writer.writeheader()
            writer.writerows(records)

    elif fixture_type == FixtureType.TEXT:
        lines = [_faker.sentence() for _ in range(count)]
        output_path.write_text("\n".join(lines), encoding="utf-8")

    elif fixture_type == FixtureType.HTTP_RESPONSE:
        data = _generate_http_response(schema, count, http_status)
        output_path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

    else:
        raise ValueError(f"Unsupported fixture_type: {fixture_type}")

    return output_path


def infer_and_generate(
    project_tests_dir: Path,
    output_path: Path,
    fixture_type: FixtureType = FixtureType.JSON,
    count: int = 5,
) -> Path:
    """
    Scan `project_tests_dir` for schema hints, then generate a fixture.
    Falls back to a minimal generic schema if nothing can be inferred.
    """
    inferrer = SchemaInferrer()
    schema = inferrer.infer_from_dir(Path(project_tests_dir))

    if not schema:
        # Fallback generic schema
        schema = {"id": "id", "name": "name", "email": "email", "created_at": "datetime"}

    return generate_fixture(output_path, fixture_type, schema, count)
