"""
test_priority_eviction_unit.py
Comprehensive unit and integration testing of the Tier 5B Priority Eviction system.
Runs entirely with mock agents, mock queues, and disk states, requiring no external LLM.
"""

import json
import pathlib
import sys
import tempfile
import textwrap
import traceback

sys.path.insert(0, str(pathlib.Path(__file__).parent))

# Script-style suite: when collected by pytest, skip module-level execution.
# Run directly: python test_priority_eviction_unit.py
if __name__ != "__main__":
    import pytest

    pytest.skip(
        "Script-style suite — run: python test_priority_eviction_unit.py",
        allow_module_level=True,
    )

# ---------------------------------------------------------------------------
# Setup Mocks & Stubs
# ---------------------------------------------------------------------------

class FakeMsg:
    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)
        if not hasattr(self, "payload"):
            self.payload = {}
        if not hasattr(self, "msg_id"):
            self.msg_id = "fake_msg_id"

class FakeBus:
    def __init__(self):
        self.sent = []
        self.nacked = []
    def send(self, msg):
        self.sent.append(msg)
    def nack(self, msg, increment_retry=True):
        self.nacked.append((msg, increment_retry))
    def has_active_work(self) -> bool:
        return False

# Patch Message.create so seed_idea can call it
import pipeline.message_bus as mb_mod
_orig_create = mb_mod.Message.create
def _fake_create(from_agent, to_agent, type, payload, **kw):
    m = FakeMsg(from_agent=from_agent, to_agent=to_agent, type=type, payload=payload)
    return m
mb_mod.Message.create = staticmethod(_fake_create)

import pipeline.runner as runner
import agent as agent_mod
import pipeline.agents.executor as exec_mod
import pipeline.agents.idea_planner as ip_mod

# ---------------------------------------------------------------------------
# Test Harness
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

def create_mock_project(pipeline_dir, slug, status="phase_1_executing", priority=0, evict_requested=False, extra=None):
    proj_dir = pipeline_dir / "projects" / slug
    proj_dir.mkdir(parents=True, exist_ok=True)
    state_dir = proj_dir / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    ws_dir = proj_dir / "workspace"
    ws_dir.mkdir(parents=True, exist_ok=True)
    
    state = {
        "title": slug.replace("_", " ").title(),
        "status": status,
        "priority_tier": priority,
        "evict_requested": evict_requested,
    }
    if extra:
        state.update(extra)
        
    (state_dir / "current_idea.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
    return proj_dir

# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------

print("\n=== Priority Eviction Unit Tests ===\n")

# -- Test 1: Priority Parsing from master_ideas.md --
print("Test 1: Parsing priority_tier from master_ideas.md")
with tempfile.TemporaryDirectory() as tmp:
    tmp_path = pathlib.Path(tmp)
    pipeline_dir = tmp_path / ".pipeline"
    pipeline_dir.mkdir(parents=True)
    
    # Patch runner globals
    runner.PROJECT_ROOT = tmp_path
    runner.PIPELINE_DIR = pipeline_dir
    runner._seeded_this_session.clear()
    
    ideas_text = """
    - [ ] **[Low Pri Project]** — [description. priority: 2]
    """
    (tmp_path / "master_ideas.md").write_text(textwrap.dedent(ideas_text), encoding="utf-8")
    
    bus = FakeBus()
    status = runner.seed_from_master_list(bus)
    
    check("seeding returns 'seeded'", status == "seeded")
    check("one message sent", len(bus.sent) == 1)
    payload = bus.sent[0].payload if bus.sent else {}
    check("priority_tier matches parsed value", payload.get("priority_tier") == 2)
    check("description cleaned of priority suffix", "priority:" not in payload.get("idea", ""))

# -- Test 2: Saving Priority in current_idea.json via IdeaPlannerAgent --
print("\nTest 2: Saving priority_tier in current_idea.json via IdeaPlannerAgent")
with tempfile.TemporaryDirectory() as tmp:
    tmp_path = pathlib.Path(tmp)
    proj_dir = tmp_path / ".pipeline" / "projects" / "test_idea"
    proj_dir.mkdir(parents=True)
    
    class MockIdeaPlanner(ip_mod.IdeaPlannerAgent):
        def __init__(self, bus_obj, run_dir, slug):
            self.bus = bus_obj
            self.role = "idea_planner"
            self._run_dir = run_dir
            self._current_slug = slug
        def call_agent(self, task, **kw):
            class R:
                completed = True
                answer = "## Phase 1: Dev\n- Task 1"
                tokens_used = 100
                steps_used = 1
            return R()
            
    planner = MockIdeaPlanner(FakeBus(), tmp_path, "test_idea")
    msg = FakeMsg(
        payload={
            "idea_slug": "test_idea",
            "idea": "A test project description",
            "title": "Test Idea",
            "priority_tier": 5
        }
    )
    planner.handle(msg)
    
    state_file = proj_dir / "state" / "current_idea.json"
    check("current_idea.json exists", state_file.exists())
    if state_file.exists():
        state = json.loads(state_file.read_text(encoding="utf-8"))
        check("priority_tier saved in current_idea.json", state.get("priority_tier") == 5)

# -- Test 3: check_preemption(slug) Raises InterruptedError --
print("\nTest 3: check_preemption(slug) raises InterruptedError when evict_requested=True")
with tempfile.TemporaryDirectory() as tmp:
    tmp_path = pathlib.Path(tmp)
    # Patch agent's relative workspace lookup to use temp folder
    # check_preemption uses Path(".pipeline") / "projects" / slug / "state" / "current_idea.json"
    # So we change working directory temporarily to test it.
    import os
    old_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        pipeline_dir = tmp_path / ".pipeline"
        create_mock_project(pipeline_dir, "my_project", status="phase_1_executing", priority=1, evict_requested=True)
        
        raised = False
        try:
            agent_mod.check_preemption("my_project")
        except InterruptedError as e:
            raised = True
            check("correct error message", str(e) == "PreemptionInterrupt")
            
        check("check_preemption raised InterruptedError", raised)
    finally:
        os.chdir(old_cwd)

# -- Test 4: Eviction Controller Selection Logic --
print("\nTest 4: Eviction Controller selects lowest priority and requests eviction")
with tempfile.TemporaryDirectory() as tmp:
    tmp_path = pathlib.Path(tmp)
    pipeline_dir = tmp_path / ".pipeline"
    pipeline_dir.mkdir(parents=True)
    
    # Patch runner globals
    runner.PROJECT_ROOT = tmp_path
    runner.PIPELINE_DIR = pipeline_dir
    runner._seeded_this_session.clear()
    
    # Create 2 running projects: project_low (priority 1), project_mid (priority 3)
    create_mock_project(pipeline_dir, "project_low", status="phase_1_executing", priority=1)
    create_mock_project(pipeline_dir, "project_mid", status="phase_2_executing", priority=3)
    
    # Create a higher priority unseeded project in master_ideas.md: project_high (priority 5)
    ideas_text = """
    - [ ] **[Project High]** — [high priority. priority: 5]
    """
    (tmp_path / "master_ideas.md").write_text(textwrap.dedent(ideas_text), encoding="utf-8")
    
    bus = FakeBus()
    # If parallel_seeds = 2, active projects = 2 (full), then high-priority project (5) ready
    # should evict project_low (priority 1).
    runner._check_priority_eviction(bus, parallel_seeds=2)
    
    # Verify project_low got evict_requested=True
    low_state_file = pipeline_dir / "projects" / "project_low" / "state" / "current_idea.json"
    low_state = json.loads(low_state_file.read_text(encoding="utf-8"))
    check("low priority project flagged for preemption", low_state.get("evict_requested") is True)
    
    # Verify project_mid did not get flagged
    mid_state_file = pipeline_dir / "projects" / "project_mid" / "state" / "current_idea.json"
    mid_state = json.loads(mid_state_file.read_text(encoding="utf-8"))
    check("mid priority project NOT flagged for preemption", mid_state.get("evict_requested") is False)

# -- Test 5: Executor Interruption Checkpoint & Discrepancy Scanning --
print("\nTest 5: Executor Agent checkpointing and discrepancy scanning")
with tempfile.TemporaryDirectory() as tmp:
    tmp_path = pathlib.Path(tmp)
    proj_dir = tmp_path / ".pipeline" / "projects" / "test_exec"
    proj_dir.mkdir(parents=True)
    
    class MockExecutor(exec_mod.ExecutorAgent):
        def __init__(self, bus_obj, run_dir, slug):
            self.bus = bus_obj
            self.role = "executor"
            self._run_dir = run_dir
            self._current_slug = slug
            
    exec_agent = MockExecutor(FakeBus(), tmp_path, "test_exec")
    
    # Create files in workspace
    ws_dir = proj_dir / "workspace"
    ws_dir.mkdir(parents=True)
    file_a = ws_dir / "file_a.py"
    file_a.write_text("print('hello')", encoding="utf-8")
    file_b = ws_dir / "file_b.txt"
    file_b.write_text("content b", encoding="utf-8")
    
    # Create current_idea.json
    state_dir = proj_dir / "state"
    state_dir.mkdir(parents=True)
    current_idea = {"status": "phase_2_executing", "priority_tier": 4, "evict_requested": True}
    (state_dir / "current_idea.json").write_text(json.dumps(current_idea), encoding="utf-8")
    
    # Trigger preemption save
    exec_agent._save_interrupt_checkpoint()
    
    # 1. Verify current_idea.json updated
    state_after = json.loads((state_dir / "current_idea.json").read_text(encoding="utf-8"))
    check("status set to 'evicted'", state_after.get("status") == "evicted")
    check("pre_evict_status captured", state_after.get("pre_evict_status") == "phase_2_executing")
    check("evict_requested cleared", state_after.get("evict_requested") is False)
    
    # 2. Verify file_changes.json saved
    manifest_file = state_dir / "file_changes.json"
    check("file_changes.json exists", manifest_file.exists())
    if manifest_file.exists():
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        check("file_a.py captured in manifest", "file_a.py" in manifest)
        check("file_b.txt captured in manifest", "file_b.txt" in manifest)
        
    # 3. Simulate external modifications to workspace:
    # - Modify file_a.py
    file_a.write_text("print('hello modified')", encoding="utf-8")
    # - Delete file_b.txt
    file_b.unlink()
    # - Add file_c.py
    file_c = ws_dir / "file_c.py"
    file_c.write_text("print('new')", encoding="utf-8")
    
    # Trigger discrepancy check
    warning_prompt = exec_agent._check_discrepancy_and_build_warning()
    print("      Generated warning prompt:\n" + textwrap.indent(warning_prompt, "      "))
    
    check("warning prompt contains ADDED", "file_c.py" in warning_prompt)
    check("warning prompt contains MODIFIED", "file_a.py" in warning_prompt)
    check("warning prompt contains DELETED", "file_b.txt" in warning_prompt)
    check("manifest file deleted after check", not manifest_file.exists())

# -- Test 6: Rebuilding queues restores evicted status --
print("\nTest 6: Rebuilding queues restores evicted project status")
with tempfile.TemporaryDirectory() as tmp:
    tmp_path = pathlib.Path(tmp)
    pipeline_dir = tmp_path / ".pipeline"
    pipeline_dir.mkdir(parents=True)
    
    runner.PROJECT_ROOT = tmp_path
    runner.PIPELINE_DIR = pipeline_dir
    
    # Create an evicted project
    proj_dir = create_mock_project(
        pipeline_dir, 
        "evicted_project", 
        status="evicted", 
        priority=3, 
        extra={"pre_evict_status": "phase_2_executing", "evict_requested": True}
    )
    # Create dummy tasks.md so it doesn't get re-routed to planning
    tasks_file = proj_dir / "phases" / "phase_2" / "tasks.md"
    tasks_file.parent.mkdir(parents=True, exist_ok=True)
    tasks_file.write_text("- [ ] Task 1", encoding="utf-8")
    
    bus = FakeBus()
    # Rebuild queue
    runner._rebuild_queues_from_state(bus, ideas_path=None)
    
    # Check that current_idea.json status is restored and evict_requested is false
    state_file = pipeline_dir / "projects" / "evicted_project" / "state" / "current_idea.json"
    state = json.loads(state_file.read_text(encoding="utf-8"))
    check("status restored to phase_2_executing", state.get("status") == "phase_2_executing")
    check("evict_requested cleared", state.get("evict_requested") is False)

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print("\n==================================================")
success_count = sum(1 for _, ok in results if ok)
total_count = len(results)
print(f"{success_count}/{total_count} tests passed")
if success_count == total_count:
    print("All tests passed! Priority Eviction system is completely correct!")
    sys.exit(0)
else:
    print("Some tests failed!")
    sys.exit(1)
