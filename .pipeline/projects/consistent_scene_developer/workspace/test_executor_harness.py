"""
test_executor_harness.py
Tests the executor harness: agent initialization, tool execution, message passing,
state management, error handling, timeouts, resource limits, multi-agent,
recovery, and cleanup.
"""

import json
import os
import pathlib
import subprocess
import sys
import tempfile
import textwrap
import time

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


# ── Import the executor harness ────────────────────────────────────────────

try:
    from pipeline.executor import (
        Executor,
        Agent,
        Message,
        ToolRegistry,
        run_task,
        run_pipeline,
    )
    EXECUTOR_OK = True
except Exception as e:
    print(f"  [FAIL] Importing executor: {e}")
    EXECUTOR_OK = False


# ── A. AGENT INITIALIZATION ────────────────────────────────────────────

print("\n=== A. Agent Initialization ===\n")

if EXECUTOR_OK:
    # Test 1: Agent can be instantiated
    agent = Agent(name="test_agent", tools=[])
    check("Agent can be instantiated", agent is not None)
    check("Agent has name attribute", agent.name == "test_agent")

    # Test 2: Agent with default tools
    agent = Agent(name="default_agent")
    check("Agent with default tools can be instantiated", agent is not None)

    # Test 3: Agent with custom config
    config = {"max_turns": 5, "timeout": 30}
    agent = Agent(name="config_agent", config=config)
    check("Agent with custom config can be instantiated", agent is not None)

    # Test 4: Agent state is initialized
    agent = Agent(name="state_agent")
    check("Agent has messages list", hasattr(agent, 'messages'))
    check("Agent has turn count", hasattr(agent, 'turn_count'))

    # Test 5: Agent with system prompt
    agent = Agent(name="prompt_agent", system_prompt="You are a helpful assistant.")
    check("Agent with system prompt can be instantiated", agent is not None)


# ── B. TOOL EXECUTION ────────────────────────────────────────────

print("\n=== B. Tool Execution ===\n")

if EXECUTOR_OK:
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)

        # Test 6: write_file tool
        agent = Agent(name="tool_agent")
        result = agent.execute_tool("write_file", {"path": str(tmp / "test.txt"), "content": "hello"})
        check("write_file tool works", (tmp / "test.txt").exists())

        # Test 7: read_file tool
        content = agent.execute_tool("read_file", {"path": str(tmp / "test.txt")})
        check("read_file tool works", "hello" in content)

        # Test 8: list_tree tool
        tree = agent.execute_tool("list_tree", {"path": str(tmp)})
        check("list_tree tool works", isinstance(tree, str) and "test.txt" in tree)

        # Test 9: run_shell tool
        out = agent.execute_tool("run_shell", {"command": "echo HELLO", "cwd": str(tmp)})
        check("run_shell tool works", "HELLO" in out)

        # Test 10: search_in_files tool
        hits = agent.execute_tool("search_in_files", {"pattern": "hello", "path": str(tmp), "file_glob": "*.txt"})
        check("search_in_files tool works", "test.txt" in hits)

        # Test 11: patch_file tool
        agent.execute_tool("write_file", {"path": str(tmp / "patch.txt"), "content": "x = 1\n"})
        agent.execute_tool("patch_file", {"path": str(tmp / "patch.txt"), "old": "x = 1", "new": "x = 2"})
        content = (tmp / "patch.txt").read_text()
        check("patch_file tool works", "x = 2" in content)

        # Test 12: delete_file tool
        agent.execute_tool("write_file", {"path": str(tmp / "del.txt"), "content": "bye"})
        agent.execute_tool("delete_file", {"path": str(tmp / "del.txt")})
        check("delete_file tool works", not (tmp / "del.txt").exists())


# ── C. MESSAGE PASSING ────────────────────────────────────────────

print("\n=== C. Message Passing ===\n")

if EXECUTOR_OK:
    # Test 13: Message can be created
    msg = Message(role="user", content="Hello")
    check("Message can be created", msg.role == "user" and msg.content == "Hello")

    # Test 14: Message can be created with different roles
    msg = Message(role="assistant", content="Hi there")
    check("Message with assistant role works", msg.role == "assistant")

    # Test 15: Messages are stored in agent
    agent = Agent(name="msg_agent")
    agent.add_message(Message(role="user", content="test"))
    check("Messages are stored in agent", len(agent.messages) > 0)

    # Test 16: Message history is preserved
    agent.add_message(Message(role="assistant", content="response"))
    check("Message history preserved", len(agent.messages) == 2)


# ── D. STATE MANAGEMENT ────────────────────────────────────────────

print("\n=== D. State Management ===\n")

if EXECUTOR_OK:
    # Test 17: Agent state persists across turns
    agent = Agent(name="state_agent")
    agent.add_message(Message(role="user", content="task 1"))
    agent.turn_count += 1
    agent.add_message(Message(role="assistant", content="done 1"))
    agent.turn_count += 1
    check("State persists across turns", agent.turn_count == 2)

    # Test 18: Agent state can be serialized
    agent = Agent(name="serial_agent")
    agent.add_message(Message(role="user", content="test"))
    state = agent.to_dict()
    check("Agent state can be serialized", isinstance(state, dict))

    # Test 19: Agent state can be deserialized
    restored = Agent.from_dict(state)
    check("Agent state can be deserialized", restored.name == "serial_agent")
    check("Deserialized messages preserved", len(restored.messages) == len(agent.messages))

    # Test 20: Agent state can be saved to file
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        agent = Agent(name="file_agent")
        agent.add_message(Message(role="user", content="test"))
        filepath = str(tmp / "state.json")
        agent.save_state(filepath)
        check("Agent state saved to file", (tmp / "state.json").exists())

        restored = Agent.load_state(filepath)
        check("Agent state loaded from file", restored.name == "file_agent")


# ── E. ERROR HANDLING ────────────────────────────────────────────

print("\n=== E. Error Handling ===\n")

if EXECUTOR_OK:
    # Test 21: Invalid tool raises error
    agent = Agent(name="error_agent")
    try:
        agent.execute_tool("nonexistent_tool", {})
        check("Invalid tool raises error", False, "Should have raised")
    except (KeyError, ValueError, Exception) as e:
        check("Invalid tool raises error", True)

    # Test 22: Tool with wrong arguments raises error
    agent = Agent(name="arg_error_agent")
    try:
        agent.execute_tool("write_file", {"wrong_arg": "value"})
        check("Wrong arguments raises error", False, "Should have raised")
    except (KeyError, ValueError, Exception) as e:
        check("Wrong arguments raises error", True)

    # Test 23: Agent handles tool errors gracefully
    agent = Agent(name="graceful_agent")
    result = agent.execute_tool("run_shell", {"command": "nonexistent_command_xyz", "cwd": "/tmp"})
    check("Agent handles tool errors gracefully", result is not None)


# ── F. TIMEOUT HANDLING ────────────────────────────────────────────

print("\n=== F. Timeout Handling ===\n")

if EXECUTOR_OK:
    # Test 24: run_shell with timeout
    agent = Agent(name="timeout_agent")
    start = time.time()
    result = agent.execute_tool("run_shell", {"command": "sleep 0.1", "cwd": "/tmp", "timeout": 5})
    elapsed = time.time() - start
    check("run_shell with timeout works", elapsed < 5)

    # Test 25: Long-running command is terminated
    agent = Agent(name="long_agent")
    start = time.time()
    result = agent.execute_tool("run_shell", {"command": "sleep 10", "cwd": "/tmp", "timeout": 1})
    elapsed = time.time() - start
    check("Long command is terminated", elapsed < 5)


# ── G. RESOURCE LIMITS ────────────────────────────────────────────

print("\n=== G. Resource Limits ===\n")

if EXECUTOR_OK:
    # Test 26: Agent respects max_turns
    agent = Agent(name="limit_agent", config={"max_turns": 3})
    check("Agent has max_turns config", agent.config.get("max_turns") == 3)

    # Test 27: Agent respects timeout config
    agent = Agent(name="timeout_config_agent", config={"timeout": 60})
    check("Agent has timeout config", agent.config.get("timeout") == 60)


# ── H. MULTI-AGENT COORDINATION ───────────────────────────────────

print("\n=== H. Multi-Agent Coordination ===\n")

if EXECUTOR_OK:
    # Test 28: Multiple agents can be created
    agents = [
        Agent(name="agent1"),
        Agent(name="agent2"),
        Agent(name="agent3"),
    ]
    check("Multiple agents can be created", len(agents) == 3)

    # Test 29: Agents can communicate
    agent1 = Agent(name="sender")
    agent2 = Agent(name="receiver")
    agent1.add_message(Message(role="assistant", content="Hello agent2"))
    check("Agents can send messages", len(agent1.messages) > 0)


# ── I. RECOVERY ────────────────────────────────────────────

print("\n=== I. Recovery ===\n")

if EXECUTOR_OK:
    # Test 30: Agent can be restarted
    agent = Agent(name="restart_agent")
    agent.add_message(Message(role="user", content="task"))
    agent.turn_count = 1
    # Simulate restart by creating new agent with same state
    state = agent.to_dict()
    agent = Agent.from_dict(state)
    check("Agent can be restarted", agent.turn_count == 1)

    # Test 31: Failed agent can be recovered
    agent = Agent(name="fail_agent")
    try:
        agent.execute_tool("nonexistent_tool", {})
    except Exception:
        pass
    # Agent should still be usable
    result = agent.execute_tool("write_file", {"path": "/tmp/recovery_test.txt", "content": "recovered"})
    check("Failed agent can be recovered", (pathlib.Path("/tmp/recovery_test.txt")).exists())


# ── J. CLEANUP ────────────────────────────────────────────

print("\n=== J. Cleanup ===\n")

if EXECUTOR_OK:
    # Test 32: Executor can be instantiated
    executor = Executor()
    check("Executor can be instantiated", executor is not None)

    # Test 33: Executor can run a task
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        result = run_task(
            task="Write a file",
            prompt=f"Write 'hello' to {tmp / 'task_test.txt'}",
            output_dir=str(tmp),
            max_turns=5,
        )
        check("Executor can run a task", result is not None)
        check("Task output exists", (tmp / "task_test.txt").exists())

    # Test 34: Executor can run a pipeline
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        pipeline_results = run_pipeline(
            tasks=[
                {"task": "Create file", "prompt": f"Write 'file1' to {tmp / 'p1.txt'}"},
                {"task": "Create file", "prompt": f"Write 'file2' to {tmp / 'p2.txt'}"},
            ],
            output_dir=str(tmp),
        )
        check("Executor can run a pipeline", len(pipeline_results) == 2)
        check("Pipeline outputs exist", (tmp / "p1.txt").exists() and (tmp / "p2.txt").exists())


# ── SUMMARY ──────────────────────────────────────────────────────────────────

print(f"\n{'='*60}")
passed = sum(1 for _, ok in results if ok)
failed = sum(1 for _, ok in results if not ok)
total = len(results)
print(f"  PASS:  {passed}/{total}")
print(f"  FAIL:  {failed}/{total}")

if failed > 0:
    print(f"\nFailed tests:")
    for name, ok in results:
        if not ok:
            print(f"  - {name}")
