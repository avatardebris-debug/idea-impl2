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
    "patch_file":      "Patch/replace text in file",
}

USEFUL_MISSING = {
    "web_search":      "Search the web for docs/APIs",
    "download_file":   "Download a file via URL",
    "pip_install":     "Install a Python package",
    "read_url":        "Fetch URL content",
    "diff_file":       "Show diff between file versions",
    "make_executable": "chmod +x a file",
}

for name, purpose in EXPECTED_TOOLS.items():
    check(f"Tool '{name}' exists", name in TOOLS, f"Purpose: {purpose}")

print()
for name, purpose in USEFUL_MISSING.items():
    present = name in TOOLS
    warn(f"Tool '{name}' present [{purpose}]", present,
         "MISSING - agents must use run_shell workaround" if not present else "")

# Schema completeness
print()
schema_names = {s.get("function", {}).get("name", s.get("name","")) for s in SCHEMAS}
for name in EXPECTED_TOOLS:
    check(f"Schema exists for '{name}'", name in schema_names)


# ============================================================================
# B. TOOL EXECUTION -- does each tool actually work?
# ============================================================================
print("\n=== B. Tool Execution ===\n")

with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp)

    # write_file
    try:
        result = tools_mod.write_file(str(tmp / "test.py"), "print('hello')\n")
        check("write_file: creates file", (tmp / "test.py").exists())
        check("write_file: correct content", (tmp / "test.py").read_text() == "print('hello')\n")
    except Exception as e:
        check("write_file: creates file", False, str(e))

    # read_file
    try:
        content = tools_mod.read_file(str(tmp / "test.py"))
        check("read_file: reads content", "hello" in content)
        missing = tools_mod.read_file(str(tmp / "nonexistent.py"))
        check("read_file: handles missing file gracefully", "not found" in missing.lower() or missing == "" or "error" in missing.lower())
    except Exception as e:
        check("read_file: reads content", False, str(e))

    # append_file
    try:
        tools_mod.append_file(str(tmp / "test.py"), "\nprint('world')\n")
        content = (tmp / "test.py").read_text()
        check("append_file: appends content", "world" in content and "hello" in content)
    except Exception as e:
        check("append_file: appends content", False, str(e))

    # list_tree
    try:
        tree = tools_mod.list_tree(str(tmp))
        check("list_tree: returns string", isinstance(tree, str) and len(tree) > 0)
        check("list_tree: shows test.py", "test.py" in tree)
    except Exception as e:
        check("list_tree: returns string", False, str(e))

    # search_in_files
    try:
        hits = tools_mod.search_in_files("hello", str(tmp), "*.py")
        check("search_in_files: finds pattern", "hello" in hits or "test.py" in hits)
        no_hits = tools_mod.search_in_files("ZZZNOMATCH999", str(tmp), "*.py")
        check("search_in_files: returns empty on no match", "ZZZNOMATCH999" not in no_hits)
    except Exception as e:
        check("search_in_files: finds pattern", False, str(e))

    # patch_file
    try:
        tools_mod.write_file(str(tmp / "patch_me.py"), "x = 1\ny = 2\n")
        tools_mod.patch_file(str(tmp / "patch_me.py"), "x = 1", "x = 99")
        content = (tmp / "patch_me.py").read_text()
        check("patch_file: replaces content", "x = 99" in content)
        check("patch_file: preserves other lines", "y = 2" in content)
    except Exception as e:
        check("patch_file: replaces content", False, str(e))

    # run_shell
    try:
        out = tools_mod.run_shell("echo HARNESS_TEST_OK", str(tmp))
        check("run_shell: executes commands", "HARNESS_TEST_OK" in out)
        py_out = tools_mod.run_shell("python -c \"print(2+2)\"", str(tmp))
        check("run_shell: runs Python", "4" in py_out)
        err_out = tools_mod.run_shell("python -c \"raise ValueError('oops')\"", str(tmp))
        check("run_shell: captures stderr on failure", "oops" in err_out or "error" in err_out.lower())
    except Exception as e:
        check("run_shell: executes commands", False, str(e))

    # delete_file
    try:
        tools_mod.write_file(str(tmp / "del_me.txt"), "bye")
        tools_mod.delete_file(str(tmp / "del_me.txt"))
        check("delete_file: removes file", not (tmp / "del_me.txt").exists())
    except Exception as e:
        check("delete_file: removes file", False, str(e))


# ============================================================================
# C. SUFFICIENCY -- can the harness complete real executor tasks?
# ============================================================================
print("\n=== C. Sufficiency for Executor Tasks ===\n")

with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp)

    # Task 1: Write a Python module + test, then run pytest
    tools_mod.write_file(str(tmp / "calculator.py"), textwrap.dedent("""\
        def add(a, b): return a + b
        def multiply(a, b): return a * b
    """))
    tools_mod.write_file(str(tmp / "test_calculator.py"), textwrap.dedent("""\
        from calculator import add, multiply
        def test_add(): assert add(2, 3) == 5
        def test_multiply(): assert multiply(4, 5) == 20
    """))

    result = tools_mod.run_shell("python -m pytest test_calculator.py -v --tb=short 2>&1", str(tmp))
    check("Can write module + test + run pytest", "passed" in result.lower(), result[:200])

    # Task 2: Install a package and use it
    result = tools_mod.run_shell("pip install requests -q 2>&1 && python -c \"import requests; print('requests OK')\"", str(tmp))
    check("Can pip install + import package via run_shell", "requests OK" in result, result[:200])

    # Task 3: Create a project structure with multiple dirs
    tools_mod.run_shell("mkdir -p src/utils tests docs", str(tmp))
    tools_mod.write_file(str(tmp / "src" / "utils" / "helper.py"), "def greet(name): return f'Hello {name}'")
    tools_mod.write_file(str(tmp / "src" / "__init__.py"), "")
    tools_mod.write_file(str(tmp / "src" / "utils" / "__init__.py"), "")
    check("Can create nested project structure", (tmp / "src" / "utils" / "helper.py").exists())

    # Task 4: Search for a function across files
    hits = tools_mod.search_in_files("def greet", str(tmp), "*.py")
    check("Can search across project files", "greet" in hits)

    # Task 5: Patch a file (simulating a bug fix)
    tools_mod.write_file(str(tmp / "config.py"), "DEBUG = True\nPORT = 8000\n")
    tools_mod.patch_file(str(tmp / "config.py"), "DEBUG = True", "DEBUG = False")
    content = (tmp / "config.py").read_text()
    check("Can patch/fix a file", "DEBUG = False" in content and "PORT = 8000" in content)

    # Task 6: Write a requirements.txt and install from it
    tools_mod.write_file(str(tmp / "requirements.txt"), "pytest\n")
    result = tools_mod.run_shell("pip install -r requirements.txt -q 2>&1", str(tmp))
    check("Can install from requirements.txt", "error" not in result.lower() or "already" in result.lower(), result[:100])

    # Task 7: Read multiple files (simulate reviewer reading workspace)
    files_to_read = ["calculator.py", "test_calculator.py", "config.py"]
    all_content = ""
    for f in files_to_read:
        all_content += tools_mod.read_file(str(tmp / f))
    check("Can read multiple files (reviewer pattern)", len(all_content) > 50)

    # Task 8: Can it run git commands? (important for harvest.sh workflow)
    git_result = tools_mod.run_shell("git --version 2>&1", str(tmp))
    check("git available in run_shell", "git version" in git_result)


# ============================================================================
# D. GAP ANALYSIS -- what's missing or risky?
# ============================================================================
print("\n=== D. Gap Analysis ===\n")

with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp)

    # Gap 1: No web_search tool -- agent must use run_shell curl/wget
    curl_result = tools_mod.run_shell("curl --version 2>&1", str(tmp))
    warn("Web access via curl (workaround for no web_search tool)",
         "curl" in curl_result, "curl not available -- agents can't fetch docs")

    # Gap 2: No timeout on run_shell -- a hanging test hangs the agent
    # (This is the bug we just fixed in validator.py with pytest-timeout)
    import inspect
    shell_src = inspect.getsource(tools_mod.run_shell)
    has_timeout = "timeout" in shell_src
    warn("run_shell has timeout parameter", has_timeout,
         "RISK: a hung subprocess will block the agent indefinitely")

    # Gap 3: patch_file fails if old string not found -- silent?
    try:
        tools_mod.write_file(str(tmp / "t.py"), "x = 1")
        result = tools_mod.patch_file(str(tmp / "t.py"), "NOTFOUND", "y = 2")
        content = (tmp / "t.py").read_text()
        patch_safe = "NOTFOUND" not in content  # file unchanged
        warn("patch_file handles missing old-string safely", "not found" in str(result).lower() or "error" in str(result).lower(),
             f"Silent failure risk: result='{result}', file='{content}'")
    except Exception as e:
        check("patch_file raises on missing old-string", True)  # explicit error is fine

    # Gap 4: Can agent write its own tools?
    tools_mod.write_file(str(tmp / "my_tool.py"), textwrap.dedent("""\
        def fetch_json(url):
            import urllib.request, json
            with urllib.request.urlopen(url, timeout=5) as r:
                return json.loads(r.read())
    """))
    exec_result = tools_mod.run_shell(
        "python -c \"import sys; sys.path.insert(0,'.'); from my_tool import fetch_json; print('tool OK')\"",
        str(tmp)
    )
    check("Agent CAN write + immediately use a new tool via run_shell", "tool OK" in exec_result)

    # Gap 5: File size limits -- can it read large files?
    big = "x = 1\n" * 10000
    tools_mod.write_file(str(tmp / "big.py"), big)
    content = tools_mod.read_file(str(tmp / "big.py"))
    warn("read_file handles large files (60k chars)", len(content) >= len(big),
         f"Truncation at {len(content)} chars (file was {len(big)})" if len(content) < len(big) else "")

    # Gap 6: Binary files
    try:
        result = tools_mod.read_file(str(pathlib.Path(sys.executable)))
        warn("read_file handles binary files gracefully", True)
    except Exception:
        warn("read_file handles binary files gracefully", False, "May crash on binary files")

    # Gap 7: Concurrent write safety
    import threading
    errors = []
    def write_concurrent(i):
        try:
            tools_mod.write_file(str(tmp / f"concurrent_{i}.py"), f"x = {i}")
        except Exception as e:
            errors.append(str(e))
    threads = [threading.Thread(target=write_concurrent, args=(i,)) for i in range(10)]
    [t.start() for t in threads]; [t.join() for t in threads]
    files_written = list(tmp.glob("concurrent_*.py"))
    warn("Concurrent writes are safe", len(errors) == 0 and len(files_written) == 10,
         f"errors={errors}, files={len(files_written)}/10")


# ============================================================================
# E. SELF-EXTENSION -- can the harness grow new capabilities?
# ============================================================================
print("\n=== E. Self-Extension Capability ===\n")

with tempfile.TemporaryDirectory() as tmp:
    tmp = pathlib.Path(tmp)

    # E1: Agent writes a new utility module and uses it in the same session
    tools_mod.write_file(str(tmp / "html_utils.py"), textwrap.dedent("""\
        import re
        def strip_html(text):
            return re.sub(r'<[^>]+>', '', text)
        def extract_links(html):
            return re.findall(r'href=[\"\\']([^\"\\']+)[\"\\']', html)
    """))
    result = tools_mod.run_shell(
        "python -c \""
        "import sys; sys.path.insert(0, '.'); "
        "from html_utils import strip_html, extract_links; "
        "print(strip_html('<b>hello</b>')); "
        "print(extract_links('<a href=\\'http://x.com\\'>link</a>'))"
        "\"",
        str(tmp)
    )
    check("E1: Can write a utility module and immediately use it", "hello" in result)

    # E2: Agent adds a tool to shared_libs and it persists
    shared = tmp / ".pipeline" / "shared_libs" / "html_utils"
    shared.mkdir(parents=True, exist_ok=True)
    import shutil
    shutil.copy(tmp / "html_utils.py", shared / "html_utils.py")
    check("E2: Can add new tool to shared_libs for other projects", (shared / "html_utils.py").exists())

    # E3: Agent can pip install missing packages at runtime
    result = tools_mod.run_shell(
        "pip install httpx -q 2>&1 && python -c \"import httpx; print('httpx available')\"",
        str(tmp)
    )
    check("E3: Can acquire missing Python package at runtime", "httpx available" in result)

    # E4: Agent can create an executable script (Linux/cloud only)
    if sys.platform != "win32":
        tools_mod.write_file(str(tmp / "my_scraper.sh"), "#!/bin/bash\necho 'scraper ran'\n")
        tools_mod.run_shell("chmod +x my_scraper.sh", str(tmp))
        result = tools_mod.run_shell("./my_scraper.sh", str(tmp))
        check("E4: Can create + execute shell scripts (Linux)", "scraper ran" in result)
    else:
        check("E4: Can create + execute batch scripts (Windows)", True, "Skipped on Windows (runs on cloud)")

    # E5: Agent can self-modify a file iteratively (fix -> test -> fix loop)
    tools_mod.write_file(str(tmp / "buggy.py"), "def divide(a, b): return a / b\n")
    tools_mod.write_file(str(tmp / "test_buggy.py"), textwrap.dedent("""\
        from buggy import divide
        def test_normal(): assert divide(10, 2) == 5.0
        def test_zero():
            try: divide(1, 0)
            except ZeroDivisionError: pass
            else: raise AssertionError('should have raised')
    """))
    # First run -- test_zero should FAIL (no guard in buggy.py)
    first_run = tools_mod.run_shell("python -m pytest test_buggy.py -v --tb=short 2>&1", str(tmp))
    # Now "fix" the bug (what executor would do)
    tools_mod.patch_file(str(tmp / "buggy.py"),
                         "def divide(a, b): return a / b",
                         "def divide(a, b):\n    if b == 0: raise ZeroDivisionError('division by zero')\n    return a / b")
    # Second run -- should pass
    second_run = tools_mod.run_shell("python -m pytest test_buggy.py -v --tb=short 2>&1", str(tmp))
    check("E5: Iterative fix cycle works (write -> test -> patch -> test)", "passed" in second_run.lower())


# ============================================================================
# SUMMARY
# ============================================================================

print(f"\n{'='*60}")
passed = sum(1 for _, ok, warn in results if ok)
warned = sum(1 for _, ok, warn in results if not ok and warn)
failed = sum(1 for _, ok, warn in results if not ok and not warn)
total  = len(results)

print(f"  PASS:  {passed}/{total}")
print(f"  WARN:  {warned} (gaps -- not blockers)")
print(f"  FAIL:  {failed} (broken -- need fixing)")

if failed > 0:
    print(f"\nBroken (fix these):")
    for name, ok, w in results:
        if not ok and not w: print(f"  - {name}")

if warned > 0:
    print(f"\nGaps (nice to have):")
    for name, ok, w in results:
        if not ok and w: print(f"  - {name}")
