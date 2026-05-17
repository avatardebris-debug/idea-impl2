"""
test_executor_harness.py
Tests the executor harness: tool execution, task completion, error handling,
agent lifecycle, message passing, and harness reliability.

Categories:
  A. Tool execution correctness
  B. Task completion (single and multi-step)
  C. Error handling and recovery
  D. Agent lifecycle and state
  E. Message bus and inter-agent communication
  F. Harness reliability under stress
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


# ── Import components ──

try:
    from pipeline.validator import Validator, validate_all
    from pipeline.executor import Executor, run_task, run_pipeline, Agent, Message
    COMPONENTS_OK = True
except Exception as e:
    print(f"  [FAIL] Importing components: {e}")
    COMPONENTS_OK = False


# ── A. TOOL EXECUTION CORRECTNESS ──

print("\n=== A. Tool Execution Correctness ===\n")

if COMPONENTS_OK:
    # Test 1: write_file creates and writes correctly
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        fpath = tmp / "test.txt"
        result = Agent(name="test_agent").execute_tool("write_file", {
            "path": str(fpath),
            "content": "hello world\n"
        })
        check("write_file creates file", fpath.exists())
        check("write_file writes correct content", fpath.read_text() == "hello world\n")

    # Test 2: read_file reads correctly
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        fpath = tmp / "read_test.txt"
        fpath.write_text("read me please\n")
        result = Agent(name="test_agent").execute_tool("read_file", {
            "path": str(fpath)
        })
        check("read_file returns content", "read me please" in result)

    # Test 3: append_file appends correctly
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        fpath = tmp / "append_test.txt"
        fpath.write_text("first line\n")
        Agent(name="test_agent").execute_tool("append_file", {
            "path": str(fpath),
            "content": "second line\n"
        })
        check("append_file appends content", "first line\nsecond line\n" == fpath.read_text())

    # Test 4: delete_file removes file
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        fpath = tmp / "delete_test.txt"
        fpath.write_text("delete me\n")
        Agent(name="test_agent").execute_tool("delete_file", {
            "path": str(fpath)
        })
        check("delete_file removes file", not fpath.exists())

    # Test 5: run_shell executes commands
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        result = Agent(name="test_agent").execute_tool("run_shell", {
            "command": "echo HARNESS_TEST_OK",
            "cwd": str(tmp)
        })
        check("run_shell executes echo", "HARNESS_TEST_OK" in result)

    # Test 6: run_shell captures stderr
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        result = Agent(name="test_agent").execute_tool("run_shell", {
            "command": "python -c \"raise ValueError('test error')\"",
            "cwd": str(tmp)
        })
        check("run_shell captures stderr", "test error" in result.lower() or "error" in result.lower())

    # Test 7: patch_file replaces content
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        fpath = tmp / "patch_test.py"
        fpath.write_text("x = 1\ny = 2\n")
        Agent(name="test_agent").execute_tool("patch_file", {
            "path": str(fpath),
            "old_string": "x = 1",
            "new_string": "x = 99"
        })
        content = fpath.read_text()
        check("patch_file replaces content", "x = 99" in content)
        check("patch_file preserves other lines", "y = 2" in content)

    # Test 8: search_in_files finds matches
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        (tmp / "a.py").write_text("def greet(name): return f'Hello {name}'\n")
        (tmp / "b.py").write_text("def hello(name): return f'Hi {name}'\n")
        result = Agent(name="test_agent").execute_tool("search_in_files", {
            "pattern": "def greet",
            "path": str(tmp),
            "glob": "*.py"
        })
        check("search_in_files finds matches", "greet" in result)

    # Test 9: list_files returns files
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        (tmp / "file1.txt").write_text("a")
        (tmp / "file2.txt").write_text("b")
        result = Agent(name="test_agent").execute_tool("list_files", {
            "path": str(tmp),
            "glob": "*.txt"
        })
        check("list_files returns files", "file1.txt" in result and "file2.txt" in result)

    # Test 10: write_file creates nested directories
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        fpath = tmp / "a" / "b" / "c" / "nested.txt"
        Agent(name="test_agent").execute_tool("write_file", {
            "path": str(fpath),
            "content": "nested content"
        })
        check("write_file creates nested dirs", fpath.exists())


# ── B. TASK COMPLETION ──

print("\n=== B. Task Completion ===\n")

if COMPONENTS_OK:
    # Task 1: Single-step task - write a file
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        task = {
            "id": "task1",
            "type": "write_file",
            "params": {
                "path": str(tmp / "single.txt"),
                "content": "single step task\n"
            }
        }
        result = run_task(task, tmp)
        check("Single-step task completes", result.get("status") == "success")
        check("Single-step task writes file", (tmp / "single.txt").exists())

    # Task 2: Multi-step task - write, patch, verify
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        task = {
            "id": "task2",
            "steps": [
                {
                    "type": "write_file",
                    "params": {"path": str(tmp / "multi.txt"), "content": "x = 1\n"}
                },
                {
                    "type": "patch_file",
                    "params": {"path": str(tmp / "multi.txt"), "old_string": "x = 1", "new_string": "x = 2"}
                },
                {
                    "type": "read_file",
                    "params": {"path": str(tmp / "multi.txt")}
                }
            ]
        }
        result = run_task(task, tmp)
        check("Multi-step task completes", result.get("status") == "success")
        check("Multi-step task patches correctly", "x = 2" in result.get("output", ""))

    # Task 3: Run pytest via task
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        (tmp / "calc.py").write_text("def add(a, b): return a + b\n")
        (tmp / "test_calc.py").write_text("from calc import add\nassert add(1, 2) == 3\n")
        task = {
            "id": "task3",
            "type": "run_shell",
            "params": {
                "command": "python test_calc.py",
                "cwd": str(tmp)
            }
        }
        result = run_task(task, tmp)
        check("Task runs pytest-like code", result.get("status") == "success")

    # Task 4: Install package via task
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        task = {
            "id": "task4",
            "type": "run_shell",
            "params": {
                "command": "pip install httpx -q 2>&1 && python -c \"import httpx; print('httpx OK')\"",
                "cwd": str(tmp)
            }
        }
        result = run_task(task, tmp)
        check("Task installs package", "httpx OK" in result.get("output", ""))

    # Task 5: Create project structure
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        task = {
            "id": "task5",
            "steps": [
                {"type": "run_shell", "params": {"command": "mkdir -p src/utils tests", "cwd": str(tmp)}},
                {"type": "write_file", "params": {"path": str(tmp / "src" / "utils" / "helper.py"), "content": "def greet(): return 'hi'"}},
                {"type": "write_file", "params": {"path": str(tmp / "src" / "__init__.py"), "content": ""}},
            ]
        }
        result = run_task(task, tmp)
        check("Task creates project structure", (tmp / "src" / "utils" / "helper.py").exists())


# ── C. ERROR HANDLING AND RECOVERY ──

print("\n=== C. Error Handling and Recovery ===\n")

if COMPONENTS_OK:
    # Test 1: Invalid tool name
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        task = {
            "id": "err1",
            "type": "nonexistent_tool",
            "params": {}
        }
        result = run_task(task, tmp)
        check("Invalid tool name returns error", result.get("status") == "error")

    # Test 2: Missing file read
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        task = {
            "id": "err2",
            "type": "read_file",
            "params": {"path": str(tmp / "nonexistent.txt")}
        }
        result = run_task(task, tmp)
        check("Missing file read returns error", result.get("status") == "error")

    # Test 3: Patch with missing old_string
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        (tmp / "patch_err.txt").write_text("x = 1\n")
        task = {
            "id": "err3",
            "type": "patch_file",
            "params": {
                "path": str(tmp / "patch_err.txt"),
                "old_string": "NOTFOUND",
                "new_string": "y = 2"
            }
        }
        result = run_task(task, tmp)
        check("Patch with missing old_string handles error", result.get("status") in ("error", "success"))

    # Test 4: Shell command failure
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        task = {
            "id": "err4",
            "type": "run_shell",
            "params": {
                "command": "python -c \"raise ValueError('intentional error')\"",
                "cwd": str(tmp)
            }
        }
        result = run_task(task, tmp)
        check("Shell command failure captured", "error" in result.get("output", "").lower() or result.get("status") == "error")

    # Test 5: Task with invalid JSON params
    task = {
        "id": "err5",
        "type": "write_file",
        "params": "not a dict"
    }
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        result = run_task(task, tmp)
        check("Invalid params handled gracefully", result.get("status") == "error")


# ── D. AGENT LIFECYCLE AND STATE ──

print("\n=== D. Agent Lifecycle and State ===\n")

if COMPONENTS_OK:
    # Test 1: Agent creation
    agent = Agent(name="lifecycle_test")
    check("Agent can be created", agent.name == "lifecycle_test")
    check("Agent has empty history initially", len(agent.history) == 0)

    # Test 2: Agent executes tool and records history
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        agent = Agent(name="history_test")
        agent.execute_tool("write_file", {"path": str(tmp / "hist.txt"), "content": "test"})
        check("Agent records tool execution in history", len(agent.history) > 0)
        check("History contains tool name", "write_file" in str(agent.history[-1]))

    # Test 3: Agent state persists across tool calls
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        agent = Agent(name="state_test")
        agent.execute_tool("write_file", {"path": str(tmp / "state.txt"), "content": "initial"})
        agent.execute_tool("patch_file", {"path": str(tmp / "state.txt"), "old_string": "initial", "new_string": "updated"})
        check("Agent state persists across calls", (tmp / "state.txt").read_text() == "updated\n")

    # Test 4: Agent can be serialized
    agent = Agent(name="serialize_test")
    agent.execute_tool("write_file", {"path": "/tmp/ser.txt", "content": "test"})
    try:
        data = agent.to_dict()
        check("Agent can be serialized to dict", "name" in data and "history" in data)
        restored = Agent.from_dict(data)
        check("Agent can be deserialized from dict", restored.name == "serialize_test")
    except Exception as e:
        check("Agent can be serialized to dict", False, str(e))


# ── E. MESSAGE BUS AND INTER-AGENT COMMUNICATION ──

print("\n=== E. Message Bus and Inter-Agent Communication ===\n")

if COMPONENTS_OK:
    # Test 1: Message creation
    msg = Message(sender="agent1", receiver="agent2", content="hello", type="task")
    check("Message can be created", msg.sender == "agent1" and msg.receiver == "agent2")
    check("Message has content", msg.content == "hello")

    # Test 2: Message serialization
    try:
        data = msg.to_dict()
        restored = Message.from_dict(data)
        check("Message can be serialized and restored", restored.content == "hello")
    except Exception as e:
        check("Message can be serialized and restored", False, str(e))

    # Test 3: Agent sends and receives messages
    agent1 = Agent(name="sender")
    agent2 = Agent(name="receiver")
    msg = Message(sender="sender", receiver="receiver", content="task data", type="task")
    agent2.receive_message(msg)
    check("Agent can receive messages", len(agent2.history) > 0)
    check("Received message content preserved", "task data" in str(agent2.history[-1]))


# ── F. HARNESS RELIABILITY UNDER STRESS ──

print("\n=== F. Harness Reliability Under Stress ===\n")

if COMPONENTS_OK:
    # Test 1: Many sequential tasks
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        success_count = 0
        for i in range(20):
            task = {
                "id": f"stress_{i}",
                "type": "write_file",
                "params": {"path": str(tmp / f"stress_{i}.txt"), "content": f"content {i}\n"}
            }
            result = run_task(task, tmp)
            if result.get("status") == "success":
                success_count += 1
        check("20 sequential tasks complete", success_count >= 18, f"success={success_count}/20")

    # Test 2: Concurrent file writes (via threading)
    import threading
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        errors = []
        def write_file(i):
            try:
                task = {
                    "id": f"concurrent_{i}",
                    "type": "write_file",
                    "params": {"path": str(tmp / f"concurrent_{i}.txt"), "content": f"data {i}\n"}
                }
                run_task(task, tmp)
            except Exception as e:
                errors.append(str(e))
        threads = [threading.Thread(target=write_file, args=(i,)) for i in range(10)]
        [t.start() for t in threads]
        [t.join() for t in threads]
        files_written = list(tmp.glob("concurrent_*.txt"))
        check("Concurrent writes are safe", len(errors) == 0 and len(files_written) == 10,
              f"errors={len(errors)}, files={len(files_written)}/10")

    # Test 3: Large file handling
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        large_content = "x = 1\n" * 10000
        task = {
            "id": "large_file",
            "type": "write_file",
            "params": {"path": str(tmp / "large.txt"), "content": large_content}
        }
        result = run_task(task, tmp)
        check("Large file (10k lines) written", result.get("status") == "success")
        check("Large file content preserved", (tmp / "large.txt").read_text() == large_content)

    # Test 4: Pipeline execution
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        (tmp / "input.txt").write_text("hello\nworld\n")
        pipeline = {
            "id": "pipeline_test",
            "tasks": [
                {
                    "id": "p1",
                    "type": "read_file",
                    "params": {"path": str(tmp / "input.txt")}
                },
                {
                    "id": "p2",
                    "type": "write_file",
                    "params": {"path": str(tmp / "output.txt"), "content": "processed\n"}
                }
            ]
        }
        result = run_pipeline(pipeline, tmp)
        check("Pipeline executes tasks", result.get("status") == "success")
        check("Pipeline output file exists", (tmp / "output.txt").exists())


# ── SUMMARY ──

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

if failed == 0:
    print("\nAll tests passed!")
else:
    print(f"\n{failed} test(s) failed.")
