"""
test_harness_capabilities.py
Tests whether the agent harness has the tools it needs, can USE them correctly,
and can self-extend when a tool is missing -- all without a live Ollama instance.

Philosophy: treat the harness like a black box. Give it tasks and check outcomes.

Categories:
  A. Tool inventory -- does each tool exist and have the right signature?
  B. Tool execution -- does each tool actually DO what it says?
  C. Sufficiency -- can the executor complete real coding tasks with these tools?
  D. Gap detection -- what CAN'T the harness do right now?
  E. Self-extension -- can the executor write a new tool and use it?
"""

import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import textwrap

sys.path.insert(0, str(pathlib.Path(__file__).parent))

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"
WARN = "\033[33mWARN\033[0m"
INFO = "\033[36mINFO\033[0m"
results = []

def check(name, condition, detail="", warn_only=False):
    ok = bool(condition)
    tag = PASS if ok else (WARN if warn_only else FAIL)
    print(f"  [{tag}] {name}")
    if not ok and detail:
        print(f"         {detail}")
    results.append((name, ok, warn_only))
    return ok

def warn(name, condition, detail=""):
    return check(name, condition, detail, warn_only=True)


# ============================================================================
# A. TOOL INVENTORY
# ============================================================================
print("\n=== A. Tool Inventory ===\n")

try:
    import tools as tools_mod
    TOOLS = tools_mod.TOOLS
    SCHEMAS = tools_mod.TOOL_SCHEMAS
    check("tools.py imports cleanly", True)
except Exception as e:
    check("tools.py imports cleanly", False, str(e))
    TOOLS = {}; SCHEMAS = []

EXPECTED_TOOLS = {
    "read_file":       "Read file contents",
    "write_file":      "Write/create a file",
    "append_file":     "Append to a file",
    "list_tree":       "List directory tree",
    "delete_file":     "Delete a file",
    "run_shell":       "Run shell commands",
    "search_in_files": "Grep/search in files",
    "patch_file":      "Patch/replace text in a file",
    "list_files":      "List files matching a glob",
    "create_project":  "Create a project structure",
}

for tool_name, description in EXPECTED_TOOLS.items():
    exists = tool_name in TOOLS
    check(f"Tool '{tool_name}' exists", exists)
    if exists:
        check(f"Tool '{tool_name}' has description", bool(TOOLS[tool_name].get("description")),
              f"  description={TOOLS[tool_name].get('description', 'MISSING')[:60]}")
        check(f"Tool '{tool_name}' has params", "params" in TOOLS[tool_name],
              f"  params={TOOLS[tool_name].get('params', 'MISSING')}")


# ============================================================================
# B. TOOL EXECUTION
# ============================================================================
print("\n=== B. Tool Execution ===\n")

try:
    from pipeline.executor import Agent
    AGENT_OK = True
except Exception as e:
    check("Agent class imports", False, str(e))
    AGENT_OK = False

if AGENT_OK:
    agent = Agent(name="harness_test")

    # B1. write_file
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        fpath = tmp / "write_test.txt"
        result = agent.execute_tool("write_file", {"path": str(fpath), "content": "hello harness\n"})
        check("write_file creates file", fpath.exists())
        check("write_file writes content", fpath.read_text() == "hello harness\n")

    # B2. read_file
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        fpath = tmp / "read_test.txt"
        fpath.write_text("read me\n")
        result = agent.execute_tool("read_file", {"path": str(fpath)})
        check("read_file returns content", "read me" in result)

    # B3. append_file
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        fpath = tmp / "append_test.txt"
        fpath.write_text("line1\n")
        agent.execute_tool("append_file", {"path": str(fpath), "content": "line2\n"})
        check("append_file appends", "line1\nline2\n" == fpath.read_text())

    # B4. delete_file
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        fpath = tmp / "delete_test.txt"
        fpath.write_text("delete me\n")
        agent.execute_tool("delete_file", {"path": str(fpath)})
        check("delete_file removes", not fpath.exists())

    # B5. run_shell
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        result = agent.execute_tool("run_shell", {"command": "echo SHELL_OK", "cwd": str(tmp)})
        check("run_shell executes", "SHELL_OK" in result)

    # B6. patch_file
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        fpath = tmp / "patch_test.py"
        fpath.write_text("x = 1\ny = 2\n")
        agent.execute_tool("patch_file", {"path": str(fpath), "old_string": "x = 1", "new_string": "x = 99"})
        content = fpath.read_text()
        check("patch_file replaces", "x = 99" in content)
        check("patch_file preserves", "y = 2" in content)

    # B7. search_in_files
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        (tmp / "a.py").write_text("def greet(): pass\n")
        (tmp / "b.py").write_text("def hello(): pass\n")
        result = agent.execute_tool("search_in_files", {"pattern": "greet", "path": str(tmp), "glob": "*.py"})
        check("search_in_files finds", "greet" in result)

    # B8. list_files
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        (tmp / "f1.txt").write_text("a")
        (tmp / "f2.txt").write_text("b")
        result = agent.execute_tool("list_files", {"path": str(tmp), "glob": "*.txt"})
        check("list_files returns", "f1.txt" in result and "f2.txt" in result)

    # B9. create_project
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        result = agent.execute_tool("create_project", {
            "path": str(tmp / "proj"),
            "name": "testproj",
            "files": ["src/__init__.py", "src/main.py", "tests/test_main.py"]
        })
        check("create_project creates structure", (tmp / "proj" / "src" / "main.py").exists())


# ============================================================================
# C. SUFFICIENCY -- CAN THE EXECUTOR COMPLETE REAL TASKS?
# ============================================================================
print("\n=== C. Sufficiency: Real Coding Tasks ===\n")

if AGENT_OK:
    agent = Agent(name="sufficiency_test")

    # C1. Write a Python module and test it
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        # Write module
        agent.execute_tool("write_file", {
            "path": str(tmp / "calc.py"),
            "content": "def add(a, b):\n    return a + b\n\ndef subtract(a, b):\n    return a - b\n"
        })
        # Write test
        agent.execute_tool("write_file", {
            "path": str(tmp / "test_calc.py"),
            "content": "from calc import add, subtract\nassert add(2, 3) == 5\nassert subtract(10, 4) == 6\nprint('ALL TESTS PASSED')\n"
        })
        # Run tests
        result = agent.execute_tool("run_shell", {"command": "python test_calc.py", "cwd": str(tmp)})
        check("Task: write module + test + run", "ALL TESTS PASSED" in result)

    # C2. Create a project with structure
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        agent.execute_tool("create_project", {
            "path": str(tmp / "myapp"),
            "name": "myapp",
            "files": [
                "src/__init__.py",
                "src/app.py",
                "src/utils.py",
                "tests/__init__.py",
                "tests/test_app.py",
                "README.md",
                "requirements.txt"
            ]
        })
        check("Task: create project structure", (tmp / "myapp" / "src" / "app.py").exists())
        check("Task: create project structure", (tmp / "myapp" / "README.md").exists())

    # C3. Patch and verify
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        agent.execute_tool("write_file", {
            "path": str(tmp / "config.py"),
            "content": "DEBUG = False\nVERSION = '1.0'\n"
        })
        agent.execute_tool("patch_file", {
            "path": str(tmp / "config.py"),
            "old_string": "DEBUG = False",
            "new_string": "DEBUG = True"
        })
        content = agent.execute_tool("read_file", {"path": str(tmp / "config.py")})
        check("Task: patch and verify", "DEBUG = True" in content)

    # C4. Search and modify
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        agent.execute_tool("write_file", {
            "path": str(tmp / "app.py"),
            "content": "def greet(name):\n    return f'Hello {name}'\n\ndef farewell(name):\n    return f'Goodbye {name}'\n"
        })
        result = agent.execute_tool("search_in_files", {"pattern": "greet", "path": str(tmp), "glob": "*.py"})
        check("Task: search finds target", "greet" in result)
        agent.execute_tool("patch_file", {
            "path": str(tmp / "app.py"),
            "old_string": "def greet(name):",
            "new_string": "def greet(name):\n    return f'Hi {name}'"
        })
        content = agent.execute_tool("read_file", {"path": str(tmp / "app.py")})
        check("Task: search and modify", "Hi {name}" in content)


# ============================================================================
# D. GAP DETECTION -- WHAT CAN'T THE HARNESS DO?
# ============================================================================
print("\n=== D. Gap Detection ===\n")

# D1. No live LLM
check("Gap: No live Ollama/LLM connection", True, "Harness works without LLM but can't generate code autonomously")

# D2. No git operations
check("Gap: No git tool", "git" not in TOOLS, "Cannot commit, branch, or diff")

# D3. No package management
check("Gap: No pip install tool", "pip_install" not in TOOLS, "Cannot install packages (must use run_shell)")

# D4. No database tools
check("Gap: No database tool", "database" not in str(TOOLS).lower(), "Cannot query databases")

# D5. No HTTP client
check("Gap: No HTTP client tool", "http" not in str(TOOLS).lower(), "Cannot make HTTP requests (must use run_shell)")

# D6. No file watching
check("Gap: No file watcher", "watch" not in str(TOOLS).lower(), "Cannot watch for file changes")

# D7. No process management
check("Gap: No process manager", "process" not in str(TOOLS).lower(), "Cannot manage background processes")

# D8. No email
check("Gap: No email tool", "email" not in str(TOOLS).lower(), "Cannot send emails")

# D9. No cloud services
check("Gap: No cloud service tools", "aws" not in str(TOOLS).lower() and "gcp" not in str(TOOLS).lower(), "Cannot interact with cloud APIs")

# D10. No Docker
check("Gap: No Docker tool", "docker" not in str(TOOLS).lower(), "Cannot manage containers (must use run_shell)")


# ============================================================================
# E. SELF-EXTENSION -- CAN THE EXECUTOR WRITE A NEW TOOL AND USE IT?
# ============================================================================
print("\n=== E. Self-Extension ===\n")

if AGENT_OK:
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)

        # E1. Write a new tool file
        new_tool_code = textwrap.dedent("""
            def echo_message(message):
                '''Echo back the message.'''
                return f"Echo: {message}"
        """)
        agent.execute_tool("write_file", {
            "path": str(tmp / "my_tool.py"),
            "content": new_tool_code
        })
        check("Self-ext: write new tool file", (tmp / "my_tool.py").exists())

        # E2. Import and use the new tool
        import importlib.util
        spec = importlib.util.spec_from_file_location("my_tool", tmp / "my_tool.py")
        my_tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(my_tool)
        result = my_tool.echo_message("hello")
        check("Self-ext: use new tool", result == "Echo: hello")

        # E3. Write a tool that uses another tool
        tool_with_dep = f"""
            import sys
            sys.path.insert(0, r'{tmp}')
            from my_tool import echo_message
            def greet(name):
                return echo_message(f'Hello {{name}}')
        """
        agent.execute_tool("write_file", {
            "path": str(tmp / "my_tool_dep.py"),
            "content": tool_with_dep
        })
        check("Self-ext: write tool with dependency", (tmp / "my_tool_dep.py").exists())

        # E4. Verify the extended tool works
        spec2 = importlib.util.spec_from_file_location("my_tool_dep", tmp / "my_tool_dep.py")
        my_tool_dep = importlib.util.module_from_spec(spec2)
        spec2.loader.exec_module(my_tool_dep)
        result = my_tool_dep.greet("World")
        check("Self-ext: extended tool works", result == "Echo: Hello World")


# ============================================================================
# SUMMARY
# ============================================================================
print(f"\n{'='*60}")
passed = sum(1 for _, ok, _ in results if ok)
failed = sum(1 for _, ok, _ in results if not ok)
warned = sum(1 for _, ok, _ in results if not ok and _)
total = len(results)

print(f"  PASS:  {passed}/{total}")
print(f"  WARN:  {warned}/{total}")
print(f"  FAIL:  {failed}/{total}")

if failed > 0:
    print(f"\nFailed tests:")
    for name, ok, _ in results:
        if not ok:
            print(f"  - {name}")

if failed == 0:
    print("\nAll tests passed!")
else:
    print(f"\n{failed} test(s) failed.")
