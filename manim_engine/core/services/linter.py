"""Linting service using pycodestyle for style checks and autopep8 for auto-fix."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class LintIssue:
    line: int
    col: int
    code: str
    message: str

    def __str__(self) -> str:
        return f"Line {self.line}:{self.col} {self.code} {self.message}"


class Linter:
    """Wraps pycodestyle and autopep8 for in-memory code linting and fixing."""

    _IGNORED_CODES = ("E501",)  # long lines are common in Manim

    @staticmethod
    def lint(code: str) -> list[LintIssue]:
        """Run pycodestyle on a code string. Returns [] if pycodestyle absent.

        Args:
            code: Python source code as a string.

        Returns:
            Sorted list of LintIssue ordered by (line, col).
        """
        if not code.strip():
            return []
        try:
            import pycodestyle
        except ImportError:
            return []

        issues: list[LintIssue] = []

        class _Report(pycodestyle.BaseReport):
            def error(self, line_number, offset, text, check):
                issues.append(LintIssue(line_number, offset + 1, text[:4], text[5:]))
                return super().error(line_number, offset, text, check)

        sg = pycodestyle.StyleGuide(
            reporter=_Report,
            ignore=Linter._IGNORED_CODES,
            show_source=False,
            show_pep8=False,
        )
        sg.input_file("<string>", lines=[line + "\n" for line in code.splitlines()])
        return sorted(issues, key=lambda i: (i.line, i.col))

    @staticmethod
    def fix(code: str) -> str:
        """Run autopep8 on a code string. Returns original if autopep8 absent.

        Args:
            code: Python source code as a string.

        Returns:
            Fixed source code, or original on failure.
        """
        if not code.strip():
            return code
        try:
            import autopep8
        except ImportError:
            return code
        try:
            return autopep8.fix_code(
                code,
                options={"ignore": list(Linter._IGNORED_CODES), "max_line_length": 120},
            )
        except Exception:
            return code
