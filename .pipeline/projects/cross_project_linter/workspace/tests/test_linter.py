"""tests for cross_project_linter."""
import pathlib
from cross_project_linter.linter import check_syntax, check_project_structure, format_report

def test_check_syntax(tmp_path):
    p = tmp_path / "valid.py"
    p.write_text("def foo():\n    pass")
    assert len(check_syntax(p)) == 0
    
    p_err = tmp_path / "invalid.py"
    p_err.write_text("def foo() pass") # syntax error
    errs = check_syntax(p_err)
    assert len(errs) == 1
    assert "SyntaxError" in errs[0].message

def test_check_project_structure(tmp_path):
    errs = check_project_structure(tmp_path)
    assert len(errs) == 2 # missing pyproject.toml and tests dir
    
    (tmp_path / "pyproject.toml").touch()
    (tmp_path / "tests").mkdir()
    
    assert len(check_project_structure(tmp_path)) == 0

def test_format_report():
    assert "✅" in format_report([])
