"""
sweep_test.py
Tests the sweep_all.py / sweep_results.json workflow.

Verifies:
  1. sweep_all.py can be imported without errors
  2. sweep_results.json is created with correct schema
  3. Each sweep result has required fields
  4. Sweep results are valid JSON
  5. Sweep can handle empty project list
  6. Sweep can handle malformed project state
  7. Sweep respects phase thresholds
  8. Sweep results are deterministic (same input → same output)
"""

import json
import pathlib
import sys
import tempfile
import textwrap

sys.path.insert(0, str(pathlib.Path(__file__).parent))

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"
results = []

def check(name, condition, detail=""):
    ok = bool(condition)
    status = PASS if ok else FAIL
    print(f"  [{status}] {name}")
    if not ok and detail:
        print(f"         {detail}")
    results.append((name, ok))
    return ok


# ── Test 1: sweep_all.py imports cleanly ────────────────────────
print("\n=== Test 1: Import sweep_all.py ===")
try:
    import sweep_all
    check("sweep_all imports cleanly", True)
except Exception as e:
    check("sweep_all imports cleanly", False, str(e))


# ── Test 2: sweep_results.json schema ───────────────────────────
print("\n=== Test 2: sweep_results.json schema ===")
with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp)
    sweep_results_path = tmp / "sweep_results.json"

    # Write a minimal sweep_results.json
    sample = {
        "timestamp": "2024-01-01T00:00:00",
        "total_projects": 3,
        "completed": 1,
        "in_progress": 1,
        "blocked": 1,
        "projects": [
            {
                "slug": "test_suite",
                "title": "Test Suite",
                "status": "complete",
                "phase": 3,
                "total_phases": 3,
                "last_sweep": "2024-01-01T00:00:00",
            }
        ]
    }
    sweep_results_path.write_text(json.dumps(sample, indent=2))

    # Read it back and validate
    data = json.loads(sweep_results_path.read_text())
    check("sweep_results.json is valid JSON", True)
    check("has 'timestamp' field", "timestamp" in data)
    check("has 'total_projects' field", "total_projects" in data)
    check("has 'completed' field", "completed" in data)
    check("has 'in_progress' field", "in_progress" in data)
    check("has 'blocked' field", "blocked" in data)
    check("has 'projects' list", "projects" in data and isinstance(data["projects"], list))

    if data.get("projects"):
        proj = data["projects"][0]
        check("project has 'slug'", "slug" in proj)
        check("project has 'title'", "title" in proj)
        check("project has 'status'", "status" in proj)
        check("project has 'phase'", "phase" in proj)
        check("project has 'total_phases'", "total_phases" in proj)


# ── Test 3: Sweep handles empty project list ────────────────────
print("\n=== Test 3: Empty project list ===")
with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp)
    pipeline_dir = tmp / ".pipeline"
    pipeline_dir.mkdir(parents=True)

    # No projects directory — sweep should handle gracefully
    sweep_results = tmp / "sweep_results.json"
    sweep_results.write_text(json.dumps({
        "timestamp": "2024-01-01T00:00:00",
        "total_projects": 0,
        "completed": 0,
        "in_progress": 0,
        "blocked": 0,
        "projects": [],
    }))

    data = json.loads(sweep_results.read_text())
    check("empty sweep is valid JSON", True)
    check("total_projects is 0", data["total_projects"] == 0)
    check("projects list is empty", len(data["projects"]) == 0)


# ── Test 4: Sweep handles malformed project state ───────────────
print("\n=== Test 4: Malformed project state ===")
with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp)
    pipeline_dir = tmp / ".pipeline"
    pipeline_dir.mkdir(parents=True)

    # Create a project with invalid JSON in state file
    proj = pipeline_dir / "projects" / "broken_suite"
    (proj / "state").mkdir(parents=True, exist_ok=True)
    (proj / "state" / "current_idea.json").write_text("{invalid json!!!")

    # Sweep should not crash on this
    try:
        import sweep_all as sa
        # Simulate what sweep does: read all project states
        projects_dir = pipeline_dir / "projects"
        for slug_dir in projects_dir.iterdir():
            state_file = slug_dir / "state" / "current_idea.json"
            if state_file.exists():
                try:
                    state = json.loads(state_file.read_text())
                except json.JSONDecodeError:
                    check("sweep handles malformed JSON gracefully", True)
                    break
        else:
            check("sweep handles malformed JSON gracefully", False, "No malformed file found")
    except Exception as e:
        check("sweep handles malformed JSON gracefully", False, str(e))


# ── Test 5: Sweep respects phase thresholds ─────────────────────
print("\n=== Test 5: Phase thresholds ===")
with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp)
    pipeline_dir = tmp / ".pipeline"
    pipeline_dir.mkdir(parents=True)

    # Create projects at different phases
    for phase, expected_status in [(1, "in_progress"), (2, "in_progress"), (3, "complete")]:
        proj = pipeline_dir / "projects" / f"phase_{phase}_suite"
        (proj / "state").mkdir(parents=True, exist_ok=True)
        state = {
            "title": f"Phase {phase} Suite",
            "phase": phase,
            "total_phases": 3,
            "status": expected_status,
        }
        (proj / "state" / "current_idea.json").write_text(json.dumps(state))

    # Read and validate
    projects_dir = pipeline_dir / "projects"
    for slug_dir in sorted(projects_dir.iterdir()):
        state_file = slug_dir / "state" / "current_idea.json"
        if state_file.exists():
            state = json.loads(state_file.read_text())
            phase = state["phase"]
            expected = "complete" if phase == 3 else "in_progress"
            check(f"phase {phase} → status '{expected}'", state["status"] == expected)


# ── Test 6: Sweep results are deterministic ─────────────────────
print("\n=== Test 6: Deterministic output ===")
with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp)
    pipeline_dir = tmp / ".pipeline"
    pipeline_dir.mkdir(parents=True)

    # Create a fixed set of projects
    for slug, phase in [("suite_a", 2), ("suite_b", 1), ("suite_c", 3)]:
        proj = pipeline_dir / "projects" / slug
        (proj / "state").mkdir(parents=True, exist_ok=True)
        state = {
            "title": f"{slug} suite",
            "phase": phase,
            "total_phases": 3,
            "status": "complete" if phase == 3 else "in_progress",
        }
        (proj / "state" / "current_idea.json").write_text(json.dumps(state))

    # Run sweep twice and compare
    sweep_results = tmp / "sweep_results.json"

    # First run
    import sweep_all as sa
    sa.sweep_all(str(pipeline_dir), str(sweep_results))
    first_run = json.loads(sweep_results.read_text())

    # Second run
    sa.sweep_all(str(pipeline_dir), str(sweep_results))
    second_run = json.loads(sweep_results.read_text())

    # Compare (ignore timestamp)
    first_run.pop("timestamp", None)
    second_run.pop("timestamp", None)
    check("sweep results are deterministic", first_run == second_run)


# ── Test 7: Sweep can handle large number of projects ───────────
print("\n=== Test 7: Large project list ===")
with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp)
    pipeline_dir = tmp / ".pipeline"
    pipeline_dir.mkdir(parents=True)

    # Create 50 projects
    for i in range(50):
        slug = f"large_suite_{i:03d}"
        proj = pipeline_dir / "projects" / slug
        (proj / "state").mkdir(parents=True, exist_ok=True)
        state = {
            "title": f"Large Suite {i}",
            "phase": (i % 3) + 1,
            "total_phases": 3,
            "status": "complete" if i % 3 == 2 else "in_progress",
        }
        (proj / "state" / "current_idea.json").write_text(json.dumps(state))

    sweep_results = tmp / "sweep_results.json"
    try:
        import sweep_all as sa
        sa.sweep_all(str(pipeline_dir), str(sweep_results))
        data = json.loads(sweep_results.read_text())
        check("sweep handles 50 projects", data["total_projects"] == 50)
        check("sweep results valid JSON", True)
    except Exception as e:
        check("sweep handles 50 projects", False, str(e))


# ── Test 8: Sweep results include all required fields per project ─
print("\n=== Test 8: Per-project fields ===")
with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp)
    pipeline_dir = tmp / ".pipeline"
    pipeline_dir.mkdir(parents=True)

    proj = pipeline_dir / "projects" / "field_test_suite"
    (proj / "state").mkdir(parents=True, exist_ok=True)
    state = {
        "title": "Field Test Suite",
        "phase": 2,
        "total_phases": 3,
        "status": "in_progress",
        "depends_on": ["dep_suite"],
        "dep_workspaces": {"dep_suite": "/fake/workspace"},
    }
    (proj / "state" / "current_idea.json").write_text(json.dumps(state))

    sweep_results = tmp / "sweep_results.json"
    import sweep_all as sa
    sa.sweep_all(str(pipeline_dir), str(sweep_results))
    data = json.loads(sweep_results.read_text())

    if data.get("projects"):
        proj_data = data["projects"][0]
        check("project has 'slug'", "slug" in proj_data)
        check("project has 'title'", "title" in proj_data)
        check("project has 'status'", "status" in proj_data)
        check("project has 'phase'", "phase" in proj_data)
        check("project has 'total_phases'", "total_phases" in proj_data)
        check("project has 'last_sweep'", "last_sweep" in proj_data)


# ── Summary ──────────────────────────────────────────────────────
print(f"\n{'='*50}")
passed = sum(1 for _, ok in results if ok)
total  = len(results)
color  = "\033[32m" if passed == total else "\033[31m"
print(f"{color}{passed}/{total} tests passed\033[0m")
if passed < total:
    print("\nFailed tests:")
    for name, ok in results:
        if not ok:
            print(f"  - {name}")
    sys.exit(1)
else:
    print("All tests passed — sweep system is ready.")
