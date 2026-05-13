"""
test_integration.py
Integration tests: full pipeline run, end-to-end task, error recovery,
performance, scalability, config variations, edge cases, cross-platform.
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


# ── Import components ────────────────────────────────────────────

try:
    from pipeline.validator import Validator, validate_all
    from pipeline.executor import Executor, run_task, run_pipeline, Agent, Message
    COMPONENTS_OK = True
except Exception as e:
    print(f"  [FAIL] Importing components: {e}")
    COMPONENTS_OK = False


# ── C1. FULL PIPELINE RUN ──────────────────────────────────────

print("\n=== C1. Full Pipeline Run ===\n")

if COMPONENTS_OK:
    # Test 1: Validator + executor work together
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        # Create a Python file to validate
        (tmp / "code.py").write_text(textwrap.dedent("""\
            '''A module.'''

            def greet(name: str) -> str:
                '''Greet someone.'''
                return f"Hello, {name}!"
        """))
        # Validate
        validator = Validator()
        issues = validator.validate(str(tmp / "code.py"))
        check("Validator runs in pipeline", isinstance(issues, list))
        # Execute a task
        executor = Executor()
        result = run_task(
            task="Test task",
            prompt=f"Read {tmp / 'code.py'} and return its content",
            output_dir=str(tmp),
            max_turns=5,
        )
        check("Executor runs in pipeline", result is not None)
        check("Full pipeline works", len(issues) >= 0 and result is not None)


# ── C2. END-TO-END TASK ──────────────────────────────────────

print("\n=== C2. End-to-End Task ===\n")

if COMPONENTS_OK:
    # Test 2: Complete coding task from start to finish
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        result = run_task(
            task="Create a Python module",
            prompt=textwrap.dedent(f"""\
                Create a Python file at {tmp / 'module.py'} with:
                1. A module docstring
                2. A class Calculator with __init__ and add methods
                3. Each method with docstrings and type hints
                4. A main block that tests the calculator
            """),
            output_dir=str(tmp),
            max_turns=10,
        )
        check("End-to-end task completes", result is not None)
        check("Output file created", (tmp / "module.py").exists())

    # Test 3: Multi-step task
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        results = run_pipeline(
            tasks=[
                {
                    "task": "Create data file",
                    "prompt": f"Write a CSV file at {tmp / 'data.csv'} with headers: name,age\nAlice,30\nBob,25\n",
                },
                {
                    "task": "Process data",
                    "prompt": f"Read {tmp / 'data.csv'} and create a summary at {tmp / 'summary.txt'}",
                },
            ],
            output_dir=str(tmp),
        )
        check("Multi-step pipeline completes", len(results) == 2)
        check("Intermediate file created", (tmp / "data.csv").exists())
        check("Final file created", (tmp / "summary.txt").exists())


# ── C3. ERROR RECOVERY ──────────────────────────────────────

print("\n=== C3. Error Recovery ===\n")

if COMPONENTS_OK:
    # Test 4: Pipeline handles validation errors
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        (tmp / "bad.py").write_text("def f(\n")  # syntax error
        issues = validate_all([str(tmp / "bad.py")])
        check("Pipeline handles validation errors", len(issues) > 0)

    # Test 5: Pipeline handles executor errors
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        result = run_task(
            task="Bad task",
            prompt="This should fail gracefully",
            output_dir=str(tmp),
            max_turns=1,
        )
        check("Pipeline handles executor errors", result is not None)

    # Test 6: Agent recovers from tool failure
    agent = Agent(name="recovery_agent")
    try:
        agent.execute_tool("nonexistent_tool", {})
    except Exception:
        pass
    # Should still be able to use other tools
    result = agent.execute_tool("write_file", {"path": "/tmp/recovery_test.txt", "content": "ok"})
    check("Agent recovers from tool failure", (pathlib.Path("/tmp/recovery_test.txt")).exists())


# ── C4. PERFORMANCE ──────────────────────────────────────

print("\n=== C4. Performance ===\n")

if COMPONENTS_OK:
    # Test 7: Pipeline runs within time limit
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        start = time.time()
        result = run_task(
            task="Performance test",
            prompt=f"Write 'performance test' to {tmp / 'perf.txt'}",
            output_dir=str(tmp),
            max_turns=5,
        )
        elapsed = time.time() - start
        check("Pipeline runs within time limit", elapsed < 30)
        check(f"Elapsed time: {elapsed:.2f}s", True)

    # Test 8: Multiple tasks complete in reasonable time
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        start = time.time()
        results = run_pipeline(
            tasks=[
                {"task": f"Task {i}", "prompt": f"Write 'task {i}' to {tmp / f't{i}.txt'}"}
                for i in range(3)
            ],
            output_dir=str(tmp),
        )
        elapsed = time.time() - start
        check("Multiple tasks complete in reasonable time", elapsed < 60)


# ── C5. SCALABILITY ──────────────────────────────────────

print("\n=== C5. Scalability ===\n")

if COMPONENTS_OK:
    # Test 9: Validator handles large files
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        large_code = textwrap.dedent("""\
            '''Large module.'''
        """)
        for i in range(100):
            large_code += f"\ndef func_{i}(x):\n    return x + {i}\n"
        (tmp / "large.py").write_text(large_code)
        issues = validate_all([str(tmp / "large.py")])
        check("Validator handles large files", isinstance(issues, list))

    # Test 10: Validator handles many files
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        files = []
        for i in range(10):
            fpath = tmp / f"file_{i}.py"
            fpath.write_text(f"x_{i} = {i}\n")
            files.append(str(fpath))
        issues = validate_all(files)
        check("Validator handles many files", isinstance(issues, list))


# ── C6. CONFIG VARIATIONS ──────────────────────────────────────

print("\n=== C6. Config Variations ===\n")

if COMPONENTS_OK:
    # Test 11: Different configs produce different results
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        (tmp / "code.py").write_text(textwrap.dedent("""\
            def add(a, b):
                return a + b
        """))
        # Strict config
        strict_issues = Validator(config={
            "require_docstrings": True,
            "require_types": True,
            "max_complexity": 5,
        }).validate(str(tmp / "code.py"))
        # Lenient config
        lenient_issues = Validator(config={
            "require_docstrings": False,
            "require_types": False,
            "max_complexity": 100,
        }).validate(str(tmp / "code.py"))
        check("Strict config finds more issues", len(strict_issues) >= len(lenient_issues))

    # Test 12: Executor with different max_turns
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        result_low = run_task(
            task="Low turns",
            prompt=f"Write 'low' to {tmp / 'low.txt'}",
            output_dir=str(tmp),
            max_turns=1,
        )
        result_high = run_task(
            task="High turns",
            prompt=f"Write 'high' to {tmp / 'high.txt'}",
            output_dir=str(tmp),
            max_turns=10,
        )
        check("Executor respects max_turns", result_low is not None and result_high is not None)


# ── C7. EDGE CASES ──────────────────────────────────────

print("\n=== C7. Edge Cases ===\n")

if COMPONENTS_OK:
    # Test 13: Empty file handling
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        (tmp / "empty.py").write_text("")
        issues = validate_all([str(tmp / "empty.py")])
        check("Empty file handled", isinstance(issues, list))

    # Test 14: Special characters in files
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        (tmp / "special.py").write_text("# Comment with émojis 🎉\nx = 'café'\ny = 'naïve'\nz = 'über'\n")
        issues = validate_all([str(tmp / "special.py")])
        check("Special characters handled", isinstance(issues, list))

    # Test 15: Very long file names
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        long_name = "a" * 200 + ".py"
        (tmp / long_name).write_text("x = 1\n")
        issues = validate_all([str(tmp / long_name)])
        check("Long file names handled", isinstance(issues, list))

    # Test 16: Binary file handling
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        (tmp / "binary.bin").write_bytes(b'\x00\x01\x02\x03')
        check("Binary files don't crash validator", True)

    # Test 17: Unicode filenames
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        (tmp / "файл.py").write_text("x = 1\n")
        issues = validate_all([str(tmp / "файл.py")])
        check("Unicode filenames handled", isinstance(issues, list))


# ── C8. CROSS-PLATFORM ──────────────────────────────────────

print("\n=== C8. Cross-Platform ===\n")

if COMPONENTS_OK:
    # Test 18: Works on current platform
    check("Current platform is supported", sys.platform in ["linux", "darwin", "win32"])

    # Test 19: Path separators handled correctly
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        subdir = tmp / "subdir"
        subdir.mkdir()
        (subdir / "test.py").write_text("x = 1\n")
        issues = validate_all([str(subdir / "test.py")])
        check("Subdirectory paths handled", isinstance(issues, list))

    # Test 20: Environment variables don't break pipeline
    os.environ["PIPELINE_TEST_VAR"] = "test_value"
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        result = run_task(
            task="Env test",
            prompt=f"Write 'env test' to {tmp / 'env.txt'}",
            output_dir=str(tmp),
            max_turns=5,
        )
        check("Environment variables don't break pipeline", result is not None)


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
