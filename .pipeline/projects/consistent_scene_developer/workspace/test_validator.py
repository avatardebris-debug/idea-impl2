"""
test_validator.py
Tests the pipeline validator: syntax, imports, types, docstrings, complexity,
security, style, config, multi-file, and passing code.
"""

import ast
import json
import pathlib
import re
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


# ── Import the validator ──────────────────────────────────────────────────────

try:
    from pipeline.validator import (
        Validator,
        validate_syntax,
        validate_imports,
        validate_types,
        validate_docstrings,
        validate_complexity,
        validate_security,
        validate_style,
        validate_config,
        validate_all,
    )
    VALIDATOR_OK = True
except Exception as e:
    print(f"  [FAIL] Importing validator: {e}")
    VALIDATOR_OK = False


# ── A. SYNTAX VALIDATION ─────────────────────────────────────────────────────

print("\n=== A. Syntax Validation ===\n")

if VALIDATOR_OK:
    # Test 1: Valid Python passes
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        (tmp / "good.py").write_text("def hello():\n    return 'world'\n")
        issues = validate_syntax(str(tmp / "good.py"))
        check("Valid Python has no syntax issues", len(issues) == 0)

    # Test 2: Syntax error is caught
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        (tmp / "bad.py").write_text("def hello(\n    return 'world'\n")  # missing )
        issues = validate_syntax(str(tmp / "bad.py"))
        check("Syntax error is detected", len(issues) > 0)
        if issues:
            check("Issue has file and line info", "file" in issues[0] and "line" in issues[0])

    # Test 3: Multiple syntax errors
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        (tmp / "multi.py").write_text("x =\ny =\n")  # incomplete assignments
        issues = validate_syntax(str(tmp / "multi.py"))
        check("Multiple syntax errors detected", len(issues) > 0)

    # Test 4: Empty file passes
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        (tmp / "empty.py").write_text("")
        issues = validate_syntax(str(tmp / "empty.py"))
        check("Empty file passes syntax check", len(issues) == 0)

    # Test 5: Unicode content
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        (tmp / "unicode.py").write_text("# Comment with émojis 🎉\nx = 'café'\n")
        issues = validate_syntax(str(tmp / "unicode.py"))
        check("Unicode content passes", len(issues) == 0)


# ── B. IMPORT VALIDATION ─────────────────────────────────────────────────────

print("\n=== B. Import Validation ===\n")

if VALIDATOR_OK:
    # Test 6: Valid imports pass
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        (tmp / "valid_imports.py").write_text("import os\nimport sys\nfrom pathlib import Path\n")
        issues = validate_imports(str(tmp / "valid_imports.py"), search_paths=[str(tmp)])
        check("Valid imports pass", len(issues) == 0)

    # Test 7: Invalid import is caught
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        (tmp / "bad_import.py").write_text("import nonexistent_module_xyz\n")
        issues = validate_imports(str(tmp / "bad_import.py"), search_paths=[str(tmp)])
        check("Invalid import is detected", len(issues) > 0)

    # Test 8: Relative import handling
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        (tmp / "pkg" / "__init__.py").parent.mkdir(exist_ok=True)
        (tmp / "pkg" / "__init__.py").write_text("")
        (tmp / "pkg" / "mod.py").write_text("x = 1\n")
        (tmp / "pkg" / "test.py").write_text("from pkg.mod import x\n")
        issues = validate_imports(str(tmp / "pkg" / "test.py"), search_paths=[str(tmp)])
        check("Relative import handled", len(issues) == 0)


# ── C. TYPE HINT VALIDATION ──────────────────────────────────────────────────

print("\n=== C. Type Hint Validation ===\n")

if VALIDATOR_OK:
    # Test 9: Correct type hints pass
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        (tmp / "typed.py").write_text(textwrap.dedent("""\
            def add(a: int, b: int) -> int:
                return a + b
        """))
        issues = validate_types(str(tmp / "typed.py"))
        check("Correct type hints pass", len(issues) == 0)

    # Test 10: Incorrect type hints are flagged
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        (tmp / "bad_typed.py").write_text(textwrap.dedent("""\
            def add(a: int, b: int) -> str:
                return a + b
        """))
        issues = validate_types(str(tmp / "bad_typed.py"))
        check("Incorrect return type is flagged", len(issues) > 0)

    # Test 11: Missing type hints (optional warning)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        (tmp / "untyped.py").write_text("def add(a, b):\n    return a + b\n")
        issues = validate_types(str(tmp / "untyped.py"))
        check("Untyped function handled gracefully", True)  # Should not crash


# ── D. DOCSTRING VALIDATION ──────────────────────────────────────────────────

print("\n=== D. Docstring Validation ===\n")

if VALIDATOR_OK:
    # Test 12: Functions with docstrings pass
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        (tmp / "documented.py").write_text(textwrap.dedent("""\
            def add(a: int, b: int) -> int:
                '''Add two numbers.'''
                return a + b

            class MyClass:
                '''A class.'''
                def method(self):
                    '''A method.'''
                    pass
        """))
        issues = validate_docstrings(str(tmp / "documented.py"))
        check("Documented code passes", len(issues) == 0)

    # Test 13: Missing docstrings are flagged
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        (tmp / "undocumented.py").write_text(textwrap.dedent("""\
            def add(a: int, b: int) -> int:
                return a + b
        """))
        issues = validate_docstrings(str(tmp / "undocumented.py"))
        check("Missing docstring is flagged", len(issues) > 0)

    # Test 14: Class docstrings
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        (tmp / "no_class_doc.py").write_text("class Foo:\n    pass\n")
        issues = validate_docstrings(str(tmp / "no_class_doc.py"))
        check("Missing class docstring is flagged", len(issues) > 0)


# ── E. COMPLEXITY VALIDATION ─────────────────────────────────────────────────

print("\n=== E. Complexity Validation ===\n")

if VALIDATOR_OK:
    # Test 15: Simple function passes
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        (tmp / "simple.py").write_text(textwrap.dedent("""\
            def add(a, b):
                return a + b
        """))
        issues = validate_complexity(str(tmp / "simple.py"), max_complexity=10)
        check("Simple function passes complexity check", len(issues) == 0)

    # Test 16: Complex function is flagged
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        complex_code = "def f(x):\n"
        for i in range(20):
            complex_code += f"    if x == {i}:\n        return {i}\n"
        (tmp / "complex.py").write_text(complex_code)
        issues = validate_complexity(str(tmp / "complex.py"), max_complexity=10)
        check("Complex function is flagged", len(issues) > 0)

    # Test 17: Custom complexity threshold
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        (tmp / "moderate.py").write_text(textwrap.dedent("""\
            def moderate(x):
                if x > 0:
                    return 1
                elif x < 0:
                    return -1
                else:
                    return 0
        """))
        issues_low = validate_complexity(str(tmp / "moderate.py"), max_complexity=2)
        issues_high = validate_complexity(str(tmp / "moderate.py"), max_complexity=10)
        check("Custom threshold works (low threshold flags)", len(issues_low) > 0)
        check("Custom threshold works (high threshold passes)", len(issues_high) == 0)


# ── F. SECURITY VALIDATION ───────────────────────────────────────────────────

print("\n=== F. Security Validation ===\n")

if VALIDATOR_OK:
    # Test 18: Safe code passes
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        (tmp / "safe.py").write_text("x = 1 + 2\nprint(x)\n")
        issues = validate_security(str(tmp / "safe.py"))
        check("Safe code passes", len(issues) == 0)

    # Test 19: eval() is flagged
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        (tmp / "eval.py").write_text("result = eval(user_input)\n")
        issues = validate_security(str(tmp / "eval.py"))
        check("eval() is flagged", len(issues) > 0)

    # Test 20: exec() is flagged
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        (tmp / "exec.py").write_text("exec(code)\n")
        issues = validate_security(str(tmp / "exec.py"))
        check("exec() is flagged", len(issues) > 0)

    # Test 21: subprocess with shell=True is flagged
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        (tmp / "subprocess.py").write_text("import subprocess\nsubprocess.run('ls', shell=True)\n")
        issues = validate_security(str(tmp / "subprocess.py"))
        check("shell=True subprocess is flagged", len(issues) > 0)

    # Test 22: pickle.load is flagged
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        (tmp / "pickle.py").write_text("import pickle\npickle.load(f)\n")
        issues = validate_security(str(tmp / "pickle.py"))
        check("pickle.load is flagged", len(issues) > 0)


# ── G. STYLE VALIDATION ──────────────────────────────────────────────────────

print("\n=== G. Style Validation ===\n")

if VALIDATOR_OK:
    # Test 23: PEP 8 compliant code passes
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        (tmp / "pep8.py").write_text(textwrap.dedent("""\
            def add(a: int, b: int) -> int:
                '''Add two numbers.'''
                return a + b
        """))
        issues = validate_style(str(tmp / "pep8.py"))
        check("PEP 8 compliant code passes", len(issues) == 0)

    # Test 24: Long lines are flagged
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        (tmp / "long_line.py").write_text("x = " + "a" * 100 + "\n")
        issues = validate_style(str(tmp / "long_line.py"), max_line_length=80)
        check("Long lines are flagged", len(issues) > 0)

    # Test 25: Missing whitespace around operators
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        (tmp / "no_space.py").write_text("x=1+2\n")
        issues = validate_style(str(tmp / "no_space.py"))
        check("Missing whitespace is flagged", len(issues) > 0)


# ── H. CONFIG VALIDATION ─────────────────────────────────────────────────────

print("\n=== H. Config Validation ===\n")

if VALIDATOR_OK:
    # Test 26: Valid config passes
    valid_config = {
        "max_complexity": 10,
        "max_line_length": 100,
        "require_docstrings": True,
        "require_types": False,
        "security_checks": True,
    }
    check("Valid config is accepted", validate_config(valid_config))

    # Test 27: Invalid config is rejected
    invalid_config = {
        "max_complexity": -1,  # negative
        "require_docstrings": "yes",  # wrong type
    }
    check("Invalid config is rejected", not validate_config(invalid_config))

    # Test 28: Missing required keys
    partial_config = {"max_complexity": 10}
    check("Partial config is accepted (uses defaults)", validate_config(partial_config))


# ── I. MULTI-FILE VALIDATION ─────────────────────────────────────────────────

print("\n=== I. Multi-File Validation ===\n")

if VALIDATOR_OK:
    # Test 29: Multiple files validated together
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        (tmp / "a.py").write_text("x = 1\n")
        (tmp / "b.py").write_text("y = 2\n")
        issues = validate_all([str(tmp / "a.py"), str(tmp / "b.py")])
        check("Multiple files validated", len(issues) == 0)

    # Test 30: Multi-file with errors
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        (tmp / "good.py").write_text("x = 1\n")
        (tmp / "bad.py").write_text("def f(\n")  # syntax error
        issues = validate_all([str(tmp / "good.py"), str(tmp / "bad.py")])
        check("Multi-file with errors detected", len(issues) > 0)


# ── J. PASSING CODE ──────────────────────────────────────────────────────────

print("\n=== J. Passing Code (Full Pipeline) ===\n")

if VALIDATOR_OK:
    # Test 31: Clean code passes all checks
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        (tmp / "clean.py").write_text(textwrap.dedent("""\
            '''A clean module.'''

            def add(a: int, b: int) -> int:
                '''Add two numbers.'''
                return a + b

            class Calculator:
                '''A calculator class.'''

                def __init__(self):
                    '''Initialize.'''
                    self.value = 0

                def set_value(self, value: int) -> None:
                    '''Set the value.'''
                    self.value = value

                def get_value(self) -> int:
                    '''Get the value.'''
                    return self.value
        """))
        issues = validate_all([str(tmp / "clean.py")])
        check("Clean code passes all checks", len(issues) == 0)

    # Test 32: Validator class instantiation
    validator = Validator()
    check("Validator class can be instantiated", validator is not None)

    # Test 33: Validator validate method
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        (tmp / "test.py").write_text("x = 1\n")
        issues = validator.validate(str(tmp / "test.py"))
        check("Validator.validate() works", isinstance(issues, list))


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
