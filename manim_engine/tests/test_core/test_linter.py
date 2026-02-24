"""Unit tests for Linter and LintIssue."""
from __future__ import annotations

import sys
from unittest.mock import patch

import pytest

pycodestyle = pytest.importorskip("pycodestyle")

from core.services.linter import Linter, LintIssue  # noqa: E402


# ---------------------------------------------------------------------------
# LintIssue
# ---------------------------------------------------------------------------

def test_lint_issue_str():
    issue = LintIssue(line=3, col=1, code="W291", message="trailing whitespace")
    assert str(issue) == "Line 3:1 W291 trailing whitespace"


# ---------------------------------------------------------------------------
# Linter.lint
# ---------------------------------------------------------------------------

def test_clean_code_returns_empty():
    code = "x = 1\ny = 2\n"
    assert Linter.lint(code) == []


def test_empty_code_returns_empty():
    assert Linter.lint("") == []
    assert Linter.lint("   \n  ") == []


def test_detects_trailing_whitespace():
    code = "x = 1   \n"
    issues = Linter.lint(code)
    codes = [i.code for i in issues]
    assert any(c in ("W291", "W293") for c in codes)


def test_detects_missing_blank_lines():
    code = "class Foo:\n    pass\nclass Bar:\n    pass\n"
    issues = Linter.lint(code)
    codes = [i.code for i in issues]
    assert "E302" in codes


def test_results_sorted_by_line():
    # Multiple issues — ensure ordering
    code = "x=1\ny=2\nz=3\n"
    issues = Linter.lint(code)
    lines = [i.line for i in issues]
    assert lines == sorted(lines)


def test_e501_ignored():
    long_line = "x = " + "a" * 200 + "\n"
    issues = Linter.lint(long_line)
    assert all(i.code != "E501" for i in issues)


def test_absent_pycodestyle_returns_empty(monkeypatch):
    """Simulate pycodestyle not installed — should return []."""
    import builtins
    real_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "pycodestyle":
            raise ImportError("no module")
        return real_import(name, *args, **kwargs)

    # Remove cached module so the lazy import inside lint() is re-evaluated
    saved = sys.modules.pop("pycodestyle", None)
    try:
        with patch("builtins.__import__", side_effect=mock_import):
            result = Linter.lint("x=1\n")
        assert result == []
    finally:
        if saved is not None:
            sys.modules["pycodestyle"] = saved


# ---------------------------------------------------------------------------
# Linter.fix
# ---------------------------------------------------------------------------

def test_fix_repairs_spacing():
    pytest.importorskip("autopep8")
    code = "x=1\n"
    fixed = Linter.fix(code)
    assert "x = 1" in fixed


def test_fix_empty_returns_empty():
    pytest.importorskip("autopep8")
    assert Linter.fix("") == ""
    assert Linter.fix("   ") == "   "


def test_absent_autopep8_returns_original(monkeypatch):
    """Simulate autopep8 not installed — should return original code."""
    import builtins
    real_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "autopep8":
            raise ImportError("no module")
        return real_import(name, *args, **kwargs)

    saved = sys.modules.pop("autopep8", None)
    try:
        with patch("builtins.__import__", side_effect=mock_import):
            code = "x=1\n"
            result = Linter.fix(code)
        assert result == code
    finally:
        if saved is not None:
            sys.modules["autopep8"] = saved


def test_fix_then_lint_clean():
    """After autopep8 fix, pycodestyle should find no issues (excluding E501)."""
    pytest.importorskip("autopep8")
    code = "x=1\ny =2\n"
    fixed = Linter.fix(code)
    issues = Linter.lint(fixed)
    assert issues == [], f"Remaining issues after fix: {issues}"
