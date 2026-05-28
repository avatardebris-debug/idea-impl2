"""Finetune corpus directory layout (shared by collector and export)."""

from __future__ import annotations

import pathlib

from pipeline.paths import finetune_corpus_dir


def corpus_dir() -> pathlib.Path:
    return finetune_corpus_dir()


def raw_dir() -> pathlib.Path:
    return corpus_dir() / "raw"


def task_dir() -> pathlib.Path:
    return raw_dir() / "task"


def phase_dir() -> pathlib.Path:
    return raw_dir() / "phase"


def project_corpus_dir() -> pathlib.Path:
    return raw_dir() / "project"
