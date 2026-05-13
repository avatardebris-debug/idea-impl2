"""
test_integration.py
End-to-end integration tests for the full pipeline:
  Validator -> Executor -> Agent -> CLI

Tests the complete workflow:
  1. Input validation
  2. Task execution
  3. Agent lifecycle
  4. CLI interface
  5. Error propagation through the pipeline
"""

import json
import os
import pathlib
import subprocess
import sys
import tempfile
import textwrap

sys.path.insert(0, str(pathlib.Path(__file__).parent))

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"
results = []

def check(name, condition, detail=""):
    ok = bool(condition)
    tag = PASS if ok else FAIL
    print(f"  [{tag}] {name}")
    if not ok and detail:
        print(f"         {detail}")
    results.append((name, ok))
    return ok


# ============================================================================
# IMPORT COMPONENTS
# ============================================================================
print("\n=== Importing Components ===\n")

try:
    from pipeline.validator import Validator, validate_all
    from pipeline.executor import Executor, run_task, run_pipeline, Agent, Message
    from pipeline.runner import main as cli_main, build_parser
    COMPONENTS_OK = True
except Exception as e:
    print(f"  [FAIL] Importing components: {e}")
    COMPONENTS_OK = False


# ============================================================================
# A. VALIDATOR INTEGRATION
# ============================================================================
print("\n=== A. Validator Integration ===\n")

if COMPONENTS_OK:
    # A1. Validate correct task
    task = {
        "id": "valid_task",
        "type": "write_file",
        "params": {"path": "/tmp/test.txt", "content": "hello"}
    }
    errors = Validator.validate_task(task)
    check("Validator accepts valid task", len(errors) == 0)

    # A2. Reject invalid task (missing type)
    bad_task = {"id": "bad", "params": {}}
    errors = Validator.validate_task(bad_task)
    check("Validator rejects invalid task", len(errors) > 0)

    # A3. Validate pipeline
    pipeline = {
        "id": "valid_pipeline",
        "tasks": [
            {"id": "t1", "type": "write_file", "params": {"path": "/tmp/t1.txt", "content": "a"}},
            {"id": "t2", "type": "read_file", "params": {"path": "/tmp/t1.txt"}}
        ]
    }
    errors = Validator.validate_pipeline(pipeline)
    check("Validator accepts valid pipeline", len(errors) == 0)

    # A4. Reject pipeline with invalid task
    bad_pipeline = {
        "id": "bad_pipeline",
        "tasks": [{"id": "t1", "type": "nonexistent_tool", "params": {}}]
    }
    errors = Validator.validate_pipeline(bad_pipeline)
    check("Validator rejects invalid pipeline", len(errors) > 0)


# ============================================================================
# B. EXECUTOR INTEGRATION
# ============================================================================
print("\n=== B. Executor Integration ===\n")

if COMPONENTS_OK:
    # B1. Execute a simple task
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        task = {
            "id": "b1",
            "type": "write_file",
            "params": {"path": str(tmp / "b1.txt"), "content": "executor test\n"}
        }
        result = run_task(task, tmp)
        check("Executor runs task", result.get("status") == "success")
        check("Executor writes file", (tmp / "b1.txt").exists())

    # B2. Execute a pipeline
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        pipeline = {
            "id": "b2",
            "tasks": [
                {"id": "t1", "type": "write_file", "params": {"path": str(tmp / "b2.txt"), "content": "pipeline\n"}},
                {"id": "t2", "type": "read_file", "params": {"path": str(tmp / "b2.txt")}}
            ]
        }
        result = run_pipeline(pipeline, tmp)
        check("Executor runs pipeline", result.get("status") == "success")

    # B3. Handle task failure in pipeline
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        pipeline = {
            "id": "b3",
            "tasks": [
                {"id": "t1", "type": "write_file", "params": {"path": str(tmp / "b3.txt"), "content": "ok\n"}},
                {"id": "t2", "type": "nonexistent_tool", "params": {}}
            ]
        }
        result = run_pipeline(pipeline, tmp)
        check("Executor handles pipeline failure", result.get("status") == "error")


# ============================================================================
# C. AGENT INTEGRATION
# ============================================================================
print("\n=== C. Agent Integration ===\n")

if COMPONENTS_OK:
    # C1. Agent executes multi-step task
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        agent = Agent(name="integration_agent")
        
        # Step 1: Create a Python module
        agent.execute_tool("write_file", {
            "path": str(tmp / "module.py"),
            "content": "def add(a, b):\n    return a + b\n"
        })
        
        # Step 2: Create a test
        agent.execute_tool("write_file", {
            "path": str(tmp / "test_module.py"),
            "content": "from module import add\nassert add(1, 2) == 3\nprint('PASS')\n"
        })
        
        # Step 3: Run the test
        result = agent.execute_tool("run_shell", {"command": "python test_module.py", "cwd": str(tmp)})
        
        check("Agent multi-step task", "PASS" in result)

    # C2. Agent handles errors gracefully
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        agent = Agent(name="error_agent")
        result = agent.execute_tool("read_file", {"path": str(tmp / "nonexistent.txt")})
        check("Agent handles read error", "error" in str(result).lower() or "not found" in str(result).lower())

    # C3. Agent message passing
    agent1 = Agent(name="sender")
    agent2 = Agent(name="receiver")
    msg = Message(sender="sender", receiver="receiver", content="task_data", type="task")
    agent2.receive_message(msg)
    check("Agent message passing", len(agent2.history) > 0)


# ============================================================================
# D. CLI INTEGRATION
# ============================================================================
print("\n=== D. CLI Integration ===\n")

if COMPONENTS_OK:
    # D1. CLI with valid input
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        input_file = tmp / "input.json"
        input_file.write_text(json.dumps({
            "id": "cli_test",
            "tasks": [
                {"id": "t1", "type": "write_file", "params": {"path": str(tmp / "output.txt"), "content": "cli output\n"}}
            ]
        }))
        output_file = tmp / "output.json"
        result = cli_main(["-i", str(input_file), "-o", str(output_file)])
        check("CLI runs successfully", result == 0)
        check("CLI writes output", output_file.exists())

    # D2. CLI with invalid input
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        input_file = tmp / "invalid.json"
        input_file.write_text("not valid json")
        output_file = tmp / "output.json"
        result = cli_main(["-i", str(input_file), "-o", str(output_file)])
        check("CLI handles invalid input", result != 0)

    # D3. CLI with missing input file
    result = cli_main(["-i", "/nonexistent/file.json", "-o", "/tmp/out.json"])
    check("CLI handles missing input", result != 0)

    # D4. CLI with --help
    result = cli_main(["--help"])
    check("CLI --help works", result == 0)


# ============================================================================
# E. END-TO-END WORKFLOW
# ============================================================================
print("\n=== E. End-to-End Workflow ===\n")

if COMPONENTS_OK:
    # E1. Complete workflow: create project, write code, test
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        
        # Create input
        input_file = tmp / "e2e_input.json"
        input_file.write_text(json.dumps({
            "id": "e2e_test",
            "tasks": [
                {
                    "id": "create_project",
                    "type": "create_project",
                    "params": {
                        "path": str(tmp / "myproject"),
                        "name": "myproject",
                        "files": ["src/__init__.py", "src/app.py", "tests/test_app.py"]
                    }
                },
                {
                    "id": "write_app",
                    "type": "write_file",
                    "params": {
                        "path": str(tmp / "myproject" / "src" / "app.py"),
                        "content": "def greet(name):\n    return f'Hello {name}'\n"
                    }
                },
                {
                    "id": "write_test",
                    "type": "write_file",
                    "params": {
                        "path": str(tmp / "myproject" / "tests" / "test_app.py"),
                        "content": "from src.app import greet\nassert greet('World') == 'Hello World'\nprint('E2E TEST PASSED')\n"
                    }
                },
                {
                    "id": "run_test",
                    "type": "run_shell",
                    "params": {
                        "command": "python -m pytest tests/test_app.py -v",
                        "cwd": str(tmp / "myproject")
                    }
                }
            ]
        }))
        
        output_file = tmp / "e2e_output.json"
        result = cli_main(["-i", str(input_file), "-o", str(output_file)])
        
        check("E2E: CLI runs", result == 0)
        check("E2E: Output written", output_file.exists())
        
        # Verify the project was created
        check("E2E: Project created", (tmp / "myproject" / "src" / "app.py").exists())
        check("E2E: Test file created", (tmp / "myproject" / "tests" / "test_app.py").exists())


# ============================================================================
# SUMMARY
# ============================================================================
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
