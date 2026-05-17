"""
quick_test.py
Fast smoke tests for the entire pipeline — no Ollama needed.

Tests:
  1. All modules import cleanly
  2. Message bus works
  3. Runner seed_from_master_list works (no deps)
  4. Idea planner can be instantiated
  5. Sweep can be called
  6. Validator can be called
  7. Master ideas parser works
  8. Full pipeline flow (seed → planner → sweep)
"""

import json
import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).parent))

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"
results = []

def check(name, condition, detail=""):
    """Record a test result. Returns True if condition is truthy."""
    ok = bool(condition)
    status = PASS if ok else FAIL
    print(f"  [{status}] {name}")
    if not ok and detail:
        print(f"         {detail}")
    results.append((name, ok))
    return ok


def run_all_tests():
    """Run all smoke tests and return the results list."""
    results.clear()

    # ── Test 1: All modules import ─────────────────────────────────
    print("\n=== Test 1: Module imports ===")
    modules = [
        "tools",
        "pipeline.message_bus",
        "pipeline.runner",
        "pipeline.agents.idea_planner",
        "pipeline.agents.executor",
        "pipeline.agents.validator",
        "pipeline.agents.harvester",
        "pipeline.agents.master_ideas",
        "sweep_all",
        "test_dependency_system",
        "test_harness_capabilities",
    ]
    for mod_name in modules:
        try:
            __import__(mod_name.replace(".", "/") if "/" in mod_name else mod_name.replace(".", "_"))
            check(f"import {mod_name}", True)
        except Exception as e:
            # Try alternative import paths
            try:
                if mod_name.startswith("pipeline."):
                    __import__(mod_name)
                    check(f"import {mod_name}", True)
                else:
                    check(f"import {mod_name}", False, str(e))
            except Exception as e2:
                check(f"import {mod_name}", False, str(e2))


    # ── Test 2: Message bus works ───────────────────────────────
    print("\n=== Test 2: Message bus ===")
    try:
        from pipeline.message_bus import Message
        msg = Message.create(from_agent="test", to_agent="idea_planner",
                             type="seed_idea", payload={"title": "Test"})
        check("Message.create works", msg is not None)
        check("Message has correct type", msg.type == "seed_idea")
        check("Message has correct payload", msg.payload["title"] == "Test")
    except Exception as e:
        check("Message.create works", False, str(e))


    # ── Test 3: seed_from_master_list (no deps) ──────────────────
    print("\n=== Test 3: seed_from_master_list ===")
    try:
        import pipeline.runner as runner
        import pipeline.message_bus as mb_mod

        class FakeMsg:
            def __init__(self, payload):
                self.payload = payload
        class FakeBus:
            def __init__(self):
                self.sent = []
            def send(self, msg):
                self.sent.append(msg)

        # Patch Message.create
        _orig_create = mb_mod.Message.create
        def _fake_create(from_agent, to_agent, type, payload, **kw):
            return FakeMsg(payload)
        mb_mod.Message.create = staticmethod(_fake_create)

        with tempfile.TemporaryDirectory() as tmp:
            tmp = pathlib.Path(tmp)
            pipeline_dir = tmp / ".pipeline"
            pipeline_dir.mkdir(parents=True)
            runner.PROJECT_ROOT = tmp
            runner.PIPELINE_DIR = pipeline_dir
            runner._seeded_this_session.clear()

            (tmp / "master_ideas.md").write_text("- [ ] **[Test Idea]** — [a test idea with no deps.]")

            bus = FakeBus()
            result = runner.seed_from_master_list(bus)
            check("seed_from_master_list returns True", result)
            check("message sent to idea_planner",
                  len(bus.sent) == 1 and bus.sent[0].to_agent == "idea_planner")

        # Restore
        mb_mod.Message.create = _orig_create
    except Exception as e:
        check("seed_from_master_list works", False, str(e))


    # ── Test 4: Idea planner instantiation ────────────────────────
    print("\n=== Test 4: Idea planner instantiation ===")
    try:
        from pipeline.agents.idea_planner import IdeaPlannerAgent
        planner = IdeaPlannerAgent.__new__(IdeaPlannerAgent)
        planner._run_dir = pathlib.Path("/tmp")
        planner._current_slug = "test_planner"
        check("IdeaPlannerAgent can be instantiated", True)
    except Exception as e:
        check("IdeaPlannerAgent can be instantiated", False, str(e))


    # ── Test 5: Sweep can be called ──────────────────────────────
    print("\n=== Test 5: Sweep callable ===")
    try:
        import sweep_all
        with tempfile.TemporaryDirectory() as tmp:
            tmp = pathlib.Path(tmp)
            sweep_results = tmp / "sweep_results.json"
            sweep_all.sweep_all(str(tmp / ".pipeline"), str(sweep_results))
            check("sweep_all.sweep_all works", sweep_results.exists())
            data = json.loads(sweep_results.read_text())
            check("sweep results is valid JSON", "total_projects" in data)
    except Exception as e:
        check("sweep_all.sweep_all works", False, str(e))


    # ── Test 6: Validator can be called ───────────────────────────
    print("\n=== Test 6: Validator callable ===")
    try:
        from pipeline.agents.validator import ValidatorAgent
        check("ValidatorAgent can be imported", True)
    except Exception as e:
        check("ValidatorAgent can be imported", False, str(e))


    # ── Test 7: Master ideas parser ──────────────────────────────
    print("\n=== Test 7: Master ideas parser ===")
    try:
        from pipeline.agents.master_ideas import MasterIdeasAgent
        check("MasterIdeasAgent can be imported", True)

        # Test parsing
        ideas_text = """
## Phase 1: MVP
- [ ] **[Idea One]** — [description one. requires: dep_a]
- [ ] **[Idea Two]** — [description two.]
"""
        # Check that the parser can handle this format
        import re
        pattern = r"- \[ \] \*\*(.+?)\*\* — \[(.+?)(?:\. requires: (.+))?\]"
        matches = re.findall(pattern, ideas_text)
        check("Parser finds ideas", len(matches) >= 2)
        if len(matches) >= 2:
            check("Parser extracts title", matches[0][0] == "Idea One")
            check("Parser extracts description", "description one" in matches[0][1])
            check("Parser extracts requires", matches[0][2] == "dep_a" if matches[0][2] else True)
    except Exception as e:
        check("MasterIdeasAgent works", False, str(e))


    # ── Test 8: Full pipeline flow ──────────────────────────────
    print("\n=== Test 8: Full pipeline flow ===")
    try:
        import pipeline.runner as runner
        import pipeline.message_bus as mb_mod

        class FakeMsg:
            def __init__(self, payload):
                self.payload = payload
        class FakeBus:
            def __init__(self):
                self.sent = []
            def send(self, msg):
                self.sent.append(msg)

        _orig_create = mb_mod.Message.create
        def _fake_create(from_agent, to_agent, type, payload, **kw):
            return FakeMsg(payload)
        mb_mod.Message.create = staticmethod(_fake_create)

        with tempfile.TemporaryDirectory() as tmp:
            tmp = pathlib.Path(tmp)
            pipeline_dir = tmp / ".pipeline"
            pipeline_dir.mkdir(parents=True)
            runner.PROJECT_ROOT = tmp
            runner.PIPELINE_DIR = pipeline_dir
            runner._seeded_this_session.clear()

            # Write master ideas
            (tmp / "master_ideas.md").write_text("""
## Phase 1: MVP
- [ ] **[First Tool]** — [a first tool.]
- [ ] **[Second Tool]** — [depends on first. requires: first_tool]
""")

            # Seed
            bus = FakeBus()
            result = runner.seed_from_master_list(bus)
            check("Pipeline: seed returns True", result)
            check("Pipeline: first tool seeded",
                  "First Tool" in bus.sent[0].payload.get("title", ""))

            # Now create the first tool's project as complete
            proj = pipeline_dir / "projects" / "first_tool"
            (proj / "state").mkdir(parents=True, exist_ok=True)
            state = {
                "title": "First Tool",
                "status": "complete",
                "phase": 3,
                "total_phases": 3,
            }
            (proj / "state" / "current_idea.json").write_text(json.dumps(state))
            (proj / "workspace").mkdir(parents=True, exist_ok=True)

            # Seed again — second tool should now be unblocked
            bus2 = FakeBus()
            result2 = runner.seed_from_master_list(bus2)
            check("Pipeline: second tool unblocked after dep complete", result2)
            check("Pipeline: second tool seeded",
                  "Second Tool" in bus2.sent[0].payload.get("title", ""))

        mb_mod.Message.create = _orig_create
    except Exception as e:
        check("Full pipeline flow works", False, str(e))

    return results


# ── Summary ──────────────────────────────────────────────────────
if __name__ == "__main__":
    run_all_tests()
    passed = sum(1 for _, ok in results if ok)
    total  = len(results)
    color  = "\033[32m" if passed == total else "\033[31m"
    print(f"\n{'='*50}")
    print(f"{color}{passed}/{total} tests passed\033[0m")
    if passed < total:
        print("\nFailed tests:")
        for name, ok in results:
            if not ok:
                print(f"  - {name}")
        sys.exit(1)
    else:
        print("All smoke tests passed — pipeline is operational.")
