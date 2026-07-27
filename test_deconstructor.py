"""deconstructor v0 — parse real structure, no fixed studio template."""

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


HOSPITAL = """\
Hospital
- Emergency
  - triage nurse
  - attending physician
- Radiology: MRI tech, radiologist
- Billing: coder, collections
"""

CREDITS_NES = """\
Director - Alice
Programmer - Bob
Composer - Carol
Tester - Dana
"""

TOOLS_BLENDER = """\
Blender surface
- Core IO: open, save, export
- Animation: keyframe, bake
- Scripting
"""


def test_bare_title_needs_structure_not_fake_studio() -> None:
    from pipeline.deconstructor import build_deconstruct

    doc = build_deconstruct("small indie game studio", mode="org")
    assert doc["needs_structure"] is True
    names = {c["name"].lower() for c in doc["candidates"]}
    # Must NOT invent engineering/art/ops template
    assert not any("engineering" in n for n in names)
    assert not any(n == "implementer" for n in names)
    assert doc["status"] == "needs_structure"


def test_hospital_structure_not_studio_template() -> None:
    from pipeline.deconstructor import build_deconstruct

    doc = build_deconstruct(HOSPITAL, mode="org")
    assert doc["needs_structure"] is False
    names = {c["name"] for c in doc["candidates"]}
    assert "Emergency" in names or "emergency" in {n.lower() for n in names}
    assert any("triage" in n.lower() for n in names)
    assert any("radiologist" in n.lower() for n in names)
    assert any("billing" in n.lower() for n in names)
    # Not the old fixed template
    assert "implementer" not in {n.lower() for n in names}
    assert "pixel artist" not in {n.lower() for n in names}
    assert doc["critique"]["ok"] is True


def test_different_targets_differ() -> None:
    from pipeline.deconstructor import build_deconstruct

    a = build_deconstruct(HOSPITAL, mode="org")
    b = build_deconstruct(
        "Law firm\n- Litigation: partner, associate\n- Intake: paralegal\n",
        mode="org",
    )
    names_a = {c["name"].lower() for c in a["candidates"]}
    names_b = {c["name"].lower() for c in b["candidates"]}
    assert names_a != names_b
    assert any("litigation" in n or "associate" in n for n in names_b)
    assert any("emergency" in n or "triage" in n for n in names_a)


def test_credits_parse_roles() -> None:
    from pipeline.deconstructor import build_deconstruct, classify_name

    doc = build_deconstruct(CREDITS_NES, mode="credits")
    assert doc["needs_structure"] is False
    names = {c["name"] for c in doc["candidates"]}
    assert "Director" in names
    assert "Programmer" in names
    assert "Composer" in names
    # Director should classify human-ish
    d = next(c for c in doc["candidates"] if c["name"] == "Director")
    assert d["replacement_class"] == "human"
    assert classify_name("attending physician", mode="org") == "human"


def test_tool_surface_from_target() -> None:
    from pipeline.deconstructor import build_deconstruct

    doc = build_deconstruct(TOOLS_BLENDER, mode="tool_surface")
    names = {c["name"].lower() for c in doc["candidates"]}
    assert any("animation" in n for n in names)
    assert any("keyframe" in n or "export" in n for n in names)
    assert doc["needs_structure"] is False


def test_prose_cue_extraction() -> None:
    from pipeline.deconstructor import build_deconstruct

    doc = build_deconstruct(
        "Clinic departments include emergency, radiology, and pharmacy",
        mode="org",
    )
    assert doc["needs_structure"] is False
    names = " ".join(c["name"].lower() for c in doc["candidates"])
    assert "emergency" in names
    assert "radiology" in names
    assert "pharmacy" in names


def test_csv_single_line() -> None:
    from pipeline.deconstructor import build_deconstruct

    doc = build_deconstruct("Director, Producer, Programmer, Tester", mode="credits")
    assert len(doc["candidates"]) >= 4
    assert doc["needs_structure"] is False


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


def test_production_graph_flag_rejected() -> None:
    from pipeline.deconstructor import build_deconstruct, critique_deconstruct

    doc = build_deconstruct("Director, Producer", mode="credits")
    doc["production_graph"] = True
    crit = critique_deconstruct(doc)
    assert crit["ok"] is False
    assert any(i["code"] == "not_production" for i in crit["issues"])


def test_plan_fill_orders_actions() -> None:
    from pipeline.deconstructor import build_deconstruct, plan_fill_actions

    doc = build_deconstruct(HOSPITAL, mode="org")
    plan = plan_fill_actions(doc)
    assert plan["production_graph"] is False
    assert plan["actions"]
    assert plan["needs_structure"] is False
    classes = [a["replacement_class"] for a in plan["actions"]]
    if "skill" in classes and "human" in classes:
        assert classes.index("skill") < classes.index("human")


def test_cli_target_file(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir()
    _reload_pipeline(monkeypatch, pipeline)

    tf = tmp_path / "hospital.txt"
    tf.write_text(HOSPITAL, encoding="utf-8")
    cli_main = _cli_main()
    rc = cli_main(
        [
            "--pipeline-dir",
            str(pipeline),
            "build",
            "--mode",
            "org",
            "--target-file",
            str(tf),
            "--id",
            "hospital-org",
        ]
    )
    assert rc == 0
    saved = pipeline / "deconstructs" / "hospital-org.json"
    data = json.loads(saved.read_text(encoding="utf-8"))
    assert data["needs_structure"] is False
    names = " ".join(c["name"].lower() for c in data["candidates"])
    assert "emergency" in names


def test_cli_bare_title_exit_2(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> None:
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
            "org",
            "--target",
            "random bakery",
            "--id",
            "bakery",
        ]
    )
    assert rc == 2


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
    data = json.loads(saved.read_text(encoding="utf-8"))
    assert data["critique"]["ok"] is True


def test_enum_closed_on_hospital() -> None:
    from pipeline.deconstructor import REPLACEMENT_CLASSES, seed_candidates

    cands, _ = seed_candidates("org", HOSPITAL)
    for c in cands:
        assert c["replacement_class"] in REPLACEMENT_CLASSES
        assert c["oracle_hint"]
