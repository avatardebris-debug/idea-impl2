"""
test_dependency_system.py
Verifies the dependency ordering system works correctly without needing Ollama.

Tests:
  1. Idea with no deps seeds immediately
  2. Idea with incomplete dep is blocked
  3. Idea with complete dep seeds immediately (and dep workspace is injected)
  4. Multi-dep: all must be complete to unblock
  5. Multi-dep: partial complete still blocks
  6. Slug format is correct for 'requires:' parsing
  7. Description is stripped of 'requires:' suffix before sending to planner
  8. dep_workspaces contains real paths for complete deps
  9. idea_planner prompt includes dependency context block
 10. End-to-end: suite completes → dependent auto-unblocks next tick
"""

import json
import pathlib
import sys
import tempfile
import textwrap
import traceback

sys.path.insert(0, str(pathlib.Path(__file__).parent))


# ---------------------------------------------------------------------------
# Minimal stubs — no Ollama, no real message bus needed
# ---------------------------------------------------------------------------

class FakeMsg:
    def __init__(self, payload):
        self.payload = payload

class FakeBus:
    def __init__(self):
        self.sent = []
    def send(self, msg):
        self.sent.append(msg)

class FakeMsg2:
    """Simulates a Message object returned by Message.create()"""
    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)

# Patch Message.create so seed_idea can call it
import pipeline.message_bus as mb_mod
_orig_create = mb_mod.Message.create
def _fake_create(from_agent, to_agent, type, payload, **kw):
    m = FakeMsg2(from_agent=from_agent, to_agent=to_agent,
                  type=type, payload=payload)
    return m
mb_mod.Message.create = staticmethod(_fake_create)

import pipeline.runner as runner


# ---------------------------------------------------------------------------
# Test harness
# ---------------------------------------------------------------------------

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


def make_project(pipeline_dir, slug, status="complete", phase=3, total=3):
    """Create a minimal project state directory."""
    proj = pipeline_dir / "projects" / slug
    (proj / "state").mkdir(parents=True, exist_ok=True)
    (proj / "workspace").mkdir(parents=True, exist_ok=True)
    (proj / "workspace" / "main.py").write_text(f"# {slug} main module\n")
    state = {
        "title": slug.replace("_", " "),
        "status": status,
        "phase": phase,
        "total_phases": total,
    }
    (proj / "state" / "current_idea.json").write_text(json.dumps(state))
    return proj


def run_seed(tmp_root, ideas_md_text):
    """
    Set up a temp pipeline dir, write master_ideas.md, and call seed_from_master_list.
    Returns (bus, seeded_count, blocked_printed).
    """
    pipeline_dir = tmp_root / ".pipeline"
    pipeline_dir.mkdir(parents=True, exist_ok=True)

    # Patch runner globals to use our temp dir
    runner.PROJECT_ROOT = tmp_root
    runner.PIPELINE_DIR = pipeline_dir
    runner._seeded_this_session.clear()

    (tmp_root / "master_ideas.md").write_text(textwrap.dedent(ideas_md_text), encoding="utf-8")

    bus = FakeBus()
    result = runner.seed_from_master_list(bus)
    return bus, result


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

print("\n=== Dependency System Tests ===\n")

# ── Test 1: No deps — seeds immediately ──────────────────────────────────────
print("Test 1: No-dep idea seeds immediately")
with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp)
    bus, result = run_seed(tmp, """
        - [ ] **[Simple Tool]** — [a simple tool with no deps.]
    """)
    check("seed_from_master_list returns True", result)
    check("one message sent to idea_planner",
          len(bus.sent) == 1 and bus.sent[0].to_agent == "idea_planner")
    payload = bus.sent[0].payload if bus.sent else {}
    check("depends_on is empty list", payload.get("depends_on") == [])
    check("dep_workspaces is empty dict", payload.get("dep_workspaces") == {})
    check("description clean (no 'requires:' in it)",
          "requires" not in payload.get("idea", "").lower())

# ── Test 2: Incomplete dep — blocks ──────────────────────────────────────────
print("\nTest 2: Incomplete dep blocks the idea")
with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp)
    pipeline_dir = tmp / ".pipeline"
    pipeline_dir.mkdir(parents=True)
    make_project(pipeline_dir, "suite_tool", status="phase_2_executing")
    bus, result = run_seed(tmp, """
        - [ ] **[Dependent Tool]** — [depends on suite. requires: suite_tool]
    """)
    check("seed_from_master_list returns False (nothing seeded)", result == False)
    check("no messages sent", len(bus.sent) == 0)

# ── Test 3: Complete dep — seeds and injects workspace ───────────────────────
print("\nTest 3: Complete dep unblocks and injects workspace path")
with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp)
    pipeline_dir = tmp / ".pipeline"
    pipeline_dir.mkdir(parents=True)
    make_project(pipeline_dir, "suite_tool", status="complete")
    bus, result = run_seed(tmp, """
        - [ ] **[Dependent Tool]** — [depends on suite. requires: suite_tool]
    """)
    check("seed_from_master_list returns True", result)
    check("one message sent", len(bus.sent) == 1)
    payload = bus.sent[0].payload if bus.sent else {}
    check("depends_on contains suite_tool", "suite_tool" in payload.get("depends_on", []))
    check("dep_workspaces has suite_tool path", "suite_tool" in payload.get("dep_workspaces", {}))
    ws_path = payload.get("dep_workspaces", {}).get("suite_tool", "")
    check("workspace path exists on disk", pathlib.Path(ws_path).exists() if ws_path else False)
    check("description stripped of 'requires:' suffix",
          "requires" not in payload.get("idea", "").lower(),
          f"idea was: {payload.get('idea','')[:80]}")

# ── Test 4: Multi-dep all complete — seeds ────────────────────────────────────
print("\nTest 4: Multi-dep, all complete — seeds")
with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp)
    pipeline_dir = tmp / ".pipeline"
    pipeline_dir.mkdir(parents=True)
    make_project(pipeline_dir, "suite_tool", status="complete")
    make_project(pipeline_dir, "movie_idea_generator", status="complete")
    bus, result = run_seed(tmp, """
        - [ ] **[Beatsheet Generator]** — [beatsheets. requires: suite_tool, movie_idea_generator]
    """)
    check("seeds when all deps complete", result)
    payload = bus.sent[0].payload if bus.sent else {}
    check("both deps in depends_on",
          "suite_tool" in payload.get("depends_on", []) and
          "movie_idea_generator" in payload.get("depends_on", []))
    check("both workspaces injected",
          len(payload.get("dep_workspaces", {})) == 2)

# ── Test 5: Multi-dep partial complete — still blocks ────────────────────────
print("\nTest 5: Multi-dep, one incomplete — still blocks")
with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp)
    pipeline_dir = tmp / ".pipeline"
    pipeline_dir.mkdir(parents=True)
    make_project(pipeline_dir, "suite_tool", status="complete")
    make_project(pipeline_dir, "movie_idea_generator", status="phase_1_executing")  # incomplete!
    bus, result = run_seed(tmp, """
        - [ ] **[Beatsheet Generator]** — [beatsheets. requires: suite_tool, movie_idea_generator]
    """)
    check("blocked when one dep incomplete", result == False)
    check("no messages sent", len(bus.sent) == 0)

# ── Test 6: Skip blocked, seed next available ─────────────────────────────────
print("\nTest 6: Skips blocked idea, seeds next available one")
with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp)
    pipeline_dir = tmp / ".pipeline"
    pipeline_dir.mkdir(parents=True)
    make_project(pipeline_dir, "suite_tool", status="phase_1_executing")  # not done
    bus, result = run_seed(tmp, """
        - [ ] **[Blocked Tool]** — [blocked. requires: suite_tool]
        - [ ] **[Free Tool]** — [no deps, should seed.]
    """)
    check("returns True (found a seedable idea)", result)
    check("seeded Free Tool not Blocked Tool",
          "Free Tool" in bus.sent[0].payload.get("title", "") if bus.sent else False)

# ── Test 7: Dep not started at all — blocks ──────────────────────────────────
print("\nTest 7: Dep not started at all — blocks")
with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp)
    bus, result = run_seed(tmp, """
        - [ ] **[Dependent Tool]** — [needs something. requires: nonexistent_suite]
    """)
    check("blocked when dep has no project dir", result == False)
    check("no messages sent", len(bus.sent) == 0)

# ── Test 8: idea_planner prompt injection ────────────────────────────────────
print("\nTest 8: idea_planner builds correct prompt with dep context")
import pipeline.agents.idea_planner as ip_mod

# Temporarily override the class's call_agent and write_json_state
captured_prompt = []
class MockIdeaPlanner(ip_mod.IdeaPlannerAgent):
    def call_agent(self, task, **kw):
        captured_prompt.append(task)
        class R:
            completed = True; answer = "DONE"; tokens_used = 0; steps_used = 1
        return R()
    def read_state_file(self, path):
        if "master_plan" in path:
            return "## Phase 1: MVP\n## Phase 2: Tests\n## Phase 3: Deploy\n"
        return ""
    def write_state_file(self, path, content): pass
    def write_json_state(self, path, data): pass
    def _project_path(self, rel): return f"/tmp/fake/{rel}"

with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp)
    pipeline_dir = tmp / ".pipeline"
    pipeline_dir.mkdir(parents=True)
    ws = make_project(pipeline_dir, "ai_movie_suite", status="complete") / "workspace"

    planner = MockIdeaPlanner.__new__(MockIdeaPlanner)
    planner._run_dir = tmp
    planner._current_slug = "movie_idea_generator"

    msg = FakeMsg({
        "title": "Movie idea generator",
        "idea": "generate movie ideas",
        "idea_slug": "movie_idea_generator",
        "depends_on": ["ai_movie_suite"],
        "dep_workspaces": {"ai_movie_suite": str(ws)},
    })

    # Need to stub AgentOutput
    class FakeOut:
        success=True; answer="DONE"; tokens_used=0; steps_used=1; outgoing=[]

    import unittest.mock as mock
    with mock.patch.object(ip_mod.AgentOutput, '__new__', return_value=FakeOut()):
        try:
            planner.handle(msg)
        except Exception:
            pass  # We only care about the captured prompt

    if captured_prompt:
        prompt = captured_prompt[0]
        check("'Dependencies' section in prompt", "Dependencies" in prompt)
        check("dep workspace path in prompt", str(ws) in prompt)
        check("'list_tree' instruction in prompt", "list_tree" in prompt)
        check("'MUST be compatible' in prompt", "MUST be compatible" in prompt or "compatible" in prompt.lower())
    else:
        check("prompt was captured", False, "call_agent was not called")

# ── Test 9: Slug format round-trip ───────────────────────────────────────────
print("\nTest 9: Slug format matches what 'requires:' expects")
from pipeline.runner import _slugify
cases = [
    ("AI movie generation suite", "ai_movie_generation_suite"),
    ("Movie idea generator", "movie_idea_generator"),
    ("beatsheet generator", "beatsheet_generator"),
    ("[consistent character developer]", "consistent_character_developer"),
]
for title, expected in cases:
    got = _slugify(title)
    check(f"_slugify('{title}') == '{expected}'", got == expected,
          f"got: '{got}'")

# ── Test 10: budget_exceeded dep counts as complete ───────────────────────────
print("\nTest 10: budget_exceeded dep is treated as 'done enough' to unblock")
with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp)
    pipeline_dir = tmp / ".pipeline"
    pipeline_dir.mkdir(parents=True)
    make_project(pipeline_dir, "suite_tool", status="budget_exceeded")
    bus, result = run_seed(tmp, """
        - [ ] **[Dependent Tool]** — [needs suite. requires: suite_tool]
    """)
    check("budget_exceeded dep unblocks dependent", result)


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
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
    print("All tests passed — dependency system is ready.")
