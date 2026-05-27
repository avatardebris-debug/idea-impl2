"""Canonical pipeline output path helpers (always live-resolve)."""

from __future__ import annotations

import pathlib

from pipeline.pipeline_config import (
    PROJECT_ROOT,
    get_pipeline_dir,
    reload_pipeline_dir,
    resolve_pipeline_dir,
)

__all__ = [
    "PROJECT_ROOT",
    "get_pipeline_dir",
    "reload_pipeline_dir",
    "resolve_pipeline_dir",
    "projects_dir",
    "state_dir",
    "workflows_dir",
    "memory_dir",
    "logs_dir",
    "finetune_corpus_dir",
    "connectors_dir",
    "goals_dir",
    "shared_libs_dir",
    "registry_db",
    "capabilities_md",
    "completions_jsonl",
]


def projects_dir() -> pathlib.Path:
    return get_pipeline_dir() / "projects"


def state_dir() -> pathlib.Path:
    return get_pipeline_dir() / "state"


def workflows_dir() -> pathlib.Path:
    return get_pipeline_dir() / "workflows"


def connectors_dir() -> pathlib.Path:
    return workflows_dir() / "connectors"


def memory_dir() -> pathlib.Path:
    return get_pipeline_dir() / "memory"


def logs_dir() -> pathlib.Path:
    return get_pipeline_dir() / "logs"


def finetune_corpus_dir() -> pathlib.Path:
    return get_pipeline_dir() / "finetune_corpus"


def goals_dir() -> pathlib.Path:
    return get_pipeline_dir() / "goals"


def shared_libs_dir() -> pathlib.Path:
    return get_pipeline_dir() / "shared_libs"


def registry_db() -> pathlib.Path:
    return state_dir() / "capability_registry.sqlite"


def capabilities_md() -> pathlib.Path:
    return state_dir() / "CAPABILITIES.md"


def completions_jsonl() -> pathlib.Path:
    return state_dir() / "completions.jsonl"
