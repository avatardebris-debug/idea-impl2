"""Tests for the rebuilt diff summarizer."""

import pytest
from code_review_diff_summarizer.summarizer import (
    summarize_diff, generate_markdown_briefing,
    DiffSummary, FileSummary, RiskLevel,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SIMPLE_DIFF = """\
diff --git a/auth/login.py b/auth/login.py
index abc1234..def5678 100644
--- a/auth/login.py
+++ b/auth/login.py
@@ -10,6 +10,10 @@ def authenticate(user, password):
+    if not user:
+        raise ValueError("no user")
+    token = generate_token(user)
+    return token
-    return False
"""

RENAME_DIFF = """\
diff --git a/old_name.py b/new_name.py
similarity index 95%
rename from old_name.py
rename to new_name.py
index abc1234..def5678 100644
--- a/old_name.py
+++ b/new_name.py
@@ -1,2 +1,3 @@ class Foo:
+    pass
"""

NEW_FILE_DIFF = """\
diff --git a/utils/helper.py b/utils/helper.py
new file mode 100644
index 0000000..abc1234
--- /dev/null
+++ b/utils/helper.py
@@ -0,0 +1,5 @@
+def helper():
+    pass
"""

SENSITIVE_DIFF = """\
diff --git a/.env b/.env
index abc1234..def5678 100644
--- a/.env
+++ b/.env
@@ -1,1 +1,2 @@
+SECRET_KEY=newvalue
"""

DELETED_FILE_DIFF = """\
diff --git a/old_module.py b/old_module.py
deleted file mode 100644
index abc1234..0000000
--- a/old_module.py
+++ /dev/null
@@ -1,3 +0,0 @@
-def foo():
-    pass
"""


# ---------------------------------------------------------------------------
# Basic parsing
# ---------------------------------------------------------------------------

def test_basic_file_count():
    summary = summarize_diff(SIMPLE_DIFF)
    assert summary.files_changed == 1
    assert summary.files[0].path == "auth/login.py"


def test_addition_deletion_counts():
    summary = summarize_diff(SIMPLE_DIFF)
    f = summary.files[0]
    assert f.additions == 4
    assert f.deletions == 1
    assert f.net_delta == 3


def test_total_stats():
    summary = summarize_diff(SIMPLE_DIFF)
    assert summary.total_additions == 4
    assert summary.total_deletions == 1


# ---------------------------------------------------------------------------
# Hunk-level function attribution
# ---------------------------------------------------------------------------

def test_hunk_context_captured():
    summary = summarize_diff(SIMPLE_DIFF)
    f = summary.files[0]
    assert len(f.hunks) == 1
    # The hunk context after @@ should contain "def authenticate..."
    assert "authenticate" in f.hunks[0].context


# ---------------------------------------------------------------------------
# New / deleted / renamed detection
# ---------------------------------------------------------------------------

def test_new_file_detected():
    summary = summarize_diff(NEW_FILE_DIFF)
    f = summary.files[0]
    assert f.is_new is True
    assert f.is_deleted is False


def test_deleted_file_detected():
    summary = summarize_diff(DELETED_FILE_DIFF)
    f = summary.files[0]
    assert f.is_deleted is True


# ---------------------------------------------------------------------------
# Risk flags
# ---------------------------------------------------------------------------

def test_sensitive_path_flagged():
    summary = summarize_diff(SENSITIVE_DIFF)
    f = summary.files[0]
    levels = [r.level for r in f.risk_flags]
    assert RiskLevel.HIGH in levels
    # Global flags too
    global_levels = [r.level for r in summary.risk_flags]
    assert RiskLevel.HIGH in global_levels


def test_new_file_no_test_flagged():
    # utils/helper.py is new but no test_helper.py is in the diff
    summary = summarize_diff(NEW_FILE_DIFF)
    f = summary.files[0]
    warn_msgs = [r.message for r in f.risk_flags if r.level == RiskLevel.WARN]
    assert any("no matching test" in m for m in warn_msgs)


def test_deleted_file_flagged():
    summary = summarize_diff(DELETED_FILE_DIFF)
    f = summary.files[0]
    assert any(r.level == RiskLevel.WARN for r in f.risk_flags)


def test_large_hunk_flagged():
    big_additions = "\n".join(f"+    line_{i} = True" for i in range(60))
    diff = f"""\
diff --git a/module.py b/module.py
--- a/module.py
+++ b/module.py
@@ -1,1 +1,61 @@ def big_function():
{big_additions}
"""
    summary = summarize_diff(diff)
    f = summary.files[0]
    warn_msgs = [r.message for r in f.risk_flags]
    assert any("Large hunk" in m for m in warn_msgs)


# ---------------------------------------------------------------------------
# as_dict()
# ---------------------------------------------------------------------------

def test_as_dict_structure():
    summary = summarize_diff(SIMPLE_DIFF)
    d = summary.as_dict()
    assert "files_changed" in d
    assert "total_additions" in d
    assert "net_delta" in d
    assert isinstance(d["files"], list)
    assert "changed_functions" in d["files"][0]


# ---------------------------------------------------------------------------
# Markdown briefing
# ---------------------------------------------------------------------------

def test_markdown_briefing_contains_filename():
    summary = summarize_diff(SIMPLE_DIFF)
    md = generate_markdown_briefing(summary)
    assert "auth/login.py" in md
    assert "# Code Review Briefing" in md


def test_markdown_briefing_shows_risk():
    summary = summarize_diff(SENSITIVE_DIFF)
    md = generate_markdown_briefing(summary)
    assert "🚨" in md or "HIGH" in md


def test_markdown_briefing_shows_functions():
    summary = summarize_diff(SIMPLE_DIFF)
    md = generate_markdown_briefing(summary)
    assert "authenticate" in md


# ---------------------------------------------------------------------------
# Empty diff
# ---------------------------------------------------------------------------

def test_empty_diff():
    summary = summarize_diff("")
    assert summary.files_changed == 0
    assert summary.total_additions == 0
    assert summary.total_deletions == 0
