"""deconstructor v0 — schema, seeds, critique, plan-fill, CLI."""

from __future__ import annotations

import importlib.util
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _reload_pipeline(monkeypatch: pytest.MonkeyPatch, pipeline: pathlib.Path) -> None:
    monkeypatch.setenv("PIPELINE_DIR", str(pipeline))
    monkeypatch.delenv("PIPELINE_CLOUD", raising=False)
    from pipeline.pipeline_config import reload_pipeline_dir

    reload_pipeline_dir()


def _cli_main():
    cli_path = ROOT / "scripts" / "deconstructor.py"
    spec = importlib.util.spec_from_file_location("deconstructor_cli", cli_path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.main


def test_seed_modes_critique_ok(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir()
    _reload_pipeline(monkeypatch, pipeline)

    from pipeline.deconstructor import MODES, build_deconstruct, save_deconstruct

    for mode in sorted(MODES):
        if mode == "open":
            doc = build_deconstruct("ambiguous thing", mode=mode)
        else:
            doc = build_deconstruct(f"fixture {mode}", mode=mode)
        assert doc["schema"] == "deconstruct.v0"
        assert doc["production_graph"] is False
        assert doc["candidates"]
        assert doc["critique"]["ok"] is True, (mode, doc["critique"])
        path = save_deconstruct(doc)
        assert path.is_file()
        assert path.parent.name == "deconstructs"


def test_invalid_class_blocked(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir()
    _reload_pipeline(monkeypatch, pipeline)

    from pipeline.deconstructor import from_candidates

    doc = from_candidates(
        "bad class",
        [{"id": "x1", "name": "X", "replacement_class": "magic_ai"}],
        mode="open",
    )
    assert doc["critique"]["ok"] is False
    codes = {i["code"] for i in doc["critique"]["issues"]}
    assert "class" in codes


def test_size_budget(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir()
    _reload_pipeline(monkeypatch, pipeline)

    from pipeline.deconstructor import from_candidates

    cands = [
        {"id": f"n{i}", "name": f"N{i}", "replacement_class": "skill", "oracle_hint": "ok"}
        for i in range(5)
    ]
    doc = from_candidates("many", cands, mode="open", max_nodes=3)
    assert doc["critique"]["ok"] is False
    assert any(i["code"] == "size_budget" for i in doc["critique"]["issues"])


def test_production_graph_flag_rejected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir()
    _reload_pipeline(monkeypatch, pipeline)

    from pipeline.deconstructor import build_deconstruct, critique_deconstruct

    doc = build_deconstruct("x", mode="open")
    doc["production_graph"] = True
    crit = critique_deconstruct(doc)
    assert crit["ok"] is False
    assert any(i["code"] == "not_production" for i in crit["issues"])


def test_plan_fill_orders_actions(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir()
    _reload_pipeline(monkeypatch, pipeline)

    from pipeline.deconstructor import build_deconstruct, plan_fill_actions

    doc = build_deconstruct("indie studio", mode="org")
    plan = plan_fill_actions(doc)
    assert plan["production_graph"] is False
    assert plan["actions"]
    assert plan["by_class"]
    # skills should appear before human in sort order
    classes = [a["replacement_class"] for a in plan["actions"]]
    if "skill" in classes and "human" in classes:
        assert classes.index("skill") < classes.index("human")


def test_from_json_cli(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir()
    _reload_pipeline(monkeypatch, pipeline)

    inv = tmp_path / "inv.json"
    inv.write_text(
        json.dumps(
            {
                "target": "toy dept",
                "mode": "org",
                "candidates": [
                    {
                        "id": "eng",
                        "name": "engineering",
                        "replacement_class": "skill",
                        "oracle_hint": "build passes",
                        "depth": 0,
                    },
                    {
                        "id": "legal",
                        "name": "legal",
                        "replacement_class": "human",
                        "oracle_hint": "sign-off",
                        "depth": 0,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    cli_main = _cli_main()

    rc = cli_main(
        ["--pipeline-dir", str(pipeline), "from-json", "--path", str(inv), "--id", "toy-dept"]
    )
    assert rc == 0
    saved = pipeline / "deconstructs" / "toy-dept.json"
    assert saved.is_file()
    data = json.loads(saved.read_text(encoding="utf-8"))
    assert data["critique"]["ok"] is True
    assert len(data["candidates"]) == 2


def test_cli_build_list_plan(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir()
    _reload_pipeline(monkeypatch, pipeline)

    cli_main = _cli_main()

    rc = cli_main(
        [
            "--pipeline-dir",
            str(pipeline),
            "build",
            "--mode",
            "credits",
            "--target",
            "NES toy",
            "--id",
            "credits-nes-toy",
        ]
    )
    assert rc == 0

    rc2 = cli_main(["--pipeline-dir", str(pipeline), "list"])
    assert rc2 == 0

    rc3 = cli_main(
        ["--pipeline-dir", str(pipeline), "plan-fill", "--id", "credits-nes-toy"]
    )
    assert rc3 == 0

    rc4 = cli_main(
        ["--pipeline-dir", str(pipeline), "validate", "--id", "credits-nes-toy"]
    )
    assert rc4 == 0


def test_credits_fixture_enum_closed() -> None:
    """Inline fixture: every seed class is in closed enum."""
    from pipeline.deconstructor import REPLACEMENT_CLASSES, seed_candidates

    cands, _ = seed_candidates("credits", "fixture game")
    for c in cands:
        assert c["replacement_class"] in REPLACEMENT_CLASSES
        assert c["oracle_hint"]
