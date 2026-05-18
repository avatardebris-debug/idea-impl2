"""tests for code_reviewer."""
from unittest.mock import patch
from code_reviewer.reviewer import _fallback_review, analyze_diff, format_markdown

_DIFF = """
diff --git a/main.py b/main.py
index e69de29..d95f3ad 100644
--- a/main.py
+++ b/main.py
@@ -0,0 +1,2 @@
+def test():
+    pass
"""

def test_fallback_review():
    res = _fallback_review(_DIFF)
    assert res["files"][0]["filename"] == "main.py"

def test_analyze_diff_fallback_on_failure():
    with patch("code_reviewer.reviewer._call_ollama", return_value="invalid json"):
        res = analyze_diff(_DIFF)
    assert res["files"][0]["filename"] == "main.py"

def test_format_markdown():
    data = _fallback_review(_DIFF)
    md = format_markdown(data)
    assert "# 🔎 Code Review Summary" in md
    assert "main.py" in md
